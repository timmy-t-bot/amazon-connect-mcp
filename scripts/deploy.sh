#!/bin/bash
# =============================================================================
# Deploy Lambda Function and API Gateway
# =============================================================================
# This script deploys the Connect API Bridge infrastructure using Terraform
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="${ENVIRONMENT:-dev}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --environment|-e)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --region|-r)
            AWS_REGION="$2"
            shift 2
            ;;
        --destroy)
            DESTROY=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--environment dev|staging|prod] [--region us-east-1] [--destroy]"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Amazon Connect API Bridge Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Environment: $ENVIRONMENT"
echo "Region: $AWS_REGION"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: terraform is not installed${NC}"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}Error: AWS credentials not configured${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites met${NC}"
echo ""

# Change to terraform directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/../terraform"

cd "$TERRAFORM_DIR"

# Copy Lambda function to terraform directory
echo -e "${YELLOW}Preparing Lambda function...${NC}"
cp "$SCRIPT_DIR/../lambda/connect_api_handler.py" .

echo -e "${GREEN}✓ Lambda function ready${NC}"
echo ""

# Initialize Terraform
if [ ! -d ".terraform" ]; then
    echo -e "${YELLOW}Initializing Terraform...${NC}"
    terraform init
    echo -e "${GREEN}✓ Terraform initialized${NC}"
    echo ""
fi

if [ "$DESTROY" = true ]; then
    echo -e "${YELLOW}Destroying infrastructure...${NC}"
    terraform destroy -auto-approve \
        -var="environment=$ENVIRONMENT" \
        -var="aws_region=$AWS_REGION"
    echo -e "${GREEN}✓ Infrastructure destroyed${NC}"
else
    # Plan
    echo -e "${YELLOW}Planning Terraform changes...${NC}"
    terraform plan \
        -var="environment=$ENVIRONMENT" \
        -var="aws_region=$AWS_REGION" \
        -out=tfplan
    echo -e "${GREEN}✓ Terraform plan created${NC}"
    echo ""

    # Apply
    echo -e "${YELLOW}Applying Terraform changes...${NC}"
    terraform apply tfplan
    echo ""

    # Get outputs
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}API Gateway Endpoint:${NC}"
    terraform output -raw api_gateway_endpoint
    echo ""
    echo -e "${YELLOW}Lambda Function:${NC}"
    terraform output -raw lambda_function_name
    echo ""
    echo -e "${YELLOW}To configure MCP tools, set:${NC}"
    terraform output -raw api_gateway_endpoint | xargs -I {} echo "export CONNECT_API_BRIDGE_URL={}\"
    echo ""
fi

# Cleanup
cd "$SCRIPT_DIR"
