# Lambda Deployment Guide

This guide explains how to deploy the Lambda API Gateway bridge for the Amazon Connect MCP Server.

## Overview

The Lambda bridge provides extended functionality for Amazon Connect APIs that require:
- Multi-step orchestration
- IAM coordination
- S3 integration
- Long-running workflows

## Prerequisites

- AWS CLI configured
- Terraform >= 1.5
- Python 3.11
- IAM permissions to create Lambda, API Gateway, and S3 resources

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MCP Server                              │
│                   (Python/Boto3)                             │
└──────────────┬────────────────────────────────────────────────┘
               │ HTTP/SigV4
┌──────────────▼────────────────────────────────────────────────┐
│                  API Gateway                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ /phone-numbers/search    │ /phone-numbers/claim        │  │
│  │ /queues/create           │ /queues/update              │  │
│  │ /prompts/create        │ /hours-of-operations/create │  │
│  └────────────────┬───────────────────────────────────────────┘  │
└──────────────────┼──────────────────────────────────────────────┘
                   │
      ┌────────────┼────────────┐
      │            │            │
      ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Lambda  │  │ Lambda  │  │ Lambda  │
│ Phone # │  │ Queue   │  │ Prompt  │
│ Handler │  │ Handler │  │ Handler │
└────┬────┘  └────┬────┘  └────┬────┘
     │            │            │
     ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Connect │  │ Connect │  │ S3      │
│ API     │  │ API     │  │ Bucket  │
└─────────┘  └─────────┘  └─────────┘
```

## Deployment Options

### Option 1: Terraform Deployment (Recommended)

1. **Navigate to terraform directory**:
   ```bash
   cd terraform
   ```

2. **Create terraform.tfvars**:
   ```hcl
   aws_region        = "us-east-1"
   project_name      = "connect-mcp-bridge"
   environment       = "production"
   
   # Optional: Tagging
   tags = {
     Project     = "amazon-connect-mcp"
     Environment = "production"
   }
   ```

3. **Initialize Terraform**:
   ```bash
   terraform init
   ```

4. **Plan the deployment**:
   ```bash
   terraform plan -var-file="terraform.tfvars"
   ```

5. **Apply the configuration**:
   ```bash
   terraform apply -var-file="terraform.tfvars"
   ```

6. **Get the API Gateway URL**:
   ```bash
   terraform output api_gateway_url
   ```

### Option 2: Manual Deployment

1. **Create IAM Role for Lambda**:
   ```bash
   aws iam create-role \
     --role-name connect-mcp-lambda-role \
     --assume-role-policy-document '{
       "Version": "2012-10-17",
       "Statement": [{
         "Effect": "Allow",
         "Principal": {"Service": "lambda.amazonaws.com"},
         "Action": "sts:AssumeRole"
       }]
     }'
   ```

2. **Attach policies**:
   ```bash
   aws iam attach-role-policy \
     --role-name connect-mcp-lambda-role \
     --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
   ```

3. **Create Lambda function**:
   ```bash
   cd lambda
   zip -r function.zip connect_api_handler.py
   
   aws lambda create-function \
     --function-name connect-mcp-api-handler \
     --runtime python3.11 \
     --role arn:aws:iam::YOUR-ACCOUNT:role/connect-mcp-lambda-role \
     --handler connect_api_handler.handler \
     --zip-file fileb://function.zip
   ```

4. **Create API Gateway**:
   ```bash
   aws apigateway create-rest-api \
     --name connect-mcp-bridge \
     --endpoint-configuration REGIONAL
   ```

5. **Create resources and methods** (see terraform for full setup)

## Configuration

### Environment Variables

The Lambda function accepts these environment variables:

| Variable | Required | Description |
|:---------|:---------|:------------|
| `LOG_LEVEL` | No | Lambda log level (DEBUG, INFO, WARN, ERROR) |
| `PROMPT_BUCKET` | Yes | S3 bucket for audio prompts |
| `CONNECT_REGION` | No | AWS region for Connect (defaults to Lambda region) |

### MCP Server Configuration

After deploying the Lambda bridge, configure the MCP server:

```bash
export CONNECT_API_BRIDGE_URL="https://xxxxx.execute-api.us-east-1.amazonaws.com/prod"
export CONNECT_API_BRIDGE_ENABLED=true
export CONNECT_API_BRIDGE_API_KEY="your-api-key"  # If using API keys
```

## API Endpoints

### Phone Numbers

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/phone-numbers/search` | POST | Search available numbers |
| `/phone-numbers/claim` | POST | Claim a phone number |
| `/phone-numbers/release` | POST | Release a phone number |
| `/phone-numbers/list` | GET | List claimed numbers |

### Queues

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/queues/list` | GET | List all queues |
| `/queues/describe` | GET | Get queue details |
| `/queues/create` | POST | Create a queue |
| `/queues/update` | POST | Update a queue |
| `/queues/delete` | POST | Delete a queue |

### Hours of Operation

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/hours-of-operations/list` | GET | List hours configs |
| `/hours-of-operations/describe` | GET | Get hours details |
| `/hours-of-operations/create` | POST | Create hours config |
| `/hours-of-operations/update` | POST | Update hours config |
| `/hours-of-operations/delete` | POST | Delete hours config |

### Prompts

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/prompts/list` | GET | List prompts |
| `/prompts/describe` | GET | Get prompt details |
| `/prompts/create` | POST | Create prompt from S3 |
| `/prompts/delete` | POST | Delete prompt |

### Instances

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/instances/list` | GET | List instances |
| `/instances/describe` | GET | Get instance details |
| `/instances/update` | POST | Update instance settings |

## Security Configuration

### API Gateway Authentication

**Option 1: IAM Authentication (Recommended)**

```yaml
auth:
  type: AWS_IAM
  resource_policy:
    Version: "2012-10-17"
    Statement:
      - Effect: Allow
        Principal:
          AWS: "arn:aws:iam::YOUR-ACCOUNT:root"
        Action: "execute-api:Invoke"
        Resource: "arn:aws:execute-api:*"
```

**Option 2: API Key**

```bash
aws apigateway create-api-key \
  --name mcp-client-key \
  --enabled

aws apigateway create-usage-plan \
  --name mcp-usage-plan \
  --throttle burstLimit=100,rateLimit=50 \
  --quota limit=10000,period=DAY
```

### S3 Bucket Policy

For S3 audio prompts:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "connect.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::YOUR-BUCKET/prompts/*",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "YOUR-ACCOUNT"
        }
      }
    }
  ]
}
```

## Testing

### Test Lambda Function

```bash
aws lambda invoke \
  --function-name connect-mcp-api-handler \
  --payload '{
    "action": "list_instances",
    "resource": "instances"
  }' \
  response.json

cat response.json
```

### Test API Gateway

```bash
# With IAM auth (requires signing)
aws apigateway test-invoke-method \
  --rest-api-id xxxxx \
  --resource-id yyyyy \
  --http-method GET \
  --path-with-query-string /instances/list

# With API key
curl -H "x-api-key: YOUR-API-KEY" \
  https://xxxxx.execute-api.us-east-1.amazonaws.com/prod/instances/list
```

## Monitoring

### CloudWatch Logs

View Lambda logs:
```bash
aws logs tail /aws/lambda/connect-mcp-api-handler --follow
```

### CloudWatch Metrics

Key metrics to monitor:
- Lambda invocations and errors
- API Gateway latency and errors
- Connect API throttling

### Alarms

```hcl
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "connect-mcp-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "Lambda error rate exceeded"
  
  dimensions = {
    FunctionName = aws_lambda_function.api_handler.function_name
  }
}
```

## Troubleshooting

### Lambda Deployment Issues

| Issue | Solution |
|:------|:---------|
| Package too large | Use Lambda layers or exclude unnecessary dependencies |
| Import errors | Ensure all dependencies are included in deployment package |
| Timeout | Increase Lambda timeout (consider async for long operations) |

### API Gateway Issues

| Issue | Solution |
|:------|:---------|
| 403 Forbidden | Check IAM permissions or API key configuration |
| 404 Not Found | Verify resource path and method configuration |
| 502 Bad Gateway | Check Lambda execution logs for errors |

### Connect API Issues

| Issue | Solution |
|:------|:---------|
| Rate limiting | Implement exponential backoff in Lambda |
| Permission denied | Verify Lambda execution role has Connect permissions |
| Resource not found | Check instance ID and resource IDs |

## Cleanup

### Terraform

```bash
cd terraform
terraform destroy
```

### Manual Cleanup

```bash
aws lambda delete-function \
  --function-name connect-mcp-api-handler

aws apigateway delete-rest-api \
  --rest-api-id xxxxx

aws iam delete-role \
  --role-name connect-mcp-lambda-role
```

## References

- [Amazon Connect API Reference](https://docs.aws.amazon.com/connect/latest/APIReference/Welcome.html)
- [Lambda Python Handler](https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html)
- [API Gateway REST API](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-rest-api.html)
