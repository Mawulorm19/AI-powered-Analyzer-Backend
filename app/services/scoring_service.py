"""
Price Analyzer API - Scoring Service
Implements value score algorithm combining price, reviews, and quality.
"""
from typing import List, Optional
from ..models import Product, ProductWithAnalysis, SentimentAnalysis, Review
from ..config import get_settings


class ScoringService:
    """Service for calculating product value scores."""
    
    def __init__(self):
        self.settings = get_settings()
    
    def calculate_price_score(
        self,
        price: float,
        min_price: float,
        max_price: float
    ) -> float:
        """
        Calculate price score (0-10) where lower price = higher score.
        
        Uses inverse normalization so cheapest products get highest scores.
        
        Args:
            price: Product price
            min_price: Minimum price in comparison set
            max_price: Maximum price in comparison set
            
        Returns:
            Price score from 0 to 10
        """
        if max_price == min_price:
            return 7.5  # Default middle-high score for single price point
        
        # Inverse normalization: (max - price) / (max - min)
        normalized = (max_price - price) / (max_price - min_price)
        
        # Scale to 0-10
        score = normalized * 10
        
        return round(min(10, max(0, score)), 2)
    
    def calculate_review_score(
        self,
        rating: Optional[float],
        review_count: Optional[int],
        sentiment: Optional[SentimentAnalysis]
    ) -> float:
        """
        Calculate review score (0-10) based on rating, volume, and sentiment.
        
        Combines:
        - Average rating (0-5 scaled to 0-10)
        - Review volume bonus (more reviews = more confidence)
        - Sentiment analysis adjustment
        
        Args:
            rating: Average product rating (0-5)
            review_count: Number of reviews
            sentiment: Sentiment analysis result
            
        Returns:
            Review score from 0 to 10
        """
        # Base score from rating
        if rating is not None:
            base_score = (rating / 5) * 10
        else:
            base_score = 5.0  # Neutral if no rating
        
        # Volume confidence modifier
        # More reviews = more reliable score
        volume_modifier = 1.0
        if review_count is not None:
            if review_count >= 1000:
                volume_modifier = 1.15
            elif review_count >= 500:
                volume_modifier = 1.10
            elif review_count >= 100:
                volume_modifier = 1.05
            elif review_count >= 10:
                volume_modifier = 1.0
            else:
                volume_modifier = 0.90  # Low confidence for few reviews
        
        # Sentiment adjustment (-0.5 to +0.5 points)
        sentiment_adjustment = 0.0
        if sentiment is not None:
            # Sentiment score is -1 to 1, scale to -0.5 to 0.5
            sentiment_adjustment = sentiment.sentiment_score * 0.5
        
        # Calculate final score
        score = (base_score * volume_modifier) + sentiment_adjustment
        
        return round(min(10, max(0, score)), 2)
    
    def calculate_quality_score(
        self,
        sentiment: Optional[SentimentAnalysis],
        quality_indicators: Optional[dict] = None
    ) -> float:
        """
        Calculate quality score (0-10) based on sentiment and quality indicators.
        
        Args:
            sentiment: Sentiment analysis result
            quality_indicators: Dict with durability, performance, etc.
            
        Returns:
            Quality score from 0 to 10
        """
        scores = []
        
        # Base from sentiment
        if sentiment is not None:
            # Map -1 to 1 sentiment to 0 to 10
            sentiment_score = (sentiment.sentiment_score + 1) * 5
            scores.append(sentiment_score)
            
            # Bonus for more pros than cons
            pros_count = len(sentiment.pros)
            cons_count = len(sentiment.cons)
            if pros_count > 0 or cons_count > 0:
                ratio = pros_count / (pros_count + cons_count)
                ratio_score = ratio * 10
                scores.append(ratio_score)
        
        # Quality indicators
        if quality_indicators:
            indicator_scores = []
            for key in ['durability', 'performance', 'build_quality', 'value_for_money']:
                if key in quality_indicators:
                    indicator_scores.append(quality_indicators[key] * 10)
            
            if indicator_scores:
                scores.append(sum(indicator_scores) / len(indicator_scores))
        
        # Return average or default
        if scores:
            return round(min(10, max(0, sum(scores) / len(scores))), 2)
        
        return 5.0  # Neutral default
    
    def calculate_value_score(
        self,
        price_score: float,
        review_score: float,
        quality_score: float
    ) -> float:
        """
        Calculate overall value score using weighted average.
        
        Default weights:
        - Price: 35%
        - Reviews: 35%
        - Quality: 30%
        
        Args:
            price_score: Price score (0-10)
            review_score: Review score (0-10)
            quality_score: Quality score (0-10)
            
        Returns:
            Overall value score from 0 to 10
        """
        weighted_score = (
            price_score * self.settings.PRICE_WEIGHT +
            review_score * self.settings.REVIEW_WEIGHT +
            quality_score * self.settings.QUALITY_WEIGHT
        )
        
        return round(weighted_score, 2)
    
    def score_product(
        self,
        product: Product,
        min_price: float,
        max_price: float,
        reviews: List[Review],
        sentiment: Optional[SentimentAnalysis] = None,
        quality_indicators: Optional[dict] = None
    ) -> ProductWithAnalysis:
        """
        Calculate all scores for a product.
        
        Args:
            product: Base product data
            min_price: Minimum price in comparison set
            max_price: Maximum price in comparison set
            reviews: Product reviews
            sentiment: Sentiment analysis result
            quality_indicators: Quality metrics from AI
            
        Returns:
            ProductWithAnalysis with all scores
        """
        price_score = self.calculate_price_score(
            product.price, min_price, max_price
        )
        
        review_score = self.calculate_review_score(
            product.rating, product.review_count, sentiment
        )
        
        quality_score = self.calculate_quality_score(
            sentiment, quality_indicators
        )
        
        value_score = self.calculate_value_score(
            price_score, review_score, quality_score
        )
        
        return ProductWithAnalysis(
            **product.model_dump(),
            reviews=reviews,
            sentiment=sentiment,
            value_score=value_score,
            price_score=price_score,
            review_score=review_score,
            quality_score=quality_score
        )
    
    def score_products(
        self,
        products: List[Product],
        reviews_map: dict,
        sentiments_map: dict,
        quality_map: Optional[dict] = None
    ) -> List[ProductWithAnalysis]:
        """
        Score multiple products relative to each other.
        
        Args:
            products: List of products to score
            reviews_map: Dict mapping product_id to reviews
            sentiments_map: Dict mapping product_id to sentiment
            quality_map: Dict mapping product_id to quality indicators
            
        Returns:
            List of scored products sorted by value score
        """
        if not products:
            return []
        
        # Get price range
        prices = [p.price for p in products]
        min_price = min(prices)
        max_price = max(prices)
        
        # Score each product
        scored_products = []
        for product in products:
            reviews = reviews_map.get(product.id, [])
            sentiment = sentiments_map.get(product.id)
            quality = quality_map.get(product.id) if quality_map else None
            
            scored = self.score_product(
                product, min_price, max_price,
                reviews, sentiment, quality
            )
            scored_products.append(scored)
        
        # Sort by value score descending
        scored_products.sort(key=lambda x: x.value_score, reverse=True)
        
        return scored_products
    
    def get_best_products(
        self,
        products: List[ProductWithAnalysis]
    ) -> dict:
        """
        Get best products by different criteria.
        
        Args:
            products: List of scored products
            
        Returns:
            Dict with best_value, best_price, best_quality
        """
        if not products:
            return {
                "best_value": None,
                "best_price": None,
                "best_quality": None
            }
        
        return {
            "best_value": max(products, key=lambda x: x.value_score),
            "best_price": max(products, key=lambda x: x.price_score),
            "best_quality": max(products, key=lambda x: x.quality_score)
        }


# Singleton instance
_scoring_service: Optional[ScoringService] = None


def get_scoring_service() -> ScoringService:
    """Get the scoring service singleton."""
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = ScoringService()
    return _scoring_service
