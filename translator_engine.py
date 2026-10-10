"""
CodeAlpha Artificial Intelligence Internship - Task 1: Language Translation Tool
Core Translation Engine
-------------------------------------------------------------------------------
Features:
- Unofficial Google Translate web endpoint integration
- Fallback to MyMemory Translation API
- Automatic Source Language Detection
- 100+ Supported Languages
- Long-text intelligent sentence chunking
- Robust error handling and metadata tracking
"""

import json
import logging
import urllib.parse
from typing import Dict, Any, Optional

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

import urllib.request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TranslatorEngine")

# Supported Languages mapping: Display Name -> ISO Code
SUPPORTED_LANGUAGES = {
    "Auto Detect": "auto",
    "Afrikaans": "af",
    "Albanian": "sq",
    "Amharic": "am",
    "Arabic": "ar",
    "Armenian": "hy",
    "Azerbaijani": "az",
    "Basque": "eu",
    "Belarusian": "be",
    "Bengali": "bn",
    "Bosnian": "bs",
    "Bulgarian": "bg",
    "Catalan": "ca",
    "Cebuano": "ceb",
    "Chinese (Simplified)": "zh-CN",
    "Chinese (Traditional)": "zh-TW",
    "Corsican": "co",
    "Croatian": "hr",
    "Czech": "cs",
    "Danish": "da",
    "Dutch": "nl",
    "English": "en",
    "Esperanto": "eo",
    "Estonian": "et",
    "Filipino (Tagalog)": "tl",
    "Finnish": "fi",
    "French": "fr",
    "Frisian": "fy",
    "Galician": "gl",
    "Georgian": "ka",
    "German": "de",
    "Greek": "el",
    "Gujarati": "gu",
    "Haitian Creole": "ht",
    "Hausa": "ha",
    "Hawaiian": "haw",
    "Hebrew": "he",
    "Hindi": "hi",
    "Hmong": "hmn",
    "Hungarian": "hu",
    "Icelandic": "is",
    "Igbo": "ig",
    "Indonesian": "id",
    "Irish": "ga",
    "Italian": "it",
    "Japanese": "ja",
    "Javanese": "jw",
    "Kannada": "kn",
    "Kazakh": "kk",
    "Khmer": "km",
    "Korean": "ko",
    "Kurdish": "ku",
    "Kyrgyz": "ky",
    "Lao": "lo",
    "Latin": "la",
    "Latvian": "lv",
    "Lithuanian": "lt",
    "Luxembourgish": "lb",
    "Macedonian": "mk",
    "Malagasy": "mg",
    "Malay": "ms",
    "Malayalam": "ml",
    "Maltese": "mt",
    "Maori": "mi",
    "Marathi": "mr",
    "Mongolian": "mn",
    "Myanmar (Burmese)": "my",
    "Nepali": "ne",
    "Norwegian": "no",
    "Nyanja (Chichewa)": "ny",
    "Pashto": "ps",
    "Persian": "fa",
    "Polish": "pl",
    "Portuguese": "pt",
    "Punjabi": "pa",
    "Romanian": "ro",
    "Russian": "ru",
    "Samoan": "sm",
    "Scots Gaelic": "gd",
    "Serbian": "sr",
    "Sesotho": "st",
    "Shona": "sn",
    "Sindhi": "sd",
    "Sinhala": "si",
    "Slovak": "sk",
    "Slovenian": "sl",
    "Somali": "so",
    "Spanish": "es",
    "Sundanese": "su",
    "Swahili": "sw",
    "Swedish": "sv",
    "Tagalog": "tl",
    "Tajik": "tg",
    "Tamil": "ta",
    "Tatar": "tt",
    "Telugu": "te",
    "Thai": "th",
    "Turkish": "tr",
    "Turkmen": "tk",
    "Ukrainian": "uk",
    "Urdu": "ur",
    "Uyghur": "ug",
    "Uzbek": "uz",
    "Vietnamese": "vi",
    "Welsh": "cy",
    "Xhosa": "xh",
    "Yiddish": "yi",
    "Yoruba": "yo",
    "Zulu": "zu"
}

# Reverse mapping: ISO Code -> Display Name
CODE_TO_LANGUAGE = {code: name for name, code in SUPPORTED_LANGUAGES.items() if code != "auto"}


class TranslationEngine:
    """
    Translation engine using the unofficial Google Translate web endpoint
    and fallback providers.
    """

    def __init__(self, timeout: float = 10.0):
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def _fetch_url(self, url: str) -> str:
        """Internal helper to fetch URL response using httpx or urllib."""
        if HAS_HTTPX:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                res = client.get(url, headers=self.headers)
                res.raise_for_status()
                return res.text
        else:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return response.read().decode("utf-8")

    def _translate_google_chunk(self, text: str, src_code: str, tgt_code: str) -> Dict[str, Any]:
        """Translate one chunk with Google's unofficial web endpoint."""
        encoded_query = urllib.parse.quote(text)
        clients = ["dict-chrome-ex", "gtx"]
        last_error = None

        for client_name in clients:
            try:
                url = (
                    f"https://translate.googleapis.com/translate_a/single"
                    f"?client={client_name}&sl={src_code}&tl={tgt_code}&dt=t&q={encoded_query}"
                )
                raw_response = self._fetch_url(url)
                data = json.loads(raw_response)

                if not isinstance(data, list) or not data or not isinstance(data[0], list):
                    raise ValueError("Malformed Google translation response")

                translated_segments = [
                    item[0]
                    for item in data[0]
                    if isinstance(item, list) and item and isinstance(item[0], str)
                ]
                translated_text = "".join(translated_segments)
                if not translated_text.strip():
                    raise ValueError("Google translation response was empty")

                detected_src = data[2] if len(data) > 2 and data[2] else src_code
                if not isinstance(detected_src, str):
                    detected_src = src_code

                return {
                    "translated_text": translated_text,
                    "detected_source": detected_src
                }
            except Exception as e:
                last_error = e
                continue

        raise RuntimeError("Google translation provider failed") from last_error

    def _translate_mymemory_fallback(self, text: str, src_code: str, tgt_code: str) -> Dict[str, Any]:
        """Fallback translation via MyMemory API."""
        actual_src = "en" if src_code == "auto" else src_code
        encoded_query = urllib.parse.quote(text)
        url = f"https://api.mymemory.translated.net/get?q={encoded_query}&langpair={actual_src}|{tgt_code}"
        
        raw_response = self._fetch_url(url)
        data = json.loads(raw_response)
        if not isinstance(data, dict):
            raise ValueError("Malformed MyMemory response")
        if data.get("responseStatus") not in (None, 200, "200"):
            raise ValueError("MyMemory returned an unsuccessful status")
        response_data = data.get("responseData")
        if not isinstance(response_data, dict):
            raise ValueError("Malformed MyMemory translation data")
        translated_text = response_data.get("translatedText")
        if not isinstance(translated_text, str) or not translated_text.strip():
            raise ValueError("MyMemory returned an empty translation")
        return {
            "translated_text": translated_text,
            "detected_source": actual_src
        }

    @staticmethod
    def _resolve_language_code(language: str, allow_auto: bool) -> str:
        if not isinstance(language, str) or not language.strip():
            raise ValueError("Unsupported language")

        value = language.strip()
        code = SUPPORTED_LANGUAGES.get(value)
        if code is None:
            code = next(
                (
                    supported_code
                    for supported_code in SUPPORTED_LANGUAGES.values()
                    if supported_code.lower() == value.lower()
                ),
                None,
            )
        if code is None or (code == "auto" and not allow_auto):
            raise ValueError("Unsupported language")
        return code

    def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "es"
    ) -> Dict[str, Any]:
        """
        Translates text from source language to target language.
        
        :param text: Text string to translate
        :param source_lang: Language code (e.g. 'auto', 'en', 'es') or display name ('English')
        :param target_lang: Language code (e.g. 'fr', 'hi', 'de') or display name ('French')
        :return: Dictionary containing translation results and metadata
        """
        if not isinstance(text, str) or not text.strip():
            return {
                "success": False,
                "error": "Input text cannot be empty.",
                "original_text": text,
                "translated_text": "",
                "source_language": source_lang,
                "target_language": target_lang,
                "detected_source": None
            }

        try:
            src_code = self._resolve_language_code(source_lang, allow_auto=True)
            tgt_code = self._resolve_language_code(target_lang, allow_auto=False)
        except ValueError:
            return {
                "success": False,
                "error": "Please choose a supported source and target language.",
                "original_text": text,
                "translated_text": "",
                "source_language": source_lang,
                "target_language": target_lang,
                "detected_source": None,
            }

        # If source and target are the same and not auto, return input directly
        if src_code != "auto" and src_code == tgt_code:
            return {
                "success": True,
                "error": None,
                "original_text": text,
                "translated_text": text,
                "source_language": src_code,
                "target_language": tgt_code,
                "detected_source": src_code,
                "source_name": CODE_TO_LANGUAGE.get(src_code, src_code),
                "target_name": CODE_TO_LANGUAGE.get(tgt_code, tgt_code),
                "word_count": len(text.split()),
                "char_count": len(text)
            }

        # Keep requests below provider limits while retaining separators.
        max_chunk_size = 4000
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + max_chunk_size, len(text))
            if end < len(text):
                boundary = max(text.rfind("\n", start, end), text.rfind(" ", start, end))
                if boundary > start:
                    end = boundary + 1
            chunks.append(text[start:end])
            start = end

        translated_chunks = []
        detected_lang = src_code

        for chunk in chunks:
            try:
                result = self._translate_google_chunk(chunk, src_code, tgt_code)
                translated_chunks.append(result["translated_text"])
                if result.get("detected_source"):
                    detected_lang = result["detected_source"]
            except Exception as google_err:
                logger.warning(
                    "Primary translation provider failed (%s); trying fallback.",
                    type(google_err).__name__,
                )
                try:
                    result = self._translate_mymemory_fallback(chunk, src_code, tgt_code)
                    translated_chunks.append(result["translated_text"])
                    detected_lang = result.get("detected_source", src_code)
                except Exception as fallback_err:
                    logger.error(
                        "Both translation providers failed (primary=%s, fallback=%s).",
                        type(google_err).__name__,
                        type(fallback_err).__name__,
                    )
                    return {
                        "success": False,
                        "error": "Translation is temporarily unavailable. Please try again later.",
                        "original_text": text,
                        "translated_text": "",
                        "source_language": src_code,
                        "target_language": tgt_code,
                        "detected_source": None
                    }

        final_translated_text = "".join(translated_chunks)
        detected_name = CODE_TO_LANGUAGE.get(detected_lang, detected_lang.upper())
        target_name = CODE_TO_LANGUAGE.get(tgt_code, tgt_code.upper())

        return {
            "success": True,
            "error": None,
            "original_text": text,
            "translated_text": final_translated_text,
            "source_language": src_code,
            "target_language": tgt_code,
            "detected_source": detected_lang,
            "detected_source_name": detected_name,
            "target_name": target_name,
            "word_count": len(text.split()),
            "char_count": len(text),
            "translated_word_count": len(final_translated_text.split()),
            "translated_char_count": len(final_translated_text)
        }


# Quick CLI test functionality
if __name__ == "__main__":
    engine = TranslationEngine()
    sample = "Hello! Welcome to the CodeAlpha Artificial Intelligence Internship program."
    print(f"Translating: '{sample}'")
    res = engine.translate(sample, source_lang="auto", target_lang="es")
    print("Result:", json.dumps(res, indent=2))
