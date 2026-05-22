"""Template registry for managing contact flow templates."""

from typing import Dict, List, Optional
from pathlib import Path
import json

from .engine import TemplateEngine


class TemplateRegistry:
    """Registry for managing and accessing contact flow templates."""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        self.engine = TemplateEngine(templates_dir)
        self._templates: Dict[str, Dict] = {}
        self._refresh_registry()
    
    def _refresh_registry(self):
        """Refresh the template registry from disk."""
        self._templates.clear()
        
        for template_name in self.engine.list_templates():
            try:
                template = self.engine.load_template(template_name)
                self._templates[template_name] = template
            except Exception:
                continue  # Skip invalid templates
    
    def get_template(self, name: str) -> Optional[Dict]:
        """Get a template by name."""
        if name not in self._templates:
            try:
                self._templates[name] = self.engine.load_template(name)
            except FileNotFoundError:
                return None
        return self._templates.get(name)
    
    def list_templates(
        self,
        category: Optional[str] = None,
        flow_type: Optional[str] = None
    ) -> List[Dict]:
        """List templates with optional filtering.
        
        Args:
            category: Filter by category (outbound, inbound, shared)
            flow_type: Filter by flow type (basic, appointment, survey, etc.)
            
        Returns:
            List of template metadata
        """
        templates = []
        
        for name in self.engine.list_templates():
            info = self.engine.get_template_info(name)
            
            # Apply category filter
            if category:
                path = self.engine.templates_dir / f"{name}.json"
                if not path.exists():
                    path = self.engine.templates_dir / category / f"{name}.json"
                    if not path.exists():
                        continue
            
            # Apply flow type filter
            if flow_type and flow_type not in name.lower():
                continue
            
            templates.append(info)
        
        return templates
    
    def create_contact_flow_payload(
        self,
        template_name: str,
        parameters: Dict,
        name: str,
        description: str = "",
        tags: Optional[Dict[str, str]] = None
    ) -> Dict:
        """Create a complete contact flow payload for AWS API.
        
        Args:
            template_name: Name of the template to use
            parameters: Template parameters
            name: Name for the contact flow
            description: Description for the contact flow
            tags: Optional tags for the contact flow
            
        Returns:
            Payload ready for CreateContactFlow or UpdateContactFlowContent
        """
        # Render template content
        rendered_content = self.engine.render(template_name, parameters)
        
        # Build the payload
        payload = {
            "Name": name,
            "Description": description,
            "Content": json.dumps(rendered_content),
            "Type": "OUTBOUND"  # or determine from template
        }
        
        if tags:
            payload["Tags"] = tags
        
        return payload
    
    def get_template_schema(self, template_name: str) -> Dict:
        """Get the JSON schema for a template's parameters."""
        template = self.get_template(template_name)
        if not template:
            raise FileNotFoundError(f"Template '{template_name}' not found")
        
        variables = self.engine.extract_variables(template)
        
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": f"{template_name} Parameters",
            "properties": {},
            "required": []
        }
        
        type_mapping = {
            "string": "string",
            "integer": "integer",
            "boolean": "boolean",
            "arn": "string",
            "enum": "string"
        }
        
        for var in variables:
            prop = {
                "type": type_mapping.get(var.var_type, "string"),
                "description": var.description
            }
            
            if var.default is not None:
                prop["default"] = var.default
            
            if var.allowed_values:
                prop["enum"] = var.allowed_values
            
            if var.min_value is not None:
                prop["minimum"] = var.min_value
            if var.max_value is not None:
                prop["maximum"] = var.max_value
            
            schema["properties"][var.name] = prop
            
            if var.required:
                schema["required"].append(var.name)
        
        return schema
