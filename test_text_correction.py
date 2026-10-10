"""Tests for the online text-correction adapter."""

import httpx
import pytest

from text_correction import (
    LANGUAGETOOL_CHECK_URL,
    MAX_CORRECTION_LENGTH,
    TextCorrectionError,
    correct_text,
)


def test_correct_text_applies_replacements_from_right_to_left(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_data: dict[str, object] = {}

    def post(url: str, **kwargs: object) -> httpx.Response:
        assert url == LANGUAGETOOL_CHECK_URL
        request_data.update(kwargs)
        request = httpx.Request("POST", url)
        return httpx.Response(
            200,
            json={
                "matches": [
                    {"offset": 4, "length": 3, "replacements": [{"value": "good"}]},
                    {"offset": 0, "length": 3, "replacements": [{"value": "great"}]},
                ]
            },
            request=request,
        )

    monkeypatch.setattr("text_correction.httpx.post", post)

    assert correct_text("bad bad", language="en") == "great good"
    assert request_data["data"] == {"text": "bad bad", "language": "en"}


def test_correct_text_leaves_text_unchanged_without_suggestions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def post(url: str, **_kwargs: object) -> httpx.Response:
        return httpx.Response(200, json={"matches": []}, request=httpx.Request("POST", url))

    monkeypatch.setattr("text_correction.httpx.post", post)

    assert correct_text("Correct text") == "Correct text"


def test_correct_text_handles_non_bmp_characters_before_matches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def post(url: str, **_kwargs: object) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "matches": [
                    {"offset": 3, "length": 3, "replacements": [{"value": "good"}]}
                ]
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr("text_correction.httpx.post", post)

    assert correct_text("🙂 bad", language="en") == "🙂 good"


def test_correct_text_rejects_empty_and_oversized_text() -> None:
    with pytest.raises(ValueError, match="Enter some text"):
        correct_text("  ")

    with pytest.raises(TextCorrectionError, match="up to"):
        correct_text("a" * (MAX_CORRECTION_LENGTH + 1))


def test_correct_text_reports_http_service_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def post(url: str, **_kwargs: object) -> httpx.Response:
        request = httpx.Request("POST", url)
        return httpx.Response(503, request=request)

    monkeypatch.setattr("text_correction.httpx.post", post)

    with pytest.raises(TextCorrectionError, match="rejected the request"):
        correct_text("hello")


def test_correct_text_rejects_invalid_match_offsets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def post(url: str, **_kwargs: object) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "matches": [
                    {"offset": 100, "length": 2, "replacements": [{"value": "ok"}]}
                ]
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr("text_correction.httpx.post", post)

    with pytest.raises(TextCorrectionError, match="unexpected response"):
        correct_text("short")
