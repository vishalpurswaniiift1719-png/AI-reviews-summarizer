"""
Tests for the tools module, specifically review ingestion.
"""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.tools.fetch_reviews import fetch_and_filter_reviews, fetch_reviews
from src.config import RAW_DIR


@pytest.fixture
def mock_reviews_data():
    """Returns mock data resembling google_play_scraper output."""
    now = datetime.now()
    return [
        {
            "reviewId": "r1",
            "score": 5,
            "userName": "Alice",
            "content": "Great app!",
            "at": now - timedelta(days=1)
        },
        {
            "reviewId": "r2",
            "score": 3,
            "userName": "Bob",
            "content": "Okay but has bugs",
            "at": now - timedelta(days=10)
        },
        {
            "reviewId": "r3",
            "score": 1,
            "userName": "Charlie",
            "content": "Too old review",
            "at": now - timedelta(weeks=12) # Older than 10 weeks default
        }
    ]


@patch("src.tools.fetch_reviews.reviews")
def test_fetch_and_filter_reviews(mock_reviews, mock_reviews_data):
    """Test fetching and date filtering."""
    # Mock returns (result, continuation_token)
    mock_reviews.return_value = (mock_reviews_data, None)
    
    # Fetch reviews for the last 4 weeks (should include r1, r2, exclude r3)
    result = fetch_and_filter_reviews("test.app", 4)
    
    assert len(result) == 2
    assert result[0]["reviewId"] == "r1"
    assert result[1]["reviewId"] == "r2"
    
    # Check schema formatting
    assert result[0]["rating"] == 5
    assert result[0]["title"] == "Alice"
    assert result[0]["text"] == "Great app!"
    assert result[0]["source"] == "google_play"
    assert "date" in result[0]
    
    
@patch("src.tools.fetch_reviews.reviews")
def test_fetch_reviews_retry_logic(mock_reviews):
    """Test exponential backoff retry."""
    # Make it fail twice, then succeed
    mock_reviews.side_effect = [
        Exception("Network Error 1"),
        Exception("Network Error 2"),
        ([], None) # Success with empty list
    ]
    
    with patch("src.tools.fetch_reviews.time.sleep") as mock_sleep:
        fetch_and_filter_reviews("test.app", 1)
        assert mock_reviews.call_count == 3
        assert mock_sleep.call_count == 2
        # First delay is 2s, second is 4s (2 * 2^1)
        mock_sleep.assert_any_call(2)
        mock_sleep.assert_any_call(4)


@patch("src.tools.fetch_reviews.fetch_and_filter_reviews")
def test_fetch_reviews_tool(mock_fetch, tmp_path):
    """Test the LangChain tool interface and file writing."""
    mock_fetch.return_value = [
        {"reviewId": "r1", "rating": 5, "title": "A", "text": "Good", "date": "2026-09-14T00:00", "source": "google_play"}
    ]
    
    # Patch RAW_DIR to write to tmp_path
    with patch("src.tools.fetch_reviews.RAW_DIR", tmp_path):
        result = fetch_reviews.invoke({})
        
        assert "Fetched 1 reviews and saved" in result
        
        # Check file was written
        output_file = tmp_path / "google_play_reviews.json"
        assert output_file.exists()
        
        with open(output_file, "r") as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]["reviewId"] == "r1"


@patch("src.tools.fetch_reviews.fetch_and_filter_reviews")
def test_fetch_reviews_empty_fallback(mock_fetch):
    """Test fallback when 0 reviews are returned."""
    # First call returns empty, second call returns data
    mock_fetch.side_effect = [
        [], 
        [{"reviewId": "r1", "rating": 5, "title": "A", "text": "Good", "date": "2026-09-14T00:00", "source": "google_play"}]
    ]
    
    with patch("src.tools.fetch_reviews.RAW_DIR", Path("mock")):
        with patch("builtins.open", MagicMock()):
            result = fetch_reviews.invoke({})
            
            # It should have tried again with widened window
            assert mock_fetch.call_count == 2
            assert "Fetched 1 reviews" in result
