"""
Configuration loader for extraction rules and presets.
Supports JSON and YAML configuration files.
Uses category-based presets that work across multiple websites.
"""
import json
import yaml
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

from backend.models import ConfigPreset, ExtractionField, SelectorType


class ConfigLoader:
    """
    Loads and manages scraping configurations.
    
    Features:
    - Category-based presets that work across multiple websites
    - Generic selectors that adapt to common website patterns
    - No hard-coded site-specific configurations
    """
    
    # Category-based presets - generic and reusable across sites
    DEFAULT_PRESETS = {
        "news_articles": {
            "name": "News Articles",
            "description": "Extract article listings from news websites",
            "category": "news",
            "container_selector": "article, .article, .post, .story, .news-item, [class*='article'], [class*='news']",
            "fields": [
                {"name": "title", "selector": "h1, h2, h3, .title, .headline, [class*='title']", "selector_type": "css"},
                {"name": "link", "selector": "a", "selector_type": "css", "attribute": "href"},
                {"name": "summary", "selector": "p, .summary, .excerpt, .description, [class*='summary']", "selector_type": "css"},
                {"name": "date", "selector": "time, .date, .published, [datetime], [class*='date']", "selector_type": "css"},
                {"name": "author", "selector": ".author, .byline, [rel='author'], [class*='author']", "selector_type": "css"},
                {"name": "image", "selector": "img", "selector_type": "css", "attribute": "src"}
            ],
            "suitable_for": ["news", "blog", "magazine", "journalism"]
        },
        "ecommerce_products": {
            "name": "E-commerce Products",
            "description": "Extract product listings from e-commerce websites",
            "category": "ecommerce",
            "container_selector": ".product, .item, [data-product], .product-card, [class*='product'], [class*='item']",
            "fields": [
                {"name": "name", "selector": ".product-name, .title, h2, h3, [class*='name'], [class*='title']", "selector_type": "css"},
                {"name": "price", "selector": ".price, .product-price, [data-price], [class*='price']", "selector_type": "css"},
                {"name": "original_price", "selector": ".original-price, .was-price, del, [class*='original'], [class*='was']", "selector_type": "css"},
                {"name": "image", "selector": "img", "selector_type": "css", "attribute": "src"},
                {"name": "link", "selector": "a", "selector_type": "css", "attribute": "href"},
                {"name": "rating", "selector": ".rating, .stars, [data-rating], [class*='rating'], [class*='star']", "selector_type": "css"},
                {"name": "reviews", "selector": ".reviews, .review-count, [class*='review']", "selector_type": "css"}
            ],
            "suitable_for": ["ecommerce", "shop", "store", "marketplace", "retail"]
        },
        "blog_posts": {
            "name": "Blog Posts",
            "description": "Extract blog post content and metadata",
            "category": "blog",
            "container_selector": "article, .post, .blog-post, .entry, [class*='post'], [class*='blog']",
            "fields": [
                {"name": "title", "selector": "h1, h2, .post-title, .entry-title, [class*='title']", "selector_type": "css"},
                {"name": "content", "selector": ".content, .post-content, .entry-content, article p, [class*='content']", "selector_type": "css"},
                {"name": "date", "selector": "time, .date, .published, .post-date, [datetime], [class*='date']", "selector_type": "css"},
                {"name": "author", "selector": ".author, .post-author, [rel='author'], [class*='author']", "selector_type": "css"},
                {"name": "categories", "selector": ".category, .tag, .label, [class*='category'], [class*='tag']", "selector_type": "css", "multiple": True},
                {"name": "image", "selector": ".featured-image img, .post-image img, img", "selector_type": "css", "attribute": "src"}
            ],
            "suitable_for": ["blog", "journal", "personal", "content"]
        },
        "job_listings": {
            "name": "Job Listings",
            "description": "Extract job postings from job board websites",
            "category": "jobs",
            "container_selector": ".job, .job-listing, .position, [class*='job'], [class*='position'], [class*='listing']",
            "fields": [
                {"name": "title", "selector": "h2, h3, .title, .job-title, [class*='title']", "selector_type": "css"},
                {"name": "company", "selector": ".company, .employer, [class*='company'], [class*='employer']", "selector_type": "css"},
                {"name": "location", "selector": ".location, .city, [class*='location']", "selector_type": "css"},
                {"name": "salary", "selector": ".salary, .compensation, [class*='salary']", "selector_type": "css"},
                {"name": "description", "selector": ".description, .summary, p, [class*='description']", "selector_type": "css"},
                {"name": "link", "selector": "a", "selector_type": "css", "attribute": "href"},
                {"name": "posted_date", "selector": "time, .date, .posted, [datetime], [class*='date']", "selector_type": "css"}
            ],
            "suitable_for": ["jobs", "careers", "recruitment", "hiring"]
        },
        "real_estate": {
            "name": "Real Estate Listings",
            "description": "Extract property listings from real estate websites",
            "category": "real_estate",
            "container_selector": ".property, .listing, .home, [class*='property'], [class*='listing']",
            "fields": [
                {"name": "address", "selector": ".address, .location, [class*='address']", "selector_type": "css"},
                {"name": "price", "selector": ".price, [class*='price']", "selector_type": "css"},
                {"name": "bedrooms", "selector": ".bedrooms, .beds, [class*='bed']", "selector_type": "css"},
                {"name": "bathrooms", "selector": ".bathrooms, .baths, [class*='bath']", "selector_type": "css"},
                {"name": "square_feet", "selector": ".sqft, .area, [class*='sqft'], [class*='area']", "selector_type": "css"},
                {"name": "image", "selector": "img", "selector_type": "css", "attribute": "src"},
                {"name": "link", "selector": "a", "selector_type": "css", "attribute": "href"}
            ],
            "suitable_for": ["real_estate", "property", "housing", "rentals"]
        },
        "social_media_posts": {
            "name": "Social Media Posts",
            "description": "Extract posts from social media platforms",
            "category": "social",
            "container_selector": ".post, .tweet, .status, [class*='post'], [class*='tweet'], [class*='status']",
            "fields": [
                {"name": "content", "selector": ".content, .text, p, [class*='content'], [class*='text']", "selector_type": "css"},
                {"name": "author", "selector": ".author, .username, [class*='author'], [class*='user']", "selector_type": "css"},
                {"name": "date", "selector": "time, .date, [datetime], [class*='date'], [class*='time']", "selector_type": "css"},
                {"name": "likes", "selector": ".likes, .favorites, [class*='like'], [class*='favorite']", "selector_type": "css"},
                {"name": "shares", "selector": ".shares, .retweets, [class*='share'], [class*='retweet']", "selector_type": "css"},
                {"name": "comments", "selector": ".comments, [class*='comment']", "selector_type": "css"},
                {"name": "link", "selector": "a", "selector_type": "css", "attribute": "href"}
            ],
            "suitable_for": ["social", "social_media", "twitter", "facebook", "reddit"]
        },
        "forum_posts": {
            "name": "Forum Posts",
            "description": "Extract posts and threads from forum websites",
            "category": "forum",
            "container_selector": ".post, .thread, .topic, [class*='post'], [class*='thread']",
            "fields": [
                {"name": "title", "selector": "h2, h3, .title, .subject, [class*='title']", "selector_type": "css"},
                {"name": "content", "selector": ".content, .message, .post-content, [class*='content']", "selector_type": "css"},
                {"name": "author", "selector": ".author, .username, [class*='author'], [class*='user']", "selector_type": "css"},
                {"name": "date", "selector": "time, .date, [datetime], [class*='date']", "selector_type": "css"},
                {"name": "replies", "selector": ".replies, .responses, [class*='reply'], [class*='response']", "selector_type": "css"},
                {"name": "views", "selector": ".views, [class*='view']", "selector_type": "css"},
                {"name": "link", "selector": "a", "selector_type": "css", "attribute": "href"}
            ],
            "suitable_for": ["forum", "discussion", "community", "board"]
        },
        "directory_listings": {
            "name": "Directory Listings",
            "description": "Extract listings from directory websites",
            "category": "directory",
            "container_selector": ".listing, .item, .entry, [class*='listing'], [class*='item']",
            "fields": [
                {"name": "name", "selector": "h2, h3, .name, .title, [class*='name']", "selector_type": "css"},
                {"name": "description", "selector": ".description, .summary, p, [class*='description']", "selector_type": "css"},
                {"name": "category", "selector": ".category, .tag, [class*='category']", "selector_type": "css"},
                {"name": "location", "selector": ".location, .address, [class*='location'], [class*='address']", "selector_type": "css"},
                {"name": "phone", "selector": ".phone, .tel, [class*='phone']", "selector_type": "css"},
                {"name": "website", "selector": "a", "selector_type": "css", "attribute": "href"},
                {"name": "rating", "selector": ".rating, .stars, [class*='rating']", "selector_type": "css"}
            ],
            "suitable_for": ["directory", "listing", "yellow_pages", "business_directory"]
        },
        "generic_table": {
            "name": "Generic Table",
            "description": "Extract data from HTML tables",
            "category": "data",
            "container_selector": "table tr",
            "fields": [
                {"name": "cells", "selector": "td, th", "selector_type": "css", "multiple": True}
            ],
            "suitable_for": ["data", "statistics", "comparison", "table"]
        },
        "links_list": {
            "name": "Links List",
            "description": "Extract all links from a page",
            "category": "links",
            "container_selector": "a",
            "fields": [
                {"name": "text", "selector": ".", "selector_type": "css"},
                {"name": "url", "selector": ".", "selector_type": "css", "attribute": "href"}
            ],
            "suitable_for": ["directory", "sitemap", "links", "navigation"]
        },
        "video_listings": {
            "name": "Video Listings",
            "description": "Extract video listings from video platforms",
            "category": "video",
            "container_selector": ".video, .video-item, [class*='video']",
            "fields": [
                {"name": "title", "selector": "h2, h3, .title, [class*='title']", "selector_type": "css"},
                {"name": "channel", "selector": ".channel, .creator, [class*='channel'], [class*='creator']", "selector_type": "css"},
                {"name": "views", "selector": ".views, [class*='view']", "selector_type": "css"},
                {"name": "duration", "selector": ".duration, [class*='duration']", "selector_type": "css"},
                {"name": "date", "selector": "time, .date, [datetime], [class*='date']", "selector_type": "css"},
                {"name": "thumbnail", "selector": "img", "selector_type": "css", "attribute": "src"},
                {"name": "link", "selector": "a", "selector_type": "css", "attribute": "href"}
            ],
            "suitable_for": ["video", "youtube", "vimeo", "media"]
        }
    }
    
    # Available categories
    CATEGORIES = [
        {"id": "news", "name": "News & Articles", "description": "News websites, articles, journalism"},
        {"id": "ecommerce", "name": "E-commerce", "description": "Online stores, product listings"},
        {"id": "blog", "name": "Blogs", "description": "Blog posts, personal blogs, content sites"},
        {"id": "jobs", "name": "Job Boards", "description": "Job listings, career sites"},
        {"id": "real_estate", "name": "Real Estate", "description": "Property listings, housing"},
        {"id": "social", "name": "Social Media", "description": "Social media posts, feeds"},
        {"id": "forum", "name": "Forums", "description": "Discussion forums, communities"},
        {"id": "directory", "name": "Directories", "description": "Business directories, listings"},
        {"id": "data", "name": "Data Tables", "description": "Tables, statistics, data"},
        {"id": "links", "name": "Links", "description": "Link lists, navigation"},
        {"id": "video", "name": "Video Platforms", "description": "Video listings, media"}
    ]
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the config loader.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent.parent.parent / "config"
        self._custom_presets: Dict[str, Dict] = {}
        self._load_custom_presets()
    
    def _load_custom_presets(self):
        """Load custom presets from configuration directory (deprecated - use categories instead)."""
        if not self.config_dir.exists():
            return
        
        # Only load category-based presets, skip site-specific ones
        for file_path in self.config_dir.glob("*.json"):
            try:
                with open(file_path) as f:
                    preset = json.load(f)
                    # Only load if it has a category field (new format)
                    if "name" in preset and preset.get("category"):
                        self._custom_presets[file_path.stem] = preset
            except Exception:
                continue
        
        for file_path in self.config_dir.glob("*.yaml"):
            try:
                with open(file_path) as f:
                    preset = yaml.safe_load(f)
                    # Only load if it has a category field (new format)
                    if preset and "name" in preset and preset.get("category"):
                        self._custom_presets[file_path.stem] = preset
            except Exception:
                continue
    
    def get_preset(self, preset_name: str) -> Optional[ConfigPreset]:
        """Get a preset by name."""
        preset_data = self._custom_presets.get(preset_name) or self.DEFAULT_PRESETS.get(preset_name)
        if not preset_data:
            return None
        return self._dict_to_preset(preset_data)
    
    def get_preset_data(self, preset_name: str) -> Optional[Dict]:
        """Get raw preset data dictionary by name."""
        return self._custom_presets.get(preset_name) or self.DEFAULT_PRESETS.get(preset_name)
    
    def list_presets(self, category: Optional[str] = None) -> List[Dict[str, str]]:
        """
        List all available presets, optionally filtered by category.
        
        Args:
            category: Optional category ID to filter presets
            
        Returns:
            List of preset dictionaries with id, name, description, and category
        """
        presets = []
        all_presets = {**self.DEFAULT_PRESETS, **self._custom_presets}
        
        for key, data in all_presets.items():
            preset_category = data.get("category", "general")
            # Filter by category if specified
            if category and preset_category != category:
                continue
            
            presets.append({
                "id": key,
                "name": data.get("name", key),
                "description": data.get("description", ""),
                "category": preset_category
            })
        
        return presets
    
    def get_presets_by_category(self, category: str) -> List[Dict[str, str]]:
        """
        Get all presets for a specific category.
        
        Args:
            category: Category ID
            
        Returns:
            List of preset dictionaries
        """
        return self.list_presets(category=category)
    
    def list_categories(self) -> List[Dict[str, str]]:
        """
        List all available categories.
        
        Returns:
            List of category dictionaries
        """
        return self.CATEGORIES
    
    def suggest_presets_for_url(self, url: str) -> List[Dict[str, str]]:
        """
        Suggest presets based on URL patterns.
        
        Args:
            url: The URL to analyze
            
        Returns:
            List of suggested preset dictionaries
        """
        url_lower = url.lower()
        suggestions = []
        
        # URL pattern matching for category detection
        patterns = {
            "news": ["news", "article", "journal", "press"],
            "ecommerce": ["shop", "store", "buy", "product", "cart", "checkout"],
            "blog": ["blog", "post", "article"],
            "jobs": ["job", "career", "hiring", "recruit"],
            "real_estate": ["property", "realty", "house", "home", "rent", "sale"],
            "social": ["social", "twitter", "facebook", "reddit", "instagram"],
            "forum": ["forum", "discussion", "board", "community"],
            "directory": ["directory", "listing", "yellow", "business"],
            "video": ["video", "youtube", "vimeo", "watch"]
        }
        
        # Find matching categories
        matched_categories = set()
        for category, keywords in patterns.items():
            if any(keyword in url_lower for keyword in keywords):
                matched_categories.add(category)
        
        # Get presets for matched categories
        for category in matched_categories:
            suggestions.extend(self.get_presets_by_category(category))
        
        # If no matches, return all presets
        if not suggestions:
            suggestions = self.list_presets()
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _dict_to_preset(self, data: Dict) -> ConfigPreset:
        """Convert a dictionary to a ConfigPreset."""
        fields = []
        for f in data.get("fields", []):
            fields.append(ExtractionField(
                name=f["name"],
                selector=f["selector"],
                selector_type=SelectorType(f.get("selector_type", "css")),
                attribute=f.get("attribute"),
                multiple=f.get("multiple", False),
                default=f.get("default")
            ))
        return ConfigPreset(
            name=data["name"],
            description=data.get("description", ""),
            container_selector=data.get("container_selector"),
            fields=fields,
            suitable_for=data.get("suitable_for", [])
        )

