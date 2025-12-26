"""
Abstract base class for all scraper implementations.
Defines the interface that all scrapers must implement.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from lxml import etree
import re

from backend.models import ExtractionField, SelectorType


class BaseScraper(ABC):
    """
    Abstract base class for scraper implementations.
    
    Implements the Strategy pattern - each concrete scraper provides
    its own implementation for fetching page content, while sharing
    common extraction logic.
    """
    
    def __init__(self):
        self.name = "base"
    
    @abstractmethod
    async def fetch_page(self, url: str, timeout: int = 30, wait_for_selector: Optional[str] = None) -> str:
        """
        Fetch the HTML content of a page.
        
        Args:
            url: The URL to fetch
            timeout: Request timeout in seconds
            wait_for_selector: Optional selector to wait for (for dynamic pages)
            
        Returns:
            The HTML content of the page
        """
        pass
    
    @abstractmethod
    async def close(self):
        """Clean up any resources used by the scraper."""
        pass
    
    def extract_data(
        self,
        html: str,
        fields: List[ExtractionField],
        container_selector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract data from HTML using the provided field definitions.
        
        Args:
            html: The HTML content to parse
            fields: List of field definitions for extraction
            container_selector: Optional selector for container elements (for multiple items)
            
        Returns:
            List of dictionaries containing extracted data
        """
        soup = BeautifulSoup(html, 'lxml')
        results = []
        
        if container_selector:
            # Extract multiple items from containers
            containers = soup.select(container_selector)
            for container in containers:
                item = self._extract_fields_from_element(container, fields)
                if any(v is not None for v in item.values()):
                    results.append(item)
        else:
            # Extract single item from the whole page
            item = self._extract_fields_from_element(soup, fields)
            results.append(item)
        
        return results
    
    def _extract_fields_from_element(
        self,
        element: BeautifulSoup,
        fields: List[ExtractionField]
    ) -> Dict[str, Any]:
        """
        Extract all fields from a single element.
        
        Args:
            element: BeautifulSoup element to extract from
            fields: List of field definitions
            
        Returns:
            Dictionary of field name -> extracted value
        """
        result = {}
        
        for field in fields:
            try:
                if field.selector_type == SelectorType.CSS:
                    value = self._extract_css(element, field)
                else:
                    value = self._extract_xpath(element, field)
                
                result[field.name] = value if value is not None else field.default
            except Exception:
                result[field.name] = field.default
        
        return result
    
    def _extract_css(self, element: BeautifulSoup, field: ExtractionField) -> Any:
        """Extract data using CSS selector."""
        if field.multiple:
            elements = element.select(field.selector)
            return [self._get_element_value(el, field.attribute) for el in elements]
        else:
            el = element.select_one(field.selector)
            return self._get_element_value(el, field.attribute) if el else None
    
    def _extract_xpath(self, element: BeautifulSoup, field: ExtractionField) -> Any:
        """Extract data using XPath expression."""
        # Convert BeautifulSoup to lxml for XPath support
        html_str = str(element)
        tree = etree.HTML(html_str)
        
        elements = tree.xpath(field.selector)
        
        if not elements:
            return [] if field.multiple else None
        
        if field.multiple:
            return [self._get_xpath_value(el, field.attribute) for el in elements]
        else:
            return self._get_xpath_value(elements[0], field.attribute)
    
    def _get_element_value(self, element: BeautifulSoup, attribute: Optional[str]) -> Optional[str]:
        """Get value from a BeautifulSoup element."""
        if element is None:
            return None
        if attribute:
            return element.get(attribute)
        return self._clean_text(element.get_text())
    
    def _get_xpath_value(self, element, attribute: Optional[str]) -> Optional[str]:
        """Get value from an lxml element."""
        if element is None:
            return None
        if isinstance(element, str):
            return self._clean_text(element)
        if attribute:
            return element.get(attribute)
        return self._clean_text(element.text_content() if hasattr(element, 'text_content') else str(element))
    
    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        """Clean and normalize extracted text."""
        if text is None:
            return None
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        return text if text else None

