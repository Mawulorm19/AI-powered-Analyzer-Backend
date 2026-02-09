"""
Price Analyzer API - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import products_router
from .services import get_rapidapi_service, get_cache_service
from .config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    settings = get_settings()
    print(f"Starting Price Analyzer API (Debug: {settings.DEBUG})")
    
    yield
    
    # Shutdown
    rapidapi = get_rapidapi_service()
    await rapidapi.close()
    print("Price Analyzer API shutdown complete")


app = FastAPI(
    title="Price Analyzer API",
    description="""
    AI-powered price comparison and product analysis API.
    
    Features:
    - Multi-platform product search (Amazon, eBay, Walmart)
    - Sentiment analysis on customer reviews using Google Gemini
    - Value scoring algorithm based on price, reviews, and quality
    - Redis caching for improved performance
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    products_router,
    prefix="/api",
    tags=["Products"]
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Price Analyzer API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "search": "/api/search",
            "compare": "/api/compare",
            "analyze": "/api/analyze/{product_id}",
            "health": "/api/health"
        }
    }
