"""
FastAPI application for the web scraping system.
Provides REST API endpoints for scraping operations.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from typing import Optional, List
import os

from backend.models import ScrapeRequest, ScrapeResponse, ExtractionField, SelectorType, ScraperType
from backend.scraping_engine import ScrapingEngine
from backend.scrapers import ScraperFactory


# Application lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    yield
    # Cleanup on shutdown
    await ScraperFactory.cleanup()


# Create FastAPI app
app = FastAPI(
    title="Web Scraper API",
    description="A configurable, multi-website web scraping system",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the scraping engine
engine = ScrapingEngine()


# API Routes

@app.post("/api/scrape", response_model=ScrapeResponse, tags=["Scraping"])
async def scrape_website(request: ScrapeRequest):
    """
    Scrape a website based on the provided configuration.
    
    - **url**: Target URL to scrape
    - **scraper_type**: Type of scraper (auto, static, dynamic)
    - **fields**: List of fields to extract with their selectors
    - **container_selector**: Optional selector for repeating elements
    - **pagination**: Optional pagination configuration
    """
    response = await engine.scrape(request)
    
    if not response.success and response.error:
        status_code = 400
        if response.error.code == "TIMEOUT":
            status_code = 504
        elif response.error.code == "SCRAPE_ERROR":
            status_code = 502
        
        return JSONResponse(
            status_code=status_code,
            content=response.model_dump()
        )
    
    return response


@app.get("/api/detect", tags=["Utilities"])
async def detect_page_type(url: str = Query(..., description="URL to analyze")):
    """
    Detect whether a page is static or requires JavaScript rendering.
    
    Returns the recommended scraper type based on page analysis.
    """
    if not url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
    
    result = await engine.detect_page_type(url)
    return result


@app.get("/api/presets", tags=["Configuration"])
async def list_presets(category: Optional[str] = Query(None, description="Filter presets by category")):
    """
    List all available scraping presets.
    
    Presets provide pre-configured extraction rules for common website types.
    Can be filtered by category to get presets for specific website types.
    """
    return engine.get_presets(category=category)


@app.get("/api/presets/{preset_id}", tags=["Configuration"])
async def get_preset(preset_id: str):
    """
    Get configuration details for a specific preset.
    """
    config = engine.get_preset_config(preset_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
    return config


@app.get("/api/categories", tags=["Configuration"])
async def list_categories():
    """
    List all available scraping categories.
    
    Categories group presets by website type (e.g., news, ecommerce, blog).
    """
    return engine.list_categories()


@app.get("/api/categories/{category_id}/presets", tags=["Configuration"])
async def get_category_presets(category_id: str):
    """
    Get all presets for a specific category.
    """
    presets = engine.get_presets_by_category(category_id)
    if not presets:
        raise HTTPException(status_code=404, detail=f"Category '{category_id}' not found or has no presets")
    return presets


@app.get("/api/suggest-presets", tags=["Configuration"])
async def suggest_presets(url: str = Query(..., description="URL to analyze for preset suggestions")):
    """
    Suggest presets based on URL patterns.
    
    Analyzes the URL and suggests appropriate presets based on common patterns.
    """
    if not url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
    
    suggestions = engine.suggest_presets_for_url(url)
    return {"url": url, "suggestions": suggestions}


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "web-scraper"}


# Serve static frontend files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
css_path = os.path.join(frontend_path, "css")
js_path = os.path.join(frontend_path, "js")

if os.path.exists(css_path):
    app.mount("/css", StaticFiles(directory=css_path), name="css")
if os.path.exists(js_path):
    app.mount("/js", StaticFiles(directory=js_path), name="js")


@app.get("/", tags=["Frontend"])
async def serve_frontend():
    """Serve the frontend application."""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not found. API is running at /api"}


# Error handlers

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected errors."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"error": str(exc)}
            }
        }
    )

