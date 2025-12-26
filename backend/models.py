"""
Pydantic models for request/response validation and data structures.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any, Union
from enum import Enum


class SelectorType(str, Enum):
    """Type of selector used for extraction."""
    CSS = "css"
    XPATH = "xpath"


class ScraperType(str, Enum):
    """Type of scraper to use."""
    AUTO = "auto"
    STATIC = "static"
    DYNAMIC = "dynamic"


class ExtractionField(BaseModel):
    """Definition of a field to extract from the page."""
    name: str = Field(..., description="Name of the field to extract")
    selector: str = Field(..., description="CSS selector or XPath expression")
    selector_type: SelectorType = Field(default=SelectorType.CSS, description="Type of selector")
    attribute: Optional[str] = Field(default=None, description="HTML attribute to extract (e.g., 'href', 'src'). If None, extracts text content")
    multiple: bool = Field(default=False, description="Whether to extract multiple matching elements")
    default: Optional[str] = Field(default=None, description="Default value if extraction fails")


class PaginationConfig(BaseModel):
    """Configuration for handling pagination."""
    enabled: bool = Field(default=False, description="Whether pagination is enabled")
    next_page_selector: Optional[str] = Field(default=None, description="Selector for the next page button/link")
    max_pages: int = Field(default=5, description="Maximum number of pages to scrape")


class ScrapeRequest(BaseModel):
    """Request model for initiating a scrape operation."""
    url: str = Field(..., description="Target URL to scrape")
    scraper_type: ScraperType = Field(default=ScraperType.AUTO, description="Type of scraper to use")
    fields: List[ExtractionField] = Field(..., description="Fields to extract from the page")
    container_selector: Optional[str] = Field(default=None, description="CSS selector for the container element (for multiple items)")
    pagination: Optional[PaginationConfig] = Field(default=None, description="Pagination configuration")
    wait_for_selector: Optional[str] = Field(default=None, description="Wait for this selector before scraping (dynamic pages)")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    delay: float = Field(default=1.0, description="Delay between requests in seconds")


class ScrapeError(BaseModel):
    """Error information from a scrape operation."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")


class ScrapeResult(BaseModel):
    """Result of a successful scrape operation."""
    url: str = Field(..., description="URL that was scraped")
    scraper_used: str = Field(..., description="Type of scraper that was used")
    data: List[Dict[str, Any]] = Field(..., description="Extracted data")
    total_items: int = Field(..., description="Total number of items extracted")
    pages_scraped: int = Field(default=1, description="Number of pages scraped")
    elapsed_time: float = Field(..., description="Time taken to scrape in seconds")


class ScrapeResponse(BaseModel):
    """API response for a scrape operation."""
    success: bool = Field(..., description="Whether the operation was successful")
    result: Optional[ScrapeResult] = Field(default=None, description="Scrape result if successful")
    error: Optional[ScrapeError] = Field(default=None, description="Error information if failed")


class PageTypeDetectionResult(BaseModel):
    """Result of automatic page type detection."""
    is_dynamic: bool = Field(..., description="Whether the page requires JavaScript rendering")
    confidence: float = Field(..., description="Confidence score (0-1)")
    indicators: List[str] = Field(..., description="Indicators that led to the detection")
    recommended_scraper: ScraperType = Field(..., description="Recommended scraper type")


class ConfigPreset(BaseModel):
    """Preset configuration for common website types."""
    name: str = Field(..., description="Name of the preset")
    description: str = Field(..., description="Description of what this preset extracts")
    container_selector: Optional[str] = Field(default=None)
    fields: List[ExtractionField] = Field(...)
    suitable_for: List[str] = Field(default=[], description="Types of websites this preset works well with")

