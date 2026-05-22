"""pytest configuration and fixtures for Amazon Connect MCP tests."""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import Mock, patch

import pytest

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_aws_credentials():
    """Set up mock AWS credentials for testing."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    yield


@pytest.fixture
def test_instance_id() -> str:
    """Return a test Connect instance ID."""
    return "12345678-1234-1234-1234-123456789012"


@pytest.fixture
def test_contact_flow_id() -> str:
    """Return a test contact flow ID."""
    return "cf-12345678-1234-1234-1234-123456789012"


@pytest.fixture
def test_queue_id() -> str:
    """Return a test queue ID."""
    return "queue-12345678-1234-1234-1234-123456789012"


@pytest.fixture
def test_hours_id() -> str:
    """Return a test hours of operation ID."""
    return "hop-12345678-1234-1234-1234-123456789012"


@pytest.fixture
def test_prompt_id() -> str:
    """Return a test prompt ID."""
    return "prompt-12345678-1234-1234-1234-123456789012"


@pytest.fixture
def test_phone_number_id() -> str:
    """Return a test phone number ID."""
    return "phone-12345678-1234-1234-1234-123456789012"


@pytest.fixture
def mock_boto3_client():
    """Return a mock boto3 client."""
    with patch("boto3.client") as mock_client:
        yield mock_client


@pytest.fixture
def mock_connect_client(mock_boto3_client) -> Mock:
    """Return a mock Connect client."""
    mock = Mock()
    mock_boto3_client.return_value = mock
    return mock


@pytest.fixture
def mock_sts_client(mock_boto3_client) -> Mock:
    """Return a mock STS client."""
    mock = Mock()
    mock_boto3_client.return_value = mock
    mock.get_caller_identity.return_value = {"Account": "123456789012"}
    return mock


@pytest.fixture
def sample_instance_response() -> Dict[str, Any]:
    """Return a sample Connect instance response."""
    return {
        "Id": "12345678-1234-1234-1234-123456789012",
        "Arn": "arn:aws:connect:us-east-1:123456789012:instance/12345678-1234-1234-1234-123456789012",
        "IdentityManagementType": "CONNECT_MANAGED",
        "InstanceAlias": "test-instance",
        "CreatedTime": "2024-01-01T00:00:00.000Z",
        "ServiceRole": "arn:aws:iam::123456789012:role/connect-service-role",
        "InstanceStatus": "ACTIVE",
        "InboundCallsEnabled": True,
        "OutboundCallsEnabled": True
    }


@pytest.fixture
def sample_contact_flow_response() -> Dict[str, Any]:
    """Return a sample contact flow response."""
    return {
        "Id": "cf-12345678-1234-1234-1234-123456789012",
        "Arn": "arn:aws:connect:us-east-1:123456789012:instance/test/contact-flow/cf-123",
        "Name": "Test Flow",
        "Type": "CONTACT_FLOW",
        "Description": "Test contact flow",
        "Content": '{"Version": "2019-10-30", "StartAction": "PlayPrompt"}',
        "State": "ACTIVE"
    }


@pytest.fixture
def sample_queue_response() -> Dict[str, Any]:
    """Return a sample queue response."""
    return {
        "Id": "queue-12345678-1234-1234-1234-123456789012",
        "Arn": "arn:aws:connect:us-east-1:123456789012:instance/test/queue/queue-123",
        "Name": "Test Queue",
        "QueueType": "STANDARD",
        "Status": "ENABLED",
        "HoursOfOperationId": "hop-123",
        "MaxContacts": 100,
        "OutboundCallerConfig": {},
        "QuickConnectIds": [],
        "Tags": {}
    }


@pytest.fixture
def sample_hours_response() -> Dict[str, Any]:
    """Return a sample hours of operation response."""
    return {
        "Id": "hop-12345678-1234-1234-1234-123456789012",
        "Arn": "arn:aws:connect:us-east-1:123456789012:instance/test/operating-hours/hop-123",
        "Name": "Business Hours",
        "Description": "Standard business hours",
        "TimeZone": "America/New_York",
        "Config": [
            {
                "Day": "MONDAY",
                "StartTime": {"Hours": 9, "Minutes": 0},
                "EndTime": {"Hours": 17, "Minutes": 0}
            }
        ],
        "Tags": {}
    }


@pytest.fixture
def sample_prompt_response() -> Dict[str, Any]:
    """Return a sample prompt response."""
    return {
        "Id": "prompt-12345678-1234-1234-1234-123456789012",
        "Arn": "arn:aws:connect:us-east-1:123456789012:instance/test/prompt/prompt-123",
        "Name": "Welcome Message",
        "Description": "Welcome prompt",
        "S3Uri": "s3://my-bucket/prompts/welcome.wav",
        "Tags": {}
    }


@pytest.fixture
def sample_phone_number_response() -> Dict[str, Any]:
    """Return a sample phone number response."""
    return {
        "Id": "phone-12345678-1234-1234-1234-123456789012",
        "Arn": "arn:aws:connect:us-east-1:123456789012:instance/test/phone-number/phone-123",
        "PhoneNumber": "+1-800-555-0123",
        "PhoneNumberCountryCode": "US",
        "PhoneNumberType": "TOLL_FREE",
        "Status": "ACTIVE",
        "TargetArn": "arn:aws:connect:us-east-1:123456789012:instance/test",
        "Tags": {}
    }


@pytest.fixture
def sample_template_content() -> Dict[str, Any]:
    """Return a sample contact flow template content."""
    return {
        "Version": "2019-10-30",
        "StartAction": "PlayPrompt",
        "Actions": [
            {
                "Identifier": "PlayPrompt",
                "Type": "MessageParticipant",
                "Parameters": {
                    "Text": "{{prompt_text}}",
                    "SSML": "{{prompt_ssml}}"
                },
                "Transitions": {
                    "NextAction": "Disconnect"
                }
            }
        ],
        "Variables": {
            "prompt_text": {
                "type": "string",
                "required": True,
                "description": "Text to speak"
            },
            "prompt_ssml": {
                "type": "string",
                "required": False,
                "default": "",
                "description": "SSML version"
            }
        }
    }


@pytest.fixture(autouse=True)
def reset_env():
    """Reset environment after each test."""
    original_env = dict(os.environ)
    yield
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# Markers for test categorization
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow"
    )
