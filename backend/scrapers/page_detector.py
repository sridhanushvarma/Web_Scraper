"""
Automatic page type detection to determine if a page is static or dynamic.
"""
import re
import aiohttp
from typing import Tuple, List
from bs4 import BeautifulSoup

from backend.models import PageTypeDetectionResult, ScraperType


class PageTypeDetector:
    """
    Detects whether a page requires JavaScript rendering.
    
    Uses heuristics to analyze the initial HTML response and determine
    if the page is likely a SPA or requires JS for content loading.
    """
    
    # Indicators that suggest a page is dynamic/SPA
    DYNAMIC_INDICATORS = [
        # JavaScript frameworks
        (r'__NEXT_DATA__', 'Next.js detected'),
        (r'__NUXT__', 'Nuxt.js detected'),
        (r'ng-app|ng-controller', 'AngularJS detected'),
        (r'data-reactroot|data-react', 'React detected'),
        (r'data-v-[a-f0-9]', 'Vue.js detected'),
        (r'ember-view', 'Ember.js detected'),
        
        # Loading indicators
        (r'<noscript>.*enable javascript', 'NoScript JavaScript warning'),
        (r'loading["\s>]|spinner', 'Loading indicator present'),
        
        # Empty content containers
        (r'<div id="(app|root|main)">\s*</div>', 'Empty app container'),
        (r'<main[^>]*>\s*</main>', 'Empty main container'),
        
        # JavaScript-heavy patterns
        (r'window\.__INITIAL_STATE__', 'Initial state injection'),
        (r'window\.__DATA__', 'Data injection'),
    ]
    
    # Indicators that suggest a page is static
    STATIC_INDICATORS = [
        (r'<article', 'Article element present'),
        (r'<p>[\w\s]{50,}', 'Paragraph with substantial content'),
        (r'<table[\s\S]*?<td', 'Table with data'),
        (r'<ul[\s\S]*?<li[\s\S]*?<li', 'List with multiple items'),
        (r'class=".*content.*"[\s\S]{100,}', 'Content class with data'),
    ]
    
    async def detect(self, url: str, timeout: int = 10) -> PageTypeDetectionResult:
        """
        Detect the page type for a given URL.
        
        Args:
            url: The URL to analyze
            timeout: Request timeout
            
        Returns:
            PageTypeDetectionResult with detection details
        """
        try:
            html = await self._fetch_initial_html(url, timeout)
            is_dynamic, confidence, indicators = self._analyze_html(html)
            
            recommended = ScraperType.DYNAMIC if is_dynamic else ScraperType.STATIC
            
            return PageTypeDetectionResult(
                is_dynamic=is_dynamic,
                confidence=confidence,
                indicators=indicators,
                recommended_scraper=recommended
            )
        except Exception as e:
            # On error, default to dynamic (more robust)
            return PageTypeDetectionResult(
                is_dynamic=True,
                confidence=0.5,
                indicators=[f"Detection failed: {str(e)}", "Defaulting to dynamic"],
                recommended_scraper=ScraperType.DYNAMIC
            )
    
    async def _fetch_initial_html(self, url: str, timeout: int) -> str:
        """Fetch the initial HTML without JavaScript rendering."""
        async with aiohttp.ClientSession() as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                return await resp.text()
    
    def _analyze_html(self, html: str) -> Tuple[bool, float, List[str]]:
        """
        Analyze HTML content to determine if it's dynamic.
        
        Returns:
            Tuple of (is_dynamic, confidence, indicators)
        """
        indicators = []
        dynamic_score = 0
        static_score = 0
        
        # Check for dynamic indicators
        for pattern, description in self.DYNAMIC_INDICATORS:
            if re.search(pattern, html, re.IGNORECASE):
                indicators.append(f"🔴 {description}")
                dynamic_score += 1
        
        # Check for static indicators
        for pattern, description in self.STATIC_INDICATORS:
            if re.search(pattern, html, re.IGNORECASE):
                indicators.append(f"🟢 {description}")
                static_score += 1
        
        # Check content density
        soup = BeautifulSoup(html, 'lxml')
        text = soup.get_text(strip=True)
        
        if len(text) < 500:
            indicators.append("🔴 Low content density")
            dynamic_score += 2
        elif len(text) > 2000:
            indicators.append("🟢 High content density")
            static_score += 1
        
        # Calculate final decision
        total_checks = dynamic_score + static_score
        if total_checks == 0:
            # Default to trying static first
            return False, 0.5, ["No clear indicators found"]
        
        is_dynamic = dynamic_score > static_score
        confidence = abs(dynamic_score - static_score) / total_checks
        confidence = min(0.95, confidence + 0.3)  # Normalize to reasonable range
        
        return is_dynamic, confidence, indicators

