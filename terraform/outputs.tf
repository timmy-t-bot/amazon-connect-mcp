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
