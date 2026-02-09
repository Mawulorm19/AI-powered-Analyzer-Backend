"""
Price Analyzer API - Pydantic Models
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ProductSource(str, Enum):
    """Supported e-commerce platforms."""
    AMAZON = "amazon"
    EBAY = "ebay"
    WALMART = "walmart"


class Review(BaseModel):
    """Individual product review model."""
    text: str
    rating: float = Field(ge=0, le=5)
    author: Optional[str] = None
    date: Optional[str] = None
    verified: bool = False


class SentimentAnalysis(BaseModel):
    """Sentiment analysis result from Gemini API."""
    overall_sentiment: str  # positive, negative, neutral
    sentiment_score: float = Field(ge=-1, le=1)
    pros: List[str] = []
    cons: List[str] = []
    summary: str = ""


class Product(BaseModel):
    """Product model with all details."""
    id: str
    title: str
    price: float
    original_price: Optional[float] = None
    currency: str = "USD"
    image_url: Optional[str] = None
    product_url: str
    source: ProductSource
    rating: Optional[float] = None
    review_count: Optional[int] = None
    availability: str = "unknown"


class ProductWithAnalysis(Product):
    """Product with sentiment analysis and scoring."""
    reviews: List[Review] = []
    sentiment: Optional[SentimentAnalysis] = None
    value_score: float = 0.0
    price_score: float = 0.0
    review_score: float = 0.0
    quality_score: float = 0.0


class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(min_length=1, max_length=200)
    sources: List[ProductSource] = [ProductSource.AMAZON, ProductSource.EBAY, ProductSource.WALMART]
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    limit: int = Field(default=10, ge=1, le=50)


class SearchResponse(BaseModel):
    """Search response model."""
    query: str
    total_results: int
    products: List[Product]
    cached: bool = False


class AnalyzeRequest(BaseModel):
    """Analysis request model."""
    product_id: str
    source: ProductSource


class AnalyzeResponse(BaseModel):
    """Analysis response with recommendation."""
    product: ProductWithAnalysis
    recommendation: str
    confidence: float = Field(ge=0, le=1)
    cached: bool = False


class CompareRequest(BaseModel):
    """Request to compare multiple products."""
    product_ids: List[str] = Field(min_length=2, max_length=10)


class CompareResponse(BaseModel):
    """Comparison response with best recommendation."""
    products: List[ProductWithAnalysis]
    best_value: Optional[ProductWithAnalysis] = None
    best_price: Optional[ProductWithAnalysis] = None
    best_quality: Optional[ProductWithAnalysis] = None
    recommendation: str
    cached: bool = False


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    code: int
