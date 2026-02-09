"""
Price Analyzer API - Mock Data Service
Provides mock product data for testing when RapidAPI keys are not available.
"""
import random
from typing import List
from ..models import Product, ProductSource, Review, SentimentAnalysis


# Mock product templates
MOCK_PRODUCTS = {
    "wireless headphones": [
        {
            "title": "Sony WH-1000XM5 Wireless Noise Cancelling Headphones",
            "price": 348.00,
            "original_price": 399.99,
            "rating": 4.7,
            "review_count": 12543,
            "source": ProductSource.AMAZON,
            "image_url": "https://m.media-amazon.com/images/I/61vJtKbassL._AC_SL1500_.jpg"
        },
        {
            "title": "Apple AirPods Max - Space Gray",
            "price": 449.00,
            "original_price": 549.00,
            "rating": 4.6,
            "review_count": 8234,
            "source": ProductSource.AMAZON,
            "image_url": "https://m.media-amazon.com/images/I/81jNKu5U3lL._AC_SL1500_.jpg"
        },
        {
            "title": "Bose QuietComfort Ultra Headphones",
            "price": 379.00,
            "original_price": 429.00,
            "rating": 4.5,
            "review_count": 5621,
            "source": ProductSource.EBAY,
            "image_url": "https://m.media-amazon.com/images/I/51QnOIvVm8L._AC_SL1500_.jpg"
        },
        {
            "title": "Sennheiser Momentum 4 Wireless Headphones",
            "price": 299.95,
            "original_price": 379.95,
            "rating": 4.4,
            "review_count": 3456,
            "source": ProductSource.WALMART,
            "image_url": "https://m.media-amazon.com/images/I/61SUj2aKoEL._AC_SL1500_.jpg"
        },
        {
            "title": "JBL Tune 760NC Wireless Headphones",
            "price": 79.95,
            "original_price": 129.95,
            "rating": 4.3,
            "review_count": 7892,
            "source": ProductSource.WALMART,
            "image_url": "https://m.media-amazon.com/images/I/61SUj2aKoEL._AC_SL1500_.jpg"
        },
    ],
    "laptop stand": [
        {
            "title": "Rain Design mStand Laptop Stand - Space Gray",
            "price": 49.90,
            "original_price": 59.90,
            "rating": 4.7,
            "review_count": 15234,
            "source": ProductSource.AMAZON,
            "image_url": "https://m.media-amazon.com/images/I/71-oNMl84VL._AC_SL1500_.jpg"
        },
        {
            "title": "Twelve South Curve SE Aluminum Laptop Stand",
            "price": 59.99,
            "original_price": 79.99,
            "rating": 4.6,
            "review_count": 4521,
            "source": ProductSource.AMAZON,
            "image_url": "https://m.media-amazon.com/images/I/71-oNMl84VL._AC_SL1500_.jpg"
        },
        {
            "title": "UGREEN Laptop Stand Adjustable Height",
            "price": 29.99,
            "original_price": 39.99,
            "rating": 4.5,
            "review_count": 8765,
            "source": ProductSource.EBAY,
            "image_url": "https://m.media-amazon.com/images/I/71-oNMl84VL._AC_SL1500_.jpg"
        },
        {
            "title": "Amazon Basics Laptop Stand - Black",
            "price": 19.99,
            "original_price": 24.99,
            "rating": 4.3,
            "review_count": 23456,
            "source": ProductSource.WALMART,
            "image_url": "https://m.media-amazon.com/images/I/71-oNMl84VL._AC_SL1500_.jpg"
        },
    ],
    "default": [
        {
            "title": "Premium Product A - Top Rated",
            "price": 149.99,
            "original_price": 199.99,
            "rating": 4.8,
            "review_count": 5432,
            "source": ProductSource.AMAZON,
            "image_url": "https://via.placeholder.com/300x300?text=Product+A"
        },
        {
            "title": "Best Value Product B",
            "price": 79.99,
            "original_price": 99.99,
            "rating": 4.5,
            "review_count": 8765,
            "source": ProductSource.EBAY,
            "image_url": "https://via.placeholder.com/300x300?text=Product+B"
        },
        {
            "title": "Budget-Friendly Product C",
            "price": 39.99,
            "original_price": 49.99,
            "rating": 4.2,
            "review_count": 12345,
            "source": ProductSource.WALMART,
            "image_url": "https://via.placeholder.com/300x300?text=Product+C"
        },
        {
            "title": "Professional Product D",
            "price": 249.99,
            "original_price": 299.99,
            "rating": 4.6,
            "review_count": 3456,
            "source": ProductSource.AMAZON,
            "image_url": "https://via.placeholder.com/300x300?text=Product+D"
        },
        {
            "title": "Affordable Product E",
            "price": 24.99,
            "original_price": None,
            "rating": 4.0,
            "review_count": 6789,
            "source": ProductSource.EBAY,
            "image_url": "https://via.placeholder.com/300x300?text=Product+E"
        },
    ]
}

MOCK_REVIEWS = [
    Review(text="Excellent product! Great value for money. Highly recommend.", rating=5.0, author="John D.", verified=True),
    Review(text="Good quality, arrived quickly. Works as expected.", rating=4.0, author="Sarah M.", verified=True),
    Review(text="Love it! Using it every day. Build quality is amazing.", rating=5.0, author="Mike R.", verified=True),
    Review(text="Decent product but could be better. Some minor issues.", rating=3.0, author="Lisa K.", verified=False),
    Review(text="Perfect for my needs. Would buy again.", rating=5.0, author="Tom H.", verified=True),
    Review(text="Good but not great. Expected more for the price.", rating=3.5, author="Anna P.", verified=True),
    Review(text="Outstanding! Exceeded my expectations completely.", rating=5.0, author="Chris B.", verified=True),
    Review(text="Works well. Fast shipping. Happy with purchase.", rating=4.5, author="Emily W.", verified=True),
    Review(text="Not bad for the price. Gets the job done.", rating=3.5, author="David L.", verified=False),
    Review(text="Fantastic quality and performance. 5 stars!", rating=5.0, author="Jennifer S.", verified=True),
]

MOCK_SENTIMENTS = [
    SentimentAnalysis(
        overall_sentiment="positive",
        sentiment_score=0.85,
        pros=["Excellent build quality", "Great value for money", "Fast shipping", "Easy to use"],
        cons=["Could be cheaper", "Minor design issues"],
        summary="Customers love this product for its quality and value. Most reviews highlight the excellent build quality and ease of use."
    ),
    SentimentAnalysis(
        overall_sentiment="positive",
        sentiment_score=0.72,
        pros=["Good performance", "Reliable", "Nice design"],
        cons=["Price is a bit high", "Some features missing"],
        summary="Generally positive reviews with customers appreciating the performance and reliability. Some concerns about pricing."
    ),
    SentimentAnalysis(
        overall_sentiment="positive",
        sentiment_score=0.65,
        pros=["Affordable", "Works as described", "Good customer service"],
        cons=["Average quality", "Not the best in class"],
        summary="A solid budget option. Customers find it works well for the price point."
    ),
    SentimentAnalysis(
        overall_sentiment="neutral",
        sentiment_score=0.45,
        pros=["Cheap price", "Fast delivery"],
        cons=["Quality could be better", "Not very durable", "Missing features"],
        summary="Mixed reviews. While the price is attractive, some customers report quality issues."
    ),
]


def get_mock_products(query: str, sources: List[ProductSource], limit: int = 5) -> List[Product]:
    """
    Get mock products for testing.
    
    Args:
        query: Search query
        sources: List of sources to include
        limit: Maximum products to return
        
    Returns:
        List of mock Product objects
    """
    # Find matching mock data or use default
    query_lower = query.lower()
    mock_data = MOCK_PRODUCTS.get("default", [])
    
    for key in MOCK_PRODUCTS:
        if key in query_lower:
            mock_data = MOCK_PRODUCTS[key]
            break
    
    # Filter by source and create Product objects
    products = []
    for i, item in enumerate(mock_data):
        if item["source"] in sources and len(products) < limit:
            # Add query to title for realism
            title = item["title"]
            if query_lower not in title.lower():
                title = f"{item['title']} - {query.title()}"
            
            product = Product(
                id=f"mock_{item['source'].value}_{i}_{hash(query) % 10000}",
                title=title,
                price=item["price"] + random.uniform(-5, 5),  # Add slight variation
                original_price=item.get("original_price"),
                currency="USD",
                image_url=item.get("image_url", ""),
                product_url=f"https://example.com/product/{i}",
                source=item["source"],
                rating=item.get("rating"),
                review_count=item.get("review_count"),
                availability="in_stock"
            )
            products.append(product)
    
    return products


def get_mock_reviews(product_id: str, limit: int = 10) -> List[Review]:
    """Get mock reviews for a product."""
    return random.sample(MOCK_REVIEWS, min(limit, len(MOCK_REVIEWS)))


def get_mock_sentiment() -> SentimentAnalysis:
    """Get a random mock sentiment analysis."""
    return random.choice(MOCK_SENTIMENTS)
