"""
Unit Tests for Task 1: Language Translation Tool
-------------------------------------------------------------------------------
Runs automated verification against the Translation Engine.
"""

import pytest
from translator_engine import TranslationEngine, SUPPORTED_LANGUAGES, CODE_TO_LANGUAGE


@pytest.fixture
def engine():
    return TranslationEngine(timeout=10.0)


def test_language_mappings():
    """Ensure essential language mappings are present."""
    assert "English" in SUPPORTED_LANGUAGES
    assert "Spanish" in SUPPORTED_LANGUAGES
    assert "French" in SUPPORTED_LANGUAGES
    assert "German" in SUPPORTED_LANGUAGES
    assert "Hindi" in SUPPORTED_LANGUAGES
    assert SUPPORTED_LANGUAGES["Auto Detect"] == "auto"
    assert CODE_TO_LANGUAGE["en"] == "English"
    assert CODE_TO_LANGUAGE["es"] == "Spanish"


def test_basic_translation_en_to_es(engine):
    """Test standard translation from English to Spanish."""
    result = engine.translate("Good morning", source_lang="en", target_lang="es")
    assert result["success"] is True
    assert result["error"] is None
    # Matches 'Buen día' or 'Buenos días'
    assert "buen" in result["translated_text"].lower()
    assert result["target_language"] == "es"


def test_auto_detect_french(engine):
    """Test auto-detection of French source language."""
    sample = "Bonjour tout le monde"
    result = engine.translate(sample, source_lang="auto", target_lang="en")
    assert result["success"] is True
    assert result["detected_source"] in ["fr", "auto"]
    assert "hello" in result["translated_text"].lower() or "good" in result["translated_text"].lower()


def test_empty_string_handling(engine):
    """Test edge cases with empty or whitespace input."""
    result = engine.translate("   ", source_lang="en", target_lang="es")
    assert result["success"] is False
    assert "empty" in result["error"].lower()


def test_same_source_and_target(engine):
    """Test behavior when source and target languages are identical."""
    text = "Artificial Intelligence"
    result = engine.translate(text, source_lang="en", target_lang="en")
    assert result["success"] is True
    assert result["translated_text"] == text


def test_translation_metrics(engine):
    """Test word and character counts are correctly calculated."""
    text = "CodeAlpha internship in Artificial Intelligence"
    result = engine.translate(text, source_lang="en", target_lang="de")
    assert result["success"] is True
    assert result["word_count"] == 5
    assert result["char_count"] == len(text)
    assert result["translated_word_count"] > 0
    assert result["translated_char_count"] > 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
