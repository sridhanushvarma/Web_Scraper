"""
Static scraper implementation using requests + BeautifulSoup.
Suitable for server-rendered HTML pages that don't require JavaScript.
"""
import asyncio
import aiohttp
from typing import Optional, List
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .base_scraper import BaseScraper


class StaticScraper(BaseScraper):
    """
    Scraper for static HTML pages using aiohttp.
    
    Features:
    - Async HTTP requests
    - User-agent rotation
    - Retry logic with exponential backoff
    - Custom headers support
    """
    
    # Common user agents for rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    def __init__(self):
        super().__init__()
        self.name = "static"
        self._session: Optional[aiohttp.ClientSession] = None
        self._ua_index = 0
        try:
            self._ua = UserAgent()
        except Exception:
            self._ua = None
    
    def _get_user_agent(self) -> str:
        """Get a user agent string with rotation."""
        if self._ua:
            try:
                return self._ua.random
            except Exception:
                pass
        # Fallback to static list with rotation
        ua = self.USER_AGENTS[self._ua_index % len(self.USER_AGENTS)]
        self._ua_index += 1
        return ua
    
    def _get_headers(self) -> dict:
        """Get request headers with rotated user agent."""
        return {
            'User-Agent': self._get_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def fetch_page(
        self,
        url: str,
        timeout: int = 30,
        wait_for_selector: Optional[str] = None
    ) -> str:
        """
        Fetch page content using HTTP request.
        
        Args:
            url: The URL to fetch
            timeout: Request timeout in seconds
            wait_for_selector: Ignored for static scraper
            
        Returns:
            The HTML content of the page
            
        Raises:
            aiohttp.ClientError: On request failure
            asyncio.TimeoutError: On timeout
        """
        session = await self._get_session()
        headers = self._get_headers()
        
        async with session.get(
            url,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout),
            allow_redirects=True,
            ssl=False  # For development; enable in production
        ) as response:
            response.raise_for_status()
            return await response.text()
    
    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

