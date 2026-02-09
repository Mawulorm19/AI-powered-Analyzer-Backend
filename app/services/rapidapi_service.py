"""
Price Analyzer API - RapidAPI Service
Fetches product data from multiple e-commerce platforms via RapidAPI.
"""
import httpx
import asyncio
import hashlib
from typing import List, Optional, Dict, Any
from ..config import get_settings
from ..models import Product, ProductSource, Review
from ..utils.price_normalizer import normalize_price


class RapidAPIService:
    """Service for fetching product data from RapidAPI endpoints."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client
    
    async def close(self):
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    def _generate_product_id(self, source: str, identifier: str) -> str:
        """Generate a unique product ID."""
        combined = f"{source}:{identifier}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]
    
    async def search_amazon(
        self,
        query: str,
        limit: int = 10
    ) -> List[Product]:
        """
        Search Amazon products via RapidAPI.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of Product objects
        """
        client = await self._get_client()
        
        url = "https://real-time-amazon-data.p.rapidapi.com/search"
        headers = {
            "X-RapidAPI-Key": self.settings.RAPIDAPI_KEY,
            "X-RapidAPI-Host": self.settings.RAPIDAPI_HOST_AMAZON
        }
        params = {
            "query": query,
            "page": "1",
            "country": "US",
            "sort_by": "RELEVANCE"
        }
        
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            products = []
            items = data.get("data", {}).get("products", [])[:limit]
            
            for item in items:
                price_str = item.get("product_price", "")
                price, currency = normalize_price(price_str)
                
                original_price_str = item.get("product_original_price", "")
                original_price, _ = normalize_price(original_price_str)
                
                if price is None:
                    continue
                
                product = Product(
                    id=self._generate_product_id("amazon", item.get("asin", "")),
                    title=item.get("product_title", "Unknown"),
                    price=price,
                    original_price=original_price,
                    currency=currency,
                    image_url=item.get("product_photo", ""),
                    product_url=item.get("product_url", ""),
                    source=ProductSource.AMAZON,
                    rating=item.get("product_star_rating"),
                    review_count=item.get("product_num_ratings"),
                    availability="in_stock" if item.get("is_prime") else "unknown"
                )
                products.append(product)
            
            return products
            
        except httpx.HTTPError as e:
            print(f"Amazon API error: {e}")
            return []
    
    async def search_ebay(
        self,
        query: str,
        limit: int = 10
    ) -> List[Product]:
        """
        Search eBay products via RapidAPI.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of Product objects
        """
        client = await self._get_client()
        
        url = "https://ebay-search-result.p.rapidapi.com/search"
        headers = {
            "X-RapidAPI-Key": self.settings.RAPIDAPI_KEY,
            "X-RapidAPI-Host": self.settings.RAPIDAPI_HOST_EBAY
        }
        params = {
            "keywords": query,
            "page": "1"
        }
        
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            products = []
            items = data.get("results", [])[:limit]
            
            for item in items:
                price_str = item.get("price", {}).get("value", "")
                price, currency = normalize_price(price_str)
                
                if price is None:
                    continue
                
                product = Product(
                    id=self._generate_product_id("ebay", item.get("itemId", "")),
                    title=item.get("title", "Unknown"),
                    price=price,
                    original_price=None,
                    currency=currency,
                    image_url=item.get("image", {}).get("imageUrl", ""),
                    product_url=item.get("itemWebUrl", ""),
                    source=ProductSource.EBAY,
                    rating=None,
                    review_count=None,
                    availability="in_stock"
                )
                products.append(product)
            
            return products
            
        except httpx.HTTPError as e:
            print(f"eBay API error: {e}")
            return []
    
    async def search_walmart(
        self,
        query: str,
        limit: int = 10
    ) -> List[Product]:
        """
        Search Walmart products via RapidAPI.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of Product objects
        """
        client = await self._get_client()
        
        url = "https://walmart-api.p.rapidapi.com/search"
        headers = {
            "X-RapidAPI-Key": self.settings.RAPIDAPI_KEY,
            "X-RapidAPI-Host": self.settings.RAPIDAPI_HOST_WALMART
        }
        params = {
            "query": query,
            "page": "1"
        }
        
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            products = []
            items = data.get("items", [])[:limit]
            
            for item in items:
                price = item.get("priceInfo", {}).get("currentPrice", {}).get("price")
                
                if price is None:
                    price_str = item.get("priceInfo", {}).get("currentPrice", {}).get("priceString", "")
                    price, _ = normalize_price(price_str)
                
                if price is None:
                    continue
                
                original_price = item.get("priceInfo", {}).get("wasPrice", {}).get("price")
                
                product = Product(
                    id=self._generate_product_id("walmart", str(item.get("usItemId", ""))),
                    title=item.get("name", "Unknown"),
                    price=price,
                    original_price=original_price,
                    currency="USD",
                    image_url=item.get("imageInfo", {}).get("thumbnailUrl", ""),
                    product_url=f"https://www.walmart.com/ip/{item.get('usItemId', '')}",
                    source=ProductSource.WALMART,
                    rating=item.get("averageRating"),
                    review_count=item.get("numberOfReviews"),
                    availability="in_stock" if item.get("availabilityStatusV2", {}).get("value") == "IN_STOCK" else "unknown"
                )
                products.append(product)
            
            return products
            
        except httpx.HTTPError as e:
            print(f"Walmart API error: {e}")
            return []
    
    async def fetch_amazon_reviews(
        self,
        asin: str,
        limit: int = 10
    ) -> List[Review]:
        """
        Fetch reviews for an Amazon product.
        
        Args:
            asin: Amazon Standard Identification Number
            limit: Maximum number of reviews
            
        Returns:
            List of Review objects
        """
        client = await self._get_client()
        
        url = "https://real-time-amazon-data.p.rapidapi.com/product-reviews"
        headers = {
            "X-RapidAPI-Key": self.settings.RAPIDAPI_KEY,
            "X-RapidAPI-Host": self.settings.RAPIDAPI_HOST_AMAZON
        }
        params = {
            "asin": asin,
            "country": "US",
            "verified_purchases_only": "false",
            "images_or_videos_only": "false",
            "page": "1"
        }
        
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            reviews = []
            items = data.get("data", {}).get("reviews", [])[:limit]
            
            for item in items:
                review = Review(
                    text=item.get("review_comment", ""),
                    rating=float(item.get("review_star_rating", 0)),
                    author=item.get("review_author", "Anonymous"),
                    date=item.get("review_date", ""),
                    verified=item.get("is_verified_purchase", False)
                )
                reviews.append(review)
            
            return reviews
            
        except httpx.HTTPError as e:
            print(f"Amazon reviews API error: {e}")
            return []
    
    async def search_all(
        self,
        query: str,
        sources: List[ProductSource],
        limit: int = 10
    ) -> List[Product]:
        """
        Search across all specified sources.
        
        Args:
            query: Search query
            sources: List of sources to search
            limit: Maximum results per source
            
        Returns:
            Combined list of products from all sources
        """
        tasks = []
        
        if ProductSource.AMAZON in sources:
            tasks.append(self.search_amazon(query, limit))
        if ProductSource.EBAY in sources:
            tasks.append(self.search_ebay(query, limit))
        if ProductSource.WALMART in sources:
            tasks.append(self.search_walmart(query, limit))
        
        if not tasks:
            return []
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        products = []
        for result in results:
            if isinstance(result, list):
                products.extend(result)
            elif isinstance(result, Exception):
                print(f"Search error: {result}")
        
        return products


# Singleton instance
_rapidapi_service: Optional[RapidAPIService] = None


def get_rapidapi_service() -> RapidAPIService:
    """Get the RapidAPI service singleton."""
    global _rapidapi_service
    if _rapidapi_service is None:
        _rapidapi_service = RapidAPIService()
    return _rapidapi_service
