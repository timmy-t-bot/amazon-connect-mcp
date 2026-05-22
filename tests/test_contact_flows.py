"""Comprehensive tests for Contact Flow Tools."""

import json
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch, MagicMock

import pytest

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from amazon_connect_mcp.templates.engine import TemplateEngine, TemplateVariable
from amazon_connect_mcp.templates.registry import TemplateRegistry


@pytest.mark.unit
class TestTemplateVariable:
    """Test template variable validation."""
    
    def test_string_validation_success(self):
        """Test successful string validation."""
        var = TemplateVariable("test", "string", required=True)
        result = var.validate("hello")
        assert result == "hello"
    
    def test_string_validation_invalid_type(self):
        """Test string validation with wrong type."""
        var = TemplateVariable("test", "string", required=True)
        with pytest.raises(ValueError, match="must be a string"):
            var.validate(123)
    
    def test_string_optional_with_default(self):
        """Test optional string with default value."""
        var = TemplateVariable("test", "string", required=False, default="default_value")
        result = var.validate(None)
        assert result == "default_value"
    
    def test_string_required_missing(self):
        """Test required string when missing."""
        var = TemplateVariable("test", "string", required=True)
        with pytest.raises(ValueError, match="Required variable"):
            var.validate(None)
    
    def test_integer_validation_success(self):
        """Test successful integer validation."""
        var = TemplateVariable("timeout", "integer", default=5, min_value=1, max_value=30)
        assert var.validate(10) == 10
        assert var.validate("15") == 15
        assert var.validate(None) == 5
    
    def test_integer_validation_exceeds_max(self):
        """Test integer validation when value exceeds max."""
        var = TemplateVariable("timeout", "integer", default=5, min_value=1, max_value=30)
        with pytest.raises(ValueError, match="must be <="):
            var.validate(50)
    
    def test_integer_validation_below_min(self):
        """Test integer validation when value below min."""
        var = TemplateVariable("timeout", "integer", default=5, min_value=1, max_value=30)
        with pytest.raises(ValueError, match="must be >="):
            var.validate(0)
    
    def test_integer_validation_invalid(self):
        """Test integer validation with invalid value."""
        var = TemplateVariable("timeout", "integer", default=5, min_value=1, max_value=30)
        with pytest.raises(ValueError, match="must be an integer"):
            var.validate("not_a_number")
    
    def test_arn_validation_success(self):
        """Test successful ARN validation."""
        var = TemplateVariable("lambda_arn", "arn", required=True)
        result = var.validate("arn:aws:lambda:us-east-1:123456789:function:test")
        assert result == "arn:aws:lambda:us-east-1:123456789:function:test"
    
    def test_arn_validation_invalid(self):
        """Test ARN validation with invalid ARN."""
        var = TemplateVariable("lambda_arn", "arn", required=True)
        with pytest.raises(ValueError, match="must be a valid ARN"):
            var.validate("not-an-arn")
    
    def test_enum_validation_success(self):
        """Test successful enum validation."""
        var = TemplateVariable("status", "enum", allowed_values=["SUCCESS", "FAILED"])
        assert var.validate("SUCCESS") == "SUCCESS"
    
    def test_enum_validation_invalid(self):
        """Test enum validation with invalid value."""
        var = TemplateVariable("status", "enum", allowed_values=["SUCCESS", "FAILED"])
        with pytest.raises(ValueError, match="must be one of"):
            var.validate("UNKNOWN")
    
    def test_boolean_validation_string_true(self):
        """Test boolean validation with string 'true'."""
        var = TemplateVariable("enabled", "boolean", default=False)
        assert var.validate("true") is True
        assert var.validate("1") is True
        assert var.validate("yes") is True
    
    def test_boolean_validation_string_false(self):
        """Test boolean validation with string 'false'."""
        var = TemplateVariable("enabled", "boolean", default=True)
        assert var.validate("false") is False
        assert var.validate("0") is False
        assert var.validate("no") is False


@pytest.mark.unit
class TestTemplateEngine:
    """Test template rendering engine."""
    
    def test_render_string_simple(self):
        """Test simple string template rendering."""
        engine = TemplateEngine()
        result = engine.render_string("Hello {{name}}!", {"name": "World"})
        assert result == "Hello World!"
    
    def test_render_string_multiple_variables(self):
        """Test string with multiple variables."""
        engine = TemplateEngine()
        result = engine.render_string(
            "{{greeting}} {{name}} from {{location}}!",
            {"greeting": "Hello", "name": "World", "location": "Earth"}
        )
        assert result == "Hello World from Earth!"
    
    def test_render_string_unmatched_variable(self):
        """Test that unmatched variables are kept as-is."""
        engine = TemplateEngine()
        result = engine.render_string("Hello {{name}}!", {})
        assert result == "Hello {{name}}!"
    
    def test_find_template_variables_in_dict(self):
        """Test finding variables in a dictionary."""
        engine = TemplateEngine()
        content = {
            "text": "{{greeting}} {{name}}",
            "nested": {
                "value": "{{id}}"
            }
        }
        variables = engine.find_template_variables(content)
        assert variables == {"greeting", "name", "id"}
    
    def test_find_template_variables_in_list(self):
        """Test finding variables in a list."""
        engine = TemplateEngine()
        content = {
            "items": ["{{item1}}", "{{item2}}", "{{item1}}"]  # item1 appears twice
        }
        variables = engine.find_template_variables(content)
        assert variables == {"item1", "item2"}
    
    def test_render_recursive_dict(self):
        """Test recursive rendering of dictionary."""
        engine = TemplateEngine()
        content = {
            "message": "Hello {{name}}",
            "config": {
                "timeout": "{{timeout}}"
            }
        }
        result = engine.render_recursive(content, {"name": "World", "timeout": "10"})
        
        assert result["message"] == "Hello World"
        assert result["config"]["timeout"] == "10"
    
    def test_render_recursive_list(self):
        """Test recursive rendering of list."""
        engine = TemplateEngine()
        content = ["{{item1}}", "{{item2}}", "static"]
        result = engine.render_recursive(content, {"item1": "A", "item2": "B"})
        assert result == ["A", "B", "static"]
    
    def test_render_recursive_nested_structure(self):
        """Test recursive rendering of nested structure."""
        engine = TemplateEngine()
        content = {
            "level1": {
                "level2": [
                    {"key": "{{value}}"}
                ]
            }
        }
        result = engine.render_recursive(content, {"value": "test"})
        assert result["level1"]["level2"][0]["key"] == "test"
    
    def test_render_recursive_preserves_non_string_values(self):
        """Test that non-string values are preserved."""
        engine = TemplateEngine()
        content = {
            "number": 42,
            "boolean": True,
            "null_value": None
        }
        result = engine.render_recursive(content, {})
        assert result["number"] == 42
        assert result["boolean"] is True
        assert result["null_value"] is None
    
    @patch("pathlib.Path.exists")
    @patch("builtins.open")
    def test_load_template_success(self, mock_open, mock_exists):
        """Test successful template loading."""
        mock_exists.return_value = True
        mock_open.return_value.__enter__ = MagicMock(
            return_value=MagicMock(read=lambda: '{"Version": "2019-10-30", "Variables": {}}')
        )
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        
        engine = TemplateEngine()
        with patch.object(engine.templates_dir, "glob", return_value=[]):
            template = engine.load_template("test_template")
        
        assert template["Version"] == "2019-10-30"
    
    def test_validate_parameters_success(self):
        """Test successful parameter validation."""
        engine = TemplateEngine()
        
        # Create a mock template
        template = {
            "Version": "2019-10-30",
            "Variables": {
                "name": {"type": "string", "required": True},
                "timeout": {"type": "integer", "default": 5}
            }
        }
        
        with patch.object(engine, "load_template", return_value=template):
            result = engine.validate_parameters("test", {"name": "Test Name"})
        
        assert result["name"] == "Test Name"
        assert result["timeout"] == 5  # Default value
    
    def test_validate_parameters_missing_required(self):
        """Test validation with missing required parameter."""
        engine = TemplateEngine()
        
        template = {
            "Variables": {
                "name": {"type": "string", "required": True}
            }
        }
        
        with patch.object(engine, "load_template", return_value=template):
            with pytest.raises(ValueError, match="Missing required variables"):
                engine.validate_parameters("test", {})


@pytest.mark.unit
class TestTemplateRegistry:
    """Test template registry."""
    
    def test_get_template_success(self):
        """Test successful template retrieval."""
        registry = TemplateRegistry()
        
        mock_template = {"Version": "2019-10-30", "StartAction": "PlayPrompt"}
        
        with patch.object(registry.engine, "load_template", return_value=mock_template):
            with patch.object(registry.engine, "list_templates", return_value=["test_template"]):
                template = registry.get_template("test_template")
        
        assert template is not None
        assert template["Version"] == "2019-10-30"
    
    def test_get_template_not_found(self):
        """Test getting non-existent template."""
        registry = TemplateRegistry()
        
        with patch.object(registry.engine, "load_template", side_effect=FileNotFoundError):
            template = registry.get_template("non_existent")
        
        assert template is None
    
    def test_create_contact_flow_payload(self):
        """Test creating contact flow payload."""
        registry = TemplateRegistry()
        
        # Mock the engine methods
        with patch.object(registry.engine, "render", return_value={"Version": "2019-10-30"}):
            with patch.object(registry.engine, "validate_parameters", return_value={"prompt_text": "Hello"}):
                payload = registry.create_contact_flow_payload(
                    template_name="play_prompt_outbound",
                    parameters={"prompt_text": "Hello"},
                    name="Test Flow",
                    description="Test Description"
                )
        
        assert payload["Name"] == "Test Flow"
        assert payload["Description"] == "Test Description"
        assert json.loads(payload["Content"])["Version"] == "2019-10-30"
    
    def test_get_template_schema(self):
        """Test getting template schema."""
        registry = TemplateRegistry()
        
        template = {
            "Variables": {
                "name": {
                    "type": "string",
                    "required": True,
                    "description": "The name"
                },
                "timeout": {
                    "type": "integer",
                    "default": 5,
                    "min": 1,
                    "max": 10
                }
            }
        }
        
        with patch.object(registry, "get_template", return_value=template):
            schema = registry.get_template_schema("test_template")
        
        assert schema["type"] == "object"
        assert "name" in schema["properties"]
        assert "timeout" in schema["properties"]
        assert schema["properties"]["timeout"]["default"] == 5
        assert "name" in schema["required"]


@pytest.mark.unit
class TestContactFlowTools:
    """Test contact flow tools module functions."""
    
    @patch("contact_flows.contact_flow_tools.connect_client")
    def test_contact_flows_list_success(self, mock_client):
        """Test listing contact flows successfully."""
        mock_client.list_contact_flows.return_value = {
            "ContactFlowSummaryList": [
                {
                    "Id": "cf-123",
                    "Arn": "arn:aws:connect:us-east-1:123:instance/test/contact-flow/cf-123",
                    "Name": "Test Flow",
                    "Type": "CONTACT_FLOW",
                    "State": "ACTIVE",
                    "LastModifiedTime": "2024-01-01T00:00:00Z",
                    "LastModifiedRegion": "us-east-1"
                }
            ],
            "NextToken": None
        }
        
        from contact_flows.contact_flow_tools import contact_flows_list
        
        result = contact_flows_list(
            instance_id="test-instance",
            contact_flow_types=["CONTACT_FLOW"]
        )
        
        assert result["status"] == "success"
        assert len(result["contact_flows"]) == 1
        assert result["contact_flows"][0]["name"] == "Test Flow"
    
    @patch("contact_flows.contact_flow_tools.connect_client")
    def test_contact_flows_list_empty(self, mock_client):
        """Test listing contact flows when empty."""
        mock_client.list_contact_flows.return_value = {
            "ContactFlowSummaryList": [],
            "NextToken": None
        }
        
        from contact_flows.contact_flow_tools import contact_flows_list
        
        result = contact_flows_list(instance_id="test-instance")
        
        assert result["status"] == "success"
        assert result["contact_flows"] == []
    
    @patch("contact_flows.contact_flow_tools.connect_client")
    def test_contact_flows_list_error(self, mock_client):
        """Test listing contact flows with error."""
        mock_client.list_contact_flows.side_effect = Exception("Service error")
        
        from contact_flows.contact_flow_tools import contact_flows_list
        
        result = contact_flows_list(instance_id="test-instance")
        
        assert result["status"] == "error"
        assert "Service error" in result["error"]
    
    @patch("contact_flows.contact_flow_tools.connect_client")
    def test_contact_flows_describe_success(self, mock_client):
        """Test describing a contact flow."""
        mock_client.describe_contact_flow.return_value = {
            "ContactFlow": {
                "Id": "cf-123",
                "Arn": "arn:aws:connect:us-east-1:123:instance/test/contact-flow/cf-123",
                "Name": "Test Flow",
                "Type": "CONTACT_FLOW",
                "State": "ACTIVE",
                "Content": '{"Version": "2019-10-30", "StartAction": "PlayPrompt"}',
                "Tags": {}
            }
        }
        
        from contact_flows.contact_flow_tools import contact_flows_describe
        
        result = contact_flows_describe(
            instance_id="test-instance",
            contact_flow_id="cf-123"
        )
        
        assert result["status"] == "success"
        assert result["contact_flow"]["name"] == "Test Flow"
        assert result["contact_flow"]["content"]["Version"] == "2019-10-30"
    
    @patch("contact_flows.contact_flow_tools.connect_client")
    def test_contact_flows_describe_invalid_json(self, mock_client):
        """Test describing contact flow with invalid JSON content."""
        mock_client.describe_contact_flow.return_value = {
            "ContactFlow": {
                "Id": "cf-123",
                "Arn": "arn:aws:connect:us-east-1:123:instance/test/contact-flow/cf-123",
                "Name": "Test Flow",
                "Type": "CONTACT_FLOW",
                "State": "ACTIVE",
                "Content": "not valid json",
                "Tags": {}
            }
        }
        
        from contact_flows.contact_flow_tools import contact_flows_describe
        
        result = contact_flows_describe(
            instance_id="test-instance",
            contact_flow_id="cf-123"
        )
        
        assert result["status"] == "success"
        # Should handle invalid JSON gracefully
        assert "raw_content" in str(result["contact_flow"]["content"])
    
    @patch("contact_flows.contact_flow_tools.connect_client")
    def test_contact_flows_create_success(self, mock_client):
        """Test creating a contact flow."""
        mock_client.create_contact_flow.return_value = {
            "ContactFlowId": "cf-123",
            "ContactFlowArn": "arn:aws:connect:us-east-1:123:instance/test/contact-flow/cf-123"
        }
        
        from contact_flows.contact_flow_tools import contact_flows_create
        
        result = contact_flows_create(
            instance_id="test-instance",
            name="New Flow",
            content='{"Version": "2019-10-30"}',
            type="CONTACT_FLOW",
            description="A test flow"
        )
        
        assert result["status"] == "success"
        assert result["contact_flow_id"] == "cf-123"
        mock_client.create_contact_flow.assert_called_once()
    
    @patch("contact_flows.contact_flow_tools.connect_client")
    def test_contact_flows_delete_success(self, mock_client):
        """Test deleting a contact flow."""
        mock_client.delete_contact_flow.return_value = {}
        
        from contact_flows.contact_flow_tools import contact_flows_delete
        
        result = contact_flows_delete(
            instance_id="test-instance",
            contact_flow_id="cf-123"
        )
        
        assert result["status"] == "success"
        assert "cf-123" in result["message"]
    
    @patch("contact_flows.contact_flow_tools.connect_client")
    def test_contact_flows_update_content_success(self, mock_client):
        """Test updating contact flow content."""
        mock_client.update_contact_flow_content.return_value = {}
        
        from contact_flows.contact_flow_tools import contact_flows_update_content
        
        result = contact_flows_update_content(
            instance_id="test-instance",
            contact_flow_id="cf-123",
            content='{"Version": "2019-10-30"}'
        )
        
        assert result["status"] == "success"
        mock_client.update_contact_flow_content.assert_called_once()
    
    @patch("contact_flows.contact_flow_tools.connect_client")
    def test_contact_flows_search_with_filters(self, mock_client):
        """Test searching contact flows with filters."""
        mock_client.list_contact_flows.return_value = {
            "ContactFlowSummaryList": [
                {
                    "Id": "cf-123",
                    "Arn": "arn:aws:connect:us-east-1:123:instance/test/contact-flow/cf-123",
                    "Name": "Test Flow",
                    "Type": "CONTACT_FLOW",
                    "State": "ACTIVE"
                },
                {
                    "Id": "cf-456",
                    "Arn": "arn:aws:connect:us-east-1:123:instance/test/contact-flow/cf-456",
                    "Name": "Another Flow",
                    "Type": "OUTBOUND_WHISPER_FLOW",
                    "State": "ACTIVE"
                }
            ],
            "NextToken": None
        }
        
        from contact_flows.contact_flow_tools import contact_flows_search
        
        result = contact_flows_search(
            instance_id="test-instance",
            search_filter={
                "name_prefix": "Test",
                "contact_flow_types": ["CONTACT_FLOW"]
            }
        )
        
        assert result["status"] == "success"
        # Should filter to only flows starting with "Test"
        assert result["total_count"] >= 1


@pytest.mark.unit
class TestContactFlowToolsOutbound:
    """Test outbound contact flow creation tools."""
    
    @patch("contact_flows.contact_flow_tools.connect_client")
    @patch("contact_flows.contact_flow_tools.template_engine")
    def test_contact_flows_create_outbound_play_prompt(self, mock_engine, mock_client):
        """Test creating outbound play prompt flow."""
        mock_engine.validate_parameters.return_value = {"prompt_text": "Hello World"}
        mock_engine.render.return_value = {"Version": "2019-10-30", "StartAction": "PlayPrompt"}
        
        mock_client.create_contact_flow.return_value = {
            "ContactFlowId": "cf-123",
            "ContactFlowArn": "arn"
        }
        
        from contact_flows.contact_flow_tools import contact_flows_create_outbound
        
        result = contact_flows_create_outbound(
            instance_id="test-instance",
            name="Outbound Test",
            mode="PLAY_PROMPT",
            parameters={"prompt_text": "Hello World"}
        )
        
        assert result["status"] == "success"
        assert result["template_used"] == "play_prompt_outbound"
    
    @patch("contact_flows.contact_flow_tools.connect_client")
    @patch("contact_flows.contact_flow_tools.template_engine")
    def test_contact_flows_create_outbound_invalid_mode(self, mock_engine, mock_client):
        """Test creating outbound flow with invalid mode."""
        from contact_flows.contact_flow_tools import contact_flows_create_outbound
        
        result = contact_flows_create_outbound(
            instance_id="test-instance",
            name="Outbound Test",
            mode="INVALID_MODE",
            parameters={}
        )
        
        assert result["status"] == "error"
        assert "Invalid mode" in result["error"]
        mock_client.create_contact_flow.assert_not_called()
    
    @patch("contact_flows.contact_flow_tools.connect_client")
    @patch("contact_flows.contact_flow_tools.template_engine")
    def test_contact_flows_create_outbound_validation_error(self, mock_engine, mock_client):
        """Test creating outbound flow with validation error."""
        mock_engine.validate_parameters.side_effect = ValueError("Missing required parameter")
        
        from contact_flows.contact_flow_tools import contact_flows_create_outbound
        
        result = contact_flows_create_outbound(
            instance_id="test-instance",
            name="Outbound Test",
            mode="PLAY_PROMPT",
            parameters={}  # Missing required prompt_text
        )
        
        assert result["status"] == "error"
        assert "validation failed" in result["error"]


@pytest.mark.unit
class TestContactFlowToolsTemplate:
    """Test template-related contact flow tools."""
    
    @patch("contact_flows.contact_flow_tools.template_registry")
    def test_contact_flows_list_templates(self, mock_registry):
        """Test listing templates."""
        mock_registry.list_templates.return_value = [
            {"name": "template1", "category": "outbound"},
            {"name": "template2", "category": "inbound"}
        ]
        
        from contact_flows.contact_flow_tools import contact_flows_list_templates
        
        result = contact_flows_list_templates(category="outbound")
        
        assert result["status"] == "success"
        assert result["count"] == 2
    
    @patch("contact_flows.contact_flow_tools.template_registry")
    def test_contact_flows_get_template_schema(self, mock_registry):
        """Test getting template schema."""
        mock_registry.get_template_schema.return_value = {
            "type": "object",
            "properties": {"name": {"type": "string"}}
        }
        
        from contact_flows.contact_flow_tools import contact_flows_get_template_schema
        
        result = contact_flows_get_template_schema(template_name="my_template")
        
        assert result["status"] == "success"
        assert result["schema"]["type"] == "object"
    
    @patch("contact_flows.contact_flow_tools.template_engine")
    def test_contact_flows_validate_parameters_success(self, mock_engine):
        """Test validating parameters successfully."""
        mock_engine.validate_parameters.return_value = {"name": "Test", "timeout": 5}
        
        from contact_flows.contact_flow_tools import contact_flows_validate_parameters
        
        result = contact_flows_validate_parameters(
            template_name="my_template",
            parameters={"name": "Test"}
        )
        
        assert result["status"] == "success"
        assert result["validated_parameters"]["name"] == "Test"
    
    @patch("contact_flows.contact_flow_tools.template_engine")
    def test_contact_flows_validate_parameters_failure(self, mock_engine):
        """Test validating parameters with failure."""
        mock_engine.validate_parameters.side_effect = ValueError("Invalid parameter")
        
        from contact_flows.contact_flow_tools import contact_flows_validate_parameters
        
        result = contact_flows_validate_parameters(
            template_name="my_template",
            parameters={"invalid": "value"}
        )
        
        assert result["status"] == "error"
        assert "Invalid parameter" in result["error"]


@pytest.mark.unit
class TestContactFlowToolsVersion:
    """Test contact flow version management."""
    
    @patch("contact_flows.contact_flow_tools.connect_client")
    def test_contact_flows_create_version(self, mock_client):
        """Test creating a new version of contact flow."""
        mock_client.create_contact_flow_version.return_value = {
            "ContactFlowVersionId": "v2"
        }
        
        from contact_flows.contact_flow_tools import contact_flows_create_version
        
        result = contact_flows_create_version(
            instance_id="test-instance",
            contact_flow_id="cf-123",
            name="Version 2",
            description="New version"
        )
        
        assert result["status"] == "success"
        assert result["version_id"] == "v2"
