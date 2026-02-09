"""
Price Analyzer API - Configuration Settings
"""
import os
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # API Keys
    RAPIDAPI_KEY: str = os.getenv("RAPIDAPI_KEY", "20f7b56b76msh9496601484d062ap14fb89jsn6b5f53aaffda")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "AIzaSyDTOlL9cLRD9Lyj7Yl5xd0QeqLHbRxa2nQ")
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    
    # Cache Settings
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", 3600))  # 1 hour default
    
    # Server Settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # RapidAPI Endpoints
    RAPIDAPI_HOST_AMAZON = "real-time-amazon-data.p.rapidapi.com"
    RAPIDAPI_HOST_EBAY = "ebay-search-result.p.rapidapi.com"
    RAPIDAPI_HOST_WALMART = "walmart-api.p.rapidapi.com"
    
    # Scoring Weights
    PRICE_WEIGHT: float = 0.35
    REVIEW_WEIGHT: float = 0.35
    QUALITY_WEIGHT: float = 0.30


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
