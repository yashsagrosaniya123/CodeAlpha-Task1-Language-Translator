# 🌐 Language AI Translator

<div align="center">

![Python](https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.65-red?style=for-the-badge&logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Google Translate](https://img.shields.io/badge/Google_Translate_API-Free-orange?style=for-the-badge&logo=google)
![CodeAlpha](https://img.shields.io/badge/CodeAlpha-AI_Internship-purple?style=for-the-badge)

**Real-time AI-powered Language Translation Tool**
*CodeAlpha Artificial Intelligence Internship — Task 1*

</div>

---

## 📌 Overview

**Language AI Translator** is a full-featured language translation web application built as **Task 1** of the **CodeAlpha AI Internship**. It leverages the **Google Translate API** (free, no API key required) to instantly translate text across **100+ languages** with a beautiful, modern UI.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🌍 **100+ Languages** | Translate between any of 100+ world languages |
| 🔍 **Auto Language Detection** | Automatically detects the source language |
| 🔊 **Text-to-Speech (TTS)** | Listen to original text via gTTS and translated text with selectable neural voices |
| 🗣️ **Voice Selection** | Choose from all neural voices available for the selected translation language; counts vary by language |
| 🎧 **Download Voice** | Download generated translated speech as an MP3 file |
| ⇄ **Swap Languages** | Instantly swap source & target languages + text |
| 📋 **Copy to Clipboard** | One-click copy of translated text |
| 💾 **Download as .txt** | Download translation as a text file |
| 📜 **Session History** | View your recent translations in the sidebar |
| ⚡ **Latency Display** | Shows how fast the translation was in ms |
| 🎨 **Glassmorphism UI** | Dark mode with gradient design & glass cards |
| 🔄 **Fallback API** | Falls back to MyMemory API if Google rate-limits |

---

## 🖼️ Screenshots

> Beautiful dark-mode glassmorphism interface with gradient title, translation panels, TTS, and history sidebar.

---

## 🛠️ Tech Stack

- **Python 3.13**
- **Streamlit** — Web UI framework
- **Google Translate API** — Free translation endpoint
- **MyMemory API** — Fallback translation
- **gTTS** — Text-to-Speech audio generation
- **Edge TTS** — Selectable online neural voices for translated speech
- **pyttsx3** — Offline TTS engine (Desktop version)
- **CustomTkinter** — Desktop GUI (alternative version)
- **httpx** — HTTP client with retry support

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/yashsagrosaniya123/CodeAlpha-Task1-Language-Translator.git
cd CodeAlpha-Task1-Language-Translator
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Web App
```bash
streamlit run app.py
```

### 4. Run the Desktop App (Alternative)
```bash
python desktop_app.py
```

---

## 📁 Project Structure

```
CodeAlpha-Task1-Language-Translator/
│
├── app.py                  # 🌐 Streamlit Web Application
├── desktop_app.py          # 🖥️ CustomTkinter Desktop App
├── translator_engine.py    # ⚙️ Core Translation Engine
├── test_translator.py      # 🧪 Unit Tests (pytest)
├── requirements.txt        # 📦 Dependencies
├── .gitignore              # 🚫 Git Ignore Rules
├── LICENSE                 # 📄 MIT License
└── README.md               # 📖 Documentation
```

---

## 🧪 Run Tests

```bash
pytest test_translator.py -v
```

---

## 📦 Requirements

```
streamlit>=1.30.0
deep-translator>=1.11.0
gTTS>=2.5.0
edge-tts>=7.0.0
customtkinter>=5.2.0
pyttsx3>=2.90
httpx>=0.25.0
pytest>=8.0.0
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Yash Sagrosaniya**
📧 sagrosaniyayash234@gmail.com
🎓 CodeAlpha AI Internship — Task 1

---

<div align="center">
  Made with ❤️ for <b>CodeAlpha Artificial Intelligence Internship</b>
</div>
