"""Online spelling and grammar correction through LanguageTool."""

import logging

import httpx

logger = logging.getLogger(__name__)

LANGUAGETOOL_CHECK_URL = "https://api.languagetool.org/v2/check"
MAX_CORRECTION_LENGTH = 20_000


class TextCorrectionError(RuntimeError):
    """Raised when the online correction service cannot process the text."""


def correct_text(text: str, language: str = "auto", timeout: float = 15.0) -> str:
    """Apply LanguageTool's first suggested replacement for each text match."""
    if not text.strip():
        raise ValueError("Enter some text before requesting corrections.")
    if len(text) > MAX_CORRECTION_LENGTH:
        raise TextCorrectionError(
            f"Text correction supports up to {MAX_CORRECTION_LENGTH:,} characters at a time."
        )

    try:
        response = httpx.post(
            LANGUAGETOOL_CHECK_URL,
            data={"text": text, "language": language},
            headers={"User-Agent": "LanguageAITranslator/1.0"},
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.TimeoutException as exc:
        logger.warning("LanguageTool text correction timed out.")
        raise TextCorrectionError(
            "The correction service timed out. Please try again."
        ) from exc
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "LanguageTool text correction returned HTTP %s.",
            exc.response.status_code,
        )
        raise TextCorrectionError(
            "The correction service rejected the request. Check the selected language and try again."
        ) from exc
    except httpx.RequestError as exc:
        logger.warning("LanguageTool text correction request failed (%s).", type(exc).__name__)
        raise TextCorrectionError(
            "The correction service is temporarily unavailable. Please try again."
        ) from exc
    except ValueError as exc:
        logger.warning("LanguageTool returned invalid JSON for text correction.")
        raise TextCorrectionError(
            "The correction service returned an unreadable response. Please try again."
        ) from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("matches"), list):
        raise TextCorrectionError(
            "The correction service returned an unexpected response. Please try again."
        )

    utf16_to_python_index = {0: 0}
    utf16_offset = 0
    for python_index, character in enumerate(text, start=1):
        utf16_offset += len(character.encode("utf-16-le")) // 2
        utf16_to_python_index[utf16_offset] = python_index

    edits: list[tuple[int, int, str]] = []
    for match in payload["matches"]:
        if not isinstance(match, dict):
            raise TextCorrectionError(
                "The correction service returned an unexpected response. Please try again."
            )

        offset = match.get("offset")
        length = match.get("length")
        replacements = match.get("replacements", [])
        if (
            type(offset) is not int
            or type(length) is not int
            or offset < 0
            or length < 0
            or offset + length not in utf16_to_python_index
            or offset not in utf16_to_python_index
            or not isinstance(replacements, list)
        ):
            raise TextCorrectionError(
                "The correction service returned an unexpected response. Please try again."
            )

        if not replacements:
            continue
        if not isinstance(replacements[0], dict) or not isinstance(
            replacements[0].get("value"), str
        ):
            raise TextCorrectionError(
                "The correction service returned an unexpected response. Please try again."
            )

        replacement = replacements[0]["value"]
        python_start = utf16_to_python_index[offset]
        python_end = utf16_to_python_index[offset + length]
        if replacement != text[python_start:python_end]:
            edits.append((python_start, python_end, replacement))

    corrected = text
    last_start = len(text)
    for start, end, replacement in sorted(edits, key=lambda edit: edit[0], reverse=True):
        if end > last_start:
            continue
        corrected = corrected[:start] + replacement + corrected[end:]
        last_start = start
    return corrected
