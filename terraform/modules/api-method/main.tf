# =============================================================================
# API Gateway Method Module
# =============================================================================
# Creates API Gateway methods with Lambda integration
# =============================================================================

variable "rest_api_id" {
  description = "REST API ID"
  type        = string
}

variable "root_resource_id" {
  description = "Root resource ID"
  type        = string
}

variable "lambda_invoke_arn" {
  description = "Lambda invoke ARN"
  type        = string
}

variable "lambda_function_name" {
  description = "Lambda function name"
  type        = string
}

variable "request_template_get" {
  description = "VTL request template for GET methods"
  type        = string
}

variable "request_template_post" {
  description = "VTL request template for POST methods"
  type        = string
}

variable "endpoints" {
  description = "Map of endpoint configurations"
  type        = map(object({
    resource = string
    method   = string
  }))
}

locals {
  integration_templates = {
    GET    = var.request_template_get
    POST   = var.request_template_post
    PUT    = var.request_template_post
    DELETE = var.request_template_get
  }
}

# Create OPTIONS method for CORS
resource "aws_api_gateway_method" "cors" {
  for_each = var.endpoints

  rest_api_id   = var.rest_api_id
  resource_id   = each.value.resource
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "cors" {
  for_each = var.endpoints

  rest_api_id = var.rest_api_id
  resource_id = each.value.resource
  http_method = aws_api_gateway_method.cors[each.key].http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration" "cors" {
  for_each = var.endpoints

  rest_api_id = var.rest_api_id
  resource_id = each.value.resource
  http_method = aws_api_gateway_method.cors[each.key].http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_integration_response" "cors" {
  for_each = var.endpoints

  rest_api_id = var.rest_api_id
  resource_id = each.value.resource
  http_method = aws_api_gateway_method.cors[each.key].http_method
  status_code = aws_api_gateway_method_response.cors[each.key].status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# Create actual endpoint methods
resource "aws_api_gateway_method" "endpoint" {
  for_each = var.endpoints

  rest_api_id   = var.rest_api_id
  resource_id   = each.value.resource
  http_method   = each.value.method
  authorization = "NONE"  # Consider using API Key or Cognito for production
  api_key_required = false

  request_parameters = each.value.method == "GET" ? {
    "method.request.querystring.InstanceId" = false
  } : {}
}

resource "aws_api_gateway_method_response" "endpoint" {
  for_each = var.endpoints

  rest_api_id = var.rest_api_id
  resource_id = each.value.resource
  http_method = aws_api_gateway_method.endpoint[each.key].http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# Lambda integration
resource "aws_api_gateway_integration" "endpoint" {
  for_each = var.endpoints

  rest_api_id             = var.rest_api_id
  resource_id             = each.value.resource
  http_method             = aws_api_gateway_method.endpoint[each.key].http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.lambda_invoke_arn
}

# Additional response codes
resource "aws_api_gateway_method_response" "endpoint_400" {
  for_each = var.endpoints

  rest_api_id = var.rest_api_id
  resource_id = each.value.resource
  http_method = aws_api_gateway_method.endpoint[each.key].http_method
  status_code = "400"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_method_response" "endpoint_500" {
  for_each = var.endpoints

  rest_api_id = var.rest_api_id
  resource_id = each.value.resource
  http_method = aws_api_gateway_method.endpoint[each.key].http_method
  status_code = "500"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

output "methods_created" {
  value = { for k, v in aws_api_gateway_method.endpoint : k => v.http_method }
}

output "integrations_created" {
  value = length(aws_api_gateway_integration.endpoint)
}
