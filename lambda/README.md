# Amazon Connect API Bridge - Lambda & API Gateway

This directory contains the Lambda function and API Gateway infrastructure
to expose AWS Connect APIs that aren't directly available through existing MCP tools.

## Architecture

```
MCP Tool → HTTP Request → API Gateway → Lambda → AWS Connect API
```

## Supported Operations

### Phone Numbers
- `phone-numbers/search` - Search available phone numbers
- `phone-numbers/claim` - Claim a phone number
- `phone-numbers/release` - Release a phone number
- `phone-numbers/list` - List claimed phone numbers

### Instances
- `instances/list` - List Connect instances
- `instances/describe` - Get instance details
- `instances/update` - Update instance settings

### Queues
- `queues/list` - List queues
- `queues/describe` - Get queue details
- `queues/create` - Create a queue
- `queues/update` - Update a queue
- `queues/delete` - Delete a queue

### Hours of Operation
- `hours-of-operations/list` - List hours of operation
- `hours-of-operations/describe` - Get hours of operation details
- `hours-of-operations/create` - Create hours of operation
- `hours-of-operations/update` - Update hours of operation
- `hours-of-operations/delete` - Delete hours of operation
- `hours-of-operations/list-overrides` - List overrides (holidays)

### Prompts
- `prompts/list` - List custom prompts
- `prompts/describe` - Get prompt details
- `prompts/create` - Create a prompt from S3
- `prompts/delete` - Delete a prompt

## Files

- `connect_api_handler.py` - Main Lambda function handler
- `openapi.yaml` - OpenAPI 3.0 specification
- `requirements.txt` - Python dependencies

## Deployment

### Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform >= 1.0
3. Python 3.11

### Deploy with Terraform

```bash
cd ../terraform

# Initialize
terraform init

# Plan
terraform plan -var="environment=dev"

# Apply
terraform apply -var="environment=prod"

# Get the API endpoint
terraform output api_gateway_endpoint
```

### Environment Variables

Set these environment variables before running MCP tools:

```bash
export CONNECT_API_BRIDGE_URL="https://xxx.execute-api.us-east-1.amazonaws.com/prod"
```

Or in your MCP server configuration.

## API Authentication

The API uses AWS Signature Version 4 (SigV4) authentication.
The MCP tools automatically sign requests using boto3 credentials.

Alternative authentication methods:
- API Key (set up in API Gateway)
- Cognito Authorizer

## Local Testing

### Test Lambda Locally

```python
import json
from connect_api_handler import lambda_handler

# Test event
event = {
    "path": "/connect/phone-numbers/list",
    "httpMethod": "GET",
    "queryStringParameters": {
        "InstanceId": "your-instance-id"
    }
}

context = {}
result = lambda_handler(event, context)
print(json.dumps(result, indent=2))
```

### Test API Endpoints

```bash
# Set your API endpoint
API_URL="https://xxx.execute-api.us-east-1.amazonaws.com/prod"

# List instances
curl "${API_URL}/instances/list"

# List phone numbers
curl "${API_URL}/phone-numbers/list?InstanceId=your-instance-id"

# Search available numbers
curl -X POST "${API_URL}/phone-numbers/search" \
  -H "Content-Type: application/json" \
  -d '{
    "PhoneNumberCountryCode": "US",
    "PhoneNumberType": "TOLL_FREE"
  }'

# Claim a number
curl -X POST "${API_URL}/phone-numbers/claim" \
  -H "Content-Type: application/json" \
  -d '{
    "InstanceId": "your-instance-id",
    "PhoneNumberCountryCode": "US",
    "PhoneNumberType": "TOLL_FREE"
  }'
```

## MCP Tool Examples

### Phone Numbers

```python
# Search for available numbers
result = connect_phone_numbers_search(
    phone_number_country_code="US",
    phone_number_type="TOLL_FREE",
    max_results=10
)

# Claim a specific number
result = connect_phone_numbers_claim(
    instance_id="your-instance-id",
    phone_number="+1-800-555-0123"
)

# List claimed numbers
result = connect_phone_numbers_list(
    instance_id="your-instance-id"
)
```

### Queues

```python
# Create a queue
result = connect_queues_create(
    instance_id="your-instance-id",
    name="Sales Queue",
    hours_of_operation_id="hours-op-id",
    description="Sales team queue",
    max_contacts=100
)

# List queues
result = connect_queues_list(
    instance_id="your-instance-id"
)
```

### Hours of Operation

```python
# Create business hours
config = [
    {
        "Day": "MONDAY",
        "StartTime": {"Hours": 9, "Minutes": 0},
        "EndTime": {"Hours": 17, "Minutes": 0}
    },
    {
        "Day": "TUESDAY",
        "StartTime": {"Hours": 9, "Minutes": 0},
        "EndTime": {"Hours": 17, "Minutes": 0}
    }
    # ... etc
]

result = connect_hours_of_operations_create(
    instance_id="your-instance-id",
    name="Business Hours",
    time_zone="America/New_York",
    config=config
)
```

### Prompts

```python
# Create a prompt from S3 audio file
result = connect_prompts_create(
    instance_id="your-instance-id",
    name="Welcome Message",
    s3_uri="s3://my-bucket/prompts/welcome-message.wav",
    description="Main welcome prompt"
)
```

## Error Handling

All tools return dictionaries with a `status` field:

```python
# Success
{
    "status": "success",
    "phone_numbers": [...],
    "next_token": "..."
}

# Error
{
    "status": "error",
    "error": "Error message",
    "message": "Additional context"
}
```

## Monitoring

- CloudWatch Logs: `/aws/lambda/connect-api-bridge-*`
- API Gateway Metrics: Available in CloudWatch
- Lambda Metrics: Invocations, duration, errors

## Security Considerations

1. **IAM Permissions**: Lambda has least-privilege access to Connect APIs
2. **API Authentication**: Use SigV4, API Keys, or Cognito
3. **Input Validation**: Always validate inputs before API calls
4. **Logging**: Sensitive data is not logged
5. **CORS**: Configured for cross-origin requests

## License

Same as parent project.
