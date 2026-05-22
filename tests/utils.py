"""Test utilities and mock helpers for Amazon Connect MCP tests."""

import json
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import Mock, MagicMock

from botocore.exceptions import ClientError


class MockBoto3Client:
    """Mock boto3 client with configurable responses."""
    
    def __init__(self, service_name: str = "connect"):
        self.service_name = service_name
        self.responses: Dict[str, Any] = {}
        self.errors: Dict[str, Exception] = {}
        self.calls: List[tuple] = []
    
    def add_response(self, method_name: str, response: Any) -> "MockBoto3Client":
        """Add a mock response for a method."""
        self.responses[method_name] = response
        return self
    
    def add_error(self, method_name: str, error: Exception) -> "MockBoto3Client":
        """Add a mock error for a method."""
        self.errors[method_name] = error
        return self
    
    def add_client_error(
        self,
        method_name: str,
        error_code: str = "InternalServiceException",
        error_message: str = "Test error"
    ) -> "MockBoto3Client":
        """Add a botocore ClientError for a method."""
        error = ClientError(
            {"Error": {"Code": error_code, "Message": error_message}},
            method_name
        )
        self.errors[method_name] = error
        return self
    
    def _make_method(self, name: str) -> Callable:
        """Create a mock method."""
        def mock_method(*args, **kwargs) -> Any:
            self.calls.append((name, args, kwargs))
            
            if name in self.errors:
                raise self.errors[name]
            
            return self.responses.get(name, {})
        
        return mock_method
    
    def __getattr__(self, name: str) -> Callable:
        """Return a mock method for any attribute access."""
        return self._make_method(name)


def create_mock_connect_client() -> MockBoto3Client:
    """Create a pre-configured mock Connect client."""
    client = MockBoto3Client("connect")
    
    # Set up default responses for common methods
    client.add_response("list_instances", {
        "InstanceSummaryList": [
            _create_instance_summary("12345678-1234-1234-1234-123456789012")
        ],
        "NextToken": None
    })
    
    client.add_response("describe_instance", {
        "Instance": _create_instance_detail("12345678-1234-1234-1234-123456789012")
    })
    
    client.add_response("create_instance", {
        "Id": "12345678-1234-1234-1234-123456789012",
        "Arn": "arn:aws:connect:us-east-1:123456789012:instance/123456789012",
        "State": "CREATING"
    })
    
    client.add_response("list_contact_flows", {
        "ContactFlowSummaryList": [
            _create_contact_flow_summary("cf-123")
        ],
        "NextToken": None
    })
    
    client.add_response("describe_contact_flow", {
        "ContactFlow": _create_contact_flow_detail("cf-123")
    })
    
    client.add_response("create_contact_flow", {
        "ContactFlowId": "cf-123",
        "ContactFlowArn": "arn:aws:connect:us-east-1:123456789012:instance/test/contact-flow/cf-123"
    })
    
    client.add_response("list_queues", {
        "QueueSummaryList": [
            _create_queue_summary("queue-123")
        ],
        "NextToken": None
    })
    
    client.add_response("describe_queue", {
        "Queue": _create_queue_detail("queue-123")
    })
    
    client.add_response("create_queue", {
        "QueueId": "queue-123",
        "QueueArn": "arn:aws:connect:us-east-1:123456789012:instance/test/queue/queue-123"
    })
    
    client.add_response("list_hours_of_operations", {
        "HoursOfOperationSummaryList": [
            _create_hours_summary("hop-123")
        ],
        "NextToken": None
    })
    
    client.add_response("describe_hours_of_operation", {
        "HoursOfOperation": _create_hours_detail("hop-123")
    })
    
    client.add_response("create_hours_of_operation", {
        "HoursOfOperationId": "hop-123",
        "HoursOfOperationArn": "arn:aws:connect:us-east-1:123456789012:instance/test/operating-hours/hop-123"
    })
    
    client.add_response("list_prompts", {
        "PromptSummaryList": [
            _create_prompt_summary("prompt-123")
        ],
        "NextToken": None
    })
    
    client.add_response("describe_prompt", {
        "Prompt": _create_prompt_detail("prompt-123")
    })
    
    client.add_response("create_prompt", {
        "PromptARN": "arn:aws:connect:us-east-1:123456789012:instance/test/prompt/prompt-123",
        "PromptId": "prompt-123"
    })
    
    client.add_response("list_phone_numbers", {
        "PhoneNumberSummaryList": [
            _create_phone_number_summary("phone-123")
        ],
        "NextToken": None
    })
    
    client.add_response("describe_phone_number", {
        "PhoneNumber": _create_phone_number_detail("phone-123")
    })
    
    client.add_response("search_available_phone_numbers", {
        "PhoneNumbers": [
            {"PhoneNumber": "+1-800-555-0123", "PhoneNumberCountryCode": "US", "PhoneNumberType": "TOLL_FREE"}
        ],
        "NextToken": None
    })
    
    client.add_response("claim_phone_number", {
        "PhoneNumberId": "phone-123",
        "PhoneNumberArn": "arn:aws:connect:us-east-1:123456789012:instance/test/phone-number/phone-123"
    })
    
    return client


def _create_instance_summary(instance_id: str) -> Dict:
    """Create a sample instance summary."""
    return {
        "Id": instance_id,
        "Arn": f"arn:aws:connect:us-east-1:123456789012:instance/{instance_id}",
        "IdentityManagementType": "CONNECT_MANAGED",
        "InstanceAlias": "test-instance",
        "CreatedTime": "2024-01-01T00:00:00.000Z",
        "ServiceRole": "arn:aws:iam::123456789012:role/connect-service-role",
        "InstanceStatus": "ACTIVE",
        "StatusReason": None,
        "InboundCallsEnabled": True,
        "OutboundCallsEnabled": True
    }


def _create_instance_detail(instance_id: str) -> Dict:
    """Create a sample instance detail."""
    return {
        "Id": instance_id,
        "Arn": f"arn:aws:connect:us-east-1:123456789012:instance/{instance_id}",
        "IdentityManagementType": "CONNECT_MANAGED",
        "InstanceAlias": "test-instance",
        "CreatedTime": "2024-01-01T00:00:00.000Z",
        "ServiceRole": "arn:aws:iam::123456789012:role/connect-service-role",
        "InstanceStatus": "ACTIVE",
        "InboundCallsEnabled": True,
        "OutboundCallsEnabled": True
    }


def _create_contact_flow_summary(flow_id: str) -> Dict:
    """Create a sample contact flow summary."""
    return {
        "Id": flow_id,
        "Arn": f"arn:aws:connect:us-east-1:123456789012:instance/test/contact-flow/{flow_id}",
        "Name": "Test Flow",
        "Type": "CONTACT_FLOW",
        "State": "ACTIVE",
        "Description": "Test contact flow",
        "LastModifiedTime": "2024-01-01T00:00:00.000Z",
        "LastModifiedRegion": "us-east-1"
    }


def _create_contact_flow_detail(flow_id: str) -> Dict:
    """Create a sample contact flow detail."""
    return {
        "Id": flow_id,
        "Arn": f"arn:aws:connect:us-east-1:123456789012:instance/test/contact-flow/{flow_id}",
        "Name": "Test Flow",
        "Type": "CONTACT_FLOW",
        "State": "ACTIVE",
        "Description": "Test contact flow",
        "Content": json.dumps({
            "Version": "2019-10-30",
            "StartAction": "PlayPrompt",
            "Actions": []
        }),
        "CreatedTime": "2024-01-01T00:00:00.000Z",
        "LastModifiedTime": "2024-01-01T00:00:00.000Z",
        "LastModifiedRegion": "us-east-1",
        "Tags": {}
    }


def _create_queue_summary(queue_id: str) -> Dict:
    """Create a sample queue summary."""
    return {
        "Id": queue_id,
        "Arn": f"arn:aws:connect:us-east-1:123456789012:instance/test/queue/{queue_id}",
        "Name": "Test Queue",
        "QueueType": "STANDARD",
        "Status": "ENABLED",
        "Description": "Test queue",
        "Tags": {}
    }


def _create_queue_detail(queue_id: str) -> Dict:
    """Create a sample queue detail."""
    return {
        "Id": queue_id,
        "Arn": f"arn:aws:connect:us-east-1:123456789012:instance/test/queue/{queue_id}",
        "Name": "Test Queue",
        "QueueType": "STANDARD",
        "Status": "ENABLED",
        "Description": "Test queue",
        "HoursOfOperationId": "hop-123",
        "MaxContacts": 100,
        "OutboundCallerConfig": {
            "OutboundCallerIdName": "Test Caller",
            "OutboundCallerIdNumberId": "phone-123",
            "OutboundFlowId": "cf-outbound"
        },
        "QuickConnectIds": [],
        "Tags": {}
    }


def _create_hours_summary(hours_id: str) -> Dict:
    """Create a sample hours of operation summary."""
    return {
        "Id": hours_id,
        "Arn": f"arn:aws:connect:us-east-1:123456789012:instance/test/operating-hours/{hours_id}",
        "Name": "Business Hours"
    }


def _create_hours_detail(hours_id: str) -> Dict:
    """Create a sample hours of operation detail."""
    return {
        "Id": hours_id,
        "Arn": f"arn:aws:connect:us-east-1:123456789012:instance/test/operating-hours/{hours_id}",
        "Name": "Business Hours",
        "Description": "Standard business hours",
        "TimeZone": "America/New_York",
        "Config": [
            {
                "Day": "MONDAY",
                "StartTime": {"Hours": 9, "Minutes": 0},
                "EndTime": {"Hours": 17, "Minutes": 0}
            },
            {
                "Day": "TUESDAY",
                "StartTime": {"Hours": 9, "Minutes": 0},
                "EndTime": {"Hours": 17, "Minutes": 0}
            },
            {
                "Day": "WEDNESDAY",
                "StartTime": {"Hours": 9, "Minutes": 0},
                "EndTime": {"Hours": 17, "Minutes": 0}
            },
            {
                "Day": "THURSDAY",
                "StartTime": {"Hours": 9, "Minutes": 0},
                "EndTime": {"Hours": 17, "Minutes": 0}
            },
            {
                "Day": "FRIDAY",
                "StartTime": {"Hours": 9, "Minutes": 0},
                "EndTime": {"Hours": 17, "Minutes": 0}
            }
        ],
        "Tags": {}
    }


def _create_prompt_summary(prompt_id: str) -> Dict:
    """Create a sample prompt summary."""
    return {
        "Id": prompt_id,
        "Arn": f"arn:aws:connect:us-east-1:123456789012:instance/test/prompt/{prompt_id}",
        "Name": "Welcome Message"
    }


def _create_prompt_detail(prompt_id: str) -> Dict:
    """Create a sample prompt detail."""
    return {
        "Id": prompt_id,
        "Arn": f"arn:aws:connect:us-east-1:123456789012:instance/test/prompt/{prompt_id}",
        "Name": "Welcome Message",
        "Description": "Welcome prompt for callers",
        "S3Uri": "s3://my-bucket/prompts/welcome.wav",
        "Tags": {}
    }


def _create_phone_number_summary(phone_id: str) -> Dict:
    """Create a sample phone number summary."""
    return {
        "Id": phone_id,
        "Arn": f"arn:aws:connect:us-east-1:123456789012:instance/test/phone-number/{phone_id}",
        "PhoneNumber": "+1-800-555-0123",
        "PhoneNumberCountryCode": "US",
        "PhoneNumberType": "TOLL_FREE",
        "Status": "ACTIVE",
        "Description": "Main support number",
        "TargetArn": "arn:aws:connect:us-east-1:123456789012:instance/test",
        "Tags": {}
    }


def _create_phone_number_detail(phone_id: str) -> Dict:
    """Create a sample phone number detail."""
    return {
        "Id": phone_id,
        "Arn": f"arn:aws:connect:us-east-1:123456789012:instance/test/phone-number/{phone_id}",
        "PhoneNumber": "+1-800-555-0123",
        "PhoneNumberCountryCode": "US",
        "PhoneNumberType": "TOLL_FREE",
        "PhoneNumberDescription": "Main support number",
        "TargetArn": "arn:aws:connect:us-east-1:123456789012:instance/test",
        "Status": "ACTIVE",
        "Tags": {}
    }


class MockTemplateLoader:
    """Mock template loader for testing."""
    
    def __init__(self):
        self.templates: Dict[str, Dict] = {}
    
    def add_template(self, name: str, content: Dict) -> "MockTemplateLoader":
        """Add a template."""
        self.templates[name] = content
        return self
    
    def load(self, name: str) -> Dict:
        """Load a template."""
        if name not in self.templates:
            raise FileNotFoundError(f"Template '{name}' not found")
        return self.templates[name]
    
    def list_available(self) -> List[str]:
        """List available templates."""
        return list(self.templates.keys())


def assert_success_result(result: Dict[str, Any]) -> None:
    """Assert that a result dict has success status."""
    assert result.get("status") == "success", f"Expected success, got: {result}"


def assert_error_result(result: Dict[str, Any], expected_error: Optional[str] = None) -> None:
    """Assert that a result dict has error status."""
    assert result.get("status") == "error", f"Expected error, got: {result}"
    if expected_error:
        assert expected_error in result.get("error", ""), f"Error message should contain '{expected_error}'"
