# CloudFormation Deployment Guide

This directory contains AWS CloudFormation templates for deploying the Amazon Connect MCP Lambda Bridge.

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
│ Connect │  │ Connect │  │ Connect │
│ API     │  │ API     │  │ API     │
└─────────┘  └─────────┘  └─────────┘
```

## Files

| File | Description |
|------|-------------|
| `lambda-bridge.yaml` | Main CloudFormation template (Lambda + API Gateway + IAM) |
| `deploy.sh` | Deployment script using AWS CLI |
| `README.md` | This file |

## Quick Deploy

```bash
cd cloudformation
./deploy.sh
```

## Manual Deploy

```bash
# 1. Create the CloudFormation stack
aws cloudformation create-stack \
  --stack-name connect-api-bridge \
  --template-body file://lambda-bridge.yaml \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
  --parameters \
    ParameterKey=Environment,ParameterValue=prod

# 2. Wait for completion
aws cloudformation wait stack-create-complete \
  --stack-name connect-api-bridge

# 3. Get the API Gateway URL
aws cloudformation describe-stacks \
  --stack-name connect-api-bridge \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
  --output text
```

## Update Stack

```bash
aws cloudformation update-stack \
  --stack-name connect-api-bridge \
  --template-body file://lambda-bridge.yaml \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND
```

## Delete Stack

```bash
aws cloudformation delete-stack \
  --stack-name connect-api-bridge

aws cloudformation wait stack-delete-complete \
  --stack-name connect-api-bridge
```

## Outputs

| Output | Description |
|--------|-------------|
| `ApiGatewayUrl` | Base URL for API Gateway endpoints |
| `LambdaFunctionArn` | ARN of the Lambda function |
| `LambdaFunctionName` | Name of the Lambda function |

## API Endpoints

Once deployed, the following endpoints are available:

- `GET /phone-numbers/list`
- `POST /phone-numbers/search`
- `POST /phone-numbers/claim`
- `POST /phone-numbers/release`
- `GET /queues/list`
- `POST /queues/create`
- `POST /queues/update`
- `POST /queues/delete`
- `GET /hours-of-operations/list`
- `POST /hours-of-operations/create`
- `POST /hours-of-operations/update`
- `POST /hours-of-operations/delete`
- `GET /prompts/list`
- `POST /prompts/create`
- `POST /prompts/delete`

See [LAMBDA_BRIDGE_SPEC.md](../docs/LAMBDA_BRIDGE_SPEC.md) for detailed API documentation.
