"""
Factory for creating and managing scraper instances.
Implements the Strategy pattern for scraper selection.
"""
from typing import Optional
import asyncio

from backend.models import ScraperType
from .base_scraper import BaseScraper
from .static_scraper import StaticScraper
from .dynamic_scraper import DynamicScraper
from .page_detector import PageTypeDetector


class ScraperFactory:
    """
    Factory for creating scraper instances based on page type or user preference.
    
    Supports:
    - Manual scraper type selection
    - Automatic page type detection
    - Fallback from one scraper to another on failure
    """
    
    _static_scraper: Optional[StaticScraper] = None
    _dynamic_scraper: Optional[DynamicScraper] = None
    _detector: Optional[PageTypeDetector] = None
    
    @classmethod
    def get_static_scraper(cls) -> StaticScraper:
        """Get or create the static scraper singleton."""
        if cls._static_scraper is None:
            cls._static_scraper = StaticScraper()
        return cls._static_scraper
    
    @classmethod
    def get_dynamic_scraper(cls) -> DynamicScraper:
        """Get or create the dynamic scraper singleton."""
        if cls._dynamic_scraper is None:
            cls._dynamic_scraper = DynamicScraper()
        return cls._dynamic_scraper
    
    @classmethod
    def get_detector(cls) -> PageTypeDetector:
        """Get or create the page type detector singleton."""
        if cls._detector is None:
            cls._detector = PageTypeDetector()
        return cls._detector
    
    @classmethod
    def get_scraper(cls, scraper_type: ScraperType) -> BaseScraper:
        """
        Get a scraper instance based on the specified type.
        
        Args:
            scraper_type: The type of scraper to create
            
        Returns:
            A scraper instance
            
        Raises:
            ValueError: If scraper_type is AUTO (use get_auto_scraper instead)
        """
        if scraper_type == ScraperType.AUTO:
            raise ValueError("Use get_auto_scraper for automatic detection")
        elif scraper_type == ScraperType.STATIC:
            return cls.get_static_scraper()
        elif scraper_type == ScraperType.DYNAMIC:
            return cls.get_dynamic_scraper()
        else:
            raise ValueError(f"Unknown scraper type: {scraper_type}")
    
    @classmethod
    async def get_auto_scraper(cls, url: str) -> tuple[BaseScraper, str]:
        """
        Automatically detect the page type and return the appropriate scraper.
        
        Args:
            url: The URL to analyze
            
        Returns:
            Tuple of (scraper instance, detection reason)
        """
        detector = cls.get_detector()
        result = await detector.detect(url)
        
        if result.recommended_scraper == ScraperType.DYNAMIC:
            return cls.get_dynamic_scraper(), f"Dynamic (confidence: {result.confidence:.2f})"
        else:
            return cls.get_static_scraper(), f"Static (confidence: {result.confidence:.2f})"
    
    @classmethod
    async def scrape_with_fallback(
        cls,
        url: str,
        primary_type: ScraperType,
        timeout: int = 30,
        wait_for_selector: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Scrape a page with automatic fallback on failure.
        
        Args:
            url: The URL to scrape
            primary_type: The primary scraper type to try first
            timeout: Request timeout
            wait_for_selector: Selector to wait for (dynamic only)
            
        Returns:
            Tuple of (HTML content, scraper name used)
        """
        scrapers_to_try = []
        
        if primary_type == ScraperType.STATIC:
            scrapers_to_try = [
                (cls.get_static_scraper(), "static"),
                (cls.get_dynamic_scraper(), "dynamic (fallback)")
            ]
        elif primary_type == ScraperType.DYNAMIC:
            scrapers_to_try = [
                (cls.get_dynamic_scraper(), "dynamic"),
                (cls.get_static_scraper(), "static (fallback)")
            ]
        else:  # AUTO
            scraper, reason = await cls.get_auto_scraper(url)
            scrapers_to_try = [
                (scraper, scraper.name),
                (cls.get_static_scraper() if scraper.name == "dynamic" else cls.get_dynamic_scraper(),
                 f"{'static' if scraper.name == 'dynamic' else 'dynamic'} (fallback)")
            ]
        
        last_error = None
        for scraper, name in scrapers_to_try:
            try:
                html = await scraper.fetch_page(url, timeout, wait_for_selector)
                return html, name
            except Exception as e:
                last_error = e
                continue
        
        raise last_error or Exception("All scrapers failed")
    
    @classmethod
    async def cleanup(cls):
        """Clean up all scraper resources."""
        if cls._static_scraper:
            await cls._static_scraper.close()
            cls._static_scraper = None
        if cls._dynamic_scraper:
            await cls._dynamic_scraper.close()
            cls._dynamic_scraper = None

