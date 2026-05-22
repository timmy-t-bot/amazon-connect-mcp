"""Comprehensive tests for component modules (instance, queues, hours, prompts, phone numbers)."""

import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tests.utils import (
    create_mock_connect_client,
    assert_success_result,
    assert_error_result,
    _create_instance_detail,
    _create_queue_detail,
    _create_hours_detail,
    _create_prompt_detail,
    _create_phone_number_detail,
)


@pytest.mark.unit
class TestInstanceManager:
    """Test instance management functions."""
    
    def test_connect_instances_create_success(self):
        """Test creating an instance successfully."""
        with patch("amazon_connect_mcp.components.instance_manager._get_connect_client") as mock_get_client:
            mock_client = create_mock_connect_client()
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.instance_manager import connect_instances_create
            
            result = connect_instances_create(
                instance_alias="test-instance",
                identity_management_type="CONNECT_MANAGED",
                tags={"Environment": "Test"}
            )
            
            assert result["status"] == "success"
            assert result["instance_alias"] == "test-instance"
            assert result["state"] == "CREATING"
    
    def test_connect_instances_create_client_error(self):
        """Test creating an instance with client error."""
        with patch("amazon_connect_mcp.components.instance_manager._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.create_instance.side_effect = ClientError(
                {"Error": {"Code": "LimitExceededException", "Message": "Instance limit exceeded"}},
                "create_instance"
            )
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.instance_manager import (
                connect_instances_create, ConnectInstanceError
            )
            
            with pytest.raises(ConnectInstanceError, match="LimitExceededException"):
                connect_instances_create(instance_alias="test-instance")
    
    def test_connect_instances_list_success(self):
        """Test listing instances successfully."""
        with patch("amazon_connect_mcp.components.instance_manager._get_connect_client") as mock_get_client:
            mock_client = create_mock_connect_client()
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.instance_manager import connect_instances_list
            
            result = connect_instances_list(max_results=10)
            
            assert_success_result(result)
            assert len(result["instances"]) == 1
            assert result["instances"][0]["instance_alias"] == "test-instance"
    
    def test_connect_instances_describe_success(self):
        """Test describing an instance successfully."""
        with patch("amazon_connect_mcp.components.instance_manager._get_connect_client") as mock_get_client:
            mock_client = create_mock_connect_client()
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.instance_manager import connect_instances_describe
            
            result = connect_instances_describe(
                instance_id="12345678-1234-1234-1234-123456789012"
            )
            
            assert_success_result(result)
            assert result["instance_alias"] == "test-instance"
    
    def test_connect_instances_describe_not_found(self):
        """Test describing non-existent instance."""
        with patch("amazon_connect_mcp.components.instance_manager._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.describe_instance.side_effect = ClientError(
                {"Error": {"Code": "ResourceNotFoundException", "Message": "Instance not found"}},
                "describe_instance"
            )
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.instance_manager import (
                connect_instances_describe, ConnectInstanceError
            )
            
            with pytest.raises(ConnectInstanceError, match="ResourceNotFoundException"):
                connect_instances_describe(instance_id="non-existent")
    
    def test_connect_instances_update_success(self):
        """Test updating instance settings successfully."""
        with patch("amazon_connect_mcp.components.instance_manager._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.update_instance_attribute.return_value = {}
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.instance_manager import connect_instances_update
            
            result = connect_instances_update(
                instance_id="12345678-1234-1234-1234-123456789012",
                inbound_calls_enabled=True,
                outbound_calls_enabled=True
            )
            
            assert_success_result(result)
            assert "INBOUND_CALLS" in result["updated_attributes"]
            assert "OUTBOUND_CALLS" in result["updated_attributes"]
    
    def test_connect_instances_update_partial_failure(self):
        """Test partial failure when updating instance."""
        with patch("amazon_connect_mcp.components.instance_manager._get_connect_client") as mock_get_client:
            mock_client = Mock()
            # First call succeeds, second fails
            mock_client.update_instance_attribute.side_effect = [
                {},
                ClientError(
                    {"Error": {"Code": "InvalidRequestException", "Message": "Cannot update"}},
                    "update_instance_attribute"
                )
            ]
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.instance_manager import connect_instances_update
            
            result = connect_instances_update(
                instance_id="12345678-1234-1234-1234-123456789012",
                inbound_calls_enabled=True,
                contact_flow_logs_enabled=True
            )
            
            assert result["status"] == "partial_success"
            assert "errors" in result
    
    def test_connect_instances_delete_success(self):
        """Test deleting an instance successfully."""
        with patch("amazon_connect_mcp.components.instance_manager._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.delete_instance.return_value = {}
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.instance_manager import connect_instances_delete
            
            result = connect_instances_delete(
                instance_id="12345678-1234-1234-1234-123456789012"
            )
            
            assert_success_result(result)
            mock_client.delete_instance.assert_called_once_with(
                InstanceId="12345678-1234-1234-1234-123456789012"
            )


@pytest.mark.unit
class TestQueues:
    """Test queue management functions."""
    
    def test_connect_queues_list_success(self):
        """Test listing queues successfully."""
        with patch("amazon_connect_mcp.components.queues._get_connect_client") as mock_get_client:
            mock_client = create_mock_connect_client()
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.queues import connect_queues_list
            
            result = connect_queues_list(
                instance_id="12345678-1234-1234-1234-123456789012",
                queue_types=["STANDARD"]
            )
            
            assert_success_result(result)
            assert len(result["queues"]) == 1
            assert result["queues"][0]["name"] == "Test Queue"
    
    def test_connect_queues_list_empty(self):
        """Test listing queues when empty."""
        with patch("amazon_connect_mcp.components.queues._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.list_queues.return_value = {"QueueSummaryList": []}
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.queues import connect_queues_list
            
            result = connect_queues_list(
                instance_id="12345678-1234-1234-1234-123456789012"
            )
            
            assert_success_result(result)
            assert result["queues"] == []
    
    def test_connect_queues_describe_success(self):
        """Test describing a queue successfully."""
        with patch("amazon_connect_mcp.components.queues._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.describe_queue.return_value = {
                "Queue": _create_queue_detail("queue-123")
            }
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.queues import connect_queues_describe
            
            result = connect_queues_describe(
                instance_id="12345678-1234-1234-1234-123456789012",
                queue_id="queue-123"
            )
            
            # describe returns success at top level and data
            assert result["status"] == "success"
            assert result["name"] == "Test Queue"
            assert result["id"] == "queue-123"
    
    def test_connect_queues_create_success(self):
        """Test creating a queue successfully."""
        with patch("amazon_connect_mcp.components.queues._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.create_queue.return_value = {
                "QueueId": "new-queue-123",
                "QueueArn": "arn:aws:connect:us-east-1:123456789012:instance/test/queue/new-queue-123"
            }
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.queues import connect_queues_create
            
            result = connect_queues_create(
                instance_id="12345678-1234-1234-1234-123456789012",
                name="Support Queue",
                hours_of_operation_id="hop-123",
                description="Main support queue",
                max_contacts=50
            )
            
            assert_success_result(result)
            assert result["queue_id"] == "new-queue-123"
    
    def test_connect_queues_create_with_optional_params(self):
        """Test creating a queue with all optional parameters."""
        with patch("amazon_connect_mcp.components.queues._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.create_queue.return_value = {
                "QueueId": "queue-123",
                "QueueArn": "arn"
            }
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.queues import connect_queues_create
            
            result = connect_queues_create(
                instance_id="12345678-1234-1234-1234-123456789012",
                name="Test Queue",
                hours_of_operation_id="hop-123",
                tags={"key": "value"},
                outbound_caller_config={"name": "Test"},
                quick_connect_ids=["qc-1"]
            )
            
            assert_success_result(result)
            # Verify correct params passed
            call_kwargs = mock_client.create_queue.call_args[1]
            assert call_kwargs["Tags"] == {"key": "value"}
    
    def test_connect_queues_update_success(self):
        """Test updating a queue successfully."""
        with patch("amazon_connect_mcp.components.queues._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.update_queue.return_value = {}
            mock_client.update_queue_name.return_value = {}
            mock_client.update_queue_status.return_value = {}
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.queues import connect_queues_update
            
            result = connect_queues_update(
                instance_id="12345678-1234-1234-1234-123456789012",
                queue_id="queue-123",
                name="Updated Queue",
                description="Updated description",
                max_contacts=200
            )
            
            assert_success_result(result)
            assert "name" in result["updated_fields"]
    
    def test_connect_queues_delete_success(self):
        """Test deleting a queue successfully."""
        with patch("amazon_connect_mcp.components.queues._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.delete_queue.return_value = {}
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.queues import connect_queues_delete
            
            result = connect_queues_delete(
                instance_id="12345678-1234-1234-1234-123456789012",
                queue_id="queue-123"
            )
            
            assert_success_result(result)
            mock_client.delete_queue.assert_called_once()
    
    def test_connect_queues_delete_error(self):
        """Test deleting a queue with error."""
        with patch("amazon_connect_mcp.components.queues._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.delete_queue.side_effect = ClientError(
                {"Error": {"Code": "ResourceInUse", "Message": "Queue is in use"}},
                "delete_queue"
            )
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.queues import (
                connect_queues_delete, ConnectQueueError
            )
            
            with pytest.raises(ConnectQueueError, match="ResourceInUse"):
                connect_queues_delete(
                    instance_id="12345678-1234-1234-1234-123456789012",
                    queue_id="queue-123"
                )


@pytest.mark.unit
class TestHoursOfOperations:
    """Test hours of operation management functions."""
    
    def test_connect_hours_of_operations_list_success(self):
        """Test listing hours of operations successfully."""
        with patch("amazon_connect_mcp.components.hours_of_operation._get_connect_client") as mock_get_client:
            mock_client = create_mock_connect_client()
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.hours_of_operation import connect_hours_of_operations_list
            
            result = connect_hours_of_operations_list(
                instance_id="12345678-1234-1234-1234-123456789012"
            )
            
            assert_success_result(result)
            assert len(result["hours_of_operations"]) == 1
    
    def test_connect_hours_of_operations_describe_success(self):
        """Test describing hours of operation successfully."""
        with patch("amazon_connect_mcp.components.hours_of_operation._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.describe_hours_of_operation.return_value = {
                "HoursOfOperation": _create_hours_detail("hop-123")
            }
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.hours_of_operation import connect_hours_of_operations_describe
            
            result = connect_hours_of_operations_describe(
                instance_id="12345678-1234-1234-1234-123456789012",
                hours_of_operation_id="hop-123"
            )
            
            assert_success_result(result)
            assert result["name"] == "Business Hours"
    
    def test_connect_hours_of_operations_create_success(self):
        """Test creating hours of operation successfully."""
        with patch("amazon_connect_mcp.components.hours_of_operation._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.create_hours_of_operation.return_value = {
                "HoursOfOperationId": "new-hop-123",
                "HoursOfOperationArn": "arn:aws:connect:us-east-1:123456789012:instance/test/hop/new-hop-123"
            }
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.hours_of_operation import connect_hours_of_operations_create
            
            config = [
                {
                    "Day": "MONDAY",
                    "StartTime": {"Hours": 9, "Minutes": 0},
                    "EndTime": {"Hours": 17, "Minutes": 0}
                }
            ]
            
            result = connect_hours_of_operations_create(
                instance_id="12345678-1234-1234-1234-123456789012",
                name="Business Hours",
                time_zone="America/New_York",
                config=config,
                description="Standard hours"
            )
            
            assert_success_result(result)
            assert result["hours_of_operation_id"] == "new-hop-123"
    
    def test_connect_hours_of_operations_create_invalid_config(self):
        """Test creating hours with invalid config."""
        with patch("amazon_connect_mcp.components.hours_of_operation._get_connect_client") as mock_get_client:
            mock_get_client.return_value = Mock()
            
            from amazon_connect_mcp.components.hours_of_operation import (
                connect_hours_of_operations_create, ConnectHoursOfOperationError
            )
            
            # Invalid config - missing required fields
            config = [{"invalid": "config"}]
            
            with pytest.raises(ConnectHoursOfOperationError, match="config item must have"):
                connect_hours_of_operations_create(
                    instance_id="12345678-1234-1234-1234-123456789012",
                    name="Test",
                    time_zone="UTC",
                    config=config
                )
    
    def test_connect_hours_of_operations_update_success(self):
        """Test updating hours of operation successfully."""
        with patch("amazon_connect_mcp.components.hours_of_operation._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.update_hours_of_operation_name.return_value = {}
            mock_client.update_hours_of_operation_config.return_value = {}
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.hours_of_operation import connect_hours_of_operations_update
            
            result = connect_hours_of_operations_update(
                instance_id="12345678-1234-1234-1234-123456789012",
                hours_of_operation_id="hop-123",
                name="Updated Hours"
            )
            
            assert_success_result(result)
    
    def test_connect_hours_of_operations_delete_success(self):
        """Test deleting hours of operation successfully."""
        with patch("amazon_connect_mcp.components.hours_of_operation._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.delete_hours_of_operation.return_value = {}
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.hours_of_operation import connect_hours_of_operations_delete
            
            result = connect_hours_of_operations_delete(
                instance_id="12345678-1234-1234-1234-123456789012",
                hours_of_operation_id="hop-123"
            )
            
            assert_success_result(result)
    
    def test_connect_hours_of_operations_create_override_success(self):
        """Test creating hours override successfully."""
        with patch("amazon_connect_mcp.components.hours_of_operation._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.create_hours_of_operation_override.return_value = {
                "HoursOfOperationOverrideId": "override-123"
            }
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.hours_of_operation import connect_hours_of_operations_create_override
            
            result = connect_hours_of_operations_create_override(
                instance_id="12345678-1234-1234-1234-123456789012",
                hours_of_operation_id="hop-123",
                name="Holiday Hours",
                description="Christmas hours",
                start_time={"Hours": 9, "Minutes": 0},
                end_time={"Hours": 14, "Minutes": 0},
                override_config=[]
            )
            
            assert_success_result(result)
            assert result["override_id"] == "override-123"


@pytest.mark.unit
class TestPrompts:
    """Test prompt management functions."""
    
    def test_connect_prompts_list_success(self):
        """Test listing prompts successfully."""
        with patch("amazon_connect_mcp.components.prompts._get_connect_client") as mock_get_client:
            mock_client = create_mock_connect_client()
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.prompts import connect_prompts_list
            
            result = connect_prompts_list(
                instance_id="12345678-1234-1234-1234-123456789012"
            )
            
            assert_success_result(result)
            assert len(result["prompts"]) == 1
    
    def test_connect_prompts_describe_success(self):
        """Test describing a prompt successfully."""
        with patch("amazon_connect_mcp.components.prompts._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.describe_prompt.return_value = {
                "Prompt": _create_prompt_detail("prompt-123")
            }
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.prompts import connect_prompts_describe
            
            result = connect_prompts_describe(
                instance_id="12345678-1234-1234-1234-123456789012",
                prompt_id="prompt-123"
            )
            
            assert_success_result(result)
            assert result["name"] == "Welcome Message"
    
    def test_connect_prompts_create_success(self):
        """Test creating a prompt successfully."""
        with patch("amazon_connect_mcp.components.prompts._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.create_prompt.return_value = {
                "PromptARN": "arn:aws:connect:us-east-1:123456789012:instance/test/prompt/new-prompt",
                "PromptId": "new-prompt"
            }
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.prompts import connect_prompts_create
            
            result = connect_prompts_create(
                instance_id="12345678-1234-1234-1234-123456789012",
                name="Welcome Message",
                s3_uri="s3://my-bucket/prompts/welcome.wav",
                description="Welcome prompt"
            )
            
            assert_success_result(result)
            assert result["prompt_id"] == "new-prompt"
    
    def test_connect_prompts_create_client_error(self):
        """Test creating a prompt with client error."""
        with patch("amazon_connect_mcp.components.prompts._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.create_prompt.side_effect = ClientError(
                {"Error": {"Code": "InvalidParameterException", "Message": "Invalid S3 URI"}},
                "create_prompt"
            )
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.prompts import (
                connect_prompts_create, ConnectPromptError
            )
            
            with pytest.raises(ConnectPromptError, match="Invalid S3 URI"):
                connect_prompts_create(
                    instance_id="12345678-1234-1234-1234-123456789012",
                    name="Welcome",
                    s3_uri="invalid://uri"
                )
    
    def test_connect_prompts_delete_success(self):
        """Test deleting a prompt successfully."""
        with patch("amazon_connect_mcp.components.prompts._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.delete_prompt.return_value = {}
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.prompts import connect_prompts_delete
            
            result = connect_prompts_delete(
                instance_id="12345678-1234-1234-1234-123456789012",
                prompt_id="prompt-123"
            )
            
            assert_success_result(result)


@pytest.mark.unit
class TestPhoneNumbers:
    """Test phone number management functions."""
    
    def test_connect_phone_numbers_search_success(self):
        """Test searching for available phone numbers."""
        with patch("amazon_connect_mcp.components.phone_numbers._get_connect_client") as mock_get_client:
            mock_client = create_mock_connect_client()
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.phone_numbers import connect_phone_numbers_search
            
            result = connect_phone_numbers_search(
                phone_number_country_code="US",
                phone_number_type="TOLL_FREE"
            )
            
            assert_success_result(result)
            assert len(result["phone_numbers"]) == 1
    
    def test_connect_phone_numbers_list_success(self):
        """Test listing claimed phone numbers."""
        with patch("amazon_connect_mcp.components.phone_numbers._get_connect_client") as mock_get_client:
            mock_client = create_mock_connect_client()
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.phone_numbers import connect_phone_numbers_list
            
            result = connect_phone_numbers_list(
                instance_id="12345678-1234-1234-1234-123456789012",
                phone_number_types=["TOLL_FREE"]
            )
            
            assert_success_result(result)
    
    def test_connect_phone_numbers_claim_with_specific_number(self):
        """Test claiming a specific phone number."""
        with patch("amazon_connect_mcp.components.phone_numbers._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.claim_phone_number.return_value = {
                "PhoneNumberId": "phone-123",
                "PhoneNumberArn": "arn:aws:connect:us-east-1:123456789012:instance/test/phone-number/phone-123"
            }
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.phone_numbers import connect_phone_numbers_claim
            
            result = connect_phone_numbers_claim(
                instance_id="12345678-1234-1234-1234-123456789012",
                phone_number="+1-800-555-0123"
            )
            
            assert_success_result(result)
            assert result["phone_number_id"] == "phone-123"
    
    def test_connect_phone_numbers_describe_success(self):
        """Test describing a phone number successfully."""
        with patch("amazon_connect_mcp.components.phone_numbers._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.describe_phone_number.return_value = {
                "PhoneNumber": _create_phone_number_detail("phone-123")
            }
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.phone_numbers import connect_phone_numbers_describe
            
            result = connect_phone_numbers_describe(
                instance_id="12345678-1234-1234-1234-123456789012",
                phone_number_id="phone-123"
            )
            
            assert_success_result(result)
            assert result["phone_number"] == "+1-800-555-0123"
    
    def test_connect_phone_numbers_release_success(self):
        """Test releasing a phone number successfully."""
        with patch("amazon_connect_mcp.components.phone_numbers._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.release_phone_number.return_value = {}
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.phone_numbers import connect_phone_numbers_release
            
            result = connect_phone_numbers_release(
                instance_id="12345678-1234-1234-1234-123456789012",
                phone_number_id="phone-123"
            )
            
            assert_success_result(result)
    
    def test_connect_phone_numbers_release_error(self):
        """Test releasing a phone number with error."""
        with patch("amazon_connect_mcp.components.phone_numbers._get_connect_client") as mock_get_client:
            mock_client = Mock()
            mock_client.release_phone_number.side_effect = ClientError(
                {"Error": {"Code": "ResourceInUse", "Message": "Number is in use"}},
                "release_phone_number"
            )
            mock_get_client.return_value = mock_client
            
            from amazon_connect_mcp.components.phone_numbers import (
                connect_phone_numbers_release, ConnectPhoneNumberError
            )
            
            with pytest.raises(ConnectPhoneNumberError, match="ResourceInUse"):
                connect_phone_numbers_release(
                    instance_id="12345678-1234-1234-1234-123456789012",
                    phone_number_id="phone-123"
                )
