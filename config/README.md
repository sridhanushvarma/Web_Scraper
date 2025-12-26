# Configuration Directory

This directory contains preset configurations for the web scraper.

## Category-Based Presets

The scraper now uses **category-based presets** that work across multiple websites, rather than site-specific configurations. This makes the scraper more flexible and easier to use.

### Available Categories

- **News & Articles** - News websites, articles, journalism
- **E-commerce** - Online stores, product listings
- **Blogs** - Blog posts, personal blogs, content sites
- **Job Boards** - Job listings, career sites
- **Real Estate** - Property listings, housing
- **Social Media** - Social media posts, feeds
- **Forums** - Discussion forums, communities
- **Directories** - Business directories, listings
- **Data Tables** - Tables, statistics, data
- **Links** - Link lists, navigation
- **Video Platforms** - Video listings, media

### Creating Custom Presets

To create a custom preset, create a JSON or YAML file in this directory with the following structure:

```json
{
    "name": "My Custom Preset",
    "description": "Description of what this preset extracts",
    "category": "news",
    "container_selector": ".item, article",
    "fields": [
        {
            "name": "title",
            "selector": "h2, .title",
            "selector_type": "css"
        },
        {
            "name": "link",
            "selector": "a",
            "selector_type": "css",
            "attribute": "href"
        }
    ],
    "suitable_for": ["news", "articles"]
}
```

**Important**: Custom presets must include a `category` field to be loaded.

### Deprecated Files

Files with `.deprecated` extension are old site-specific configurations that are no longer used. The scraper now uses category-based presets that work across multiple websites.

