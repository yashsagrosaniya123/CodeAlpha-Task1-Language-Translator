import asyncio
import io
import time
from typing import Optional
import edge_tts
import streamlit as st
from gtts import gTTS
from translator_engine import TranslationEngine, SUPPORTED_LANGUAGES, CODE_TO_LANGUAGE

# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Language AI Translator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Premium CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Base reset ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Background gradient ── */
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #1a1a4e 40%, #24243e 100%);
    min-height: 100vh;
}

/* ── Hide Streamlit default elements ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Hero Header ── */
.hero-header {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
}
.hero-visual {
    position: relative;
    width: 156px;
    height: 156px;
    margin: 0 auto 1rem;
    display: grid;
    place-items: center;
    perspective: 700px;
}
.globe-sphere {
    position: relative;
    width: 106px;
    height: 106px;
    overflow: hidden;
    border: 1px solid rgba(191, 219, 254, 0.65);
    border-radius: 50%;
    background:
        radial-gradient(ellipse at 32% 24%, rgba(255,255,255,0.9), transparent 8%),
        radial-gradient(ellipse at 35% 28%, #a5f3fc 0%, #38bdf8 18%, #6366f1 53%, #312e81 78%);
    box-shadow:
        inset -15px -10px 24px rgba(15, 12, 41, 0.65),
        inset 7px 5px 14px rgba(255,255,255,0.25),
        0 0 34px rgba(96, 165, 250, 0.42);
    animation: globe-float 4s ease-in-out infinite;
    transform-style: preserve-3d;
}
.globe-sphere::before,
.globe-sphere::after {
    position: absolute;
    content: "";
    pointer-events: none;
}
.globe-sphere::before {
    inset: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent 0 17px,
        rgba(191, 219, 254, 0.35) 18px,
        transparent 19px 25px
    );
    border-radius: 50%;
    transform: rotate(-18deg) scale(1.06);
}
.globe-sphere::after {
    top: -8%;
    bottom: -8%;
    left: 27%;
    width: 44%;
    border: 1px solid rgba(224, 242, 254, 0.55);
    border-radius: 50%;
    box-shadow: 12px 0 0 -1px rgba(224, 242, 254, 0.28);
    transform: rotate(18deg);
}
.globe-orbit {
    position: absolute;
    width: 144px;
    height: 56px;
    border: 1px solid rgba(167, 139, 250, 0.65);
    border-radius: 50%;
    transform: rotate(-24deg);
}
.globe-orbit::after {
    position: absolute;
    top: 5px;
    left: 19px;
    width: 8px;
    height: 8px;
    content: "";
    border-radius: 50%;
    background: #a78bfa;
    box-shadow: 0 0 12px #a78bfa;
}
.globe-orbit.orbit-back {
    width: 132px;
    height: 46px;
    border-color: rgba(52, 211, 153, 0.5);
    transform: rotate(38deg);
    animation: orbit-turn 12s linear infinite;
}
.globe-token {
    position: absolute;
    display: grid;
    width: 32px;
    height: 32px;
    place-items: center;
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 11px;
    background: rgba(30, 41, 89, 0.9);
    box-shadow: 0 8px 20px rgba(0,0,0,0.25);
    color: #e0e7ff;
    font-size: 0.8rem;
    font-weight: 700;
    animation: token-float 3s ease-in-out infinite;
}
.globe-token.token-left {
    top: 20px;
    left: 2px;
}
.globe-token.token-right {
    right: 0;
    bottom: 16px;
    color: #6ee7b7;
    animation-delay: -1.5s;
}
@keyframes globe-float {
    0%, 100% { transform: translateY(0) rotateY(-12deg); }
    50% { transform: translateY(-7px) rotateY(12deg); }
}
@keyframes orbit-turn {
    to { transform: rotate(398deg); }
}
@keyframes token-float {
    0%, 100% { transform: translateY(0) rotate(-6deg); }
    50% { transform: translateY(-5px) rotate(6deg); }
}
.hero-title {
    font-size: 3.2rem;
    font-weight: 800;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px;
    line-height: 1.1;
    margin-bottom: 0.4rem;
}
@media (max-width: 640px) {
    .hero-header { padding-top: 1.5rem; }
    .hero-title { font-size: 2.25rem; }
}
@media (prefers-reduced-motion: reduce) {
    .globe-sphere,
    .globe-orbit.orbit-back,
    .globe-token {
        animation: none;
    }
}
.hero-subtitle {
    font-size: 1.05rem;
    color: #94a3b8;
    font-weight: 400;
    margin-bottom: 1rem;
}
.badge {
    display: inline-block;
    background: rgba(167,139,250,0.15);
    border: 1px solid rgba(167,139,250,0.35);
    color: #a78bfa;
    border-radius: 50px;
    padding: 4px 16px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 1rem;
}

/* ── Glass Card ── */
.glass-card {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 20px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1rem;
}

/* ── Language bar ── */
.lang-bar {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}

/* ── Section label ── */
.section-label {
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #60a5fa;
    margin-bottom: 0.5rem;
}

/* ── Textareas ── */
textarea {
    background: rgba(15,12,41,0.6) !important;
    border: 1.5px solid rgba(255,255,255,0.10) !important;
    border-radius: 14px !important;
    color: #f1f5f9 !important;
    font-size: 1.05rem !important;
    line-height: 1.7 !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color 0.2s !important;
    resize: none !important;
}
textarea:focus {
    border-color: rgba(167,139,250,0.6) !important;
    box-shadow: 0 0 0 3px rgba(167,139,250,0.12) !important;
}
textarea:disabled {
    background: rgba(26,26,78,0.5) !important;
    color: #e2e8f0 !important;
    border-color: rgba(255,255,255,0.06) !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1.5px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    color: #f1f5f9 !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    transition: all 0.2s ease !important;
    border: none !important;
    padding: 0.55rem 1.2rem !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(0,0,0,0.3) !important;
}

/* ── Primary translate button ── */
div[data-testid="stHorizontalBlock"] > div:nth-child(1) > div > div > div > button[kind="primary"] {
    background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
    color: white !important;
    padding: 0.65rem 2rem !important;
    font-size: 1rem !important;
}

/* ── Stats row ── */
.stats-row {
    display: flex;
    gap: 12px;
    margin: 0.8rem 0;
    flex-wrap: wrap;
}
.stat-pill {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 50px;
    padding: 4px 14px;
    font-size: 0.78rem;
    color: #94a3b8;
    font-weight: 500;
}

/* ── Detected badge ── */
.detected-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(52,211,153,0.12);
    border: 1px solid rgba(52,211,153,0.3);
    border-radius: 50px;
    padding: 4px 14px;
    font-size: 0.78rem;
    color: #34d399;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

/* ── Divider ── */
.glowing-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(167,139,250,0.4), transparent);
    margin: 1.5rem 0;
}

/* ── Footer ── */
.footer {
    text-align: center;
    padding: 2rem 0 1rem;
    color: #475569;
    font-size: 0.82rem;
}
.footer span {
    color: #7c3aed;
    font-weight: 600;
}

/* ── History item ── */
.history-item {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
    color: #cbd5e1;
}
.history-arrow {
    color: #7c3aed;
    font-weight: 700;
    font-size: 0.75rem;
}

/* ── Feature chips ── */
.feature-chip {
    display: inline-block;
    background: rgba(96,165,250,0.10);
    border: 1px solid rgba(96,165,250,0.20);
    border-radius: 50px;
    padding: 3px 12px;
    font-size: 0.75rem;
    color: #60a5fa;
    margin: 3px 2px;
}
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.3rem 0 0.85rem;
}
.sidebar-brand-mark {
    position: relative;
    display: grid;
    width: 48px;
    height: 48px;
    flex: 0 0 48px;
    place-items: center;
    overflow: hidden;
    border: 1px solid rgba(191, 219, 254, 0.42);
    border-radius: 16px;
    background: linear-gradient(145deg, #38bdf8 0%, #6366f1 52%, #312e81 100%);
    box-shadow:
        inset 3px 3px 8px rgba(255,255,255,0.3),
        inset -5px -6px 10px rgba(15,12,41,0.42),
        0 5px 0 #29245f,
        0 10px 18px rgba(56, 189, 248, 0.2);
    color: #fff;
    font-size: 1.35rem;
    font-weight: 700;
    transform: perspective(120px) rotateX(7deg) rotateY(-8deg);
}
.sidebar-brand-mark::after {
    position: absolute;
    top: -13px;
    left: 20px;
    width: 25px;
    height: 68px;
    content: "";
    border: 1px solid rgba(224, 242, 254, 0.65);
    border-radius: 50%;
    transform: rotate(35deg);
}
.sidebar-brand-copy {
    min-width: 0;
}
.sidebar-brand-title {
    color: #f1f5f9;
    font-size: 1.02rem;
    font-weight: 750;
    letter-spacing: -0.3px;
    line-height: 1.2;
}
.sidebar-brand-subtitle {
    margin-top: 4px;
    color: #94a3b8;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.5px;
}
.icon-3d {
    position: relative;
    display: inline-grid;
    width: 30px;
    height: 30px;
    flex: 0 0 30px;
    place-items: center;
    border: 1px solid rgba(255,255,255,0.24);
    border-radius: 10px;
    background: linear-gradient(145deg, #60a5fa, #4f46e5 68%, #3730a3);
    box-shadow:
        inset 2px 2px 5px rgba(255,255,255,0.3),
        inset -3px -4px 6px rgba(15,12,41,0.32),
        0 3px 0 #312e81,
        0 5px 9px rgba(3,7,18,0.25);
    color: #fff;
    font-size: 0.9rem;
    font-weight: 750;
    line-height: 1;
    text-shadow: 0 1px 2px rgba(15,12,41,0.38);
    transform: perspective(90px) rotateX(8deg) rotateY(-7deg);
}
.icon-3d::after {
    position: absolute;
    top: 3px;
    left: 5px;
    width: 8px;
    height: 3px;
    content: "";
    border-radius: 50%;
    background: rgba(255,255,255,0.55);
    filter: blur(0.4px);
}
.icon-3d.icon-green {
    background: linear-gradient(145deg, #6ee7b7, #059669 68%, #065f46);
    box-shadow: inset 2px 2px 5px rgba(255,255,255,0.3), inset -3px -4px 6px rgba(15,12,41,0.3), 0 3px 0 #064e3b, 0 5px 9px rgba(3,7,18,0.25);
}
.icon-3d.icon-violet {
    background: linear-gradient(145deg, #c4b5fd, #8b5cf6 68%, #5b21b6);
    box-shadow: inset 2px 2px 5px rgba(255,255,255,0.3), inset -3px -4px 6px rgba(15,12,41,0.3), 0 3px 0 #4c1d95, 0 5px 9px rgba(3,7,18,0.25);
}
.feature-list {
    display: grid;
    gap: 0.55rem;
    margin: 0.65rem 0 0.9rem;
}
.feature-chip {
    display: flex;
    width: 100%;
    align-items: center;
    gap: 0.7rem;
    margin: 0;
    padding: 0.48rem 0.65rem;
    border-color: rgba(148, 163, 184, 0.13);
    border-radius: 13px;
    background: rgba(255,255,255,0.035);
    color: #cbd5e1;
    font-size: 0.8rem;
    transition: background 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}
.feature-chip:hover {
    transform: translateX(2px);
    border-color: rgba(129, 140, 248, 0.32);
    background: rgba(99, 102, 241, 0.08);
}
.section-label {
    display: flex;
    align-items: center;
    gap: 0.6rem;
}
.selector-label {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    margin: 0.15rem 0 0.5rem;
    color: #cbd5e1;
    font-size: 0.9rem;
    font-weight: 600;
}
.selector-label .icon-3d {
    width: 26px;
    height: 26px;
    flex-basis: 26px;
    border-radius: 8px;
    font-size: 0.78rem;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: rgba(15,12,41,0.95) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
section[data-testid="stSidebar"] * {
    color: #cbd5e1 !important;
}

/* ── Audio player ── */
audio {
    width: 100% !important;
    border-radius: 10px !important;
    margin-top: 6px !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background: rgba(52,211,153,0.15) !important;
    border: 1px solid rgba(52,211,153,0.35) !important;
    color: #34d399 !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
}
.stDownloadButton > button:hover {
    background: rgba(52,211,153,0.25) !important;
    transform: translateY(-2px) !important;
}

/* ── Code block for copy ── */
.stCodeBlock {
    border-radius: 12px !important;
    background: rgba(0,0,0,0.3) !important;
}

/* ── Spinner ── */
.stSpinner > div {
    border-top-color: #a78bfa !important;
}

/* ── UI polish ── */
.stApp {
    background:
        radial-gradient(ellipse at 78% 3%, rgba(79, 70, 229, 0.18), transparent 34%),
        radial-gradient(ellipse at 14% 48%, rgba(14, 165, 233, 0.08), transparent 30%),
        linear-gradient(135deg, #0b1024 0%, #141735 48%, #17152f 100%);
}
.block-container {
    max-width: 1360px;
    padding-top: 1rem;
    padding-bottom: 2rem;
}
.hero-header {
    padding: 1.15rem 1rem 0.8rem;
}
.hero-visual {
    width: 128px;
    height: 116px;
    margin-bottom: 0.25rem;
}
.globe-sphere {
    width: 88px;
    height: 88px;
}
.globe-orbit {
    width: 122px;
    height: 48px;
}
.globe-orbit.orbit-back {
    width: 112px;
    height: 40px;
}
.globe-token.token-left {
    top: 14px;
    left: 1px;
}
.globe-token.token-right {
    right: 0;
    bottom: 9px;
}
.hero-title {
    font-size: clamp(2.1rem, 4vw, 3rem);
    letter-spacing: -1.5px;
}
.hero-subtitle {
    margin: 0 auto 0.65rem;
    max-width: 620px;
    line-height: 1.6;
}
.badge {
    padding: 6px 15px;
    background: rgba(124, 58, 237, 0.12);
    border-color: rgba(167, 139, 250, 0.28);
}
div[data-testid="stHorizontalBlock"]:has(.stSelectbox) {
    align-items: end;
    padding: 0.85rem 1rem 0.35rem;
    border: 1px solid rgba(148, 163, 184, 0.13);
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(255,255,255,0.055), rgba(255,255,255,0.025));
    box-shadow: 0 14px 36px rgba(3, 7, 18, 0.15);
}
div[data-testid="stColumn"]:has(textarea) {
    padding: 1.15rem;
    border: 1px solid rgba(148, 163, 184, 0.14);
    border-radius: 22px;
    background: linear-gradient(155deg, rgba(255,255,255,0.055), rgba(255,255,255,0.022));
    box-shadow: 0 18px 44px rgba(3, 7, 18, 0.16);
}
.section-label {
    margin: 0.1rem 0 0.75rem;
    color: #a5b4fc;
    letter-spacing: 1.2px;
}
textarea {
    min-height: 230px;
    padding: 1rem !important;
    background: rgba(8, 13, 31, 0.62) !important;
    border-color: rgba(148, 163, 184, 0.18) !important;
    border-radius: 16px !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
textarea:focus {
    border-color: rgba(129, 140, 248, 0.72) !important;
    box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.13) !important;
}
.stSelectbox > div > div {
    min-height: 46px;
    background: rgba(8, 13, 31, 0.42) !important;
    border-color: rgba(148, 163, 184, 0.19) !important;
    border-radius: 13px !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.stSelectbox > div > div:focus-within {
    border-color: rgba(129, 140, 248, 0.72) !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
}
.stButton > button,
.stDownloadButton > button {
    min-height: 42px;
    padding-right: 0.65rem !important;
    padding-left: 0.65rem !important;
    white-space: nowrap;
    border: 1px solid rgba(148, 163, 184, 0.16) !important;
    background: rgba(255, 255, 255, 0.055) !important;
    color: #e2e8f0 !important;
    box-shadow: 0 5px 16px rgba(3, 7, 18, 0.12);
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: rgba(165, 180, 252, 0.4) !important;
    background: rgba(99, 102, 241, 0.14) !important;
    box-shadow: 0 8px 22px rgba(3, 7, 18, 0.22) !important;
}
.stButton > button[kind="primary"] {
    border: 1px solid rgba(196, 181, 253, 0.35) !important;
    background: linear-gradient(120deg, #7c3aed, #4f46e5 62%, #2563eb) !important;
    box-shadow: 0 8px 24px rgba(79, 70, 229, 0.28);
    color: #fff !important;
}
.stButton > button:focus-visible,
.stDownloadButton > button:focus-visible {
    outline: 3px solid rgba(129, 140, 248, 0.78) !important;
    outline-offset: 3px;
}
.stats-row {
    gap: 8px;
    margin: 0.75rem 0 1rem;
}
.stat-pill {
    padding: 5px 12px;
    border-color: rgba(148, 163, 184, 0.13);
    background: rgba(148, 163, 184, 0.07);
}
.detected-badge {
    padding: 6px 13px;
    background: rgba(16, 185, 129, 0.1);
}
.glowing-divider {
    margin: 1.2rem 0;
    background: linear-gradient(90deg, transparent, rgba(129, 140, 248, 0.4), rgba(56, 189, 248, 0.28), transparent);
}
.glass-card {
    border-color: rgba(148, 163, 184, 0.13);
    background: linear-gradient(145deg, rgba(255,255,255,0.06), rgba(255,255,255,0.025));
    box-shadow: 0 12px 30px rgba(3, 7, 18, 0.12);
}
.history-item {
    transition: border-color 0.2s ease, background 0.2s ease, transform 0.2s ease;
}
.history-item:hover {
    transform: translateX(2px);
    border-color: rgba(129, 140, 248, 0.3);
    background: rgba(99, 102, 241, 0.08);
}
@media (max-width: 640px) {
    .block-container {
        padding: 0.6rem 0.85rem 1.5rem;
    }
    .hero-header {
        padding-top: 0.9rem;
    }
    .hero-visual {
        transform: scale(0.88);
        margin-bottom: -0.4rem;
    }
    div[data-testid="stHorizontalBlock"]:has(.stSelectbox) {
        padding: 0.65rem 0.75rem 0.2rem;
    }
    div[data-testid="stColumn"]:has(textarea) {
        padding: 0.8rem;
        border-radius: 18px;
    }
}
</style>
""", unsafe_allow_html=True)


# ─── Engine & Session State ───────────────────────────────────────────────────
@st.cache_resource
def get_engine():
    return TranslationEngine()

engine = get_engine()

for key, default in [
    ("history", []),
    ("source_lang", "Auto Detect"),
    ("target_lang", "Hindi"),
    ("input_text", ""),
    ("result", None),
    ("output_audio_bytes", None),
    ("output_audio_key", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def generate_audio(text: str, lang_code: str) -> Optional[io.BytesIO]:
    try:
        code = lang_code if lang_code and lang_code != "auto" else "en"
        code = code.split("-")[0]
        tts = gTTS(text=text[:500], lang=code, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception:
        return None


@st.cache_data(ttl=86400)
def get_tts_voices() -> list[dict[str, str]]:
    return asyncio.run(edge_tts.list_voices())


async def generate_voice_audio(text: str, voice: str) -> bytes:
    communicator = edge_tts.Communicate(text=text[:500], voice=voice)
    audio = bytearray()
    async for chunk in communicator.stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
    if not audio:
        raise RuntimeError("The speech service returned an empty audio file.")
    return bytes(audio)


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class='sidebar-brand'>
        <div class='sidebar-brand-mark' aria-hidden='true'>文</div>
        <div class='sidebar-brand-copy'>
            <div class='sidebar-brand-title'>Language AI</div>
            <div class='sidebar-brand-subtitle'>TRANSLATOR</div>
        </div>
    </div>
    <p style='color:#7c3aed;font-size:0.78rem;font-weight:600;text-transform:uppercase;letter-spacing:1px;'>CodeAlpha Internship · Task 1</p>
    """, unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("<div class='section-label'><span class='icon-3d icon-violet' aria-hidden='true'>✦</span>Capabilities</div>", unsafe_allow_html=True)
    features = [
        ("⌕", "Auto Language Detection", ""),
        ("◎", "100+ Languages", "icon-green"),
        ("♫", "Selectable Voice", "icon-violet"),
        ("↓", "Download Voice", "icon-green"),
        ("▣", "Copy & Download", ""),
        ("⇄", "Swap Languages", "icon-violet"),
        ("◷", "Session History", "icon-green"),
    ]
    feature_markup = "".join(
        f"<div class='feature-chip'><span class='icon-3d {style}' aria-hidden='true'>{icon}</span><span>{label}</span></div>"
        for icon, label, style in features
    )
    st.markdown(f"<div class='feature-list'>{feature_markup}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div class='section-label'><span class='icon-3d icon-green' aria-hidden='true'>◷</span>History</div>", unsafe_allow_html=True)

    if st.session_state.history:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.history = []
            st.rerun()
        for item in reversed(st.session_state.history[-6:]):
            st.markdown(f"""
            <div class='history-item'>
                <div class='history-arrow'>▸ {item['src']} → {item['tgt']}</div>
                <div style='color:#94a3b8;font-size:0.78rem;margin-top:2px;'>{item['text'][:55]}{'...' if len(item['text'])>55 else ''}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<p style='color:#475569;font-size:0.85rem;'>No translations yet.</p>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<p style='color:#334155;font-size:0.75rem;'>Powered by Google Translate API</p>", unsafe_allow_html=True)


# ─── Hero Header ─────────────────────────────────────────────────────────────
st.markdown("""
<div class='hero-header'>
    <div class='hero-visual' role='img' aria-label='Animated three-dimensional globe with language symbols'>
        <div class='globe-orbit orbit-back'></div>
        <div class='globe-orbit'></div>
        <div class='globe-sphere'></div>
        <div class='globe-token token-left' aria-hidden='true'>A</div>
        <div class='globe-token token-right' aria-hidden='true'>文</div>
    </div>
    <div class='badge'>CodeAlpha AI Internship · Task 1</div>
    <div class='hero-title'>Language AI Translator</div>
    <div class='hero-subtitle'>Break language barriers instantly — powered by AI & Google Translate</div>
</div>
""", unsafe_allow_html=True)

# ─── Language Selector Bar ────────────────────────────────────────────────────
language_names = list(SUPPORTED_LANGUAGES.keys())
target_names = [n for n in language_names if n != "Auto Detect"]

col_src, col_swap, col_tgt = st.columns([5, 1, 5])

with col_src:
    st.markdown("<div class='selector-label'><span class='icon-3d' aria-hidden='true'>文</span>Source language</div>", unsafe_allow_html=True)
    src_idx = language_names.index(st.session_state.source_lang) if st.session_state.source_lang in language_names else 0
    selected_src = st.selectbox("Source Language", language_names, index=src_idx, key="sel_src", label_visibility="collapsed")

with col_swap:
    st.markdown("<div style='height:33px'></div>", unsafe_allow_html=True)
    if st.button("Swap", help="Swap languages", use_container_width=True):
        if selected_src != "Auto Detect":
            # Swap
            st.session_state.source_lang = st.session_state.target_lang
            st.session_state.target_lang = selected_src
            if st.session_state.result and st.session_state.result.get("translated_text"):
                st.session_state.input_text = st.session_state.result["translated_text"]
                st.session_state.result = None
            st.rerun()
        else:
            st.warning("Set a specific source language to swap.")

with col_tgt:
    st.markdown("<div class='selector-label'><span class='icon-3d icon-violet' aria-hidden='true'>A文</span>Target language</div>", unsafe_allow_html=True)
    tgt_idx = target_names.index(st.session_state.target_lang) if st.session_state.target_lang in target_names else 0
    selected_tgt = st.selectbox("Target Language", target_names, index=tgt_idx, key="sel_tgt", label_visibility="collapsed")

st.session_state.source_lang = selected_src
st.session_state.target_lang = selected_tgt

st.markdown("<hr class='glowing-divider'>", unsafe_allow_html=True)

# ─── Translation Workspace ────────────────────────────────────────────────────
left, right = st.columns(2, gap="large")

# ── Left: Input ──────────────────────────────────────────────────────────────
with left:
    st.markdown("<div class='section-label'><span class='icon-3d' aria-hidden='true'>✎</span>Your Text</div>", unsafe_allow_html=True)
    user_input = st.text_area(
        label="input",
        value=st.session_state.input_text,
        height=230,
        placeholder="Type or paste your text here…",
        label_visibility="collapsed",
        key="txt_input"
    )
    st.session_state.input_text = user_input

    # Stats pills
    chars = len(user_input)
    words = len(user_input.split()) if user_input.strip() else 0
    st.markdown(f"""
    <div class='stats-row'>
        <span class='stat-pill'>{chars} characters</span>
        <span class='stat-pill'>{words} words</span>
    </div>
    """, unsafe_allow_html=True)

    # Action buttons
    b1, b2, b3 = st.columns([3, 1.5, 1.5])
    with b1:
        translate_btn = st.button("🚀 Translate Now", type="primary", use_container_width=True)
    with b2:
        if st.button("🧹 Clear", use_container_width=True):
            st.session_state.input_text = ""
            st.session_state.result = None
            st.rerun()
    with b3:
        listen_in = st.button("🔊 Listen", key="listen_in", use_container_width=True)

    if listen_in and user_input.strip():
        src_code = SUPPORTED_LANGUAGES.get(selected_src, "en")
        with st.spinner("Generating audio…"):
            audio = generate_audio(user_input, src_code)
        if audio:
            st.audio(audio, format="audio/mp3")
        else:
            st.warning("Audio not available for this language.")


# ── Right: Output ────────────────────────────────────────────────────────────
with right:
    st.markdown("<div class='section-label'><span class='icon-3d icon-violet' aria-hidden='true'>文</span>Translation</div>", unsafe_allow_html=True)

    res = st.session_state.result

    if res and res.get("success"):
        output = res["translated_text"]
        detected_name = res.get("detected_source_name", "")
        latency = res.get("latency_ms", "—")

        st.markdown(f"<div class='detected-badge'>Detected: {detected_name} &nbsp;·&nbsp; {latency} ms</div>", unsafe_allow_html=True)

        st.text_area(
            label="output",
            value=output,
            height=230,
            disabled=True,
            label_visibility="collapsed",
            key="txt_output"
        )

        o_chars = len(output)
        o_words = len(output.split()) if output.strip() else 0
        st.markdown(f"""
        <div class='stats-row'>
            <span class='stat-pill'>{o_chars} characters</span>
            <span class='stat-pill'>{o_words} words</span>
            <span class='stat-pill'>{res.get('target_name','')}</span>
        </div>
        """, unsafe_allow_html=True)

        target_code = SUPPORTED_LANGUAGES.get(selected_tgt, "en")
        voice_load_error = None
        try:
            available_voices = get_tts_voices()
            language_voices = [
                voice for voice in available_voices
                if voice.get("Locale", "").split("-")[0].lower() == target_code.split("-")[0].lower()
            ]
        except Exception as exc:
            language_voices = []
            voice_load_error = exc
            st.error(f"Could not load voice options: {exc}")

        if language_voices:
            voice_labels = {
                f"{voice.get('ShortName', 'Unknown').split('-')[-1].removesuffix('Neural')} "
                f"({voice.get('Gender', 'Unknown')}) — {voice.get('Locale', '')}":
                    voice["ShortName"]
                for voice in language_voices
            }
            voice_label = st.selectbox(
                f"🗣️ Voice for {selected_tgt} ({len(voice_labels)} available)",
                list(voice_labels),
                key=f"output_voice_{target_code}",
                help="Available voices depend on the selected language. Choose a voice, then click Listen.",
            )
            selected_voice = voice_labels[voice_label]
        else:
            selected_voice = None
            if voice_load_error is None:
                st.warning(f"No selectable speech voices are available for {selected_tgt}.")

        b4, b5, b6 = st.columns(3)
        with b4:
            st.code(output[:300], language="")
        with b5:
            listen_out = st.button("🔊 Listen", key="listen_out", use_container_width=True)
            audio_key = (output, selected_tgt, selected_voice)
            if st.session_state.output_audio_key != audio_key:
                st.session_state.output_audio_bytes = None
                st.session_state.output_audio_key = audio_key

            if listen_out:
                if selected_voice is None:
                    if voice_load_error is None:
                        st.warning(f"No selectable speech voices are available for {selected_tgt}.")
                else:
                    try:
                        with st.spinner("Generating audio…"):
                            st.session_state.output_audio_bytes = asyncio.run(
                                generate_voice_audio(output, selected_voice)
                            )
                    except Exception as exc:
                        st.session_state.output_audio_bytes = None
                        st.error(f"Could not generate speech: {exc}")

            if st.session_state.output_audio_bytes:
                st.audio(st.session_state.output_audio_bytes, format="audio/mp3")
                st.download_button(
                    "🎧 Download Voice",
                    data=st.session_state.output_audio_bytes,
                    file_name=(
                        f"translation_{selected_tgt.lower().replace(' ', '_')}_"
                        f"{selected_voice.split('-')[-1].lower()}.mp3"
                    ),
                    mime="audio/mpeg",
                    use_container_width=True,
                )
        with b6:
            st.download_button(
                "💾 Download",
                data=output,
                file_name=f"translation_{selected_tgt.lower().replace(' ','_')}.txt",
                mime="text/plain",
                use_container_width=True
            )

    elif res and not res.get("success"):
        st.error(f"❌ {res.get('error', 'Translation failed')}")
        st.text_area("output", value="", height=230, disabled=True, label_visibility="collapsed")

    else:
        st.text_area(
            label="output",
            value="",
            height=230,
            disabled=True,
            placeholder="Translation will appear here…",
            label_visibility="collapsed",
        )
        st.markdown("<div class='stats-row'><span class='stat-pill'>Awaiting translation</span></div>", unsafe_allow_html=True)


# ─── Translation Logic ────────────────────────────────────────────────────────
if translate_btn:
    if not user_input.strip():
        st.warning("⚠️ Please enter some text to translate!")
    else:
        with st.spinner("🔄 Translating with AI…"):
            t0 = time.time()
            result = engine.translate(
                text=user_input,
                source_lang=selected_src,
                target_lang=selected_tgt
            )
            result["latency_ms"] = round((time.time() - t0) * 1000, 1)
        st.session_state.result = result
        if result.get("success"):
            st.session_state.history.append({
                "src": result.get("detected_source_name", selected_src),
                "tgt": result.get("target_name", selected_tgt),
                "text": user_input,
                "translated": result["translated_text"],
                "time": time.strftime("%H:%M"),
            })
        st.rerun()


# ─── Stats Banner ─────────────────────────────────────────────────────────────
st.markdown("<hr class='glowing-divider'>", unsafe_allow_html=True)

s1, s2, s3, s4 = st.columns(4)
stats = [
    ("100+", "Languages", "◎", "icon-green"),
    ("Fast", "AI Translation", "⚡", ""),
    ("TTS", "Audio Playback", "♫", "icon-violet"),
    ("Free", "No API Key Needed", "✓", "icon-green"),
]
for col, (val, lbl, icon, style) in zip([s1, s2, s3, s4], stats):
    with col:
        st.markdown(f"""
        <div class='glass-card' style='text-align:center;padding:1.2rem;'>
            <div class='icon-3d {style}' aria-hidden='true' style='margin-bottom:0.55rem;'>{icon}</div>
            <div style='font-size:1.45rem;font-weight:800;color:#a78bfa;'>{val}</div>
            <div style='font-size:0.8rem;color:#64748b;margin-top:4px;'>{lbl}</div>
        </div>
        """, unsafe_allow_html=True)


# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class='footer'>
    Built with ❤️ for <span>CodeAlpha Artificial Intelligence Internship</span> · Task 1<br>
    <span style='color:#334155;'>Google Translate API · gTTS · Streamlit · Python 3.13</span>
</div>
""", unsafe_allow_html=True)
