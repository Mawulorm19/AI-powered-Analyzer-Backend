"""
Price Analyzer API - Gemini AI Service
Integrates Google Gemini 3 API for sentiment analysis and recommendations.
"""
import json
import asyncio
from typing import List, Optional
import google.generativeai as genai
from ..config import get_settings
from ..models import Review, SentimentAnalysis


class GeminiService:
    """Service for AI-powered analysis using Google Gemini 3 API."""
    
    def __init__(self):
        self.settings = get_settings()
        self._configure_api()
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def _configure_api(self):
        """Configure the Gemini API with credentials."""
        genai.configure(api_key=self.settings.GEMINI_API_KEY)
    
    async def analyze_sentiment(
        self,
        reviews: List[Review],
        product_title: str
    ) -> SentimentAnalysis:
        """
        Analyze sentiment of product reviews using Gemini.
        
        Args:
            reviews: List of product reviews
            product_title: Product name for context
            
        Returns:
            SentimentAnalysis object with pros, cons, and scores
        """
        if not reviews:
            return SentimentAnalysis(
                overall_sentiment="neutral",
                sentiment_score=0.0,
                pros=[],
                cons=[],
                summary="No reviews available for analysis."
            )
        
        # Prepare review text for analysis
        reviews_text = "\n".join([
            f"Rating: {r.rating}/5 - {r.text[:500]}" 
            for r in reviews[:10]  # Limit to top 10 reviews
        ])
        
        prompt = f"""Analyze the following customer reviews for the product "{product_title}" and provide a structured sentiment analysis.

Reviews:
{reviews_text}

Provide your analysis in the following JSON format:
{{
    "overall_sentiment": "positive" | "negative" | "neutral",
    "sentiment_score": <float between -1 and 1, where -1 is very negative and 1 is very positive>,
    "pros": ["list of key positive points mentioned by customers, max 5"],
    "cons": ["list of key negative points or concerns, max 5"],
    "summary": "A brief 2-3 sentence summary of overall customer sentiment"
}}

Only respond with valid JSON, no additional text."""

        try:
            # Run synchronous API call in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            # Parse the response
            response_text = response.text.strip()
            
            # Clean up response if it has markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            result = json.loads(response_text.strip())
            
            return SentimentAnalysis(
                overall_sentiment=result.get("overall_sentiment", "neutral"),
                sentiment_score=float(result.get("sentiment_score", 0.0)),
                pros=result.get("pros", [])[:5],
                cons=result.get("cons", [])[:5],
                summary=result.get("summary", "")
            )
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse Gemini response: {e}")
            return self._fallback_sentiment_analysis(reviews)
        except Exception as e:
            print(f"Gemini API error: {e}")
            return self._fallback_sentiment_analysis(reviews)
    
    def _fallback_sentiment_analysis(
        self,
        reviews: List[Review]
    ) -> SentimentAnalysis:
        """
        Simple fallback sentiment analysis based on ratings.
        
        Args:
            reviews: List of reviews
            
        Returns:
            Basic SentimentAnalysis based on average rating
        """
        if not reviews:
            return SentimentAnalysis(
                overall_sentiment="neutral",
                sentiment_score=0.0,
                pros=[],
                cons=[],
                summary="Unable to analyze reviews."
            )
        
        avg_rating = sum(r.rating for r in reviews) / len(reviews)
        
        # Map 0-5 rating to -1 to 1 sentiment
        sentiment_score = (avg_rating - 2.5) / 2.5
        
        if avg_rating >= 4.0:
            sentiment = "positive"
        elif avg_rating >= 2.5:
            sentiment = "neutral"
        else:
            sentiment = "negative"
        
        return SentimentAnalysis(
            overall_sentiment=sentiment,
            sentiment_score=round(sentiment_score, 2),
            pros=["Based on average rating only"],
            cons=["Detailed analysis unavailable"],
            summary=f"Average rating: {avg_rating:.1f}/5 based on {len(reviews)} reviews."
        )
    
    async def generate_recommendation(
        self,
        products_data: List[dict]
    ) -> str:
        """
        Generate a recommendation comparing multiple products.
        
        Args:
            products_data: List of product data with scores
            
        Returns:
            Recommendation text
        """
        if not products_data:
            return "No products available for comparison."
        
        products_text = json.dumps(products_data, indent=2)
        
        prompt = f"""You are a shopping advisor. Based on the following product comparison data, provide a clear recommendation for which product offers the best value.

Product Data:
{products_text}

Consider:
1. Price and value for money
2. Customer reviews and sentiment
3. Quality indicators
4. Overall value score

Provide a concise 3-4 sentence recommendation explaining your choice and why. Focus on practical advice for the buyer."""

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            return response.text.strip()
            
        except Exception as e:
            print(f"Gemini recommendation error: {e}")
            
            # Fallback: recommend highest value score
            if products_data:
                best = max(products_data, key=lambda x: x.get("value_score", 0))
                return f"Based on our analysis, '{best.get('title', 'the top product')}' offers the best overall value with a score of {best.get('value_score', 0):.1f}/10."
            
            return "Unable to generate recommendation at this time."
    
    async def extract_quality_indicators(
        self,
        reviews: List[Review],
        product_title: str
    ) -> dict:
        """
        Extract quality indicators from reviews.
        
        Args:
            reviews: List of product reviews
            product_title: Product name
            
        Returns:
            Dictionary with quality metrics
        """
        if not reviews:
            return {
                "durability": 0.5,
                "performance": 0.5,
                "build_quality": 0.5,
                "value_for_money": 0.5
            }
        
        reviews_text = "\n".join([r.text[:300] for r in reviews[:10]])
        
        prompt = f"""Analyze these reviews for "{product_title}" and rate the following quality aspects from 0.0 to 1.0.

Reviews:
{reviews_text}

Respond in JSON format:
{{
    "durability": <0.0-1.0>,
    "performance": <0.0-1.0>,
    "build_quality": <0.0-1.0>,
    "value_for_money": <0.0-1.0>
}}

Only respond with valid JSON."""

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            response_text = response.text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1]
            if response_text.endswith("```"):
                response_text = response_text.rsplit("\n", 1)[0]
            
            return json.loads(response_text)
            
        except Exception as e:
            print(f"Quality extraction error: {e}")
            # Fallback based on average rating
            avg_rating = sum(r.rating for r in reviews) / len(reviews)
            normalized = avg_rating / 5.0
            return {
                "durability": normalized,
                "performance": normalized,
                "build_quality": normalized,
                "value_for_money": normalized
            }


# Singleton instance
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get the Gemini service singleton."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
