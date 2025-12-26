"""
Input validation utilities for the web scraper.
"""
import re
from typing import Tuple, Optional, List
from urllib.parse import urlparse


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, code: str, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a URL.
    
    Args:
        url: The URL to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "URL is required"
    
    if not isinstance(url, str):
        return False, "URL must be a string"
    
    url = url.strip()
    
    # Check protocol
    if not url.startswith(('http://', 'https://')):
        return False, "URL must start with http:// or https://"
    
    try:
        parsed = urlparse(url)
        
        # Check for host
        if not parsed.netloc:
            return False, "URL must include a domain"
        
        # Basic domain validation
        if '.' not in parsed.netloc and parsed.netloc != 'localhost':
            return False, "Invalid domain"
        
        return True, None
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"


def validate_css_selector(selector: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a CSS selector (basic validation).
    
    Args:
        selector: The CSS selector to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not selector:
        return False, "Selector is required"
    
    if not isinstance(selector, str):
        return False, "Selector must be a string"
    
    selector = selector.strip()
    
    # Check for empty
    if not selector:
        return False, "Selector cannot be empty"
    
    # Check for obviously invalid patterns
    invalid_patterns = [
        r'^[0-9]',  # Cannot start with a number
        r'^\.',     # Valid - class selector
        r'^#',      # Valid - ID selector
    ]
    
    # Very basic validation - just check for balanced brackets
    if selector.count('[') != selector.count(']'):
        return False, "Unbalanced square brackets in selector"
    
    if selector.count('(') != selector.count(')'):
        return False, "Unbalanced parentheses in selector"
    
    return True, None


def validate_xpath(xpath: str) -> Tuple[bool, Optional[str]]:
    """
    Validate an XPath expression (basic validation).
    
    Args:
        xpath: The XPath expression to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not xpath:
        return False, "XPath is required"
    
    if not isinstance(xpath, str):
        return False, "XPath must be a string"
    
    xpath = xpath.strip()
    
    # Check for empty
    if not xpath:
        return False, "XPath cannot be empty"
    
    # Basic structure checks
    if xpath.count('[') != xpath.count(']'):
        return False, "Unbalanced square brackets in XPath"
    
    if xpath.count('(') != xpath.count(')'):
        return False, "Unbalanced parentheses in XPath"
    
    # Check for quotes
    single_quotes = xpath.count("'")
    double_quotes = xpath.count('"')
    if single_quotes % 2 != 0 or double_quotes % 2 != 0:
        return False, "Unbalanced quotes in XPath"
    
    return True, None


def sanitize_field_name(name: str) -> str:
    """
    Sanitize a field name for use as a key.
    
    Args:
        name: The field name
        
    Returns:
        Sanitized field name
    """
    if not name:
        return "field"
    
    # Replace spaces and special characters
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name.strip())
    
    # Remove leading digits
    sanitized = re.sub(r'^[0-9]+', '', sanitized)
    
    # Ensure not empty
    if not sanitized:
        return "field"
    
    return sanitized.lower()


def validate_extraction_fields(fields: List[dict]) -> Tuple[bool, Optional[str]]:
    """
    Validate a list of extraction field configurations.
    
    Args:
        fields: List of field configurations
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not fields:
        return False, "At least one extraction field is required"
    
    seen_names = set()
    
    for i, field in enumerate(fields):
        # Check required keys
        if 'name' not in field or not field['name']:
            return False, f"Field {i + 1}: name is required"
        
        if 'selector' not in field or not field['selector']:
            return False, f"Field {i + 1}: selector is required"
        
        # Check for duplicate names
        name = field['name'].lower()
        if name in seen_names:
            return False, f"Duplicate field name: {field['name']}"
        seen_names.add(name)
        
        # Validate selector based on type
        selector_type = field.get('selector_type', 'css')
        if selector_type == 'css':
            is_valid, error = validate_css_selector(field['selector'])
        else:
            is_valid, error = validate_xpath(field['selector'])
        
        if not is_valid:
            return False, f"Field '{field['name']}': {error}"
    
    return True, None

