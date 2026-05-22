"""Amazon Connect MCP Server - Configuration.

This module handles configuration loading from environment variables
and provides AWS credential handling and Connect instance settings.
"""

import os
from typing import Optional
from dataclasses import dataclass, field
from pathlib import Path


def _get_env_or_default(key: str, default: str = "") -> str:
    """Get environment variable or default value."""
    return os.environ.get(key, default)


def _get_bool_env(key: str, default: bool = False) -> bool:
    """Get boolean environment variable."""
    value = os.environ.get(key, "").lower()
    return value in ("true", "1", "yes", "on") if value else default


@dataclass
class AWSConfig:
    """AWS Configuration settings."""
    
    region: str = field(default_factory=lambda: _get_env_or_default("AWS_REGION", "us-east-1"))
    profile: str = field(default_factory=lambda: _get_env_or_default("AWS_PROFILE", ""))
    access_key_id: str = field(default_factory=lambda: _get_env_or_default("AWS_ACCESS_KEY_ID", ""))
    secret_access_key: str = field(default_factory=lambda: _get_env_or_default("AWS_SECRET_ACCESS_KEY", ""))
    session_token: str = field(default_factory=lambda: _get_env_or_default("AWS_SESSION_TOKEN", ""))
    
    def get_boto3_session_kwargs(self) -> dict:
        """Get kwargs for boto3 Session creation."""
        kwargs = {"region_name": self.region}
        if self.profile:
            kwargs["profile_name"] = self.profile
        return kwargs


@dataclass
class ConnectInstanceConfig:
    """Amazon Connect instance configuration."""
    
    instance_id: str = field(default_factory=lambda: _get_env_or_default("CONNECT_INSTANCE_ID", ""))
    instance_alias: str = field(default_factory=lambda: _get_env_or_default("CONNECT_INSTANCE_ALIAS", ""))


@dataclass
class APIBridgeConfig:
    """Lambda/API Gateway bridge configuration."""
    
    enabled: bool = field(default_factory=lambda: _get_bool_env("CONNECT_API_BRIDGE_ENABLED", False))
    base_url: str = field(default_factory=lambda: _get_env_or_default("CONNECT_API_BRIDGE_URL", ""))
    api_key: str = field(default_factory=lambda: _get_env_or_default("CONNECT_API_BRIDGE_API_KEY", ""))
    
    def is_configured(self) -> bool:
        """Check if API bridge is properly configured."""
        return self.enabled and bool(self.base_url)


@dataclass
class MCPConfig:
    """MCP Server configuration."""
    
    server_name: str = field(default_factory=lambda: _get_env_or_default("MCP_SERVER_NAME", "amazon-connect-mcp"))
    transport: str = field(default_factory=lambda: _get_env_or_default("MCP_TRANSPORT", "stdio"))
    port: int = field(default_factory=lambda: int(_get_env_or_default("MCP_PORT", "8000")))
    
    @property
    def is_stdio_mode(self) -> bool:
        """Check if running in stdio mode."""
        return self.transport.lower() == "stdio"


@dataclass
class Config:
    """Main configuration class combining all settings."""
    
    aws: AWSConfig = field(default_factory=AWSConfig)
    connect: ConnectInstanceConfig = field(default_factory=ConnectInstanceConfig)
    api_bridge: APIBridgeConfig = field(default_factory=APIBridgeConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)
    
    # Templates directory
    templates_dir: Path = field(default_factory=lambda: Path(
        _get_env_or_default("TEMPLATES_DIR", str(Path(__file__).parent / "templates"))
    ))
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls()
    
    def validate_aws_credentials(self) -> tuple[bool, Optional[str]]:
        """Validate AWS credentials are available.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for AWS profile
        if self.aws.profile:
            return True, None
        
        # Check for explicit credentials
        if self.aws.access_key_id and self.aws.secret_access_key:
            return True, None
        
        # Check for default credentials via boto3
        try:
            import boto3
            session = boto3.Session()
            credentials = session.get_credentials()
            if credentials:
                return True, None
        except Exception:
            pass
        
        return False, "AWS credentials not found. Set AWS_PROFILE or AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY"
    
    def validate_connect_instance(self) -> tuple[bool, Optional[str]]:
        """Validate Connect instance configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.connect.instance_id:
            return False, "CONNECT_INSTANCE_ID not set"
        return True, None
    
    def get_default_instance_id(self) -> Optional[str]:
        """Get default Connect instance ID if configured."""
        return self.connect.instance_id if self.connect.instance_id else None


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create the global configuration instance.
    
    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def reload_config() -> Config:
    """Reload configuration from environment variables.
    
    Returns:
        Fresh Config instance
    """
    global _config
    _config = Config.from_env()
    return _config
