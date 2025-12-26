"""
Data normalization and transformation utilities.
Cleans and structures raw extracted data.
"""
import re
import hashlib
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse


class DataNormalizer:
    """
    Normalizes and cleans extracted data.
    
    Features:
    - Text cleaning and normalization
    - URL resolution (relative to absolute)
    - Duplicate detection and removal
    - Missing value handling
    - Data type inference
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the normalizer.
        
        Args:
            base_url: Base URL for resolving relative URLs
        """
        self.base_url = base_url
    
    def normalize(self, data: List[Dict[str, Any]], dedupe: bool = True) -> List[Dict[str, Any]]:
        """
        Normalize a list of extracted data items.
        
        Args:
            data: List of raw data dictionaries
            dedupe: Whether to remove duplicates
            
        Returns:
            List of normalized data dictionaries
        """
        normalized = []
        
        for item in data:
            normalized_item = self._normalize_item(item)
            if normalized_item:
                normalized.append(normalized_item)
        
        if dedupe:
            normalized = self._remove_duplicates(normalized)
        
        return normalized
    
    def _normalize_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize a single data item."""
        result = {}
        has_content = False
        
        for key, value in item.items():
            normalized_value = self._normalize_value(key, value)
            result[key] = normalized_value
            
            # Check if we have actual content
            if normalized_value is not None and normalized_value != '':
                if isinstance(normalized_value, list) and len(normalized_value) > 0:
                    has_content = True
                elif not isinstance(normalized_value, list):
                    has_content = True
        
        return result if has_content else None
    
    def _normalize_value(self, key: str, value: Any) -> Any:
        """Normalize a single value based on its type and field name."""
        if value is None:
            return None
        
        if isinstance(value, list):
            return [self._normalize_value(key, v) for v in value if v is not None]
        
        if isinstance(value, str):
            value = self._clean_text(value)
            
            # URL fields - resolve relative URLs
            if self._is_url_field(key) and value:
                value = self._resolve_url(value)
            
            # Price fields - normalize format
            if self._is_price_field(key) and value:
                value = self._normalize_price(value)
            
            return value
        
        return value
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ''
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove zero-width characters
        text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text
    
    def _is_url_field(self, key: str) -> bool:
        """Check if a field likely contains a URL."""
        url_indicators = ['url', 'link', 'href', 'src', 'image', 'img', 'photo']
        key_lower = key.lower()
        return any(indicator in key_lower for indicator in url_indicators)
    
    def _is_price_field(self, key: str) -> bool:
        """Check if a field likely contains a price."""
        price_indicators = ['price', 'cost', 'amount', 'fee', 'rate']
        key_lower = key.lower()
        return any(indicator in key_lower for indicator in price_indicators)
    
    def _resolve_url(self, url: str) -> str:
        """Resolve a relative URL to absolute."""
        if not url or url.startswith(('http://', 'https://', 'data:', 'javascript:')):
            return url
        
        if self.base_url:
            return urljoin(self.base_url, url)
        
        return url
    
    def _normalize_price(self, price: str) -> str:
        """Normalize price format."""
        # Keep original format but clean up
        price = re.sub(r'\s+', '', price)
        return price
    
    def _remove_duplicates(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate items based on content hash."""
        seen = set()
        unique = []
        
        for item in data:
            # Create a hash of the item content
            item_hash = self._hash_item(item)
            
            if item_hash not in seen:
                seen.add(item_hash)
                unique.append(item)
        
        return unique
    
    def _hash_item(self, item: Dict[str, Any]) -> str:
        """Create a hash of an item for duplicate detection."""
        # Sort keys for consistent hashing
        content = str(sorted(item.items()))
        return hashlib.md5(content.encode()).hexdigest()
    
    def add_metadata(self, data: List[Dict[str, Any]], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Add metadata to each item."""
        for item in data:
            item['_metadata'] = metadata
        return data

