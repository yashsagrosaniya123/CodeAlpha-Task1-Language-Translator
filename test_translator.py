"""Deterministic unit tests for translation and speech provider adapters."""

import asyncio
import io
import json

import httpx
import pytest

from speech_service import (
    generate_edge_voice_audio,
    generate_gtts_audio,
    list_edge_voices,
)
from translator_engine import CODE_TO_LANGUAGE, SUPPORTED_LANGUAGES, TranslationEngine
from ui_helpers import escape_html, format_history_item, swap_language_values


@pytest.fixture
def engine() -> TranslationEngine:
    return TranslationEngine(timeout=1.0)


def google_response(translation: str, detected: str = "en") -> str:
    return json.dumps([[[translation, "source text", None, None]], None, detected])


def mymemory_response(translation: str) -> str:
    return json.dumps({
        "responseStatus": 200,
        "responseData": {"translatedText": translation},
    })


def test_language_mappings() -> None:
    assert SUPPORTED_LANGUAGES["Auto Detect"] == "auto"
    assert CODE_TO_LANGUAGE["en"] == "English"
    assert CODE_TO_LANGUAGE["es"] == "Spanish"


def test_dynamic_history_content_is_html_escaped() -> None:
    payload = "<script>alert('xss')</script>"
    markup = format_history_item(payload, '" onmouseover="alert(1)', payload)
    assert "<script>" not in markup
    assert "&lt;script&gt;" in markup
    assert "&quot; onmouseover=&quot;alert(1)" in markup
    assert escape_html(payload) == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"


def test_language_swap_updates_widget_values_and_translated_input() -> None:
    state = {
        "sel_src": "English",
        "sel_tgt": "Spanish",
        "input_text": "Hello",
        "txt_input": "Hello",
        "result": {"translated_text": "Hola"},
    }

    assert swap_language_values(state) is True
    assert state["sel_src"] == "Spanish"
    assert state["sel_tgt"] == "English"
    assert state["input_text"] == "Hola"
    assert state["txt_input"] == "Hola"
    assert state["result"] is None


def test_language_swap_requires_explicit_source_language() -> None:
    state = {"sel_src": "Auto Detect", "sel_tgt": "Spanish"}
    assert swap_language_values(state) is False
    assert state == {"sel_src": "Auto Detect", "sel_tgt": "Spanish"}


def test_google_success_without_network(
    engine: TranslationEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(engine, "_fetch_url", lambda _url: google_response("Buenos días"))

    result = engine.translate("Good morning", "en", "es")

    assert result["success"] is True
    assert result["translated_text"] == "Buenos días"
    assert result["target_language"] == "es"


def test_empty_input_does_not_call_provider(
    engine: TranslationEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_request(_url: str) -> str:
        pytest.fail("Provider must not be called for empty input")

    monkeypatch.setattr(engine, "_fetch_url", unexpected_request)
    result = engine.translate("   ", "en", "es")
    assert result["success"] is False
    assert "empty" in result["error"].lower()


def test_same_language_returns_input_without_provider(
    engine: TranslationEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        engine,
        "_fetch_url",
        lambda _url: pytest.fail("Provider must not be called for same-language translation"),
    )
    result = engine.translate("Artificial Intelligence", "en", "en")
    assert result["success"] is True
    assert result["translated_text"] == "Artificial Intelligence"


@pytest.mark.parametrize(
    ("source", "target"),
    [("not-a-language", "es"), ("en", "invalid"), ("auto", "auto")],
)
def test_unsupported_language_codes_do_not_call_provider(
    engine: TranslationEngine,
    monkeypatch: pytest.MonkeyPatch,
    source: str,
    target: str,
) -> None:
    monkeypatch.setattr(
        engine,
        "_fetch_url",
        lambda _url: pytest.fail("Provider must not be called for unsupported languages"),
    )
    result = engine.translate("Hello", source, target)
    assert result["success"] is False
    assert "supported" in result["error"].lower()


def test_primary_http_failure_uses_mymemory_fallback(
    engine: TranslationEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fetch(url: str) -> str:
        if "translate.googleapis.com" in url:
            raise OSError("private text must not be exposed")
        return mymemory_response("Hola")

    monkeypatch.setattr(engine, "_fetch_url", fetch)
    result = engine.translate("Hello", "en", "es")
    assert result["success"] is True
    assert result["translated_text"] == "Hola"


def test_http_status_error_uses_mymemory_fallback(
    engine: TranslationEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fetch(url: str) -> str:
        if "translate.googleapis.com" in url:
            request = httpx.Request("GET", "https://translate.googleapis.com/translate_a/single")
            response = httpx.Response(503, request=request)
            raise httpx.HTTPStatusError("service unavailable", request=request, response=response)
        return mymemory_response("Hola")

    monkeypatch.setattr(engine, "_fetch_url", fetch)
    result = engine.translate("Hello", "en", "es")
    assert result["success"] is True
    assert result["translated_text"] == "Hola"


def test_both_provider_failures_return_safe_message(
    engine: TranslationEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fetch(_url: str) -> str:
        raise OSError("secret request details")

    monkeypatch.setattr(engine, "_fetch_url", fetch)
    result = engine.translate("Hello", "en", "es")
    assert result["success"] is False
    assert "temporarily unavailable" in result["error"]
    assert "secret request details" not in result["error"]


def test_malformed_google_response_uses_fallback(
    engine: TranslationEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fetch(url: str) -> str:
        if "translate.googleapis.com" in url:
            return '{"unexpected":"shape"}'
        return mymemory_response("Hola")

    monkeypatch.setattr(engine, "_fetch_url", fetch)
    result = engine.translate("Hello", "en", "es")
    assert result["success"] is True
    assert result["translated_text"] == "Hola"


@pytest.mark.parametrize("response", ["not json", '{"responseStatus":429}'])
def test_malformed_or_rejected_mymemory_response_fails_safely(
    engine: TranslationEngine,
    monkeypatch: pytest.MonkeyPatch,
    response: str,
) -> None:
    def fetch(url: str) -> str:
        if "translate.googleapis.com" in url:
            raise OSError("primary unavailable")
        return response

    monkeypatch.setattr(engine, "_fetch_url", fetch)
    result = engine.translate("Hello", "en", "es")
    assert result["success"] is False
    assert "temporarily unavailable" in result["error"]


def test_empty_google_translation_falls_back(
    engine: TranslationEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fetch(url: str) -> str:
        if "translate.googleapis.com" in url:
            return google_response("")
        return mymemory_response("Hola")

    monkeypatch.setattr(engine, "_fetch_url", fetch)
    result = engine.translate("Hello", "en", "es")
    assert result["success"] is True
    assert result["translated_text"] == "Hola"


def test_long_input_is_split_without_losing_text(
    engine: TranslationEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    text = ("hello " * 900).strip()
    chunks: list[str] = []

    def translate_chunk(chunk: str, _source: str, _target: str) -> dict[str, str]:
        chunks.append(chunk)
        return {"translated_text": chunk, "detected_source": "en"}

    monkeypatch.setattr(engine, "_translate_google_chunk", translate_chunk)
    result = engine.translate(text, "en", "es")

    assert result["success"] is True
    assert "".join(chunks) == text
    assert max(map(len, chunks)) <= 4000
    assert result["translated_text"] == text


def test_translation_metrics_with_mocked_provider(
    engine: TranslationEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(engine, "_fetch_url", lambda _url: google_response("Hola mundo"))
    result = engine.translate("Hello world", "en", "es")
    assert result["word_count"] == 2
    assert result["char_count"] == len("Hello world")
    assert result["translated_word_count"] == 2


def test_gtts_audio_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeGTTS:
        def __init__(self, text: str, lang: str, slow: bool) -> None:
            assert text == "hello"
            assert lang == "en"
            assert slow is False

        def write_to_fp(self, output: io.BytesIO) -> None:
            output.write(b"mp3")

    monkeypatch.setattr("speech_service.gTTS", FakeGTTS)
    result = generate_gtts_audio("hello", "en-US")
    assert result.read() == b"mp3"


def test_gtts_failure_uses_user_safe_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenGTTS:
        def __init__(self, **_kwargs: str) -> None:
            raise OSError("private request details")

    monkeypatch.setattr("speech_service.gTTS", BrokenGTTS)
    with pytest.raises(RuntimeError, match="temporarily unavailable") as error:
        generate_gtts_audio("hello", "en")
    assert "private request details" not in str(error.value)


def test_gtts_empty_audio_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    class EmptyGTTS:
        def __init__(self, **_kwargs: str) -> None:
            pass

        def write_to_fp(self, _output: io.BytesIO) -> None:
            return None

    monkeypatch.setattr("speech_service.gTTS", EmptyGTTS)
    with pytest.raises(RuntimeError, match="temporarily unavailable"):
        generate_gtts_audio("hello", "en")


def test_edge_voice_listing_success(monkeypatch: pytest.MonkeyPatch) -> None:
    async def voices() -> list[dict[str, str]]:
        return [{"ShortName": "en-US-Test", "Locale": "en-US"}]

    monkeypatch.setattr("speech_service.edge_tts.list_voices", voices)
    result = asyncio.run(list_edge_voices())
    assert result[0]["ShortName"] == "en-US-Test"


def test_edge_voice_listing_failure_is_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fail() -> list[dict[str, str]]:
        raise OSError("private request details")

    monkeypatch.setattr("speech_service.edge_tts.list_voices", fail)
    with pytest.raises(RuntimeError, match="temporarily unavailable") as error:
        asyncio.run(list_edge_voices())
    assert "private request details" not in str(error.value)


def test_edge_voice_listing_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    async def slow_voices() -> list[dict[str, str]]:
        await asyncio.sleep(0.1)
        return []

    monkeypatch.setattr("speech_service.edge_tts.list_voices", slow_voices)
    with pytest.raises(RuntimeError, match="temporarily unavailable"):
        asyncio.run(list_edge_voices(timeout=0.001))


def test_edge_voice_audio_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeCommunicate:
        def __init__(self, text: str, voice: str) -> None:
            assert text == "hello"
            assert voice == "en-US-Test"

        async def stream(self):
            yield {"type": "audio", "data": b"mp3"}
            yield {"type": "WordBoundary", "data": b""}

    monkeypatch.setattr("speech_service.edge_tts.Communicate", FakeCommunicate)
    result = asyncio.run(generate_edge_voice_audio("hello", "en-US-Test"))
    assert result == b"mp3"


def test_edge_voice_empty_audio_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    class EmptyCommunicate:
        def __init__(self, **_kwargs: str) -> None:
            pass

        async def stream(self):
            yield {"type": "WordBoundary", "data": b""}

    monkeypatch.setattr("speech_service.edge_tts.Communicate", EmptyCommunicate)
    with pytest.raises(RuntimeError, match="temporarily unavailable"):
        asyncio.run(generate_edge_voice_audio("hello", "en-US-Test"))


def test_edge_voice_audio_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    class SlowCommunicate:
        def __init__(self, **_kwargs: str) -> None:
            pass

        async def stream(self):
            await asyncio.sleep(0.1)
            yield {"type": "audio", "data": b"mp3"}

    monkeypatch.setattr("speech_service.edge_tts.Communicate", SlowCommunicate)
    with pytest.raises(RuntimeError, match="temporarily unavailable"):
        asyncio.run(generate_edge_voice_audio("hello", "en-US-Test", timeout=0.001))
