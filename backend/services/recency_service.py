"""
Recency-based verification routing service for DeceptiScan.

Detects whether content references recent dates/events (within configurable window, default 7 days)
and routes through external fact-checking APIs (Google Fact Check Tools API) if un-cached.
"""
import os
import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
import requests

logger = logging.getLogger(__name__)

GOOGLE_FACT_CHECK_API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


class RecencyService:
    """Service to handle recency detection and external verification routing."""

    def __init__(self, recency_window_days: int = 7):
        self.recency_window_days = recency_window_days
        self.api_key = os.environ.get("GOOGLE_FACT_CHECK_API_KEY", "")

    def is_recent_content(self, text: str) -> bool:
        """
        Check if text references dates within the recency window.
        
        Searches for date patterns (ISO dates, relative references like 'today', 'yesterday',
        or recent month-day references).
        """
        if not text:
            return False

        text_lower = text.lower()

        # Relative recent keywords
        recent_keywords = [
            "today", "yesterday", "this week", "just in", "breaking news",
            "hours ago", "days ago", "this morning", "this evening"
        ]
        if any(kw in text_lower for kw in recent_keywords):
            return True

        # Extract explicit dates (YYYY-MM-DD, Month DD, YYYY, DD Month YYYY)
        now = datetime.utcnow()
        cutoff_date = now - timedelta(days=self.recency_window_days)

        # ISO format: 2026-07-31
        iso_matches = re.findall(r'\b(20\d{2})[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b', text)
        for year, month, day in iso_matches:
            try:
                dt = datetime(int(year), int(month), int(day))
                if dt >= cutoff_date:
                    return True
            except ValueError:
                continue

        # Month Day, Year format: July 31, 2026 or Jul 31, 2026
        month_names = "january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"
        month_matches = re.findall(rf'\b({month_names})\s+([0-2]?\d|3[01]),?\s+(20\d{{2}})\b', text_lower)
        
        month_map = {
            'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
            'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
            'aug': 8, 'august': 8, 'sep': 9, 'september': 9, 'oct': 10, 'october': 10,
            'nov': 11, 'november': 11, 'dec': 12, 'december': 12
        }

        for month_str, day_str, year_str in month_matches:
            try:
                m = month_map.get(month_str[:3], 1)
                dt = datetime(int(year_str), m, int(day_str))
                if dt >= cutoff_date:
                    return True
            except ValueError:
                continue

        return False

    def query_fact_check_api(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Query Google Fact Check Tools API for matching claim reviews.
        """
        if not self.api_key:
            logger.info("Google Fact Check API key not configured; skipping external call.")
            return None

        # Take first 200 chars for query search
        query = text[:200].strip()
        try:
            params = {
                "query": query,
                "key": self.api_key,
                "languageCode": "en"
            }
            resp = requests.get(GOOGLE_FACT_CHECK_API_URL, params=params, timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                claims = data.get("claims", [])
                if claims:
                    first_claim = claims[0]
                    claim_reviews = first_claim.get("claimReview", [])
                    if claim_reviews:
                        review = claim_reviews[0]
                        rating = review.get("textualRating", "Unverified")
                        return {
                            "claim": first_claim.get("text"),
                            "rating": rating,
                            "publisher": review.get("publisher", {}).get("name"),
                            "url": review.get("url")
                        }
        except Exception as e:
            logger.error(f"Error querying Fact Check API: {e}")

        return None

    def process_recency_routing(self, text: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Main entry point for recency verification routing.
        
        Returns:
            (is_recent, recency_analysis_dict_or_none)
        """
        if not self.is_recent_content(text):
            return False, None

        logger.info("Recent content detected; attempting external verification routing.")
        fact_check = self.query_fact_check_api(text)

        if fact_check:
            # Fact check match found
            rating_lower = fact_check["rating"].lower()
            is_reliable = any(r in rating_lower for r in ["true", "correct", "accurate"])
            score = 90.0 if is_reliable else 20.0
            classification = "reliable" if is_reliable else "unreliable"

            recency_result = {
                "authenticity_score": score,
                "confidence": 0.9,
                "classification": classification,
                "warning": f"Verified via external fact check ({fact_check['publisher']}): {fact_check['rating']}",
                "sentence_analysis": [],
                "model_version": "google-factcheck-v1",
                "recency_verified": True,
                "fact_check": fact_check
            }
            return True, recency_result

        # No external verification found -> unverified_style_estimate
        recency_result = {
            "authenticity_score": 50.0,
            "confidence": 0.35,
            "classification": "unverified_style_estimate",
            "warning": "Recent content detected without external verification. Classification marked as unverified_style_estimate.",
            "sentence_analysis": [],
            "model_version": "recency-heuristic-v1",
            "recency_verified": False
        }
        return True, recency_result


_recency_service: Optional[RecencyService] = None


def get_recency_service() -> RecencyService:
    global _recency_service
    if _recency_service is None:
        _recency_service = RecencyService()
    return _recency_service
