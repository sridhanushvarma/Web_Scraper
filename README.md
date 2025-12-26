# Web Scraper - Multi-Website Data Extraction

A powerful, configuration-driven web scraping system built with FastAPI and modern web technologies. Extract structured data from any website with support for both static and dynamic content.

## Features

- **Multi-Scraper Support**: Automatic detection between static (requests + BeautifulSoup) and dynamic (Playwright) scrapers
- **Category-Based Presets**: Generic presets that work across multiple websites by category (news, ecommerce, blogs, etc.)
- **Smart Preset Suggestions**: Automatic preset suggestions based on URL patterns
- **Pagination Support**: Automatically scrape multiple pages
- **Data Export**: Export results as JSON or CSV
- **Real-time UI**: Modern web interface with live scraping status
- **Flexible Extraction**: CSS selectors and XPath support
- **Error Handling**: Robust error handling with fallback mechanisms

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js (for Playwright browser installation)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Web_Scraper
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:8000`

## Usage

### Web Interface

1. Enter a target URL
2. (Optional) Select a website category to filter presets
3. (Optional) Click "Suggest presets for URL" to get automatic suggestions
4. Select a preset or configure custom extraction fields
5. Use "Auto-detect page type" to determine the best scraper
6. Add CSS selectors for the data you want to extract
7. Configure pagination if needed
8. Click "Start Scraping"

### API Endpoints

- `POST /api/scrape` - Start a scraping operation
- `GET /api/detect?url=<url>` - Detect page type
- `GET /api/presets?category=<category>` - List available presets (optionally filtered by category)
- `GET /api/categories` - List all available categories
- `GET /api/categories/{category_id}/presets` - Get presets for a specific category
- `GET /api/suggest-presets?url=<url>` - Get preset suggestions based on URL
- `GET /api/presets/{preset_id}` - Get configuration for a specific preset
- `GET /api/health` - Health check

### Example API Request

```json
{
  "url": "https://quotes.toscrape.com",
  "scraper_type": "auto",
  "fields": [
    {
      "name": "text",
      "selector": ".text",
      "selector_type": "css"
    },
    {
      "name": "author",
      "selector": ".author",
      "selector_type": "css"
    }
  ],
  "container_selector": ".quote"
}
```

## Supported Websites & Test Sites

### Practice/Demo Sites (Safe for Testing)
- **[Quotes to Scrape](http://quotes.toscrape.com)** - Perfect for learning
- **[Books to Scrape](http://books.toscrape.com)** - E-commerce practice
- **[Scrape This Site](https://scrapethissite.com)** - Various scraping challenges
- **[HTTPBin](https://httpbin.org)** - HTTP testing service

### News & Content Sites
- **[Hacker News](https://news.ycombinator.com)** - Tech news (has preset)
- **[Reddit](https://old.reddit.com)** - Social news (use old.reddit.com)
- **[BBC News](https://www.bbc.com/news)** - News articles
- **[Wikipedia](https://en.wikipedia.org)** - Encyclopedia content

### E-commerce (Use Responsibly)
- **[Amazon](https://amazon.com)** - Product listings (respect robots.txt)
- **[eBay](https://ebay.com)** - Auction listings
- **[Etsy](https://etsy.com)** - Handmade products

### Job Boards
- **[Indeed](https://indeed.com)** - Job listings
- **[Stack Overflow Jobs](https://stackoverflow.com/jobs)** - Tech jobs
- **[AngelList](https://angel.co)** - Startup jobs

### Real Estate
- **[Zillow](https://zillow.com)** - Property listings
- **[Realtor.com](https://realtor.com)** - Real estate data

## Project Structure

```
Web_Scraper/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   ├── scraping_engine.py   # Core scraping logic
│   └── scrapers/            # Scraper implementations
├── frontend/
│   ├── index.html           # Web interface
│   ├── js/app.js           # Frontend JavaScript
│   └── css/styles.css      # Custom styles
├── config/                  # Preset configurations
│   ├── quotes_toscrape.yaml
│   └── hackernews.json
├── requirements.txt         # Python dependencies
└── run.py                  # Application runner
```

## Configuration

### Category-Based System

The scraper uses **category-based presets** instead of site-specific configurations. This means:

- **One preset works for multiple websites** in the same category
- **Generic selectors** that adapt to common website patterns
- **Easy to use** - just select a category and preset
- **Automatic suggestions** based on URL patterns

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

Create YAML or JSON files in the `config/` directory:

```yaml
name: "My Custom Preset"
description: "Extract data from websites in this category"
category: "ecommerce"  # Required: must match a category
container_selector: ".item, .product"
fields:
  - name: "title"
    selector: "h2, .title"
    selector_type: "css"
  - name: "price"
    selector: ".price, [data-price]"
    selector_type: "css"
suitable_for: ["ecommerce", "products"]
```

**Important**: Custom presets must include a `category` field to be loaded by the system.

### Field Configuration Options

- `name`: Field identifier
- `selector`: CSS selector or XPath
- `selector_type`: "css" or "xpath"
- `attribute`: HTML attribute to extract (optional)
- `multiple`: Extract multiple matches (boolean)
- `default`: Default value if extraction fails

## 🛡️ Best Practices & Ethics

### Responsible Scraping
- **Check robots.txt** before scraping any website
- **Respect rate limits** - use delays between requests
- **Don't overload servers** - scrape during off-peak hours
- **Cache results** to avoid repeated requests
- **Follow terms of service** of target websites

### Technical Best Practices
- Use appropriate scraper type (static vs dynamic)
- Implement proper error handling
- Monitor for website structure changes
- Use user agents responsibly
- Handle pagination carefully

## Advanced Features

### Pagination
```json
{
  "pagination": {
    "enabled": true,
    "next_page_selector": "a.next",
    "max_pages": 10
  }
}
```

### Dynamic Content
```json
{
  "scraper_type": "dynamic",
  "wait_for_selector": ".dynamic-content",
  "timeout": 30
}
```

## Troubleshooting

### Common Issues

1. **Playwright Installation**
   ```bash
   playwright install chromium
   ```

2. **Permission Errors**
   ```bash
   chmod +x run.py
   ```

3. **Port Already in Use**
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```

## 📊 Performance Tips

- Use static scraper for simple HTML pages
- Enable pagination only when needed
- Set appropriate timeouts
- Use container selectors for better performance
- Cache frequently accessed data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is for educational purposes. Please respect website terms of service and robots.txt files.

## Support

- Check the `/api/health` endpoint for system status
- Use the auto-detect feature for unknown websites
- Start with practice sites before scraping production websites
- Monitor the browser console for JavaScript errors

---

**Disclaimer**: This tool is for educational and research purposes. Always respect website terms of service, robots.txt files, and applicable laws when scraping websites.