#!/usr/bin/env bash
# =============================================================================
# Amazon Connect MCP - One-liner CloudFormation Deploy
# =============================================================================
# Usage:
#   ./deploy.sh [--name my-instance] [--region us-east-1] [--phone TOLL_FREE|DID]
#
# This script deploys the full Amazon Connect MCP infrastructure in one command:
#   - Amazon Connect instance
#   - Phone number (TOLL_FREE or DID)
#   - Business hours (M-F 9-5)
#   - Default queue
#   - Outbound contact flow (play-prompt)
#   - Lambda + API Gateway bridge
#   - IAM role with all permissions
#
# Prerequisites:
#   - AWS CLI installed and configured
#   - Sufficient IAM permissions (Connect, Lambda, IAM, CloudFormation, API Gateway)
# =============================================================================

set -euo pipefail

# ── Defaults ──
INSTANCE_NAME="${INSTANCE_NAME:-mcp-connect}"
AWS_REGION="${AWS_REGION:-us-east-1}"
PHONE_TYPE="${PHONE_TYPE:-TOLL_FREE}"
STACK_NAME="${STACK_NAME:-amazon-connect-mcp}"
CF_TEMPLATE="${CF_TEMPLATE:-cloudformation/infrastructure.yaml}"
CF_PARAMS=()

# ── Colors ──
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
BOLD='\033[1m'

# ── Banner ──
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║   Amazon Connect MCP - Infrastructure Deploy     ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ── Parse args ──
while [[ $# -gt 0 ]]; do
    case $1 in
        --name|-n)
            INSTANCE_NAME="$2"; shift 2 ;;
        --region|-r)
            AWS_REGION="$2"; shift 2 ;;
        --phone|-p)
            PHONE_TYPE="$2"; shift 2 ;;
        --stack|-s)
            STACK_NAME="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --name, -n   NAME     Connect instance alias (default: mcp-connect)"
            echo "  --region, -r REGION   AWS region (default: us-east-1)"
            echo "  --phone, -p  TYPE     Phone type: TOLL_FREE or DID (default: TOLL_FREE)"
            echo "  --stack, -s  NAME     CloudFormation stack name (default: amazon-connect-mcp)"
            echo "  --destroy            Destroy the stack instead of creating it"
            echo "  --help, -h           Show this help"
            echo ""
            echo "Examples:"
            echo "  $0                                          # Deploy with defaults"
            echo "  $0 --name my-cc --region us-west-2          # Custom name + region"
            echo "  $0 --phone DID --name sales-desk            # Use a DID number"
            echo "  $0 --destroy                                # Tear down everything"
            exit 0 ;;
        --destroy)
            DESTROY=true; shift ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"; exit 1 ;;
    esac
done

# ── Prerequisite checks ──
echo -e "${YELLOW}Checking prerequisites...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE_PATH="$REPO_ROOT/$CF_TEMPLATE"

if ! command -v aws &>/dev/null; then
    echo -e "${RED}ERROR: AWS CLI is not installed. Install it: https://aws.amazon.com/cli/${NC}"
    exit 1
fi

if ! aws sts get-caller-identity &>/dev/null; then
    echo -e "${RED}ERROR: AWS credentials not configured. Run 'aws configure' first.${NC}"
    exit 1
fi

if [ ! -f "$TEMPLATE_PATH" ]; then
    echo -e "${RED}ERROR: CloudFormation template not found: $TEMPLATE_PATH${NC}"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS credentials OK (Account: $ACCOUNT_ID, Region: $AWS_REGION)${NC}"

# ── Validate Phone Type ──
if [ "$PHONE_TYPE" != "TOLL_FREE" ] && [ "$PHONE_TYPE" != "DID" ]; then
    echo -e "${RED}ERROR: Phone type must be TOLL_FREE or DID, got: $PHONE_TYPE${NC}"
    exit 1
fi

# ── CF parameters ──
CF_PARAMS=(
    "ParameterKey=InstanceAlias,ParameterValue=$INSTANCE_NAME"
    "ParameterKey=ApiStageName,ParameterValue=prod"
    "ParameterKey=PhoneType,ParameterValue=$PHONE_TYPE"
)

# ── Destroy mode ──
if [ "${DESTROY:-false}" = "true" ]; then
    echo ""
    echo -e "${YELLOW}${BOLD}Destroying stack '$STACK_NAME' in $AWS_REGION...${NC}"
    aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$AWS_REGION"
    echo -e "${YELLOW}Waiting for stack deletion to complete (this may take 10-15 minutes)...${NC}"
    aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$AWS_REGION"
    echo -e "${GREEN}✓ Stack '$STACK_NAME' destroyed successfully${NC}"
    exit 0
fi

# ── Deploy ──
echo ""
echo -e "${CYAN}Deployment Configuration:${NC}"
echo -e "  Instance Name:  ${BOLD}$INSTANCE_NAME${NC}"
echo -e "  Region:         ${BOLD}$AWS_REGION${NC}"
echo -e "  Phone Type:     ${BOLD}$PHONE_TYPE${NC}"
echo -e "  Stack Name:     ${BOLD}$STACK_NAME${NC}"
echo ""

# Validate template
echo -e "${YELLOW}Validating CloudFormation template...${NC}"
if aws cloudformation validate-template --template-body "file://$TEMPLATE_PATH" --region "$AWS_REGION" &>/dev/null; then
    echo -e "${GREEN}✓ Template is valid${NC}"
else
    echo -e "${RED}ERROR: Template validation failed${NC}"
    exit 1
fi

# Deploy stack
STACK_EXISTS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" --query "Stacks[0].StackStatus" --output text 2>/dev/null || echo "DOES_NOT_EXIST")

if [ "$STACK_EXISTS" = "DOES_NOT_EXIST" ]; then
    echo -e "${YELLOW}Creating new stack '$STACK_NAME'...${NC}"
    aws cloudformation create-stack \
        --stack-name "$STACK_NAME" \
        --template-body "file://$TEMPLATE_PATH" \
        --parameters "${CF_PARAMS[@]}" \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --region "$AWS_REGION" \
        --tags Key=Project,Value=amazon-connect-mcp

    echo -e "${YELLOW}Waiting for stack creation to complete...${NC}"
    echo -e "${YELLOW}(This can take 10-20 minutes for a new Connect instance)${NC}"
    aws cloudformation wait stack-create-complete --stack-name "$STACK_NAME" --region "$AWS_REGION"
    EXIT_CODE=$?
else
    echo -e "${YELLOW}Updating existing stack '$STACK_NAME'...${NC}"
    # Use change-set for update to detect no-changes scenarios
    CHANGE_SET_NAME="mcp-update-$(date +%s)"
    aws cloudformation create-change-set \
        --stack-name "$STACK_NAME" \
        --template-body "file://$TEMPLATE_PATH" \
        --parameters "${CF_PARAMS[@]}" \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --change-set-name "$CHANGE_SET_NAME" \
        --region "$AWS_REGION"

    # Wait for change set to be ready
    sleep 5
    CHANGE_SET_STATUS=$(aws cloudformation describe-change-set \
        --stack-name "$STACK_NAME" \
        --change-set-name "$CHANGE_SET_NAME" \
        --region "$AWS_REGION" \
        --query "Status" --output text 2>/dev/null || echo "FAILED")

    if [ "$CHANGE_SET_STATUS" = "FAILED" ]; then
        REASON=$(aws cloudformation describe-change-set \
            --stack-name "$STACK_NAME" \
            --change-set-name "$CHANGE_SET_NAME" \
            --region "$AWS_REGION" \
            --query "StatusReason" --output text 2>/dev/null || echo "")
        if echo "$REASON" | grep -q "didn't contain changes"; then
            echo -e "${GREEN}✓ No changes detected. Stack is up to date.${NC}"
            aws cloudformation delete-change-set --stack-name "$STACK_NAME" --change-set-name "$CHANGE_SET_NAME" --region "$AWS_REGION" 2>/dev/null || true
        else
            echo -e "${YELLOW}Change set failed: $REASON${NC}"
            echo -e "${YELLOW}Falling back to direct update...${NC}"
            aws cloudformation update-stack \
                --stack-name "$STACK_NAME" \
                --template-body "file://$TEMPLATE_PATH" \
                --parameters "${CF_PARAMS[@]}" \
                --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
                --region "$AWS_REGION" || true
        fi
    else
        aws cloudformation execute-change-set \
            --stack-name "$STACK_NAME" \
            --change-set-name "$CHANGE_SET_NAME" \
            --region "$AWS_REGION"
    fi

    echo -e "${YELLOW}Waiting for stack update to complete...${NC}"
    aws cloudformation wait stack-update-complete --stack-name "$STACK_NAME" --region "$AWS_REGION"
    EXIT_CODE=$?
fi

if [ $EXIT_CODE -ne 0 ]; then
    echo -e "${RED}Stack operation failed. Check CloudFormation console for details.${NC}"
    exit $EXIT_CODE
fi

# ── Output results ──
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║            Deployment Complete!                   ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# Fetch stack outputs
OUTPUTS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" --query "Stacks[0].Outputs" --output json)

INSTANCE_ID=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="ConnectInstanceId") | .OutputValue')
INSTANCE_ARN=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="ConnectInstanceArn") | .OutputValue')
API_URL=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="ApiGatewayUrl") | .OutputValue')
QUEUE_ID=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="DefaultQueueId") | .OutputValue')
FLOW_ID=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="OutboundContactFlowId") | .OutputValue')
HOURS_ID=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="BusinessHoursId") | .OutputValue')

echo -e "${CYAN}Resource Summary:${NC}"
echo -e "  Instance ID:         ${BOLD}$INSTANCE_ID${NC}"
echo -e "  Instance ARN:        ${BOLD}$INSTANCE_ARN${NC}"
echo -e "  API Gateway URL:     ${BOLD}$API_URL${NC}"
echo -e "  Default Queue:       ${BOLD}$(echo "$QUEUE_ID" | awk -F'/' '{print $NF}')${NC}"
echo -e "  Outbound Flow:       ${BOLD}$(echo "$FLOW_ID" | awk -F'/' '{print $NF}')${NC}"
echo -e "  Business Hours:      ${BOLD}$(echo "$HOURS_ID" | awk -F'/' '{print $NF}')${NC}"
echo ""

# Test the API endpoint
echo -e "${YELLOW}Testing API health endpoint...${NC}"
if curl -sf "$API_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API Gateway is reachable and healthy${NC}"
else
    echo -e "${YELLOW}⚠ API endpoint not yet reachable (may take a few minutes to propagate)${NC}"
fi
echo ""

# ── MCP Config Snippet ──
echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}${BOLD}║         MCP Server Configuration                  ║${NC}"
echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Add this to your MCP client configuration (e.g., Claude Desktop, Hermes):${NC}"
echo ""

MCP_CONFIG=$(cat <<EOF
{
  "mcpServers": {
    "amazon-connect": {
      "command": "python",
      "args": ["-m", "amazon_connect_mcp.server"],
      "env": {
        "AWS_REGION": "$AWS_REGION",
        "CONNECT_INSTANCE_ID": "$INSTANCE_ID",
        "CONNECT_API_BRIDGE_URL": "$API_URL"
      }
    }
  }
}
EOF
)

echo "$MCP_CONFIG"
echo ""

# ── Claim phone number ──
echo -e "${YELLOW}Attempting to claim a $PHONE_TYPE phone number...${NC}"
SEARCH_RESULT=$(curl -sf -X POST "$API_URL/phone-numbers/search" \
    -H "Content-Type: application/json" \
    -d "{\"phone_number_country_code\":\"US\",\"phone_number_type\":\"$PHONE_TYPE\",\"max_results\":1,\"region\":\"$AWS_REGION\"}" 2>/dev/null || echo "")

if [ -n "$SEARCH_RESULT" ]; then
    PHONE_NUMBER=$(echo "$SEARCH_RESULT" | jq -r '.phone_numbers[0].phone_number // empty' 2>/dev/null)
    if [ -n "$PHONE_NUMBER" ]; then
        CLAIM_RESULT=$(curl -sf -X POST "$API_URL/phone-numbers/claim" \
            -H "Content-Type: application/json" \
            -d "{\"phone_number\":\"$PHONE_NUMBER\",\"region\":\"$AWS_REGION\"}" 2>/dev/null || echo "")
        if [ -n "$CLAIM_RESULT" ]; then
            CLAIMED_ID=$(echo "$CLAIM_RESULT" | jq -r '.phone_number_id // empty' 2>/dev/null)
            echo -e "${GREEN}✓ Phone number claimed: $PHONE_NUMBER (ID: $CLAIMED_ID)${NC}"
        else
            echo -e "${YELLOW}⚠ Could not claim phone number $PHONE_NUMBER (may require manual claiming)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ No available $PHONE_TYPE numbers found. You can claim one later via API.${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Could not search for phone numbers. API may not be ready yet.${NC}"
fi

echo ""
echo -e "${GREEN}${BOLD}Deployment complete! Your Amazon Connect MCP infrastructure is ready.${NC}"
