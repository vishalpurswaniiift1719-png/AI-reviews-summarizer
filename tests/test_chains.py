"""
Tests for LLM theme clustering and action generation.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.chains import theme_chain
from src.tools.cluster_themes import cluster_themes

@pytest.fixture
def sample_reviews():
    return [
        {"id": "1", "text": "The app crashes on checkout. Please fix."},
        {"id": "2", "text": "Checkout keeps crashing when I pay."},
        {"id": "3", "text": "Delivery was 3 days late!"},
        {"id": "4", "text": "Where is my delivery? So slow."},
    ]


def test_verify_verbatim_quote_exact(sample_reviews):
    """Test when the quote is exactly in the text."""
    quote = "Delivery was 3 days late!"
    result = theme_chain.verify_verbatim_quote(quote, sample_reviews)
    assert result == quote


def test_verify_verbatim_quote_fuzzy(sample_reviews):
    """Test fuzzy fallback when quote is slightly off."""
    # LLM might return slightly altered text (e.g., 'crashed' instead of 'crashes')
    quote = "The app crashed on checkout." 
    result = theme_chain.verify_verbatim_quote(quote, sample_reviews)
    # Should fall back to the closest match because partial ratio is high
    assert result == "The app crashes on checkout. Please fix."


@patch("src.chains.theme_chain.get_llm")
def test_run_theme_clustering(mock_get_llm, sample_reviews):
    """Test clustering logic with a mocked LLM."""
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm
    
    # Mock the chain invocation result directly
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {
        "themes": [
            {
                "theme_name": "Checkout Crashes",
                "description": "App crashes during payment",
                "review_ids": ["1", "2"],
                "representative_quote": "Checkout keeps crashing when I pay."
            },
            {
                "theme_name": "Late Delivery",
                "description": "Deliveries are arriving late",
                "review_ids": ["3", "4"],
                "representative_quote": "Delivery was 3 days late!"
            }
        ]
    }
    
    with patch("src.chains.theme_chain.CLUSTERING_PROMPT") as mock_prompt:
        # Override the | operator to return our mock chain
        mock_prompt.__or__.return_value.__or__.return_value = mock_chain
        
        themes = theme_chain.run_theme_clustering(sample_reviews)
        
        assert len(themes) == 2
        assert themes[0]["review_count"] == 2
        assert themes[0]["theme_name"] == "Checkout Crashes"
        # Quote should remain exact
        assert themes[0]["representative_quote"] == "Checkout keeps crashing when I pay."


@patch("src.chains.theme_chain.get_llm")
def test_run_action_generation(mock_get_llm):
    """Test action generation with a mocked LLM."""
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm
    
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {
        "actions": [
            {"title": "Fix Checkout", "description": "Investigate crash logs during payment."},
            {"title": "Improve Tracking", "description": "Add real-time tracking for late deliveries."},
            {"title": "Better Comms", "description": "Notify users of delays proactively."}
        ]
    }
    
    with patch("src.chains.theme_chain.ACTION_PROMPT") as mock_prompt:
        mock_prompt.__or__.return_value.__or__.return_value = mock_chain
        
        top_themes = [{
            "theme_name": "Test", 
            "description": "Test Desc", 
            "representative_quote": "Test Quote"
        }]
        actions = theme_chain.run_action_generation(top_themes)
        
        assert len(actions) == 3
        assert actions[0]["title"] == "Fix Checkout"


@patch("src.tools.cluster_themes.run_theme_clustering")
@patch("src.tools.cluster_themes.run_action_generation")
def test_cluster_themes_tool(mock_actions, mock_clustering, tmp_path):
    """Test the LangChain tool interface and file writing."""
    mock_clustering.return_value = [
        {"theme_name": "T1", "review_count": 5},
        {"theme_name": "T2", "review_count": 3},
        {"theme_name": "T3", "review_count": 2},
        {"theme_name": "T4", "review_count": 1}, # Should be dropped (only top 3)
    ]
    
    mock_actions.return_value = [
        {"title": "A1", "description": "D1"},
        {"title": "A2", "description": "D2"},
        {"title": "A3", "description": "D3"}
    ]
    
    # Write a dummy cleaned_reviews.json
    cleaned_path = tmp_path / "cleaned_reviews.json"
    import json
    with open(cleaned_path, "w") as f:
        json.dump([{"id": "1", "text": "A"}, {"id": "2", "text": "B"}], f)
        
    with patch("src.tools.cluster_themes.PROCESSED_DIR", tmp_path):
        result = cluster_themes.invoke({})
        
        assert "Successfully generated 3 themes and 3 actions" in result
        
        # Check output file
        out_path = tmp_path / "themes_and_actions.json"
        assert out_path.exists()
        
        with open(out_path, "r") as f:
            data = json.load(f)
            assert len(data["themes"]) == 3
            assert data["themes"][0]["theme_name"] == "T1"
            assert len(data["actions"]) == 3
