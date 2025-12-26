#!/usr/bin/env python3
"""
Run script for the Web Scraper application.
Starts the FastAPI server with uvicorn.
"""
import uvicorn
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🕷️ Starting Web Scraper Server...")
    print("📍 Open http://localhost:8000 in your browser")
    print("-" * 50)
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

