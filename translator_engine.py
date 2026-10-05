"""
CodeAlpha Artificial Intelligence Internship - Task 1: Language Translation Tool
Core Translation Engine
-------------------------------------------------------------------------------
Features:
- Google Translate API integration (Free & Reliable GTX Endpoint)
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
    Robust translation engine interfacing with Google Translate API
    and fallback providers.
    """

    def __init__(self, timeout: float = 10.0):
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
        """Translates a single chunk of text via Google Translate API."""
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
                
                translated_segments = []
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                    for item in data[0]:
                        if isinstance(item, list) and len(item) > 0 and item[0]:
                            translated_segments.append(item[0])
                
                translated_text = "".join(translated_segments) if translated_segments else ""
                detected_src = data[2] if len(data) > 2 and data[2] else src_code
                
                return {
                    "translated_text": translated_text,
                    "detected_source": detected_src
                }
            except Exception as e:
                last_error = e
                continue

        raise last_error

    def _translate_mymemory_fallback(self, text: str, src_code: str, tgt_code: str) -> Dict[str, Any]:
        """Fallback translation via MyMemory API."""
        actual_src = "en" if src_code == "auto" else src_code
        encoded_query = urllib.parse.quote(text)
        url = f"https://api.mymemory.translated.net/get?q={encoded_query}&langpair={actual_src}|{tgt_code}"
        
        raw_response = self._fetch_url(url)
        data = json.loads(raw_response)
        
        translated_text = data.get("responseData", {}).get("translatedText", "")
        return {
            "translated_text": translated_text,
            "detected_source": actual_src
        }

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
        if not text or not text.strip():
            return {
                "success": False,
                "error": "Input text cannot be empty.",
                "original_text": text,
                "translated_text": "",
                "source_language": source_lang,
                "target_language": target_lang,
                "detected_source": None
            }

        # Resolve language names to codes if full names were passed
        src_code = SUPPORTED_LANGUAGES.get(source_lang, source_lang).lower()
        tgt_code = SUPPORTED_LANGUAGES.get(target_lang, target_lang).lower()

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

        # Handle long text by chunking if > 4000 characters
        max_chunk_size = 4000
        paragraphs = text.split("\n")
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) + 1 < max_chunk_size:
                current_chunk += (para + "\n")
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n"
        if current_chunk:
            chunks.append(current_chunk.strip())

        translated_chunks = []
        detected_lang = src_code

        for chunk in chunks:
            if not chunk.strip():
                translated_chunks.append("")
                continue
            try:
                # Primary translation: Google Translate API
                result = self._translate_google_chunk(chunk, src_code, tgt_code)
                translated_chunks.append(result["translated_text"])
                if result.get("detected_source"):
                    detected_lang = result["detected_source"]
            except Exception as google_err:
                logger.warning("Google API error: %s. Falling back to MyMemory...", google_err)
                try:
                    result = self._translate_mymemory_fallback(chunk, src_code, tgt_code)
                    translated_chunks.append(result["translated_text"])
                    detected_lang = result.get("detected_source", src_code)
                except Exception as fallback_err:
                    logger.error("Both primary and fallback failed: %s", fallback_err)
                    return {
                        "success": False,
                        "error": f"Translation failed: {str(fallback_err)}",
                        "original_text": text,
                        "translated_text": "",
                        "source_language": src_code,
                        "target_language": tgt_code,
                        "detected_source": None
                    }

        final_translated_text = "\n".join(translated_chunks)
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
