"""Contact Flow Template Engine for parameterizing and rendering flow JSON."""

import json
import re
from typing import Any, Dict, List, Optional, Union
from pathlib import Path


class TemplateVariable:
    """Represents a template variable with validation."""
    
    def __init__(
        self,
        name: str,
        var_type: str,
        required: bool = False,
        default: Any = None,
        description: str = "",
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        allowed_values: Optional[List[str]] = None,
        ssml_enabled: bool = False
    ):
        self.name = name
        self.var_type = var_type
        self.required = required
        self.default = default
        self.description = description
        self.min_value = min_value
        self.max_value = max_value
        self.allowed_values = allowed_values
        self.ssml_enabled = ssml_enabled
    
    def validate(self, value: Any) -> Any:
        """Validate and potentially transform a value."""
        if value is None:
            if self.required:
                raise ValueError(f"Required variable '{self.name}' is missing")
            return self.default
        
        # Type validation
        if self.var_type == "string" and not isinstance(value, str):
            raise ValueError(f"Variable '{self.name}' must be a string")
        elif self.var_type == "integer":
            if not isinstance(value, int):
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    raise ValueError(f"Variable '{self.name}' must be an integer")
        elif self.var_type == "boolean":
            if isinstance(value, str):
                value = value.lower() in ("true", "1", "yes", "on")
            else:
                value = bool(value)
        elif self.var_type == "arn":
            if not isinstance(value, str):
                raise ValueError(f"Variable '{self.name}' must be an ARN string")
            if not value.startswith("arn:"):
                raise ValueError(f"Variable '{self.name}' must be a valid ARN")
        elif self.var_type == "enum":
            if self.allowed_values and str(value) not in self.allowed_values:
                raise ValueError(
                    f"Variable '{self.name}' must be one of: {self.allowed_values}"
                )
        
        # Range validation
        if self.min_value is not None and value < self.min_value:
            raise ValueError(
                f"Variable '{self.name}' must be >= {self.min_value}"
            )
        if self.max_value is not None and value > self.max_value:
            raise ValueError(
                f"Variable '{self.name}' must be <= {self.max_value}"
            )
        
        return value


class TemplateEngine:
    """Engine for rendering parameterized contact flow templates."""
    
    VARIABLE_PATTERN = re.compile(r"\{\{(\w+)\}\}")
    
    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or Path(__file__).parent
        self._template_cache: Dict[str, Dict] = {}
        self._variable_cache: Dict[str, List[TemplateVariable]] = {}
    
    def load_template(self, template_name: str) -> Dict:
        """Load a template from file or cache."""
        if template_name in self._template_cache:
            return self._template_cache[template_name]
        
        template_path = self.templates_dir / f"{template_name}.json"
        if not template_path.exists():
            # Check subdirectories
            for subdir in ["outbound", "inbound", "shared"]:
                alt_path = self.templates_dir / subdir / f"{template_name}.json"
                if alt_path.exists():
                    template_path = alt_path
                    break
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template '{template_name}' not found")
        
        # Read raw content first (templates may have non-JSON placeholders)
        with open(template_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        # Find all {{variable}} placeholders in the raw template
        placeholder_pattern = re.compile(r'\{\{(\w+)\}\}')
        placeholders = set(placeholder_pattern.findall(raw_content))
        
        # Create temporary JSON-compatible version by replacing placeholders
        # with dummy values that won't break JSON parsing
        temp_content = raw_content
        for placeholder in placeholders:
            # The placeholder pattern is {{variable_name}}
            placeholder_pattern_str = '{{' + placeholder + '}}'
            
            # Use type-specific defaults based on common variable naming
            if 'timeout' in placeholder.lower() or 'wait' in placeholder.lower():
                temp_content = temp_content.replace(placeholder_pattern_str, '0')
            elif 'arn' in placeholder.lower():
                temp_content = temp_content.replace(
                    placeholder_pattern_str, 
                    '"arn:aws:temp:placeholder"'
                )
            elif 'boolean' in placeholder.lower() or 'enabled' in placeholder.lower() or \
                 'needed' in placeholder.lower() or placeholder == 'callback_needed':
                temp_content = temp_content.replace(placeholder_pattern_str, 'false')
            elif placeholder in ['min', 'max']:  # Integer values
                temp_content = temp_content.replace(placeholder_pattern_str, '1')
            else:
                # Default to empty string for text variables 
                temp_content = temp_content.replace(placeholder_pattern_str, '""')
        
        # Parse the JSON with placeholders replaced
        template = json.loads(temp_content)
        
        self._template_cache[template_name] = template
        return template
    
    def extract_variables(self, template: Dict) -> List[TemplateVariable]:
        """Extract variable definitions from a template."""
        variables = []
        
        if "Variables" in template:
            for name, config in template["Variables"].items():
                variables.append(TemplateVariable(
                    name=name,
                    var_type=config.get("type", "string"),
                    required=config.get("required", False),
                    default=config.get("default"),
                    description=config.get("description", ""),
                    min_value=config.get("min"),
                    max_value=config.get("max"),
                    allowed_values=config.get("values"),
                    ssml_enabled=config.get("ssml_enabled", False)
                ))
        
        return variables
    
    def find_template_variables(self, content: Any) -> set:
        """Find all {{variable}} placeholders in content."""
        variables = set()
        
        if isinstance(content, dict):
            for value in content.values():
                variables.update(self.find_template_variables(value))
        elif isinstance(content, list):
            for item in content:
                variables.update(self.find_template_variables(item))
        elif isinstance(content, str):
            matches = self.VARIABLE_PATTERN.findall(content)
            variables.update(matches)
        
        return variables
    
    def render_string(self, value: str, variables: Dict[str, Any]) -> str:
        """Render a string template with variable substitution."""
        def replace_var(match):
            var_name = match.group(1)
            if var_name in variables:
                return str(variables[var_name])
            return match.group(0)  # Keep original if not found
        
        return self.VARIABLE_PATTERN.sub(replace_var, value)
    
    def render_recursive(self, content: Any, variables: Dict[str, Any]) -> Any:
        """Recursively render template content with variable substitution."""
        if isinstance(content, dict):
            rendered = {}
            for key, value in content.items():
                # Don't render variable definitions
                if key == "Variables":
                    continue
                rendered[key] = self.render_recursive(value, variables)
            return rendered
        elif isinstance(content, list):
            return [self.render_recursive(item, variables) for item in content]
        elif isinstance(content, str):
            return self.render_string(content, variables)
        else:
            return content
    
    def validate_parameters(
        self,
        template_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate parameters against template variable definitions."""
        template = self.load_template(template_name)
        variables = self.extract_variables(template)
        
        validated = {}
        required_vars = {v.name for v in variables if v.required}
        provided_vars = set(parameters.keys())
        
        # Check for missing required variables
        missing = required_vars - provided_vars
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        
        # Validate each provided parameter
        var_map = {v.name: v for v in variables}
        for name, value in parameters.items():
            if name in var_map:
                validated[name] = var_map[name].validate(value)
            else:
                # Warn about unknown variables but still include them
                validated[name] = value
        
        # Set defaults for optional variables not provided
        for var in variables:
            if var.name not in validated and var.default is not None:
                validated[var.name] = var.default
        
        return validated
    
    def render(
        self,
        template_name: str,
        parameters: Dict[str, Any]
    ) -> Dict:
        """Render a template with validated parameters."""
        # Validate parameters first
        validated_params = self.validate_parameters(template_name, parameters)
        
        # Load and render template
        template = self.load_template(template_name)
        rendered = self.render_recursive(template, validated_params)
        
        return rendered
    
    def get_template_info(self, template_name: str) -> Dict:
        """Get template metadata and variable information."""
        template = self.load_template(template_name)
        variables = self.extract_variables(template)
        found_vars = self.find_template_variables(template)
        
        return {
            "name": template_name,
            "version": template.get("Version", "unknown"),
            "start_action": template.get("StartAction"),
            "variable_count": len(variables),
            "variables": [
                {
                    "name": v.name,
                    "type": v.var_type,
                    "required": v.required,
                    "default": v.default,
                    "description": v.description
                }
                for v in variables
            ],
            "placeholders_found": list(found_vars)
        }
    
    def list_templates(self) -> List[str]:
        """List available templates in the templates directory."""
        templates = []
        
        for pattern in ["*.json", "outbound/*.json", "inbound/*.json", "shared/*.json"]:
            for path in self.templates_dir.glob(pattern):
                template_name = path.stem
                templates.append(template_name)
        
        return sorted(templates)
