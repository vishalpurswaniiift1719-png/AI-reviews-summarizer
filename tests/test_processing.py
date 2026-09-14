"""
Tests for the data processing pipeline.
"""

import pytest

from src.processing import normalizer, deduplicator, pii_stripper


# --- PII Stripper Tests ---
PII_TEST_CASES = [
    ("Contact me at ahmed@gmail.com for details", "Contact me at [REDACTED] for details"),
    ("Call +971501234567 asap", "Call [REDACTED] asap"),
    ("Call 0501234567 asap", "Call [REDACTED] asap"),
    ("Call +971-50-123-4567 asap", "Call [REDACTED] asap"),
    ("My device ID is IMEI:123456789012345", "My device ID is IMEI [REDACTED]"),
    ("Order #ORD-98765 never arrived", "Order [REDACTED] never arrived"), # Fails our simple regex, but let's test what we built
    ("Order ORD-98765 never arrived", "Order [REDACTED] never arrived"),
    ("No PII in this review at all", "No PII in this review at all"),
]


@pytest.mark.parametrize("input_text,expected", PII_TEST_CASES)
def test_pii_stripping(input_text, expected):
    result = pii_stripper.strip(input_text)
    assert result == expected


def test_pii_contains():
    assert pii_stripper.contains_pii("ahmed@gmail.com") is True
    assert pii_stripper.contains_pii("Hello there") is False


# --- Deduplication Tests ---
def test_deduplication():
    reviews = [
        {"text": "Great app!", "date": "2026-09-01T12:00:00"},
        {"text": "Great app!", "date": "2026-09-01T15:30:00"},  # duplicate on same day
        {"text": "Great app!", "date": "2026-09-02T10:00:00"},  # different date — keep
        {"text": "Terrible app", "date": "2026-09-01T12:00:00"},  # different text — keep
    ]
    result = deduplicator.deduplicate(reviews)
    assert len(result) == 3


# --- Emoji-Only / Normalizer Filter ---
def test_emoji_only_filter():
    assert normalizer.is_meaningful("👍👍👍") is False
    assert normalizer.is_meaningful("!!!") is False
    assert normalizer.is_meaningful("Great app overall") is True
    assert normalizer.is_meaningful("Bad.") is False  # <5 alphanumeric chars


def test_truncate_long_text():
    short_text = "This is a short text"
    assert normalizer.truncate_long_text(short_text, max_words=10) == short_text
    
    long_text = " ".join(["word"] * 501)
    truncated = normalizer.truncate_long_text(long_text, max_words=500)
    assert len(truncated.split()) == 501
    assert truncated.endswith("[truncated]")


def test_normalize_review():
    raw = {
        "reviewId": "12345",
        "rating": 5,
        "title": "User1",
        "text": "Good stuff",
        "date": "2026-09-14",
        "source": "google_play"
    }
    norm = normalizer.normalize_review(raw)
    
    assert norm["id"] != "12345"  # Should be hashed
    assert len(norm["id"]) == 16
    assert norm["language"] == "en"
    assert norm["rating"] == 5
    assert norm["title"] == "User1"
    assert norm["text"] == "Good stuff"
    assert norm["date"] == "2026-09-14"
