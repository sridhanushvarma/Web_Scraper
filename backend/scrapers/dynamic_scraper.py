"""
Dynamic scraper implementation using Playwright.
Suitable for JavaScript-rendered pages and SPAs.
"""
import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from tenacity import retry, stop_after_attempt, wait_exponential

from .base_scraper import BaseScraper


class DynamicScraper(BaseScraper):
    """
    Scraper for dynamic JavaScript-rendered pages using Playwright.
    
    Features:
    - Headless browser automation
    - JavaScript rendering support
    - Wait for specific elements
    - Lazy-loading content handling
    - Anti-detection measures
    """
    
    def __init__(self):
        super().__init__()
        self.name = "dynamic"
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
    
    async def _ensure_browser(self):
        """Ensure the browser is launched and ready."""
        if self._browser is None or not self._browser.is_connected():
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-infobars',
                    '--window-size=1920,1080',
                ]
            )
            self._context = await self._browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                java_script_enabled=True,
            )
            # Add anti-detection scripts
            await self._context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            """)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def fetch_page(
        self,
        url: str,
        timeout: int = 30,
        wait_for_selector: Optional[str] = None
    ) -> str:
        """
        Fetch page content using headless browser.
        
        Args:
            url: The URL to fetch
            timeout: Request timeout in seconds
            wait_for_selector: Optional selector to wait for before extracting content
            
        Returns:
            The rendered HTML content of the page
        """
        await self._ensure_browser()
        
        page: Page = await self._context.new_page()
        
        try:
            # Navigate to the page
            await page.goto(url, wait_until='networkidle', timeout=timeout * 1000)
            
            # Wait for specific selector if provided
            if wait_for_selector:
                await page.wait_for_selector(wait_for_selector, timeout=timeout * 1000)
            
            # Scroll to trigger lazy loading
            await self._scroll_page(page)
            
            # Wait a bit for any lazy-loaded content
            await asyncio.sleep(1)
            
            # Get the rendered HTML
            html = await page.content()
            return html
            
        finally:
            await page.close()
    
    async def _scroll_page(self, page: Page):
        """Scroll the page to trigger lazy loading."""
        try:
            await page.evaluate("""
                async () => {
                    const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
                    const scrollHeight = document.body.scrollHeight;
                    const viewportHeight = window.innerHeight;
                    let currentPosition = 0;
                    
                    while (currentPosition < scrollHeight) {
                        window.scrollTo(0, currentPosition);
                        currentPosition += viewportHeight;
                        await delay(200);
                    }
                    
                    // Scroll back to top
                    window.scrollTo(0, 0);
                }
            """)
        except Exception:
            # Ignore scroll errors
            pass
    
    async def close(self):
        """Close the browser and clean up resources."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

