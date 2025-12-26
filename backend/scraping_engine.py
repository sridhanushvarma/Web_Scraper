"""
Core scraping engine that orchestrates the entire scraping process.
"""
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple

from backend.models import (
    ScrapeRequest, ScrapeResult, ScrapeError, ScrapeResponse,
    ScraperType, ExtractionField
)
from backend.scrapers import ScraperFactory
from backend.utils.data_normalizer import DataNormalizer
from backend.config.config_loader import ConfigLoader


class ScrapingEngine:
    """
    Main scraping engine that coordinates all scraping operations.
    
    Features:
    - Automatic scraper selection
    - Pagination support
    - Data normalization
    - Error handling with fallbacks
    """
    
    def __init__(self):
        self.config_loader = ConfigLoader()
    
    async def scrape(self, request: ScrapeRequest) -> ScrapeResponse:
        """
        Execute a scraping operation based on the request.
        
        Args:
            request: The scrape request with URL and extraction rules
            
        Returns:
            ScrapeResponse with results or error information
        """
        start_time = time.time()
        
        try:
            # Validate URL
            if not request.url or not request.url.startswith(('http://', 'https://')):
                return ScrapeResponse(
                    success=False,
                    error=ScrapeError(
                        code="INVALID_URL",
                        message="URL must start with http:// or https://",
                        details={"url": request.url}
                    )
                )
            
            # Validate fields
            if not request.fields:
                return ScrapeResponse(
                    success=False,
                    error=ScrapeError(
                        code="NO_FIELDS",
                        message="At least one extraction field is required",
                        details=None
                    )
                )
            
            # Execute scraping
            all_data = []
            pages_scraped = 0
            current_url = request.url
            scraper_used = ""
            
            max_pages = request.pagination.max_pages if request.pagination and request.pagination.enabled else 1
            
            for page_num in range(max_pages):
                # Fetch page content
                html, scraper_name = await ScraperFactory.scrape_with_fallback(
                    url=current_url,
                    primary_type=request.scraper_type,
                    timeout=request.timeout,
                    wait_for_selector=request.wait_for_selector
                )
                scraper_used = scraper_name
                pages_scraped += 1
                
                # Extract data
                scraper = ScraperFactory.get_static_scraper()  # Use for extraction only
                page_data = scraper.extract_data(
                    html=html,
                    fields=request.fields,
                    container_selector=request.container_selector
                )
                
                all_data.extend(page_data)
                
                # Handle pagination
                if request.pagination and request.pagination.enabled and page_num < max_pages - 1:
                    next_url = self._find_next_page(html, request.pagination.next_page_selector, current_url)
                    if next_url:
                        current_url = next_url
                        await asyncio.sleep(request.delay)
                    else:
                        break
            
            # Normalize data
            normalizer = DataNormalizer(base_url=request.url)
            normalized_data = normalizer.normalize(all_data, dedupe=True)
            
            elapsed_time = time.time() - start_time
            
            return ScrapeResponse(
                success=True,
                result=ScrapeResult(
                    url=request.url,
                    scraper_used=scraper_used,
                    data=normalized_data,
                    total_items=len(normalized_data),
                    pages_scraped=pages_scraped,
                    elapsed_time=round(elapsed_time, 2)
                )
            )
            
        except asyncio.TimeoutError:
            return ScrapeResponse(
                success=False,
                error=ScrapeError(
                    code="TIMEOUT",
                    message=f"Request timed out after {request.timeout} seconds",
                    details={"url": request.url, "timeout": request.timeout}
                )
            )
        except Exception as e:
            return ScrapeResponse(
                success=False,
                error=ScrapeError(
                    code="SCRAPE_ERROR",
                    message=str(e),
                    details={"url": request.url, "error_type": type(e).__name__}
                )
            )
    
    def _find_next_page(self, html: str, selector: Optional[str], current_url: str) -> Optional[str]:
        """Find the URL of the next page."""
        if not selector:
            return None
        
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin
        
        soup = BeautifulSoup(html, 'lxml')
        next_link = soup.select_one(selector)
        
        if next_link and next_link.get('href'):
            return urljoin(current_url, next_link.get('href'))
        
        return None
    
    async def detect_page_type(self, url: str) -> Dict[str, Any]:
        """Detect the page type for a URL."""
        from backend.scrapers.page_detector import PageTypeDetector
        
        detector = PageTypeDetector()
        result = await detector.detect(url)
        
        return {
            "is_dynamic": result.is_dynamic,
            "confidence": result.confidence,
            "indicators": result.indicators,
            "recommended_scraper": result.recommended_scraper.value
        }
    
    def get_presets(self, category: Optional[str] = None) -> List[Dict[str, str]]:
        """Get available configuration presets, optionally filtered by category."""
        return self.config_loader.list_presets(category=category)
    
    def get_presets_by_category(self, category: str) -> List[Dict[str, str]]:
        """Get all presets for a specific category."""
        return self.config_loader.get_presets_by_category(category)
    
    def list_categories(self) -> List[Dict[str, str]]:
        """List all available categories."""
        return self.config_loader.list_categories()
    
    def suggest_presets_for_url(self, url: str) -> List[Dict[str, str]]:
        """Suggest presets based on URL patterns."""
        return self.config_loader.suggest_presets_for_url(url)
    
    def get_preset_config(self, preset_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific preset."""
        preset = self.config_loader.get_preset(preset_id)
        if not preset:
            return None
        
        # Get category from preset data
        preset_data = self.config_loader.get_preset_data(preset_id)
        category = preset_data.get("category", "general") if preset_data else "general"
        
        return {
            "name": preset.name,
            "description": preset.description,
            "category": category,
            "container_selector": preset.container_selector,
            "fields": [
                {
                    "name": f.name,
                    "selector": f.selector,
                    "selector_type": f.selector_type.value,
                    "attribute": f.attribute,
                    "multiple": f.multiple,
                    "default": f.default
                }
                for f in preset.fields
            ],
            "suitable_for": preset.suitable_for
        }

