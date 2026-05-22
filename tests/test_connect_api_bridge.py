"""Comprehensive tests for Connect API Bridge Lambda handler."""

import json
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch, MagicMock

import pytest

# Ensure lambda is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "lambda"))

from connect_api_handler import (
    lambda_handler,
    search_available_numbers,
    claim_phone_number,
    release_phone_number,
    list_phone_numbers,
    list_instances,
    describe_instance,
    update_instance,
    list_queues,
    describe_queue,
    create_queue,
    update_queue,
    delete_queue,
    list_hours_of_operations,
    describe_hours_of_operation,
    create_hours_of_operation,
    update_hours_of_operation,
    delete_hours_of_operation,
    list_prompts,
    describe_prompt,
    create_prompt,
    delete_prompt,
)


@pytest.fixture
def mock_connect_client():
    """Set up a mock boto3 connect client."""
    with patch("connect_api_handler.connect_client") as mock_client:
        yield mock_client


@pytest.fixture
def mock_sts_client():
    """Set up a mock boto3 STS client."""
    with patch("connect_api_handler.sts_client") as mock_client:
        mock_client.get_caller_identity.return_value = {"Account": "123456789012"}
        yield mock_client


@pytest.mark.unit
class TestLambdaHandler:
    """Test Lambda handler entry point."""
    
    def test_lambda_handler_list_instances(self, mock_connect_client, mock_sts_client):
        """Test lambda handler for list instances."""
        mock_connect_client.list_instances.return_value = {
            "InstanceSummaryList": [
                {"Id": "inst-123", "Arn": "arn", "InstanceAlias": "test"}
            ]
        }
        
        event = {
            "path": "/instances/list",
            "httpMethod": "GET",
            "queryStringParameters": None
        }
        
        result = lambda_handler(event, {})
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "success"
    
    def test_lambda_handler_invalid_path(self, mock_connect_client, mock_sts_client):
        """Test lambda handler for invalid path."""
        event = {
            "path": "/invalid/path",
            "httpMethod": "GET",
            "queryStringParameters": None
        }
        
        result = lambda_handler(event, {})
        
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert body["status"] == "error"
        assert "Unknown action" in body["error"]
    
    def test_lambda_handler_cors_options(self, mock_connect_client, mock_sts_client):
        """Test lambda handler for CORS preflight."""
        event = {
            "path": "/phone-numbers/list",
            "httpMethod": "OPTIONS",
            "queryStringParameters": None
        }
        
        result = lambda_handler(event, {})
        
        assert result["statusCode"] == 200
        assert result["headers"]["Access-Control-Allow-Origin"] == "*"
    
    def test_lambda_handler_post_with_body(self, mock_connect_client, mock_sts_client):
        """Test lambda handler with POST body."""
        mock_connect_client.list_queues.return_value = {
            "QueueSummaryList": [{"Id": "q-123", "Name": "Test"}]
        }
        
        event = {
            "path": "/queues/list",
            "httpMethod": "POST",
            "body": json.dumps({"InstanceId": "inst-123"})
        }
        
        result = lambda_handler(event, {})
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "success"
    
    def test_lambda_handler_malformed_json(self, mock_connect_client, mock_sts_client):
        """Test lambda handler with malformed JSON body."""
        event = {
            "path": "/queues/list",
            "httpMethod": "POST",
            "body": "{invalid json}"
        }
        
        result = lambda_handler(event, {})
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "error"
        assert "JSON" in body["error"] or "Unexpected token" in body["error"]
    
    def test_lambda_handler_exception_handling(self, mock_connect_client, mock_sts_client):
        """Test lambda handler exception handling."""
        mock_connect_client.list_instances.side_effect = Exception("AWS error")
        
        event = {
            "path": "/instances/list",
            "httpMethod": "GET",
            "queryStringParameters": None
        }
        
        result = lambda_handler(event, {})
        
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "error"
        assert "AWS error" in body["error"]


@pytest.mark.unit
class TestPhoneNumberOperations:
    """Test phone number Lambda operations."""
    
    def test_search_available_numbers_success(self, mock_connect_client):
        """Test searching available numbers."""
        mock_connect_client.search_available_phone_numbers.return_value = {
            "PhoneNumbers": [
                {"PhoneNumber": "+1-800-555-0123", "PhoneNumberCountryCode": "US", "PhoneNumberType": "TOLL_FREE"}
            ],
            "NextToken": None
        }
        
        params = {
            "PhoneNumberCountryCode": "US",
            "PhoneNumberType": "TOLL_FREE"
        }
        
        result = search_available_numbers(params)
        
        assert result["status"] == "success"
        assert len(result["phone_numbers"]) == 1
        assert result["phone_numbers"][0]["phone_number"] == "+1-800-555-0123"
    
    def test_search_available_numbers_with_prefix(self, mock_connect_client):
        """Test searching with prefix filter."""
        mock_connect_client.search_available_phone_numbers.return_value = {
            "PhoneNumbers": [],
            "NextToken": None
        }
        
        params = {
            "PhoneNumberCountryCode": "US",
            "PhoneNumberType": "DID",
            "PhoneNumberPrefix": "+1555"
        }
        
        result = search_available_numbers(params)
        
        mock_connect_client.search_available_phone_numbers.assert_called_once()
        call_kwargs = mock_connect_client.search_available_phone_numbers.call_args[1]
        assert call_kwargs["PhoneNumberPrefix"] == "+1555"
    
    def test_search_available_numbers_error(self, mock_connect_client):
        """Test search error handling."""
        mock_connect_client.search_available_phone_numbers.side_effect = Exception("Search failed")
        
        params = {
            "PhoneNumberCountryCode": "US",
            "PhoneNumberType": "TOLL_FREE"
        }
        
        result = search_available_numbers(params)
        
        assert result["status"] == "error"
        assert "Search failed" in result["error"]
    
    def test_claim_phone_number_specific(self, mock_connect_client):
        """Test claiming a specific phone number."""
        mock_connect_client.claim_phone_number.return_value = {
            "PhoneNumberId": "phone-123",
            "PhoneNumberArn": "arn:aws:connect:us-east-1:123456789012:instance/test/phone-123"
        }
        
        params = {
            "InstanceId": "inst-123",
            "PhoneNumber": "+1-800-555-0123"
        }
        
        result = claim_phone_number(params)
        
        assert result["status"] == "success"
        assert result["phone_number_id"] == "phone-123"
        mock_connect_client.claim_phone_number.assert_called_once()
    
    def test_claim_phone_number_auto_search_and_claim(self, mock_connect_client):
        """Test auto-search and claim when number not specified."""
        mock_connect_client.search_available_phone_numbers.return_value = {
            "PhoneNumbers": [{"PhoneNumber": "+1-800-555-9999", "PhoneNumberCountryCode": "US", "PhoneNumberType": "TOLL_FREE"}]
        }
        mock_connect_client.claim_phone_number.return_value = {
            "PhoneNumberId": "phone-auto",
            "PhoneNumberArn": "arn"
        }
        
        params = {
            "InstanceId": "inst-123",
            "PhoneNumberCountryCode": "US",
            "PhoneNumberType": "TOLL_FREE"
        }
        
        result = claim_phone_number(params)
        
        assert result["status"] == "success"
        mock_connect_client.search_available_phone_numbers.assert_called_once()
        mock_connect_client.claim_phone_number.assert_called_once()
    
    def test_claim_phone_number_no_numbers_available(self, mock_connect_client):
        """Test claim when no numbers available."""
        mock_connect_client.search_available_phone_numbers.return_value = {
            "PhoneNumbers": []
        }
        
        params = {
            "InstanceId": "inst-123",
            "PhoneNumberCountryCode": "US",
            "PhoneNumberType": "TOLL_FREE"
        }
        
        result = claim_phone_number(params)
        
        assert result["status"] == "error"
        assert "No available phone numbers" in result["error"]
    
    def test_release_phone_number_success(self, mock_connect_client):
        """Test releasing a phone number."""
        mock_connect_client.release_phone_number.return_value = {}
        
        params = {
            "InstanceId": "inst-123",
            "PhoneNumberId": "phone-123"
        }
        
        result = release_phone_number(params)
        
        assert result["status"] == "success"
        mock_connect_client.release_phone_number.assert_called_once_with(
            InstanceId="inst-123",
            PhoneNumberId="phone-123"
        )
    
    def test_list_phone_numbers_success(self, mock_connect_client):
        """Test listing phone numbers."""
        mock_connect_client.list_phone_numbers.return_value = {
            "PhoneNumberSummaryList": [
                {
                    "Id": "phone-1",
                    "PhoneNumber": "+1-800-555-0123",
                    "PhoneNumberCountryCode": "US",
                    "PhoneNumberType": "TOLL_FREE"
                }
            ],
            "NextToken": None
        }
        
        params = {"InstanceId": "inst-123"}
        
        result = list_phone_numbers(params)
        
        assert result["status"] == "success"
        assert len(result["phone_numbers"]) == 1
        assert result["phone_numbers"][0]["phone_number"] == "+1-800-555-0123"
    
    def test_list_phone_numbers_with_filters(self, mock_connect_client):
        """Test listing with filters."""
        mock_connect_client.list_phone_numbers.return_value = {
            "PhoneNumberSummaryList": [],
            "NextToken": None
        }
        
        params = {
            "InstanceId": "inst-123",
            "PhoneNumberCountryCodes": ["US", "UK"],
            "PhoneNumberTypes": ["TOLL_FREE"],
            "MaxResults": 10
        }
        
        result = list_phone_numbers(params)
        
        call_kwargs = mock_connect_client.list_phone_numbers.call_args[1]
        assert call_kwargs["PhoneNumberCountryCodes"] == ["US", "UK"]
        assert call_kwargs["PhoneNumberTypes"] == ["TOLL_FREE"]


@pytest.mark.unit
class TestInstanceOperations:
    """Test instance Lambda operations."""
    
    def test_list_instances_success(self, mock_connect_client):
        """Test listing instances."""
        mock_connect_client.list_instances.return_value = {
            "InstanceSummaryList": [
                {
                    "Id": "inst-123",
                    "Arn": "arn:aws:connect:us-east-1:123456789012:instance/inst-123",
                    "IdentityManagementType": "CONNECT_MANAGED",
                    "InstanceAlias": "Test Instance",
                    "InboundCallsEnabled": True,
                    "OutboundCallsEnabled": True
                }
            ]
        }
        
        result = list_instances({})
        
        assert result["status"] == "success"
        assert len(result["instances"]) == 1
        assert result["instances"][0]["instance_alias"] == "Test Instance"
    
    def test_list_instances_with_max_results(self, mock_connect_client):
        """Test list instances with max results."""
        mock_connect_client.list_instances.return_value = {"InstanceSummaryList": []}
        
        result = list_instances({"MaxResults": 10})
        
        mock_connect_client.list_instances.assert_called_once_with(MaxResults=10)
    
    def test_describe_instance_success(self, mock_connect_client):
        """Test describing an instance."""
        mock_connect_client.describe_instance.return_value = {
            "Instance": {
                "Id": "inst-123",
                "Arn": "arn:aws:connect:us-east-1:123456789012:instance/inst-123",
                "InstanceAlias": "Test Instance",
                "InstanceStatus": "ACTIVE",
                "InboundCallsEnabled": True
            }
        }
        
        result = describe_instance({"InstanceId": "inst-123"})
        
        assert result["status"] == "success"
        assert result["instance"]["id"] == "inst-123"
        assert result["instance"]["instance_alias"] == "Test Instance"
    
    def test_describe_instance_error(self, mock_connect_client):
        """Test describe instance error handling."""
        mock_connect_client.describe_instance.side_effect = Exception("Instance not found")
        
        result = describe_instance({"InstanceId": "non-existent"})
        
        assert result["status"] == "error"
        assert "Instance not found" in result["error"]
    
    def test_update_instance_single_attribute(self, mock_connect_client):
        """Test updating single attribute."""
        mock_connect_client.update_instance_attribute.return_value = {}
        
        result = update_instance({
            "InstanceId": "inst-123",
            "InboundCallsEnabled": True
        })
        
        assert result["status"] == "success"
        assert "INBOUND_CALLS" in result["updated_attributes"]
        mock_connect_client.update_instance_attribute.assert_called_once()
    
    def test_update_instance_multiple_attributes(self, mock_connect_client):
        """Test updating multiple attributes."""
        mock_connect_client.update_instance_attribute.return_value = {}
        
        result = update_instance({
            "InstanceId": "inst-123",
            "InboundCallsEnabled": True,
            "OutboundCallsEnabled": True,
            "ContactFlowLogsEnabled": True,
            "ContactLensAnalyticsEnabled": False
        })
        
        assert result["status"] == "success"
        assert len(result["updated_attributes"]) == 4
    
    def test_update_instance_no_attributes(self, mock_connect_client):
        """Test update with no attributes to update."""
        result = update_instance({"InstanceId": "inst-123"})
        
        assert result["status"] == "success"
        assert result["updated_attributes"] == []


@pytest.mark.unit
class TestQueueOperations:
    """Test queue Lambda operations."""
    
    def test_list_queues_success(self, mock_connect_client):
        """Test listing queues."""
        mock_connect_client.list_queues.return_value = {
            "QueueSummaryList": [
                {"Id": "q-123", "Arn": "arn", "Name": "Support", "QueueType": "STANDARD"}
            ]
        }
        
        result = list_queues({"InstanceId": "inst-123"})
        
        assert result["status"] == "success"
        assert len(result["queues"]) == 1
    
    def test_list_queues_with_types_filter(self, mock_connect_client):
        """Test list queues with type filter."""
        mock_connect_client.list_queues.return_value = {"QueueSummaryList": []}
        
        result = list_queues({"InstanceId": "inst-123", "QueueTypes": ["STANDARD"]})
        
        mock_connect_client.list_queues.assert_called_once_with(
            InstanceId="inst-123",
            QueueTypes=["STANDARD"]
        )
    
    def test_describe_queue_success(self, mock_connect_client):
        """Test describing a queue."""
        mock_connect_client.describe_queue.return_value = {
            "Queue": {
                "Id": "q-123",
                "Name": "Support",
                "QueueType": "STANDARD",
                "Status": "ENABLED"
            }
        }
        
        result = describe_queue({"InstanceId": "inst-123", "QueueId": "q-123"})
        
        assert result["status"] == "success"
        assert result["queue"]["name"] == "Support"
    
    def test_create_queue_success(self, mock_connect_client):
        """Test creating a queue."""
        mock_connect_client.create_queue.return_value = {
            "QueueId": "q-new",
            "QueueArn": "arn:aws:connect:us-east-1:123456789012:instance/inst-123/queue/q-new"
        }
        
        result = create_queue({
            "InstanceId": "inst-123",
            "Name": "New Queue",
            "HoursOfOperationId": "hop-123"
        })
        
        assert result["status"] == "success"
        assert result["queue_id"] == "q-new"
    
    def test_create_queue_with_optional_params(self, mock_connect_client):
        """Test creating queue with all optional params."""
        mock_connect_client.create_queue.return_value = {
            "QueueId": "q-new",
            "QueueArn": "arn"
        }
        
        result = create_queue({
            "InstanceId": "inst-123",
            "Name": "New Queue",
            "HoursOfOperationId": "hop-123",
            "Description": "Test",
            "MaxContacts": 100,
            "QuickConnectIds": ["qc-1"],
            "Tags": {"key": "value"}
        })
        
        call_kwargs = mock_connect_client.create_queue.call_args[1]
        assert call_kwargs["Description"] == "Test"
        assert call_kwargs["MaxContacts"] == 100
    
    def test_update_queue_success(self, mock_connect_client):
        """Test updating a queue."""
        mock_connect_client.update_queue.return_value = {}
        mock_connect_client.update_queue_name.return_value = {}
        
        result = update_queue({
            "InstanceId": "inst-123",
            "QueueId": "q-123",
            "HoursOfOperationId": "hop-2"
        })
        
        assert result["status"] == "success"
    
    def test_delete_queue_success(self, mock_connect_client):
        """Test deleting a queue."""
        mock_connect_client.delete_queue.return_value = {}
        
        result = delete_queue({"InstanceId": "inst-123", "QueueId": "q-123"})
        
        assert result["status"] == "success"
        assert "Queue q-123" in result["message"]


@pytest.mark.unit
class TestHoursOperations:
    """Test hours of operation Lambda operations."""
    
    def test_list_hours_of_operations_success(self, mock_connect_client):
        """Test listing hours of operations."""
        mock_connect_client.list_hours_of_operations.return_value = {
            "HoursOfOperationSummaryList": [
                {"Id": "hop-123", "Arn": "arn", "Name": "Business Hours"}
            ]
        }
        
        result = list_hours_of_operations({"InstanceId": "inst-123"})
        
        assert result["status"] == "success"
        assert len(result["hours_of_operations"]) == 1
    
    def test_describe_hours_of_operation_success(self, mock_connect_client):
        """Test describing hours of operation."""
        mock_connect_client.describe_hours_of_operation.return_value = {
            "HoursOfOperation": {
                "Id": "hop-123",
                "Name": "Business Hours",
                "TimeZone": "America/New_York",
                "Config": [{"Day": "MONDAY", "StartTime": {"Hours": 9}, "EndTime": {"Hours": 17}}]
            }
        }
        
        result = describe_hours_of_operation({
            "InstanceId": "inst-123",
            "HoursOfOperationId": "hop-123"
        })
        
        assert result["status"] == "success"
        assert result["hours_of_operation"]["time_zone"] == "America/New_York"
    
    def test_create_hours_of_operation_success(self, mock_connect_client):
        """Test creating hours of operation."""
        mock_connect_client.create_hours_of_operation.return_value = {
            "HoursOfOperationId": "hop-new",
            "HoursOfOperationArn": "arn"
        }
        
        config = [{"Day": "MONDAY", "StartTime": {"Hours": 9, "Minutes": 0}, "EndTime": {"Hours": 17, "Minutes": 0}}]
        
        result = create_hours_of_operation({
            "InstanceId": "inst-123",
            "Name": "Business Hours",
            "TimeZone": "America/New_York",
            "Config": config
        })
        
        assert result["status"] == "success"
    
    def test_update_hours_of_operation_success(self, mock_connect_client):
        """Test updating hours of operation."""
        mock_connect_client.update_hours_of_operation_name.return_value = {}
        
        result = update_hours_of_operation({
            "InstanceId": "inst-123",
            "HoursOfOperationId": "hop-123",
            "Name": "Updated Hours"
        })
        
        assert result["status"] == "success"
    
    def test_delete_hours_of_operation_success(self, mock_connect_client):
        """Test deleting hours of operation."""
        mock_connect_client.delete_hours_of_operation.return_value = {}
        
        result = delete_hours_of_operation({
            "InstanceId": "inst-123",
            "HoursOfOperationId": "hop-123"
        })
        
        assert result["status"] == "success"


@pytest.mark.unit
class TestPromptOperations:
    """Test prompt Lambda operations."""
    
    def test_list_prompts_success(self, mock_connect_client):
        """Test listing prompts."""
        mock_connect_client.list_prompts.return_value = {
            "PromptSummaryList": [
                {"Id": "prompt-123", "Arn": "arn", "Name": "Welcome"}
            ]
        }
        
        result = list_prompts({"InstanceId": "inst-123"})
        
        assert result["status"] == "success"
        assert len(result["prompts"]) == 1
    
    def test_describe_prompt_success(self, mock_connect_client):
        """Test describing a prompt."""
        mock_connect_client.describe_prompt.return_value = {
            "Prompt": {
                "Id": "prompt-123",
                "Name": "Welcome Message",
                "S3Uri": "s3://bucket/prompt.wav"
            }
        }
        
        result = describe_prompt({"InstanceId": "inst-123", "PromptId": "prompt-123"})
        
        assert result["status"] == "success"
        assert result["prompt"]["name"] == "Welcome Message"
    
    def test_create_prompt_success(self, mock_connect_client):
        """Test creating a prompt."""
        mock_connect_client.create_prompt.return_value = {
            "PromptId": "prompt-new",
            "PromptARN": "arn:aws:connect:us-east-1:123456789012:instance/inst-123/prompt-new"
        }
        
        result = create_prompt({
            "InstanceId": "inst-123",
            "Name": "New Prompt",
            "S3Uri": "s3://bucket/prompt.wav",
            "Description": "Test prompt"
        })
        
        assert result["status"] == "success"
        assert result["prompt_id"] == "prompt-new"
    
    def test_delete_prompt_success(self, mock_connect_client):
        """Test deleting a prompt."""
        mock_connect_client.delete_prompt.return_value = {}
        
        result = delete_prompt({"InstanceId": "inst-123", "PromptId": "prompt-123"})
        
        assert result["status"] == "success"


@pytest.mark.unit
class TestConnectApiBridgeModule:
    """Test the connect_api_bridge.py module."""
    
    @patch.dict("os.environ", {"CONNECT_API_BRIDGE_URL": "https://test.execute-api.us-east-1.amazonaws.com/prod"})
    @patch("amazon_connect_mcp.connect_api_bridge.requests")
    @patch("amazon_connect_mcp.connect_api_bridge.boto3.Session")
    def test_get_api_url_from_env(self, mock_session, mock_requests):
        """Test getting API URL from environment."""
        from amazon_connect_mcp.connect_api_bridge import _get_api_url
        
        url = _get_api_url()
        assert url == "https://test.execute-api.us-east-1.amazonaws.com/prod"
    
    @patch.dict("os.environ", {}, clear=True)
    def test_get_api_url_missing(self):
        """Test error when API URL not set."""
        from amazon_connect_mcp.connect_api_bridge import _get_api_url
        
        with pytest.raises(ValueError, match="CONNECT_API_BRIDGE_URL"):
            _get_api_url()
    
    @patch.dict("os.environ", {"CONNECT_API_BRIDGE_URL": "https://test.execute-api.us-east-1.amazonaws.com/prod"})
    @patch("amazon_connect_mcp.connect_api_bridge.requests.get")
    @patch("amazon_connect_mcp.connect_api_bridge.boto3.Session")
    def test_make_get_request_success(self, mock_session, mock_get):
        """Test making GET request."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success", "data": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        from amazon_connect_mcp.connect_api_bridge import _make_get_request
        
        result = _make_get_request("instances/list", {})
        
        assert result["status"] == "success"
        mock_get.assert_called_once()
    
    @patch.dict("os.environ", {"CONNECT_API_BRIDGE_URL": "https://test.execute-api.us-east-1.amazonaws.com/prod"})
    @patch("amazon_connect_mcp.connect_api_bridge.requests.get")
    @patch("amazon_connect_mcp.connect_api_bridge.boto3.Session")
    def test_make_get_request_failure(self, mock_session, mock_get):
        """Test GET request failure handling."""
        mock_get.side_effect = Exception("Network error")
        
        from amazon_connect_mcp.connect_api_bridge import _make_get_request
        
        result = _make_get_request("instances/list", {})
        
        assert result["status"] == "error"
        assert "Network error" in result["error"]
    
    @patch.dict("os.environ", {"CONNECT_API_BRIDGE_URL": "https://test.execute-api.us-east-1.amazonaws.com/prod"})
    @patch("amazon_connect_mcp.connect_api_bridge.requests.post")
    @patch("amazon_connect_mcp.connect_api_bridge.boto3.Session")
    def test_make_post_request_success(self, mock_session, mock_post):
        """Test making POST request."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success", "created": True}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        from amazon_connect_mcp.connect_api_bridge import _make_post_request
        
        result = _make_post_request("queues/create", {"InstanceId": "inst-123", "Name": "Test"})
        
        assert result["status"] == "success"
        mock_post.assert_called_once()
