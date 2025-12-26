"""
Rate limiting and anti-blocking utilities for the web scraper.
"""
import asyncio
import time
from typing import Dict, Optional
from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass
class DomainState:
    """Track request state for a domain."""
    last_request_time: float = 0
    request_count: int = 0
    blocked: bool = False
    blocked_until: float = 0


class RateLimiter:
    """
    Rate limiter to prevent overwhelming target servers and avoid blocking.
    
    Features:
    - Per-domain rate limiting
    - Adaptive delays based on response patterns
    - Blocking detection and cooldown
    """
    
    def __init__(
        self,
        min_delay: float = 1.0,
        max_delay: float = 10.0,
        requests_before_increase: int = 10,
        block_cooldown: float = 60.0
    ):
        """
        Initialize the rate limiter.
        
        Args:
            min_delay: Minimum delay between requests to same domain
            max_delay: Maximum delay between requests
            requests_before_increase: Number of requests before increasing delay
            block_cooldown: Time to wait when a domain blocks us
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.requests_before_increase = requests_before_increase
        self.block_cooldown = block_cooldown
        self._domain_states: Dict[str, DomainState] = {}
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc.lower()
    
    def _get_state(self, domain: str) -> DomainState:
        """Get or create state for a domain."""
        if domain not in self._domain_states:
            self._domain_states[domain] = DomainState()
        return self._domain_states[domain]
    
    async def wait_for_slot(self, url: str) -> None:
        """
        Wait for the appropriate time before making a request.
        
        Args:
            url: The URL being requested
        """
        domain = self._get_domain(url)
        state = self._get_state(domain)
        current_time = time.time()
        
        # Check if domain is in cooldown from blocking
        if state.blocked and current_time < state.blocked_until:
            wait_time = state.blocked_until - current_time
            await asyncio.sleep(wait_time)
            state.blocked = False
        
        # Calculate delay based on request count
        delay = self.min_delay
        if state.request_count > self.requests_before_increase:
            # Increase delay progressively
            multiplier = min(state.request_count // self.requests_before_increase, 5)
            delay = min(self.min_delay * (1 + multiplier * 0.5), self.max_delay)
        
        # Wait if needed
        time_since_last = current_time - state.last_request_time
        if time_since_last < delay:
            await asyncio.sleep(delay - time_since_last)
        
        # Update state
        state.last_request_time = time.time()
        state.request_count += 1
    
    def mark_blocked(self, url: str) -> None:
        """
        Mark a domain as having blocked us.
        
        Args:
            url: The URL that returned a blocking response
        """
        domain = self._get_domain(url)
        state = self._get_state(domain)
        state.blocked = True
        state.blocked_until = time.time() + self.block_cooldown
        state.request_count = 0  # Reset count
    
    def is_blocked(self, url: str) -> bool:
        """Check if a domain is currently in cooldown."""
        domain = self._get_domain(url)
        state = self._get_state(domain)
        
        if state.blocked and time.time() >= state.blocked_until:
            state.blocked = False
        
        return state.blocked
    
    def reset_domain(self, url: str) -> None:
        """Reset rate limiting state for a domain."""
        domain = self._get_domain(url)
        if domain in self._domain_states:
            del self._domain_states[domain]


# Singleton instance
rate_limiter = RateLimiter()


def is_blocked_response(status_code: int, body: str = "") -> bool:
    """
    Detect if a response indicates we've been blocked.
    
    Args:
        status_code: HTTP status code
        body: Response body (optional)
        
    Returns:
        True if the response indicates blocking
    """
    # Common blocking status codes
    if status_code in (403, 429, 503, 520, 521, 522, 523, 524):
        return True
    
    # Check for CAPTCHA or block indicators in body
    block_indicators = [
        'captcha',
        'robot',
        'blocked',
        'access denied',
        'rate limit',
        'too many requests',
        'cloudflare'
    ]
    
    body_lower = body.lower()
    return any(indicator in body_lower for indicator in block_indicators)

