# =============================================================================
# AWS Connect API Bridge Infrastructure
# =============================================================================
# This Terraform configuration deploys:
# - Lambda function to proxy Connect API calls
# - API Gateway REST API
# - IAM roles and policies
# - CloudWatch log groups
# =============================================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# =============================================================================
# Variables
# =============================================================================

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "connect-api-bridge"
}

variable "lambda_runtime" {
  description = "Python runtime version for Lambda"
  type        = string
  default     = "python3.11"
}

variable "lambda_memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

# =============================================================================
# Data Sources
# =============================================================================

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# =============================================================================
# IAM Role for Lambda
# =============================================================================

resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy-${var.environment}"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/*"
      },
      {
        Effect = "Allow"
        Action = [
          "connect:ListPhoneNumbers",
          "connect:DescribePhoneNumber",
          "connect:ClaimPhoneNumber",
          "connect:ReleasePhoneNumber",
          "connect:SearchAvailablePhoneNumbers",
          "connect:ListInstances",
          "connect:DescribeInstance",
          "connect:UpdateInstanceAttribute",
          "connect:ListQueues",
          "connect:DescribeQueue",
          "connect:CreateQueue",
          "connect:UpdateQueue",
          "connect:UpdateQueueName",
          "connect:DeleteQueue",
          "connect:ListHoursOfOperations",
          "connect:DescribeHoursOfOperation",
          "connect:CreateHoursOfOperation",
          "connect:UpdateHoursOfOperation",
          "connect:UpdateHoursOfOperationConfig",
          "connect:DeleteHoursOfOperation",
          "connect:ListHoursOfOperationOverrides",
          "connect:ListPrompts",
          "connect:DescribePrompt",
          "connect:CreatePrompt",
          "connect:DeletePrompt",
          "connect:TagResource",
          "connect:UntagResource"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sts:GetCallerIdentity"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach the basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# =============================================================================
# Lambda Function
# =============================================================================

# Package the Lambda function
data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda_function.zip"

  source {
    filename = "connect_api_handler.py"
    content  = file("${path.module}/connect_api_handler.py")
  }
}

resource "aws_lambda_function" "connect_api" {
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  function_name = "${var.project_name}-${var.environment}"
  role          = aws_iam_role.lambda_role.arn
  handler       = "connect_api_handler.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  environment {
    variables = {
      ENVIRONMENT = var.environment
      LOG_LEVEL   = "INFO"
    }
  }

  tags = {
    Name = "${var.project_name}-lambda"
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_policy
  ]
}

# =============================================================================
# CloudWatch Log Group for Lambda
# =============================================================================

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.connect_api.function_name}"
  retention_in_days = var.log_retention_days
}

# =============================================================================
# API Gateway REST API
# =============================================================================

resource "aws_api_gateway_rest_api" "connect_api" {
  name        = "${var.project_name}-api-${var.environment}"
  description = "API Gateway for Amazon Connect API Bridge"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

# =============================================================================
# API Gateway Resources and Methods - Phone Numbers
# =============================================================================

# /phone-numbers
resource "aws_api_gateway_resource" "phone_numbers" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_rest_api.connect_api.root_resource_id
  path_part   = "phone-numbers"
}

resource "aws_api_gateway_resource" "phone_numbers_search" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.phone_numbers.id
  path_part   = "search"
}

resource "aws_api_gateway_resource" "phone_numbers_claim" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.phone_numbers.id
  path_part   = "claim"
}

resource "aws_api_gateway_resource" "phone_numbers_release" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.phone_numbers.id
  path_part   = "release"
}

resource "aws_api_gateway_resource" "phone_numbers_list" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.phone_numbers.id
  path_part   = "list"
}

# =============================================================================
# API Gateway Resources and Methods - Instances
# =============================================================================

resource "aws_api_gateway_resource" "instances" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_rest_api.connect_api.root_resource_id
  path_part   = "instances"
}

resource "aws_api_gateway_resource" "instances_list" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.instances.id
  path_part   = "list"
}

resource "aws_api_gateway_resource" "instances_describe" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.instances.id
  path_part   = "describe"
}

resource "aws_api_gateway_resource" "instances_update" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.instances.id
  path_part   = "update"
}

# =============================================================================
# API Gateway Resources and Methods - Queues
# =============================================================================

resource "aws_api_gateway_resource" "queues" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_rest_api.connect_api.root_resource_id
  path_part   = "queues"
}

resource "aws_api_gateway_resource" "queues_list" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.queues.id
  path_part   = "list"
}

resource "aws_api_gateway_resource" "queues_describe" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.queues.id
  path_part   = "describe"
}

resource "aws_api_gateway_resource" "queues_create" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.queues.id
  path_part   = "create"
}

resource "aws_api_gateway_resource" "queues_update" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.queues.id
  path_part   = "update"
}

resource "aws_api_gateway_resource" "queues_delete" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.queues.id
  path_part   = "delete"
}

# =============================================================================
# API Gateway Resources and Methods - Hours of Operation
# =============================================================================

resource "aws_api_gateway_resource" "hours_of_operations" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_rest_api.connect_api.root_resource_id
  path_part   = "hours-of-operations"
}

resource "aws_api_gateway_resource" "hours_of_operations_list" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.hours_of_operations.id
  path_part   = "list"
}

resource "aws_api_gateway_resource" "hours_of_operations_describe" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.hours_of_operations.id
  path_part   = "describe"
}

resource "aws_api_gateway_resource" "hours_of_operations_create" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.hours_of_operations.id
  path_part   = "create"
}

resource "aws_api_gateway_resource" "hours_of_operations_update" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.hours_of_operations.id
  path_part   = "update"
}

resource "aws_api_gateway_resource" "hours_of_operations_delete" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.hours_of_operations.id
  path_part   = "delete"
}

resource "aws_api_gateway_resource" "hours_of_operations_list_overrides" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.hours_of_operations.id
  path_part   = "list-overrides"
}

# =============================================================================
# API Gateway Resources and Methods - Prompts
# =============================================================================

resource "aws_api_gateway_resource" "prompts" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_rest_api.connect_api.root_resource_id
  path_part   = "prompts"
}

resource "aws_api_gateway_resource" "prompts_list" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.prompts.id
  path_part   = "list"
}

resource "aws_api_gateway_resource" "prompts_describe" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.prompts.id
  path_part   = "describe"
}

resource "aws_api_gateway_resource" "prompts_create" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.prompts.id
  path_part   = "create"
}

resource "aws_api_gateway_resource" "prompts_delete" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  parent_id   = aws_api_gateway_resource.prompts.id
  path_part   = "delete"
}

# =============================================================================
# Lambda Integration
# =============================================================================

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.connect_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.connect_api.execution_arn}/*/*"
}

# =============================================================================
# Request/Response Models and Method Settings
# =============================================================================

# Common request template for body parameters
locals {
  request_template_get = <<-EOT
    {
      "body" : $input.json('$'),
      "headers" : {
        #foreach($header in $input.params().header.keySet())
          "$header" : "$util.escapeJavaScript($input.params().header.get($header))"
          #if($foreach.hasNext),#end
        #end
      },
      "method" : "$context.httpMethod",
      "params" : {
        #foreach($param in $input.params().path.keySet())
          "$param" : "$util.escapeJavaScript($input.params().path.get($param))"
          #if($foreach.hasNext),#end
        #end
      },
      "query" : {
        #foreach($queryParam in $input.params().querystring.keySet())
          "$queryParam" : "$util.escapeJavaScript($input.params().querystring.get($queryParam))"
          #if($foreach.hasNext),#end
        #end
      }
    }
  EOT

  request_template_post = <<-EOT
    {
      "body" : $input.json('$'),
      "headers" : {
        #foreach($header in $input.params().header.keySet())
          "$header" : "$util.escapeJavaScript($input.params().header.get($header))"
          #if($foreach.hasNext),#end
        #end
      },
      "method" : "$context.httpMethod",
      "params" : {
        #foreach($param in $input.params().path.keySet())
          "$param" : "$util.escapeJavaScript($input.params().path.get($param))"
          #if($foreach.hasNext),#end
        #end
      },
      "query" : {
        #foreach($queryParam in $input.params().querystring.keySet())
          "$queryParam" : "$util.escapeJavaScript($input.params().querystring.get($queryParam))"
          #if($foreach.hasNext),#end
        #end
      }
    }
  EOT
}

# Module for API Gateway methods
module "api_methods" {
  source = "./modules/api-method"

  rest_api_id              = aws_api_gateway_rest_api.connect_api.id
  root_resource_id         = aws_api_gateway_rest_api.connect_api.root_resource_id
  lambda_invoke_arn        = aws_lambda_function.connect_api.invoke_arn
  lambda_function_name     = aws_lambda_function.connect_api.function_name
  request_template_get     = local.request_template_get
  request_template_post    = local.request_template_post

  endpoints = {
    # Phone Numbers
    phone-numbers_search = {
      resource = aws_api_gateway_resource.phone_numbers_search.id
      method   = "POST"
    }
    phone-numbers_claim = {
      resource = aws_api_gateway_resource.phone_numbers_claim.id
      method   = "POST"
    }
    phone-numbers_release = {
      resource = aws_api_gateway_resource.phone_numbers_release.id
      method   = "POST"
    }
    phone-numbers_list = {
      resource = aws_api_gateway_resource.phone_numbers_list.id
      method   = "GET"
    }

    # Instances
    instances_list = {
      resource = aws_api_gateway_resource.instances_list.id
      method   = "GET"
    }
    instances_describe = {
      resource = aws_api_gateway_resource.instances_describe.id
      method   = "GET"
    }
    instances_update = {
      resource = aws_api_gateway_resource.instances_update.id
      method   = "POST"
    }

    # Queues
    queues_list = {
      resource = aws_api_gateway_resource.queues_list.id
      method   = "GET"
    }
    queues_describe = {
      resource = aws_api_gateway_resource.queues_describe.id
      method   = "GET"
    }
    queues_create = {
      resource = aws_api_gateway_resource.queues_create.id
      method   = "POST"
    }
    queues_update = {
      resource = aws_api_gateway_resource.queues_update.id
      method   = "POST"
    }
    queues_delete = {
      resource = aws_api_gateway_resource.queues_delete.id
      method   = "POST"
    }

    # Hours of Operation
    hours_of_operations_list = {
      resource = aws_api_gateway_resource.hours_of_operations_list.id
      method   = "GET"
    }
    hours_of_operations_describe = {
      resource = aws_api_gateway_resource.hours_of_operations_describe.id
      method   = "GET"
    }
    hours_of_operations_create = {
      resource = aws_api_gateway_resource.hours_of_operations_create.id
      method   = "POST"
    }
    hours_of_operations_update = {
      resource = aws_api_gateway_resource.hours_of_operations_update.id
      method   = "POST"
    }
    hours_of_operations_delete = {
      resource = aws_api_gateway_resource.hours_of_operations_delete.id
      method   = "POST"
    }
    hours_of_operations_list_overrides = {
      resource = aws_api_gateway_resource.hours_of_operations_list_overrides.id
      method   = "GET"
    }

    # Prompts
    prompts_list = {
      resource = aws_api_gateway_resource.prompts_list.id
      method   = "GET"
    }
    prompts_describe = {
      resource = aws_api_gateway_resource.prompts_describe.id
      method   = "GET"
    }
    prompts_create = {
      resource = aws_api_gateway_resource.prompts_create.id
      method   = "POST"
    }
    prompts_delete = {
      resource = aws_api_gateway_resource.prompts_delete.id
      method   = "POST"
    }
  }
}

# =============================================================================
# API Gateway Deployment
# =============================================================================

resource "aws_api_gateway_deployment" "connect_api" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id

  triggers = {
    redeployment = sha256(jsonencode(aws_api_gateway_rest_api.connect_api.body))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    module.api_methods
  ]
}

resource "aws_api_gateway_stage" "connect_api" {
  deployment_id = aws_api_gateway_deployment.connect_api.id
  rest_api_id   = aws_api_gateway_rest_api.connect_api.id
  stage_name    = var.environment

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_logs.arn
    format          = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      responseLength = "$context.responseLength"
      duration       = "$context.duration"
    })
  }

  depends_on = [
    aws_cloudwatch_log_group.api_gateway_logs
  ]
}

resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.connect_api.id
  stage_name  = aws_api_gateway_stage.connect_api.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled = true
    logging_level   = "INFO"
  }
}

# =============================================================================
# CloudWatch Log Group for API Gateway
# =============================================================================

resource "aws_cloudwatch_log_group" "api_gateway_logs" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}"
  retention_in_days = var.log_retention_days
}

# =============================================================================
# API Gateway Account Settings
# =============================================================================

resource "aws_api_gateway_account" "main" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch.arn
}

resource "aws_iam_role" "api_gateway_cloudwatch" {
  name = "${var.project_name}-api-gateway-cloudwatch-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "api_gateway_cloudwatch" {
  name = "${var.project_name}-api-gateway-cloudwatch-policy-${var.environment}"
  role = aws_iam_role.api_gateway_cloudwatch.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:PutLogEvents",
          "logs:GetLogEvents",
          "logs:FilterLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# =============================================================================
# Outputs
# =============================================================================

output "api_gateway_endpoint" {
  description = "API Gateway endpoint URL"
  value       = "${aws_api_gateway_stage.connect_api.invoke_url}"
}

output "api_gateway_id" {
  description = "API Gateway REST API ID"
  value       = aws_api_gateway_rest_api.connect_api.id
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.connect_api.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.connect_api.arn
}
