"""
Price Analyzer API - Test Suite for Scoring Logic
Tests scoring on 5 disparate products to validate the algorithm.
"""
import pytest
from app.services.scoring_service import ScoringService
from app.models import Product, ProductSource, Review, SentimentAnalysis


@pytest.fixture
def scoring_service():
    """Create scoring service instance."""
    return ScoringService()


@pytest.fixture
def test_products():
    """Create 5 disparate test products."""
    return [
        # 1. Budget product with good reviews
        Product(
            id="prod_001",
            title="Budget Wireless Earbuds",
            price=29.99,
            original_price=49.99,
            currency="USD",
            image_url="https://example.com/earbuds.jpg",
            product_url="https://amazon.com/earbuds",
            source=ProductSource.AMAZON,
            rating=4.5,
            review_count=2500,
            availability="in_stock"
        ),
        # 2. Premium product with excellent reviews
        Product(
            id="prod_002",
            title="Premium Noise Cancelling Headphones",
            price=349.99,
            original_price=399.99,
            currency="USD",
            image_url="https://example.com/headphones.jpg",
            product_url="https://amazon.com/headphones",
            source=ProductSource.AMAZON,
            rating=4.8,
            review_count=8500,
            availability="in_stock"
        ),
        # 3. Mid-range product with average reviews
        Product(
            id="prod_003",
            title="Standard Over-Ear Headphones",
            price=89.99,
            original_price=99.99,
            currency="USD",
            image_url="https://example.com/standard.jpg",
            product_url="https://ebay.com/standard",
            source=ProductSource.EBAY,
            rating=3.5,
            review_count=450,
            availability="in_stock"
        ),
        # 4. Cheap product with poor reviews
        Product(
            id="prod_004",
            title="Ultra Budget Wired Earphones",
            price=7.99,
            original_price=None,
            currency="USD",
            image_url="https://example.com/cheap.jpg",
            product_url="https://walmart.com/cheap",
            source=ProductSource.WALMART,
            rating=2.1,
            review_count=150,
            availability="in_stock"
        ),
        # 5. New product with no reviews
        Product(
            id="prod_005",
            title="New Gaming Headset",
            price=149.99,
            original_price=179.99,
            currency="USD",
            image_url="https://example.com/gaming.jpg",
            product_url="https://walmart.com/gaming",
            source=ProductSource.WALMART,
            rating=None,
            review_count=0,
            availability="in_stock"
        ),
    ]


@pytest.fixture
def test_sentiments():
    """Create sentiment analysis results for test products."""
    return {
        "prod_001": SentimentAnalysis(
            overall_sentiment="positive",
            sentiment_score=0.75,
            pros=["Great value", "Good sound quality", "Long battery life"],
            cons=["No noise cancelling", "Cheap case"],
            summary="Excellent budget option with surprising quality."
        ),
        "prod_002": SentimentAnalysis(
            overall_sentiment="positive",
            sentiment_score=0.92,
            pros=["Best noise cancelling", "Premium build", "Excellent sound", "Long battery"],
            cons=["Expensive", "Heavy"],
            summary="Premium headphones with outstanding performance."
        ),
        "prod_003": SentimentAnalysis(
            overall_sentiment="neutral",
            sentiment_score=0.15,
            pros=["Comfortable", "Decent sound"],
            cons=["Build quality issues", "Short cable", "No warranty"],
            summary="Average headphones with some quality concerns."
        ),
        "prod_004": SentimentAnalysis(
            overall_sentiment="negative",
            sentiment_score=-0.65,
            pros=["Very cheap"],
            cons=["Breaks easily", "Poor sound", "Uncomfortable", "No bass"],
            summary="Low quality product that may not last long."
        ),
        "prod_005": SentimentAnalysis(
            overall_sentiment="neutral",
            sentiment_score=0.0,
            pros=[],
            cons=[],
            summary="No reviews available for analysis."
        ),
    }


class TestPriceScore:
    """Test price scoring functionality."""
    
    def test_lowest_price_gets_highest_score(self, scoring_service):
        """Lowest price should get score of 10."""
        score = scoring_service.calculate_price_score(7.99, 7.99, 349.99)
        assert score == 10.0
    
    def test_highest_price_gets_lowest_score(self, scoring_service):
        """Highest price should get score of 0."""
        score = scoring_service.calculate_price_score(349.99, 7.99, 349.99)
        assert score == 0.0
    
    def test_mid_price_gets_mid_score(self, scoring_service):
        """Middle price should get approximately middle score."""
        score = scoring_service.calculate_price_score(178.99, 7.99, 349.99)
        assert 4.0 <= score <= 6.0
    
    def test_same_price_range(self, scoring_service):
        """When all prices are same, should return default score."""
        score = scoring_service.calculate_price_score(100.0, 100.0, 100.0)
        assert score == 7.5


class TestReviewScore:
    """Test review scoring functionality."""
    
    def test_high_rating_high_score(self, scoring_service):
        """High rating with many reviews should get high score."""
        sentiment = SentimentAnalysis(
            overall_sentiment="positive",
            sentiment_score=0.9,
            pros=["Great"],
            cons=[],
            summary="Excellent"
        )
        score = scoring_service.calculate_review_score(4.8, 8500, sentiment)
        assert score >= 9.0
    
    def test_low_rating_low_score(self, scoring_service):
        """Low rating should get low score."""
        sentiment = SentimentAnalysis(
            overall_sentiment="negative",
            sentiment_score=-0.7,
            pros=[],
            cons=["Bad"],
            summary="Poor"
        )
        score = scoring_service.calculate_review_score(2.1, 150, sentiment)
        assert score <= 5.0
    
    def test_no_rating_neutral_score(self, scoring_service):
        """No rating should get neutral score."""
        score = scoring_service.calculate_review_score(None, None, None)
        assert score == 5.0
    
    def test_volume_modifier(self, scoring_service):
        """More reviews should increase score slightly."""
        score_low = scoring_service.calculate_review_score(4.0, 5, None)
        score_high = scoring_service.calculate_review_score(4.0, 1000, None)
        assert score_high > score_low


class TestQualityScore:
    """Test quality scoring functionality."""
    
    def test_positive_sentiment_high_score(self, scoring_service):
        """Positive sentiment should give high quality score."""
        sentiment = SentimentAnalysis(
            overall_sentiment="positive",
            sentiment_score=0.9,
            pros=["Great", "Excellent", "Perfect"],
            cons=["Minor issue"],
            summary="Excellent"
        )
        score = scoring_service.calculate_quality_score(sentiment)
        assert score >= 7.0
    
    def test_negative_sentiment_low_score(self, scoring_service):
        """Negative sentiment should give low quality score."""
        sentiment = SentimentAnalysis(
            overall_sentiment="negative",
            sentiment_score=-0.8,
            pros=[],
            cons=["Bad", "Terrible", "Awful", "Broken"],
            summary="Poor"
        )
        score = scoring_service.calculate_quality_score(sentiment)
        assert score <= 3.0


class TestValueScore:
    """Test overall value score calculation."""
    
    def test_value_score_weights(self, scoring_service):
        """Value score should use proper weights."""
        value = scoring_service.calculate_value_score(10.0, 10.0, 10.0)
        assert value == 10.0
        
        value = scoring_service.calculate_value_score(0.0, 0.0, 0.0)
        assert value == 0.0
    
    def test_balanced_scores(self, scoring_service):
        """Balanced scores should give balanced value."""
        value = scoring_service.calculate_value_score(5.0, 5.0, 5.0)
        assert value == 5.0


class TestProductScoring:
    """Test complete product scoring."""
    
    def test_score_products(self, scoring_service, test_products, test_sentiments):
        """Test scoring multiple products."""
        reviews_map = {p.id: [] for p in test_products}
        
        scored = scoring_service.score_products(
            test_products,
            reviews_map,
            test_sentiments
        )
        
        # Should return same number of products
        assert len(scored) == 5
        
        # Should be sorted by value score
        for i in range(len(scored) - 1):
            assert scored[i].value_score >= scored[i + 1].value_score
    
    def test_best_products(self, scoring_service, test_products, test_sentiments):
        """Test finding best products by criteria."""
        reviews_map = {p.id: [] for p in test_products}
        
        scored = scoring_service.score_products(
            test_products,
            reviews_map,
            test_sentiments
        )
        
        bests = scoring_service.get_best_products(scored)
        
        assert bests["best_value"] is not None
        assert bests["best_price"] is not None
        assert bests["best_quality"] is not None
    
    def test_disparate_products_ranking(self, scoring_service, test_products, test_sentiments):
        """Test that disparate products are ranked sensibly."""
        reviews_map = {p.id: [] for p in test_products}
        
        scored = scoring_service.score_products(
            test_products,
            reviews_map,
            test_sentiments
        )
        
        # The budget product with good reviews should rank highly
        budget_product = next(p for p in scored if p.id == "prod_001")
        assert budget_product.value_score >= 6.0
        
        # The premium product should have high quality but lower value due to price
        premium_product = next(p for p in scored if p.id == "prod_002")
        assert premium_product.quality_score >= 8.0
        
        # The cheap product with poor reviews should rank low
        cheap_product = next(p for p in scored if p.id == "prod_004")
        assert cheap_product.quality_score <= 4.0


class TestPriceNormalization:
    """Test price normalization utility."""
    
    def test_usd_prices(self):
        from app.utils.price_normalizer import normalize_price
        
        price, currency = normalize_price("$29.99")
        assert price == 29.99
        assert currency == "USD"
        
        price, currency = normalize_price("$1,299.99")
        assert price == 1299.99
    
    def test_european_format(self):
        from app.utils.price_normalizer import normalize_price
        
        price, currency = normalize_price("€99,50")
        assert price is not None
        assert currency == "EUR"
    
    def test_invalid_prices(self):
        from app.utils.price_normalizer import normalize_price
        
        price, currency = normalize_price("")
        assert price is None
        
        price, currency = normalize_price("Free")
        assert price is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
