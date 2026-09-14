"""
Tests for the configuration module.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestConfigValidation:
    """Test configuration loading and validation."""

    def test_google_play_app_id_default(self):
        """Default app ID is set to Noon buyer app."""
        from src import config
        assert config.GOOGLE_PLAY_APP_ID == "com.noon.buyerapp"

    def test_review_weeks_in_range(self):
        """REVIEW_WEEKS is within valid range [1, 52]."""
        from src import config
        assert 1 <= config.REVIEW_WEEKS <= 52

    def test_data_directories_exist(self):
        """All data directories are created on config load."""
        from src import config
        assert config.RAW_DIR.exists()
        assert config.PROCESSED_DIR.exists()
        assert config.PULSES_DIR.exists()

    def test_data_directories_are_directories(self):
        """Data paths are directories, not files."""
        from src import config
        assert config.RAW_DIR.is_dir()
        assert config.PROCESSED_DIR.is_dir()
        assert config.PULSES_DIR.is_dir()

    def test_project_root_is_correct(self):
        """PROJECT_ROOT points to the workspace root."""
        from src import config
        assert (config.PROJECT_ROOT / "requirements.txt").exists()

    def test_config_summary_runs_without_error(self, capsys):
        """print_config_summary() executes without raising."""
        from src.config import print_config_summary
        print_config_summary()
        captured = capsys.readouterr()
        assert "AI Reviews Summarizer" in captured.out
        assert "GEMINI_API_KEY" in captured.out

    def test_api_key_is_masked_in_summary(self, capsys):
        """API key is not printed in full in the summary."""
        from src.config import print_config_summary, GEMINI_API_KEY
        print_config_summary()
        captured = capsys.readouterr()
        # Full key should NOT appear; masked version should
        assert GEMINI_API_KEY not in captured.out
        assert "***" in captured.out
