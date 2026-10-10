"""Speech provider adapters with bounded requests and user-safe errors."""

import asyncio
import io
import logging

import edge_tts
from gtts import gTTS

logger = logging.getLogger(__name__)


def generate_gtts_audio(text: str, lang_code: str) -> io.BytesIO:
    code = lang_code if lang_code and lang_code != "auto" else "en"
    code = code.split("-")[0]
    try:
        audio = io.BytesIO()
        gTTS(text=text[:500], lang=code, slow=False).write_to_fp(audio)
        if not audio.tell():
            raise ValueError("The speech provider returned no audio.")
        audio.seek(0)
        return audio
    except Exception as exc:
        logger.warning("gTTS request failed (%s).", type(exc).__name__)
        raise RuntimeError("Text-to-speech is temporarily unavailable. Please try again.") from exc


async def list_edge_voices(timeout: float = 20.0) -> list[dict[str, str]]:
    try:
        voices = await asyncio.wait_for(edge_tts.list_voices(), timeout=timeout)
        if not isinstance(voices, list):
            raise ValueError("The speech provider returned an invalid voice list.")
        return voices
    except Exception as exc:
        logger.warning("Could not load Edge TTS voices (%s).", type(exc).__name__)
        raise RuntimeError("Voice options are temporarily unavailable.") from exc


async def generate_edge_voice_audio(
    text: str,
    voice: str,
    timeout: float = 30.0,
) -> bytes:
    async def collect_audio() -> bytes:
        communicator = edge_tts.Communicate(text=text[:500], voice=voice)
        audio = bytearray()
        async for chunk in communicator.stream():
            if chunk.get("type") == "audio":
                audio.extend(chunk.get("data", b""))
        if not audio:
            raise ValueError("The speech provider returned no audio.")
        return bytes(audio)

    try:
        return await asyncio.wait_for(collect_audio(), timeout=timeout)
    except Exception as exc:
        logger.warning("Edge TTS request failed (%s).", type(exc).__name__)
        raise RuntimeError("Speech generation is temporarily unavailable. Please try again.") from exc
