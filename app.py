import io
import time
from typing import Optional
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


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌐 Language AI Translator")
    st.markdown("<p style='color:#7c3aed;font-size:0.82rem;font-weight:600;text-transform:uppercase;letter-spacing:1px;'>CodeAlpha Internship · Task 1</p>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### ⚡ Capabilities")
    for feat in ["🔍 Auto Language Detection", "🌍 100+ Languages", "🔊 Text-to-Speech", "📋 Copy & Download", "⇄ Swap Languages", "📜 Session History"]:
        st.markdown(f"<span class='feature-chip'>{feat}</span>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🕒 History")

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
    <div class='badge'>🎓 CodeAlpha AI Internship · Task 1</div>
    <div class='hero-title'>🌐 Language AI Translator</div>
    <div class='hero-subtitle'>Break language barriers instantly — powered by AI & Google Translate</div>
</div>
""", unsafe_allow_html=True)

# ─── Language Selector Bar ────────────────────────────────────────────────────
language_names = list(SUPPORTED_LANGUAGES.keys())
target_names = [n for n in language_names if n != "Auto Detect"]

col_src, col_swap, col_tgt = st.columns([5, 1, 5])

with col_src:
    src_idx = language_names.index(st.session_state.source_lang) if st.session_state.source_lang in language_names else 0
    selected_src = st.selectbox("🔍 Source Language", language_names, index=src_idx, key="sel_src")

with col_swap:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("⇄", help="Swap languages", use_container_width=True):
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
    tgt_idx = target_names.index(st.session_state.target_lang) if st.session_state.target_lang in target_names else 0
    selected_tgt = st.selectbox("🎯 Target Language", target_names, index=tgt_idx, key="sel_tgt")

st.session_state.source_lang = selected_src
st.session_state.target_lang = selected_tgt

st.markdown("<hr class='glowing-divider'>", unsafe_allow_html=True)

# ─── Translation Workspace ────────────────────────────────────────────────────
left, right = st.columns(2, gap="large")

# ── Left: Input ──────────────────────────────────────────────────────────────
with left:
    st.markdown("<div class='section-label'>✏️ Your Text</div>", unsafe_allow_html=True)
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
        <span class='stat-pill'>📝 {chars} characters</span>
        <span class='stat-pill'>📖 {words} words</span>
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
    st.markdown("<div class='section-label'>✨ Translation</div>", unsafe_allow_html=True)

    res = st.session_state.result

    if res and res.get("success"):
        output = res["translated_text"]
        detected_name = res.get("detected_source_name", "")
        latency = res.get("latency_ms", "—")

        st.markdown(f"<div class='detected-badge'>✅ Detected: {detected_name} &nbsp;·&nbsp; ⚡ {latency}ms</div>", unsafe_allow_html=True)

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
            <span class='stat-pill'>📝 {o_chars} characters</span>
            <span class='stat-pill'>📖 {o_words} words</span>
            <span class='stat-pill'>🌍 {res.get('target_name','')}</span>
        </div>
        """, unsafe_allow_html=True)

        b4, b5, b6 = st.columns(3)
        with b4:
            st.code(output[:300], language="")
        with b5:
            listen_out = st.button("🔊 Listen", key="listen_out", use_container_width=True)
            if listen_out:
                tgt_code = SUPPORTED_LANGUAGES.get(selected_tgt, "en")
                with st.spinner("Generating audio…"):
                    audio = generate_audio(output, tgt_code)
                if audio:
                    st.audio(audio, format="audio/mp3")
                else:
                    st.warning("Audio not available.")
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
        st.markdown("<div class='stats-row'><span class='stat-pill'>⏳ Awaiting translation</span></div>", unsafe_allow_html=True)


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
    ("100+", "Languages"),
    ("⚡ Fast", "AI Translation"),
    ("🔊 TTS", "Audio Playback"),
    ("🔒 Free", "No API Key Needed"),
]
for col, (val, lbl) in zip([s1, s2, s3, s4], stats):
    with col:
        st.markdown(f"""
        <div class='glass-card' style='text-align:center;padding:1.2rem;'>
            <div style='font-size:1.6rem;font-weight:800;color:#a78bfa;'>{val}</div>
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
