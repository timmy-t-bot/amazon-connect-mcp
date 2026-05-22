# Amazon Connect MCP - Terraform Infrastructure

This directory contains Terraform configuration to deploy the Amazon Connect API Bridge.

## Quick Start

```bash
# Deploy everything
./deploy.sh --environment dev

# Deploy to production
./deploy.sh --environment prod

# Destroy resources
./deploy.sh --environment dev --destroy
```

## Configuration

Edit `terraform.tfvars` to customize deployment:

```hcl
aws_region        = "us-west-2"
environment       = "prod"
project_name      = "my-connect-bridge"
lambda_memory_size = 1024
log_retention_days = 90
```

## Files

- `main.tf` - Main Terraform configuration
- `variables.tf` - Input variables (if split)
- `outputs.tf` - Output values (if split)
- `modules/api-method/` - Module for API Gateway methods

## Resources Created

| Resource | Type | Description |
|----------|------|-------------|
| Lambda | Function | Connect API proxy |
| API Gateway | REST API | HTTP endpoints |
| IAM | Role + Policy | Lambda permissions |
| CloudWatch | Log Groups | Logging |

## Lambda Permissions

The Lambda role has these Connect API permissions:

- Phone Numbers: List, Describe, Claim, Release, Search
- Instances: List, Describe, Update Attributes
- Queues: List, Describe, Create, Update, Delete
- Hours of Operation: Full CRUD + Overrides
- Prompts: List, Describe, Create, Delete

## Security

- Least-privilege IAM policies
- CloudWatch logging enabled
- API Gateway metrics
- No hardcoded secrets
