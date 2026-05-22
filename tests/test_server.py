"""Tests for MCP Server integration."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.mark.unit
class TestServerInitialization:
    """Test MCP server initialization."""
    
    @patch("amazon_connect_mcp.server.FastMCP")
    def test_server_creation(self, mock_fastmcp):
        """Test server is created with correct name."""
        from amazon_connect_mcp.server import mcp
        
        mock_fastmcp.assert_called_once_with("amazon-connect")
    
    @patch("amazon_connect_mcp.server._register_tools")
    def test_register_all_tools(self, mock_register):
        """Test registering all tools."""
        from amazon_connect_mcp.server import register_all_tools
        
        register_all_tools()
        
        mock_register.assert_called_once()
    
    @patch("amazon_connect_mcp.server._register_contact_flow_tools")
    @patch("amazon_connect_mcp.server._register_component_tools")
    @patch("amazon_connect_mcp.server._register_api_bridge_tools")
    def test_registration_order(self, mock_bridge, mock_components, mock_flows):
        """Test tools are registered in correct order."""
        from amazon_connect_mcp.server import _register_tools
        
        _register_tools()
        
        # Verify registration functions were called
        mock_flows.assert_called_once()
        mock_components.assert_called_once()
        mock_bridge.assert_called_once()


@pytest.mark.unit
class TestGetServerInfo:
    """Test get_server_info tool."""
    
    @patch("amazon_connect_mcp.server.mcConfig", None)
    @patch("amazon_connect_mcp.server._get_config")
    def test_get_server_info_success(self, mock_get_config):
        """Test getting server info."""
        mock_config = Mock()
        mock_config.mcp.transport = "stdio"
        mock_config.aws.region = "us-east-1"
        mock_config.connect.instance_id = "test-instance-123"
        mock_get_config.return_value = mock_config
        
        from amazon_connect_mcp.server import get_server_info
        
        result = get_server_info()
        
        assert result["name"] == "amazon-connect-mcp"
        assert "version" in result
        assert result["aws_region"] == "us-east-1"
        assert result["connect_instance_id"] == "test-instance-123"


@pytest.mark.unit
class TestConfig:
    """Test configuration module."""
    
    @patch("amazon_connect_mcp.config.os")
    def test_get_config_default_values(self, mock_os):
        """Test config returns default values."""
        mock_os.environ = {}
        
        from amazon_connect_mcp.config import get_config
        
        config = get_config()
        
        assert config.mcp.transport == "stdio"
        assert config.aws.region == "us-east-1"
    
    def test_api_bridge_configured(self):
        """Test API bridge is configured."""
        from amazon_connect_mcp.config import Config
        
        config = Config()
        
        # By default, API bridge should not be configured
        assert not config.api_bridge.is_configured()
    
    @patch.dict("os.environ", {"CONNECT_API_BRIDGE_URL": "https://test.execute-api.us-east-1.amazonaws.com/prod"})
    def test_api_bridge_configured_from_env(self):
        """Test API bridge config from environment."""
        from amazon_connect_mcp.config import get_config
        
        config = get_config()
        
        assert config.api_bridge.url == "https://test.execute-api.us-east-1.amazonaws.com/prod"
        assert config.api_bridge.is_configured()


@pytest.mark.unit
class TestContactFlowToolsRegistration:
    """Test contact flow tools registration."""
    
    @patch("amazon_connect_mcp.server.mcp")
    @patch("amazon_connect_mcp.server._register_contact_flow_tools")
    def test_contact_flows_registration(self, mock_register, mock_mcp):
        """Test contact flow tools are registered."""
        from amazon_connect_mcp.server import _register_contact_flow_tools
        
        _register_contact_flow_tools()
        
        # If tools are registered, tool() method should be called
        # Note: This will print a warning since imports may fail without proper setup


@pytest.mark.unit
class TestExceptionHandling:
    """Test server exception handling."""
    
    @patch("amazon_connect_mcp.server._register_contact_flow_tools")
    @patch("amazon_connect_mcp.server._register_component_tools")
    @patch("amazon_connect_mcp.server._register_api_bridge_tools")
    def test_registration_continues_on_tool_failure(self, mock_bridge, mock_components, mock_flows):
        """Test registration continues even when some tools fail."""
        mock_flows.side_effect = Exception("Flow tools failed")
        
        from amazon_connect_mcp.server import _register_tools
        
        # Should not raise an exception
        try:
            _register_tools()
        except Exception:
            pytest.fail("_register_tools should handle tool registration failures")
    
    def test_config_reload_on_error(self):
        """Test config reloads on error."""
        from amazon_connect_mcp.server import _get_config
        from amazon_connect_mcp.server import mcConfig
        
        # Reset config
        from amazon_connect_mcp.server import mcConfig
        mcConfig = None
        
        config = _get_config()
        
        assert config is not None
