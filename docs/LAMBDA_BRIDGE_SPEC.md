# Lambda/API Gateway Bridge - Implementation Specifications

## Overview

This document details the Lambda functions and API Gateway endpoints required to bridge gaps in direct AWS SDK support for the Amazon Connect MCP Server.

---

## Function 1: connect-instance-manager

**Purpose**: Handle instance lifecycle operations that require IAM coordination

### IAM Role Requirements
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "connect:CreateInstance",
        "connect:DeleteInstance",
        "connect:ReplicateInstance",
        "connect:DescribeInstance",
        "connect:UpdateInstanceAttribute",
        "connect:AssociateInstanceStorageConfig",
        "ds:CreateAlias",
        "ds:DescribeDirectories"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:PutRolePolicy",
        "iam:AttachRolePolicy",
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::*:role/AmazonConnectInstanceRole-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::connect-audio-prompts-*/*"
    }
  ]
}
```

### Handler Code (Python)
```python
# lambda/instance_manager/handler.py
import json
import boto3
import os
from datetime import datetime

def handler(event, context):
    action = event['action']
    
    operations = {
        'create': create_instance,
        'delete': delete_instance,
        'replicate': replicate_instance,
        'describe': describe_instance
    }
    
    if action not in operations:
        return {'statusCode': 400, 'error': f'Unknown action: {action}'}
    
    try:
        result = operations[action](event)
        return {'statusCode': 200, 'body': result}
    except Exception as e:
        return {'statusCode': 500, 'error': str(e)}

def create_instance(params):
    """Create Connect instance with proper IAM setup."""
    client = boto3.client('connect')
    iam = boto3.client('iam')
    
    # 1. Create IAM role for Connect
    role_name = f"AmazonConnectInstanceRole-{params['instance_alias']}"
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "connect.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    try:
        role = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        
        # Attach required policies
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AmazonConnectServiceLinkedRolePolicy"
        )
    except iam.exceptions.EntityAlreadyExistsException:
        role = iam.get_role(RoleName=role_name)
    
    # 2. Create Connect instance
    response = client.create_instance(
        IdentityManagementType='CONNECT_MANAGED',
        InboundCallsEnabled=True,
        OutboundCallsEnabled=True,
        InstanceAlias=params['instance_alias'],
        Tags={
            'CreatedBy': 'MCP-Bridge',
            'CreatedAt': datetime.utcnow().isoformat()
        }
    )
    
    # 3. Enable storage if requested
    if params.get('enable_call_recording'):
        storage_config = {
            'StorageType': 'S3',
            'S3Config': {
                'BucketName': params['recording_bucket'],
                'BucketPrefix': 'recordings/',
                'EncryptionConfig': {
                    'EncryptionType': 'KMS',
                    'KeyId': params['kms_key_id']
                }
            }
        }
        client.associate_instance_storage_config(
            InstanceId=response['Id'],
            ResourceType='CALL_RECORDINGS',
            StorageConfig=storage_config
        )
    
    return {
        'instance_id': response['Id'],
        'arn': response['Arn'],
        'status': 'CREATING',
        'dashboard_url': f"https://{params['instance_alias']}.my.connect.aws/"
    }

def replicate_instance(params):
    """Replicate instance to another region (DR/failover)."""
    client = boto3.client('connect')
    
    # This is a long-running operation
    # Consider using Step Functions for coordination
    
    response = client.replicate_instance(
        InstanceId=params['source_instance_id'],
        ReplicaRegion=params['target_region'],
        ReplicaAlias=params.get('replica_alias', f"{params['source_alias']}-replica")
    )
    
    return {
        'replication_id': response.get('ReplicationId', 'pending'),
        'target_region': params['target_region'],
        'status': 'IN_PROGRESS',
        'estimated_time_minutes': 30
    }

def delete_instance(params):
    """Delete Connect instance and cleanup."""
    client = boto3.client('connect')
    
    # Remove storage configs first
    storage_configs = client.list_instance_storage_configs(
        InstanceId=params['instance_id'],
        ResourceType='CALL_RECORDINGS'
    )
    
    for config in storage_configs.get('StorageConfigs', []):
        client.disassociate_instance_storage_config(
            InstanceId=params['instance_id'],
            ResourceType='CALL_RECORDINGS',
            AssociationId=config['AssociationId']
        )
    
    # Delete instance
    client.delete_instance(
        InstanceId=params['instance_id'],
        DeleteAutoScalingGroup=True,
        DeleteAutoScalingPolicy=True,
        ClientToken=context.aws_request_id
    )
    
    return {'status': 'DELETING', 'instance_id': params['instance_id']}

def describe_instance(params):
    """Get instance details with additional computed fields."""
    client = boto3.client('connect')
    
    response = client.describe_instance(InstanceId=params['instance_id'])
    instance = response['Instance']
    
    # Compute quota usage
    telephone_numbers = client.list_phone_numbers_v2(
        TargetArn=instance['Arn'],
        MaxResults=1
    )
    
    return {
        'instance_id': instance['Id'],
        'arn': instance['Arn'],
        'alias': instance['IdentityManagement']['InstanceAlias'],
        'status': instance['InstanceStatus'],
        'inbound_calls_enabled': instance['InboundCallsEnabled'],
        'outbound_calls_enabled': instance['OutboundCallsEnabled'],
        'region': instance['Arn'].split(':')[3],
        'quota_usage': {
            'claimed_numbers': telephone_numbers.get('ApproximateTotalCount', 0),
            'limit': 100  # Standard limit
        }
    }
```

---

## Function 2: connect-prompt-manager

**Purpose**: Handle prompt creation with SSML support and audio synthesis

### Handler Code (Python)
```python
# lambda/prompt_manager/handler.py
import json
import boto3
import os
import hashlib
from io import BytesIO

def handler(event, context):
    action = event['action']
    
    operations = {
        'create_ssml_prompt': create_ssml_prompt,
        'update_ssml_prompt': update_ssml_prompt,
        'get_prompt_audio': get_prompt_audio,
        'validate_ssml': validate_ssml
    }
    
    if action not in operations:
        return {'statusCode': 400, 'error': f'Unknown action: {action}'}
    
    try:
        result = operations[action](event)
        return {'statusCode': 200, 'body': result}
    except Exception as e:
        return {'statusCode': 500, 'error': str(e)}

def create_ssml_prompt(params):
    """Create a prompt with SSML content."""
    connect = boto3.client('connect')
    s3 = boto3.client('s3')
    polly = boto3.client('polly')
    
    instance_id = params['instance_id']
    prompt_name = params['prompt_name']
    ssml_content = params['ssml_content']
    
    # 1. Generate audio using Polly
    audio_response = polly.synthesize_speech(
        Text=ssml_content,
        TextType='ssml',
        VoiceId=params.get('voice_id', 'Joanna'),
        OutputFormat='mp3'
    )
    
    # 2. Upload to S3
    bucket = os.environ['PROMPT_BUCKET']
    prompt_hash = hashlib.md5(ssml_content.encode()).hexdigest()
    s3_key = f"prompts/{instance_id}/{prompt_name}_{prompt_hash}.mp3"
    
    s3.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=audio_response['AudioStream'].read(),
        ContentType='audio/mpeg',
        Metadata={
            'PromptName': prompt_name,
            'SSMLHash': prompt_hash,
            'VoiceId': params.get('voice_id', 'Joanna')
        }
    )
    
    # 3. Create Connect prompt (pointing to S3 URL via Lambda integration)
    # Note: Connect supports WAV format directly, MP3 requires S3 URL
    
    response = connect.create_prompt(
        InstanceId=instance_id,
        Name=prompt_name,
        S3Uri=f"s3://{bucket}/{s3_key}"
    )
    
    return {
        'prompt_id': response['PromptARN'].split('/')[-1],
        'arn': response['PromptARN'],
        's3_location': f"s3://{bucket}/{s3_key}",
        'content_hash': prompt_hash,
        'voice_id': params.get('voice_id', 'Joanna'),
        'ssml_length': len(ssml_content)
    }

def update_ssml_prompt(params):
    """Update an existing prompt with new SSML."""
    connect = boto3.client('connect')
    
    instance_id = params['instance_id']
    prompt_id = params['prompt_id']
    
    # Delete old prompt
    try:
        connect.delete_prompt(
            InstanceId=instance_id,
            PromptId=prompt_id
        )
    except connect.exceptions.ResourceNotFoundException:
        pass
    
    # Create new prompt (effectively an update)
    return create_ssml_prompt({
        'instance_id': instance_id,
        'prompt_name': params.get('new_name', f"updated_{params['prompt_id']}"),
        'ssml_content': params['ssml_content'],
        'voice_id': params.get('voice_id', 'Joanna')
    })

def get_prompt_audio(params):
    """Get pre-signed URL for prompt audio."""
    s3 = boto3.client('s3')
    
    bucket = os.environ['PROMPT_BUCKET']
    s3_key = params['s3_key']
    
    url = s3.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': bucket,
            'Key': s3_key,
            'ResponseContentType': 'audio/mpeg'
        },
        ExpiresIn=3600
    )
    
    return {
        'url': url,
        'expires_in': 3600,
        'format': 'audio/mpeg'
    }

def validate_ssml(params):
    """Validate SSML syntax."""
    import xml.etree.ElementTree as ET
    
    ssml = params['ssml_content']
    
    # Basic validation
    issues = []
    
    # Check for required root element
    if not ssml.strip().startswith('<speak'):
        issues.append("SSML must start with <speak> element")
    
    # Check for supported elements
    supported_tags = ['speak', 'break', 'emphasis', 'lang', 'phoneme', 
                      'prosody', 'say-as', 'sub', 'voice']
    
    # Attempt parse
    try:
        ET.fromstring(f"<?xml version='1.0' encoding='UTF-8'?>{ssml}")
    except ET.ParseError as e:
        issues.append(f"XML Parse Error: {str(e)}")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'supported_tags': supported_tags
    }
```

---

## Function 3: connect-workflow-manager

**Purpose**: Coordinated multi-step operations with rollback capability

### Handler Code (Python)
```python
# lambda/workflow_manager/handler.py
import json
import boto3
from datetime import datetime

def handler(event, context):
    action = event['action']
    
    operations = {
        'claim_and_associate': claim_and_associate_workflow,
        'create_outbound_flow': create_outbound_flow_workflow,
        'onboard_outbound_campaign': onboard_campaign_workflow,
        'check_workflow_status': check_status,
        'rollback_workflow': rollback
    }
    
    if action not in operations:
        return {'statusCode': 400, 'error': f'Unknown action: {action}'}
    
    try:
        result = operations[action](event)
        return {'statusCode': 200, 'body': result}
    except Exception as e:
        return {'statusCode': 500, 'error': str(e)}

def claim_and_associate_workflow(params):
    """Claim phone number and associate to contact flow."""
    connect = boto3.client('connect')
    
    # Store workflow state for potential rollback
    workflow_id = context.aws_request_id
    steps_completed = []
    
    try:
        # Step 1: Search for available numbers
        if 'target_phone_number' not in params:
            search_response = connect.search_available_phone_numbers(
                InstanceId=params['instance_id'],
                PhoneNumberCountry=params.get('country', 'US'),
                PhoneNumberType=params.get('number_type', 'TOLL_FREE'),
                MaxResults=5
            )
            
            if not search_response['AvailableNumbers']:
                raise Exception("No available phone numbers found")
            
            target_number = search_response['AvailableNumbers'][0]['PhoneNumber']
        else:
            target_number = params['target_phone_number']
        
        steps_completed.append({'step': 'search', 'number': target_number})
        
        # Step 2: Claim the number
        claim_response = connect.claim_phone_number(
            TargetArn=f"arn:aws:connect:{params['region']}:*:instance/{params['instance_id']}",
            PhoneNumber=target_number,
            Tags={
                'WorkflowId': workflow_id,
                'Purpose': params.get('purpose', 'outbound-calling')
            }
        )
        
        phone_number_id = claim_response['PhoneNumberId']
        steps_completed.append({'step': 'claim', 'phone_number_id': phone_number_id})
        
        # Step 3: Associate to contact flow
        if 'contact_flow_id' in params:
            connect.associate_phone_number_contact_flow(
                InstanceId=params['instance_id'],
                PhoneNumberId=phone_number_id,
                ContactFlowId=params['contact_flow_id']
            )
            steps_completed.append({'step': 'associate_flow', 'flow_id': params['contact_flow_id']})
        
        # Store state in DynamoDB for rollback capability
        store_workflow_state(workflow_id, steps_completed)
        
        return {
            'workflow_id': workflow_id,
            'status': 'COMPLETED',
            'phone_number': target_number,
            'phone_number_id': phone_number_id,
            'steps': steps_completed
        }
        
    except Exception as e:
        # Store failed state
        store_workflow_state(workflow_id, steps_completed, error=str(e))
        raise

def create_outbound_flow_workflow(params):
    """Create complete outbound flow with prompts and routing."""
    connect = boto3.client('connect')
    
    workflow_id = context.aws_request_id
    created_resources = []
    
    try:
        # Step 1: Create SSML prompts if provided
        prompt_arns = {}
        if 'prompts' in params:
            lambda_client = boto3.client('lambda')
            for prompt_name, ssml_content in params['prompts'].items():
                response = lambda_client.invoke(
                    FunctionName='connect-prompt-manager',
                    Payload=json.dumps({
                        'action': 'create_ssml_prompt',
                        'instance_id': params['instance_id'],
                        'prompt_name': f"{params['flow_name']}_{prompt_name}",
                        'ssml_content': ssml_content
                    })
                )
                result = json.loads(response['Payload'].read())
                if result.get('statusCode') == 200:
                    prompt_arns[prompt_name] = json.loads(result['body'])
                    created_resources.append({'type': 'prompt', 'id': prompt_arns[prompt_name]['prompt_id']})
        
        # Step 2: Build flow content from template
        flow_content = build_outbound_flow_content(
            params['flow_template'],
            prompt_arns,
            params.get('attributes', {})
        )
        
        # Step 3: Create the flow
        flow_response = connect.create_contact_flow(
            InstanceId=params['instance_id'],
            Name=params['flow_name'],
            Type='CONTACT_FLOW',
            Content=json.dumps(flow_content),
            Description=params.get('description', 'Generated by MCP Workflow'),
            Tags={
                'WorkflowId': workflow_id,
                'Template': params['flow_template']
            }
        )
        
        created_resources.append({
            'type': 'contact_flow',
            'id': flow_response['ContactFlowId'],
            'arn': flow_response['ContactFlowARN']
        })
        
        store_workflow_state(workflow_id, created_resources)
        
        return {
            'workflow_id': workflow_id,
            'status': 'COMPLETED',
            'resources': created_resources,
            'flow_id': flow_response['ContactFlowId'],
            'flow_arn': flow_response['ContactFlowARN']
        }
        
    except Exception as e:
        store_workflow_state(workflow_id, created_resources, error=str(e), failed=True)
        raise

def onboard_campaign_workflow(params):
    """Complete onboarding for outbound campaigns."""
    campaigns = boto3.client('connect-campaigns')
    
    # This is a long-running operation that requires:
    # 1. KMS key grant
    # 2. EventBridge rule creation
    # 3. Amazon S3 bucket setup
    # 4. Connect instance integration
    
    response = campaigns.start_instance_onboarding_job(
        ConnectInstanceId=params['instance_id'],
        EncryptionConfig={
            'Enabled': params.get('encryption_enabled', False),
            'EncryptionType': 'KMS',
            'KeyArn': params.get('kms_key_arn') if params.get('encryption_enabled') else None
        }
    )
    
    return {
        'workflow_id': response['Id'],
        'status': 'IN_PROGRESS',
        'onboarding_job_id': response['Id'],
        'estimated_completion': '10 minutes'
    }

def store_workflow_state(workflow_id, steps, error=None, failed=False):
    """Store workflow state in DynamoDB for recovery/rollback."""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['WORKFLOW_TABLE'])
    
    table.put_item(Item={
        'workflow_id': workflow_id,
        'timestamp': datetime.utcnow().isoformat(),
        'steps': steps,
        'error': error,
        'failed': failed,
        'ttl': int((datetime.utcnow().timestamp() + 86400))  # 24 hour TTL
    })

def check_status(params):
    """Check status of long-running workflow."""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['WORKFLOW_TABLE'])
    
    response = table.get_item(Key={'workflow_id': params['workflow_id']})
    
    if 'Item' not in response:
        return {'statusCode': 404, 'error': 'Workflow not found'}
    
    item = response['Item']
    return {
        'workflow_id': item['workflow_id'],
        'status': 'FAILED' if item['failed'] else 'COMPLETED',
        'steps': item['steps'],
        'error': item.get('error'),
        'timestamp': item['timestamp']
    }

def rollback(params):
    """Rollback a failed workflow."""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['WORKFLOW_TABLE'])
    
    response = table.get_item(Key={'workflow_id': params['workflow_id']})
    
    if 'Item' not in response:
        return {'statusCode': 404, 'error': 'Workflow not found'}
    
    item = response['Item']
    steps = item['steps']
    
    connect = boto3.client('connect')
    
    # Rollback in reverse order
    for step in reversed(steps):
        try:
            if step['type'] == 'contact_flow':
                connect.delete_contact_flow(
                    InstanceId=params['instance_id'],
                    ContactFlowId=step['id']
                )
            elif step['type'] == 'prompt':
                connect.delete_prompt(
                    InstanceId=params['instance_id'],
                    PromptId=step['id']
                )
            elif step['type'] == 'phone_number':
                connect.release_phone_number(
                    InstanceId=params['instance_id'],
                    PhoneNumberId=step['id']
                )
        except Exception as e:
            # Log but continue rollback
            print(f"Error rolling back {step['type']} {step['id']}: {e}")
    
    # Mark as rolled back
    table.update_item(
        Key={'workflow_id': params['workflow_id']},
        UpdateExpression='set rollback_completed = :val',
        ExpressionAttributeValues={':val': True}
    )
    
    return {
        'workflow_id': params['workflow_id'],
        'status': 'ROLLED_BACK',
        'rollback_time': datetime.utcnow().isoformat()
    }

def build_outbound_flow_content(template, prompts, attributes):
    """Build Contact Flow JSON from template."""
    # Template expansion logic (simplified)
    # Full implementation would use Jinja2 or similar
    
    base_actions = [
        {
            "Identifier": "Start",
            "Type": "SetVoice",
            "Parameters": {"VoiceId": attributes.get('voice_id', 'Joanna')},
            "Transitions": {"NextAction": "PlayWelcome"}
        },
        {
            "Identifier": "PlayWelcome",
            "Type": "MessageParticipant",
            "Parameters": {
                "Text": attributes.get('greeting_message', 'Hello')
            },
            "Transitions": {"NextAction": "Disconnect"}
        },
        {
            "Identifier": "Disconnect",
            "Type": "DisconnectParticipant",
            "Parameters": {}
        }
    ]
    
    return {
        "Version": "2019-10-30",
        "StartAction": "Start",
        "Actions": base_actions
    }
```

---

## API Gateway Configuration

### OpenAPI Specification (Partial)

```yaml
openapi: 3.0.1
info:
  title: Amazon Connect MCP Bridge
  version: '1.0'
  description: Lambda bridge for Amazon Connect MCP Server

paths:
  /bridge/health:
    get:
      summary: Health check
      responses:
        '200':
          description: Service is healthy

  /bridge/instance:
    post:
      summary: Instance lifecycle operations
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                action:
                  type: string
                  enum: [create, delete, replicate, describe]
      x-amazon-apigateway-integration:
        uri: arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{instance_manager_arn}/invocations
        httpMethod: POST
        type: aws_proxy

  /bridge/prompt:
    post:
      summary: Prompt management
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                action:
                  type: string
                  enum: [create_ssml_prompt, update_ssml_prompt, get_prompt_audio, validate_ssml]
      x-amazon-apigateway-integration:
        uri: arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{prompt_manager_arn}/invocations
        httpMethod: POST
        type: aws_proxy

  /bridge/workflow:
    post:
      summary: Workflow execution
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                action:
                  type: string
                  enum: [claim_and_associate, create_outbound_flow, onboard_outbound_campaign]
      x-amazon-apigateway-integration:
        uri: arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{workflow_manager_arn}/invocations
        httpMethod: POST
        type: aws_proxy

  /bridge/workflow/{workflowId}:
    get:
      summary: Check workflow status
      parameters:
        - name: workflowId
          in: path
          required: true
          schema:
            type: string
      x-amazon-apigateway-integration:
        uri: arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{workflow_manager_arn}/invocations
        httpMethod: POST
        type: aws_proxy
    delete:
      summary: Rollback workflow
      parameters:
        - name: workflowId
          in: path
          required: true
          schema:
            type: string
      x-amazon-apigateway-integration:
        uri: arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{workflow_manager_arn}/invocations
        httpMethod: POST
        type: aws_proxy
```

---

## Deployment Configuration

### Lambda Environment Variables

| Variable | Function | Description |
|----------|----------|-------------|
| `PROMPT_BUCKET` | prompt-manager | S3 bucket for audio files |
| `WORKFLOW_TABLE` | workflow-manager | DynamoDB table for state |
| `CONNECT_INSTANCE_ROLE_PREFIX` | instance-manager | IAM role prefix |
| `API_GATEWAY_STAGE` | All | API stage name |
| `LOG_LEVEL` | All | DEBUG, INFO, WARN |

### Required S3 Buckets

```
connect-mcp-bridge-{account-id}-{region}/
├── prompts/
│   └── {instance-id}/
│       └── *.mp3
├── recordings/
│   └── {instance-id}/
│       └── *.wav
└── exports/
    └── {workflow-id}/
        └── *.json
```

### Required DynamoDB Tables

```
Table: ConnectMCPTWorkflowState
- workflow_id (PK, String)
- timestamp (String)
- steps (Map)
- error (String, nullable)
- failed (Boolean)
- rollback_completed (Boolean)
- ttl (Number)

GSI: FailedWorkflowsIndex
- failed (partition key)
- timestamp (sort key)
```