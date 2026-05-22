"""End-to-end integration tests for Amazon Connect MCP (using mocks).

These tests verify the full flow of operations without requiring actual AWS credentials.
They use extensive mocking to simulate AWS service responses.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.mark.integration
@pytest.mark.unit
class TestInstanceWorkflow:
    """Test complete instance management workflow."""
    
    @patch("amazon_connect_mcp.components.instance_manager.boto3")
    def test_complete_instance_lifecycle(self, mock_boto):
        """Test creating, listing, updating, and deleting an instance."""
        mock_client = Mock()
        mock_boto.client.return_value = mock_client
        
        from amazon_connect_mcp.components.instance_manager import (
            connect_instances_create,
            connect_instances_list,
            connect_instances_describe,
            connect_instances_update,
            connect_instances_delete
        )
        
        # Create instance
        mock_client.create_instance.return_value = {
            "Id": "inst-123",
            "Arn": "arn:aws:connect:us-east-1:123456789012:instance/inst-123",
            "State": "CREATING"
        }
        
        create_result = connect_instances_create(
            instance_alias="test-instance",
            identity_management_type="CONNECT_MANAGED"
        )
        
        assert create_result["status"] == "success"
        assert create_result["instance_alias"] == "test-instance"
        instance_id = create_result["instance_id"]
        
        # List instances
        mock_client.list_instances.return_value = {
            "InstanceSummaryList": [
                {"Id": instance_id, "Arn": "arn", "InstanceAlias": "test-instance"}
            ]
        }
        
        list_result = connect_instances_list()
        assert list_result["status"] == "success"
        assert len(list_result["instances"]) == 1
        
        # Describe instance
        mock_client.describe_instance.return_value = {
            "Instance": {
                "Id": instance_id,
                "Arn": "arn:aws:connect:us-east-1:123456789012:instance/inst-123",
                "InstanceAlias": "test-instance",
                "InstanceStatus": "ACTIVE"
            }
        }
        
        describe_result = connect_instances_describe(instance_id=instance_id)
        assert describe_result["status"] == "success"
        assert describe_result["id"] == instance_id
        
        # Update instance
        mock_client.update_instance_attribute.return_value = {}
        
        update_result = connect_instances_update(
            instance_id=instance_id,
            inbound_calls_enabled=True,
            outbound_calls_enabled=True
        )
        
        assert update_result["status"] == "success"
        
        # Delete instance
        mock_client.delete_instance.return_value = {}
        
        delete_result = connect_instances_delete(instance_id=instance_id)
        assert delete_result["status"] == "success"


@pytest.mark.integration
@pytest.mark.unit
class TestQueueWorkflow:
    """Test complete queue management workflow."""
    
    @patch("amazon_connect_mcp.components.queues.boto3")
    def test_complete_queue_lifecycle(self, mock_boto):
        """Test creating, listing, updating, and deleting a queue."""
        mock_client = Mock()
        mock_boto.client.return_value = mock_client
        
        from amazon_connect_mcp.components.queues import (
            connect_queues_create,
            connect_queues_list,
            connect_queues_describe,
            connect_queues_update,
            connect_queues_delete
        )
        
        instance_id = "inst-123"
        
        # Create queue
        mock_client.create_queue.return_value = {
            "QueueId": "queue-123",
            "QueueArn": f"arn:aws:connect:us-east-1:123456789012:instance/{instance_id}/queue/queue-123"
        }
        
        create_result = connect_queues_create(
            instance_id=instance_id,
            name="Support Queue",
            hours_of_operation_id="hop-123",
            description="Test queue",
            max_contacts=100
        )
        
        assert create_result["status"] == "success"
        queue_id = create_result["queue_id"]
        
        # List queues
        mock_client.list_queues.return_value = {
            "QueueSummaryList": [
                {"Id": queue_id, "Arn": "arn", "Name": "Support Queue", "QueueType": "STANDARD"}
            ]
        }
        
        list_result = connect_queues_list(instance_id=instance_id)
        assert list_result["status"] == "success"
        
        # Describe queue
        mock_client.describe_queue.return_value = {
            "Queue": {
                "Id": queue_id,
                "Name": "Support Queue",
                "QueueType": "STANDARD",
                "Status": "ENABLED"
            }
        }
        
        describe_result = connect_queues_describe(instance_id=instance_id, queue_id=queue_id)
        assert describe_result["status"] == "success"
        
        # Update queue
        mock_client.update_queue.return_value = {}
        mock_client.update_queue_name.return_value = {}
        mock_client.update_queue_status.return_value = {}
        
        update_result = connect_queues_update(
            instance_id=instance_id,
            queue_id=queue_id,
            name="Updated Support Queue"
        )
        
        assert update_result["status"] == "success"
        
        # Delete queue
        mock_client.delete_queue.return_value = {}
        
        delete_result = connect_queues_delete(instance_id=instance_id, queue_id=queue_id)
        assert delete_result["status"] == "success"


@pytest.mark.integration
@pytest.mark.unit
class TestContactFlowWorkflow:
    """Test contact flow management workflow."""
    
    @patch("contact_flows.contact_flow_tools.connect_client")
    @patch("contact_flows.contact_flow_tools.template_engine")
    def test_contact_flow_lifecycle(self, mock_template_engine, mock_boto_client):
        """Test creating, updating, and deleting a contact flow."""
        from contact_flows.contact_flow_tools import (
            contact_flows_create,
            contact_flows_list,
            contact_flows_describe,
            contact_flows_update_content,
            contact_flows_delete
        )
        
        instance_id = "inst-123"
        
        # Create contact flow
        mock_boto_client.create_contact_flow.return_value = {
            "ContactFlowId": "cf-123",
            "ContactFlowArn": f"arn:aws:connect:us-east-1:123456789012:instance/{instance_id}/cf-123"
        }
        
        create_result = contact_flows_create(
            instance_id=instance_id,
            name="Test Flow",
            content='{"Version": "2019-10-30", "StartAction": "PlayPrompt"}',
            type="CONTACT_FLOW"
        )
        
        assert create_result["status"] == "success"
        flow_id = create_result["contact_flow_id"]
        
        # List contact flows
        mock_boto_client.list_contact_flows.return_value = {
            "ContactFlowSummaryList": [
                {
                    "Id": flow_id,
                    "Arn": "arn",
                    "Name": "Test Flow",
                    "Type": "CONTACT_FLOW",
                    "State": "ACTIVE"
                }
            ]
        }
        
        list_result = contact_flows_list(instance_id=instance_id)
        assert list_result["status"] == "success"
        
        # Describe contact flow
        mock_boto_client.describe_contact_flow.return_value = {
            "ContactFlow": {
                "Id": flow_id,
                "Name": "Test Flow",
                "Type": "CONTACT_FLOW",
                "State": "ACTIVE",
                "Content": '{"Version": "2019-10-30"}'
            }
        }
        
        describe_result = contact_flows_describe(
            instance_id=instance_id,
            contact_flow_id=flow_id
        )
        assert describe_result["status"] == "success"
        
        # Update contact flow
        mock_boto_client.update_contact_flow_content.return_value = {}
        
        update_result = contact_flows_update_content(
            instance_id=instance_id,
            contact_flow_id=flow_id,
            content='{"Version": "2019-10-30", "StartAction": "Updated"}'
        )
        
        assert update_result["status"] == "success"
        
        # Delete contact flow
        mock_boto_client.delete_contact_flow.return_value = {}
        
        delete_result = contact_flows_delete(
            instance_id=instance_id,
            contact_flow_id=flow_id
        )
        assert delete_result["status"] == "success"


@pytest.mark.integration
@pytest.mark.unit
class TestTemplateWorkflow:
    """Test template-based contact flow workflow."""
    
    def test_create_outbound_flow_from_template(self):
        """Test creating an outbound flow using a template."""
        with patch("contact_flows.contact_flow_tools.template_engine") as mock_engine, \
             patch("contact_flows.contact_flow_tools.connect_client") as mock_client:
            
            mock_engine.validate_parameters.return_value = {
                "prompt_text": "Hello",
                "prompt_ssml": "<speak>Hello</speak>"
            }
            mock_engine.render.return_value = {
                "Version": "2019-10-30",
                "StartAction": "PlayPrompt"
            }
            
            mock_client.create_contact_flow.return_value = {
                "ContactFlowId": "cf-outbound",
                "ContactFlowArn": "arn:aws:connect:us-east-1:123456789012:instance/test/cf-outbound"
            }
            
            from contact_flows.contact_flow_tools import contact_flows_create_outbound
            
            result = contact_flows_create_outbound(
                instance_id="test-instance",
                name="Outbound Campaign",
                mode="PLAY_PROMPT",
                parameters={"prompt_text": "Hello"}
            )
            
            assert result["status"] == "success"
            assert result["mode"] == "PLAY_PROMPT"
            assert result["template_used"] == "play_prompt_outbound"


@pytest.mark.integration
@pytest.mark.unit
class TestPhoneNumberWorkflow:
    """Test phone number management workflow."""
    
    @patch("amazon_connect_mcp.components.phone_numbers.boto3")
    def test_phone_number_lifecycle(self, mock_boto):
        """Test complete phone number lifecycle."""
        mock_client = Mock()
        mock_boto.client.return_value = mock_client
        
        from amazon_connect_mcp.components.phone_numbers import (
            connect_phone_numbers_search,
            connect_phone_numbers_claim,
            connect_phone_numbers_list,
            connect_phone_numbers_describe,
            connect_phone_numbers_release
        )
        
        instance_id = "inst-123"
        
        # Search for available numbers
        mock_client.search_available_phone_numbers.return_value = {
            "PhoneNumbers": [
                {"PhoneNumber": "+1-800-555-0123", "PhoneNumberCountryCode": "US", "PhoneNumberType": "TOLL_FREE"}
            ]
        }
        
        search_result = connect_phone_numbers_search(
            phone_number_country_code="US",
            phone_number_type="TOLL_FREE"
        )
        
        assert search_result["status"] == "success"
        assert len(search_result["phone_numbers"]) == 1
        
        # Claim a number
        mock_client.claim_phone_number.return_value = {
            "PhoneNumberId": "phone-123",
            "PhoneNumberArn": f"arn:aws:connect:us-east-1:123456789012:instance/{instance_id}/phone-123"
        }
        
        claim_result = connect_phone_numbers_claim(
            instance_id=instance_id,
            phone_number="+1-800-555-0123"
        )
        
        assert claim_result["status"] == "success"
        phone_id = claim_result["phone_number_id"]
        
        # List phone numbers
        mock_client.list_phone_numbers.return_value = {
            "PhoneNumberSummaryList": [
                {
                    "Id": phone_id,
                    "PhoneNumber": "+1-800-555-0123",
                    "PhoneNumberCountryCode": "US",
                    "PhoneNumberType": "TOLL_FREE",
                    "Status": "ACTIVE"
                }
            ]
        }
        
        list_result = connect_phone_numbers_list(instance_id=instance_id)
        assert list_result["status"] == "success"
        
        # Describe phone number
        mock_client.describe_phone_number.return_value = {
            "PhoneNumber": {
                "Id": phone_id,
                "PhoneNumber": "+1-800-555-0123",
                "Status": "ACTIVE"
            }
        }
        
        describe_result = connect_phone_numbers_describe(
            instance_id=instance_id,
            phone_number_id=phone_id
        )
        assert describe_result["status"] == "success"
        
        # Release phone number
        mock_client.release_phone_number.return_value = {}
        
        release_result = connect_phone_numbers_release(
            instance_id=instance_id,
            phone_number_id=phone_id
        )
        assert release_result["status"] == "success"


@pytest.mark.integration
@pytest.mark.unit
class TestHoursOfOperationWorkflow:
    """Test hours of operation workflow."""
    
    @patch("amazon_connect_mcp.components.hours_of_operation.boto3")
    def test_hours_workflow(self, mock_boto):
        """Test complete hours of operation lifecycle."""
        mock_client = Mock()
        mock_boto.client.return_value = mock_client
        
        from amazon_connect_mcp.components.hours_of_operation import (
            connect_hours_of_operations_create,
            connect_hours_of_operations_list,
            connect_hours_of_operations_describe,
            connect_hours_of_operations_update,
            connect_hours_of_operations_delete
        )
        
        instance_id = "inst-123"
        
        # Create hours of operation
        mock_client.create_hours_of_operation.return_value = {
            "HoursOfOperationId": "hop-123",
            "HoursOfOperationArn": f"arn:aws:connect:us-east-1:123456789012:instance/{instance_id}/hop-123"
        }
        
        config = [
            {
                "Day": "MONDAY",
                "StartTime": {"Hours": 9, "Minutes": 0},
                "EndTime": {"Hours": 17, "Minutes": 0}
            }
        ]
        
        create_result = connect_hours_of_operations_create(
            instance_id=instance_id,
            name="Business Hours",
            time_zone="America/New_York",
            config=config
        )
        
        assert create_result["status"] == "success"
        hop_id = create_result["hours_of_operation_id"]
        
        # List hours
        mock_client.list_hours_of_operations.return_value = {
            "HoursOfOperationSummaryList": [{"Id": hop_id, "Name": "Business Hours"}]
        }
        
        list_result = connect_hours_of_operations_list(instance_id=instance_id)
        assert list_result["status"] == "success"
        
        # Describe hours
        mock_client.describe_hours_of_operation.return_value = {
            "HoursOfOperation": {
                "Id": hop_id,
                "Name": "Business Hours",
                "TimeZone": "America/New_York"
            }
        }
        
        describe_result = connect_hours_of_operations_describe(
            instance_id=instance_id,
            hours_of_operation_id=hop_id
        )
        assert describe_result["status"] == "success"
        
        # Update hours
        mock_client.update_hours_of_operation_name.return_value = {}
        
        update_result = connect_hours_of_operations_update(
            instance_id=instance_id,
            hours_of_operation_id=hop_id,
            name="Updated Business Hours"
        )
        assert update_result["status"] == "success"
        
        # Delete hours
        mock_client.delete_hours_of_operation.return_value = {}
        
        delete_result = connect_hours_of_operations_delete(
            instance_id=instance_id,
            hours_of_operation_id=hop_id
        )
        assert delete_result["status"] == "success"


@pytest.mark.integration
@pytest.mark.unit
class TestPromptWorkflow:
    """Test prompt management workflow."""
    
    @patch("amazon_connect_mcp.components.prompts.boto3")
    def test_prompt_lifecycle(self, mock_boto):
        """Test complete prompt lifecycle."""
        mock_client = Mock()
        mock_boto.client.return_value = mock_client
        
        from amazon_connect_mcp.components.prompts import (
            connect_prompts_create,
            connect_prompts_list,
            connect_prompts_describe,
            connect_prompts_delete
        )
        
        instance_id = "inst-123"
        
        # Create prompt
        mock_client.create_prompt.return_value = {
            "PromptARN": f"arn:aws:connect:us-east-1:123456789012:instance/{instance_id}/prompt-new",
            "PromptId": "prompt-new"
        }
        
        create_result = connect_prompts_create(
            instance_id=instance_id,
            name="Welcome Message",
            s3_uri="s3://my-bucket/prompts/welcome.wav",
            description="Welcome prompt"
        )
        
        assert create_result["status"] == "success"
        prompt_id = create_result["prompt_id"]
        
        # List prompts
        mock_client.list_prompts.return_value = {
            "PromptSummaryList": [{"Id": prompt_id, "Name": "Welcome Message"}]
        }
        
        list_result = connect_prompts_list(instance_id=instance_id)
        assert list_result["status"] == "success"
        
        # Describe prompt
        mock_client.describe_prompt.return_value = {
            "Prompt": {
                "Id": prompt_id,
                "Name": "Welcome Message",
                "S3Uri": "s3://my-bucket/prompts/welcome.wav"
            }
        }
        
        describe_result = connect_prompts_describe(
            instance_id=instance_id,
            prompt_id=prompt_id
        )
        assert describe_result["status"] == "success"
        
        # Delete prompt
        mock_client.delete_prompt.return_value = {}
        
        delete_result = connect_prompts_delete(
            instance_id=instance_id,
            prompt_id=prompt_id
        )
        assert delete_result["status"] == "success"


@pytest.mark.integration
@pytest.mark.unit
class TestLambdaApiBridgeEndToEnd:
    """Test Lambda API bridge end-to-end."""
    
    def test_api_handler_full_workflow(self):
        """Test complete API workflow through Lambda handler."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "lambda"))
        
        with patch("connect_api_handler.connect_client") as mock_client:
            # Set up mock responses
            mock_client.list_instances.return_value = {
                "InstanceSummaryList": [{"Id": "inst-123", "InstanceAlias": "Test"}]
            }
            
            from connect_api_handler import lambda_handler
            
            # List instances
            event = {
                "path": "/instances/list",
                "httpMethod": "GET",
                "queryStringParameters": None
            }
            
            result = lambda_handler(event, {})
            
            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert body["status"] == "success"
            
            # Create queue through API
            mock_client.create_queue.return_value = {
                "QueueId": "q-123",
                "QueueArn": "arn:aws:connect:us-east-1:123456789012:instance/inst-123/queue/q-123"
            }
            
            event = {
                "path": "/queues/create",
                "httpMethod": "POST",
                "body": json.dumps({
                    "InstanceId": "inst-123",
                    "Name": "API Test Queue",
                    "HoursOfOperationId": "hop-123"
                })
            }
            
            result = lambda_handler(event, {})
            
            assert result["statusCode"] == 200
            body = json.loads(result["body"])
            assert body["status"] == "success"
