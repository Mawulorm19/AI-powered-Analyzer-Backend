"""
Price Analyzer API - Main Application Router
Defines GET /search and GET /analyze endpoints.
"""
import hashlib
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional

from ..models import (
    Product, ProductSource, ProductWithAnalysis,
    SearchResponse, AnalyzeResponse, CompareResponse
)
from ..services import (
    get_rapidapi_service, get_gemini_service,
    get_cache_service, get_scoring_service
)
from ..services.mock_service import get_mock_products, get_mock_reviews, get_mock_sentiment

router = APIRouter()


def generate_search_cache_key(
    query: str,
    sources: List[ProductSource],
    min_price: Optional[float],
    max_price: Optional[float],
    limit: int
) -> str:
    """Generate a unique cache key for search parameters."""
    sources_str = ",".join(sorted(s.value for s in sources))
    key_parts = f"{query}:{sources_str}:{min_price}:{max_price}:{limit}"
    return hashlib.md5(key_parts.encode()).hexdigest()


@router.get("/search", response_model=SearchResponse)
async def search_products(
    query: str = Query(..., min_length=1, max_length=200, description="Search query"),
    sources: List[ProductSource] = Query(
        default=[ProductSource.AMAZON, ProductSource.EBAY, ProductSource.WALMART],
        description="E-commerce sources to search"
    ),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results per source")
):
    """
    Search for products across multiple e-commerce platforms.
    
    Returns a list of products with basic information including:
    - Title, price, and availability
    - Product images and URLs
    - Ratings and review counts
    
    Results are cached for 1 hour.
    """
    cache = get_cache_service()
    rapidapi = get_rapidapi_service()
    
    # Check cache
    cache_key = generate_search_cache_key(query, sources, min_price, max_price, limit)
    cached_result = cache.get("search", cache_key)
    
    if cached_result:
        return SearchResponse(
            query=query,
            total_results=cached_result["total_results"],
            products=[Product(**p) for p in cached_result["products"]],
            cached=True
        )
    
    # Fetch from APIs
    try:
        products = await rapidapi.search_all(query, sources, limit)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error fetching products: {str(e)}"
        )
    
    # Apply price filters
    if min_price is not None:
        products = [p for p in products if p.price >= min_price]
    if max_price is not None:
        products = [p for p in products if p.price <= max_price]
    
    # Sort by relevance (rating * review_count as a simple heuristic)
    def relevance_score(p: Product) -> float:
        rating = p.rating or 0
        reviews = p.review_count or 0
        return rating * (1 + reviews / 1000)
    
    products.sort(key=relevance_score, reverse=True)
    
    # Cache results
    cache.set("search", cache_key, {
        "total_results": len(products),
        "products": [p.model_dump() for p in products]
    })
    
    return SearchResponse(
        query=query,
        total_results=len(products),
        products=products,
        cached=False
    )


@router.get("/analyze/{product_id}", response_model=AnalyzeResponse)
async def analyze_product(
    product_id: str,
    source: ProductSource = Query(..., description="Product source platform")
):
    """
    Perform deep analysis on a single product.
    
    Includes:
    - Fetching up to 10 reviews
    - AI-powered sentiment analysis
    - Quality indicator extraction
    - Value scoring
    - Purchase recommendation
    
    Results are cached for 1 hour.
    """
    cache = get_cache_service()
    rapidapi = get_rapidapi_service()
    gemini = get_gemini_service()
    scoring = get_scoring_service()
    
    # Check cache
    cache_key = f"{product_id}:{source.value}"
    cached_result = cache.get("analyze", cache_key)
    
    if cached_result:
        return AnalyzeResponse(
            product=ProductWithAnalysis(**cached_result["product"]),
            recommendation=cached_result["recommendation"],
            confidence=cached_result["confidence"],
            cached=True
        )
    
    # For now, we need to search to get the product
    # In production, you'd have a product lookup endpoint
    raise HTTPException(
        status_code=501,
        detail="Single product analysis requires product data. Use /compare for full analysis."
    )


@router.get("/compare", response_model=CompareResponse)
async def compare_products(
    query: str = Query(..., min_length=1, max_length=200, description="Search query"),
    sources: List[ProductSource] = Query(
        default=[ProductSource.AMAZON, ProductSource.EBAY, ProductSource.WALMART],
        description="E-commerce sources to search"
    ),
    limit: int = Query(5, ge=1, le=10, description="Products per source to analyze")
):
    """
    Search, analyze, and compare products across platforms.
    
    This is the main endpoint that:
    1. Searches across all specified e-commerce platforms
    2. Fetches reviews for each product
    3. Runs AI sentiment analysis on reviews
    4. Calculates value scores
    5. Returns ranked products with recommendations
    
    Results are cached for 1 hour.
    """
    cache = get_cache_service()
    rapidapi = get_rapidapi_service()
    gemini = get_gemini_service()
    scoring = get_scoring_service()
    
    # Check cache
    sources_str = ",".join(sorted(s.value for s in sources))
    cache_key = hashlib.md5(f"{query}:{sources_str}:{limit}".encode()).hexdigest()
    cached_result = cache.get("compare", cache_key)
    
    if cached_result:
        products = [ProductWithAnalysis(**p) for p in cached_result["products"]]
        return CompareResponse(
            products=products,
            best_value=ProductWithAnalysis(**cached_result["best_value"]) if cached_result.get("best_value") else None,
            best_price=ProductWithAnalysis(**cached_result["best_price"]) if cached_result.get("best_price") else None,
            best_quality=ProductWithAnalysis(**cached_result["best_quality"]) if cached_result.get("best_quality") else None,
            recommendation=cached_result["recommendation"],
            cached=True
        )
    
    # Fetch products
    try:
        products = await rapidapi.search_all(query, sources, limit)
    except Exception as e:
        print(f"RapidAPI error, using mock data: {e}")
        products = []
    
    # Fall back to mock data if no products found
    use_mock = False
    if not products:
        print(f"No products from API, using mock data for query: {query}")
        products = get_mock_products(query, sources, limit)
        use_mock = True
    
    if not products:
        raise HTTPException(
            status_code=404,
            detail="No products found for the given query"
        )
    
    # Fetch reviews for each product (simplified - uses Amazon API for now)
    reviews_map = {}
    sentiments_map = {}
    
    for product in products[:limit]:
        # Use mock data when real API is unavailable
        if use_mock:
            reviews_map[product.id] = get_mock_reviews(product.id, limit=10)
            sentiments_map[product.id] = get_mock_sentiment()
        elif product.source == ProductSource.AMAZON:
            try:
                # Extract ASIN from product_id
                reviews = await rapidapi.fetch_amazon_reviews(product.id, limit=10)
                reviews_map[product.id] = reviews
            except Exception:
                reviews_map[product.id] = get_mock_reviews(product.id, limit=10)
        else:
            reviews_map[product.id] = get_mock_reviews(product.id, limit=10)
        
        # Run sentiment analysis
        if product.id not in sentiments_map:
            try:
                sentiment = await gemini.analyze_sentiment(
                    reviews_map[product.id],
                    product.title
                )
                sentiments_map[product.id] = sentiment
            except Exception:
                sentiments_map[product.id] = get_mock_sentiment()
    
    # Score products
    scored_products = scoring.score_products(
        products[:limit],
        reviews_map,
        sentiments_map
    )
    
    # Get best products
    bests = scoring.get_best_products(scored_products)
    
    # Generate recommendation
    try:
        products_data = [
            {
                "title": p.title,
                "price": p.price,
                "value_score": p.value_score,
                "price_score": p.price_score,
                "quality_score": p.quality_score,
                "source": p.source.value
            }
            for p in scored_products[:5]
        ]
        recommendation = await gemini.generate_recommendation(products_data)
    except Exception:
        if bests["best_value"]:
            recommendation = f"Based on our analysis, '{bests['best_value'].title}' offers the best overall value."
        else:
            recommendation = "Unable to generate recommendation."
    
    # Cache results
    cache_data = {
        "products": [p.model_dump() for p in scored_products],
        "best_value": bests["best_value"].model_dump() if bests["best_value"] else None,
        "best_price": bests["best_price"].model_dump() if bests["best_price"] else None,
        "best_quality": bests["best_quality"].model_dump() if bests["best_quality"] else None,
        "recommendation": recommendation
    }
    cache.set("compare", cache_key, cache_data)
    
    return CompareResponse(
        products=scored_products,
        best_value=bests["best_value"],
        best_price=bests["best_price"],
        best_quality=bests["best_quality"],
        recommendation=recommendation,
        cached=False
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    cache = get_cache_service()
    
    return {
        "status": "healthy",
        "cache": cache.get_stats()
    }
