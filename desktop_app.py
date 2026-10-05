"""
CodeAlpha Artificial Intelligence Internship - Task 1: Language Translation Tool
Desktop Application (CustomTkinter GUI)
-------------------------------------------------------------------------------
Features:
- Modern dark-mode UI with high-DPI scaling
- Dual side-by-side translation panels
- 100+ Supported Languages with Auto-Detection
- Instant Swap Languages (⇄)
- Copy translated text to Clipboard with visual confirmation
- Text-to-Speech (TTS) engine integration via pyttsx3 (threaded)
- Real-time character & word counters
- Error-resilient asynchronous translation execution
"""

import threading
import time
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False

from translator_engine import TranslationEngine, SUPPORTED_LANGUAGES, CODE_TO_LANGUAGE

# Set CustomTkinter appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class LanguageTranslatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CodeAlpha AI - Language Translation Tool")
        self.geometry("980x680")
        self.minsize(860, 600)

        # Initialize Translation Engine
        self.engine = TranslationEngine()

        # Initialize TTS Engine safely
        self.tts_lock = threading.Lock()

        # Build UI Components
        self._create_header()
        self._create_language_selector_bar()
        self._create_translation_workspace()
        self._create_status_bar()

    def _create_header(self):
        header_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray85", "#1e1e2d"))
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        title_label = ctk.CTkLabel(
            header_frame,
            text="🌐 AI Language Translation Tool",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(anchor="w", padx=20, pady=(10, 2))

        sub_label = ctk.CTkLabel(
            header_frame,
            text="CodeAlpha Artificial Intelligence Internship • Task 1 (Google Translate API + TTS)",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        sub_label.pack(anchor="w", padx=20, pady=(0, 10))

    def _create_language_selector_bar(self):
        bar_frame = ctk.CTkFrame(self, corner_radius=10)
        bar_frame.pack(fill="x", padx=20, pady=5)

        self.language_list = list(SUPPORTED_LANGUAGES.keys())
        self.target_languages = [name for name in self.language_list if name != "Auto Detect"]

        # Source Language Selector
        src_label = ctk.CTkLabel(bar_frame, text="Source:", font=ctk.CTkFont(weight="bold"))
        src_label.pack(side="left", padx=(15, 5), pady=12)

        self.src_combo = ctk.CTkComboBox(
            bar_frame,
            values=self.language_list,
            width=200,
            command=self._on_source_changed
        )
        self.src_combo.set("Auto Detect")
        self.src_combo.pack(side="left", padx=5, pady=12)

        # Swap Button
        self.swap_btn = ctk.CTkButton(
            bar_frame,
            text="⇄ Swap",
            width=80,
            fg_color="#4f46e5",
            hover_color="#4338ca",
            command=self._swap_languages
        )
        self.swap_btn.pack(side="left", padx=15, pady=12)

        # Target Language Selector
        tgt_label = ctk.CTkLabel(bar_frame, text="Target:", font=ctk.CTkFont(weight="bold"))
        tgt_label.pack(side="left", padx=(5, 5), pady=12)

        self.tgt_combo = ctk.CTkComboBox(
            bar_frame,
            values=self.target_languages,
            width=200
        )
        self.tgt_combo.set("Spanish")
        self.tgt_combo.pack(side="left", padx=5, pady=12)

        # Translate Action Button
        self.translate_btn = ctk.CTkButton(
            bar_frame,
            text="🚀 Translate",
            width=140,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            command=self._start_translation_thread
        )
        self.translate_btn.pack(side="right", padx=15, pady=12)

    def _create_translation_workspace(self):
        work_frame = ctk.CTkFrame(self, fg_color="transparent")
        work_frame.pack(fill="both", expand=True, padx=20, pady=10)
        work_frame.grid_columnconfigure((0, 1), weight=1, uniform="col")
        work_frame.grid_rowconfigure(0, weight=1)

        # Left Column - Input Panel
        input_card = ctk.CTkFrame(work_frame, corner_radius=10)
        input_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        input_header = ctk.CTkFrame(input_card, fg_color="transparent")
        input_header.pack(fill="x", padx=15, pady=(10, 5))

        input_title = ctk.CTkLabel(input_header, text="Input Text", font=ctk.CTkFont(size=14, weight="bold"))
        input_title.pack(side="left")

        self.input_counter_label = ctk.CTkLabel(input_header, text="0 chars | 0 words", font=ctk.CTkFont(size=11), text_color="gray")
        self.input_counter_label.pack(side="right")

        self.input_textbox = ctk.CTkTextbox(input_card, font=ctk.CTkFont(size=13), wrap="word")
        self.input_textbox.pack(fill="both", expand=True, padx=15, pady=5)
        self.input_textbox.bind("<KeyRelease>", self._update_input_counters)

        input_actions = ctk.CTkFrame(input_card, fg_color="transparent")
        input_actions.pack(fill="x", padx=15, pady=(5, 12))

        self.clear_btn = ctk.CTkButton(
            input_actions, text="🧹 Clear", width=80, fg_color="#ef4444", hover_color="#dc2626", command=self._clear_input
        )
        self.clear_btn.pack(side="left", padx=(0, 8))

        self.paste_btn = ctk.CTkButton(
            input_actions, text="📋 Paste", width=80, fg_color="#64748b", hover_color="#475569", command=self._paste_input
        )
        self.paste_btn.pack(side="left")

        self.listen_in_btn = ctk.CTkButton(
            input_actions, text="🔊 Listen", width=80, fg_color="#0284c7", hover_color="#0369a1", command=lambda: self._speak_text(self.input_textbox.get("1.0", "end-1c"))
        )
        self.listen_in_btn.pack(side="right")

        # Right Column - Output Panel
        output_card = ctk.CTkFrame(work_frame, corner_radius=10)
        output_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        output_header = ctk.CTkFrame(output_card, fg_color="transparent")
        output_header.pack(fill="x", padx=15, pady=(10, 5))

        output_title = ctk.CTkLabel(output_header, text="Translated Output", font=ctk.CTkFont(size=14, weight="bold"))
        output_title.pack(side="left")

        self.output_counter_label = ctk.CTkLabel(output_header, text="0 chars | 0 words", font=ctk.CTkFont(size=11), text_color="gray")
        self.output_counter_label.pack(side="right")

        self.output_textbox = ctk.CTkTextbox(output_card, font=ctk.CTkFont(size=13), wrap="word")
        self.output_textbox.pack(fill="both", expand=True, padx=15, pady=5)

        output_actions = ctk.CTkFrame(output_card, fg_color="transparent")
        output_actions.pack(fill="x", padx=15, pady=(5, 12))

        self.copy_btn = ctk.CTkButton(
            output_actions, text="📋 Copy Text", width=100, fg_color="#3b82f6", hover_color="#2563eb", command=self._copy_output
        )
        self.copy_btn.pack(side="left", padx=(0, 8))

        self.listen_out_btn = ctk.CTkButton(
            output_actions, text="🔊 Listen", width=80, fg_color="#0284c7", hover_color="#0369a1", command=lambda: self._speak_text(self.output_textbox.get("1.0", "end-1c"))
        )
        self.listen_out_btn.pack(side="right")

    def _create_status_bar(self):
        self.status_frame = ctk.CTkFrame(self, height=32, corner_radius=0, fg_color=("gray90", "#181824"))
        self.status_frame.pack(fill="x", side="bottom")

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready. Select languages and enter text to translate.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.status_label.pack(side="left", padx=20, pady=4)

    def _update_input_counters(self, event=None):
        text = self.input_textbox.get("1.0", "end-1c")
        chars = len(text)
        words = len(text.split())
        self.input_counter_label.configure(text=f"{chars} chars | {words} words")

    def _on_source_changed(self, choice):
        if choice == "Auto Detect":
            self.status_label.configure(text="Source set to Auto Detect. The engine will detect the language automatically.")
        else:
            self.status_label.configure(text=f"Source set to: {choice}")

    def _swap_languages(self):
        src = self.src_combo.get()
        tgt = self.tgt_combo.get()

        if src == "Auto Detect":
            messagebox.showinfo("Cannot Swap", "Cannot swap when source language is 'Auto Detect'. Please select a specific language.")
            return

        self.src_combo.set(tgt)
        self.tgt_combo.set(src)

        # Swap texts
        in_text = self.input_textbox.get("1.0", "end-1c")
        out_text = self.output_textbox.get("1.0", "end-1c")

        self.input_textbox.delete("1.0", "end")
        self.input_textbox.insert("1.0", out_text)

        self.output_textbox.delete("1.0", "end")
        self.output_textbox.insert("1.0", in_text)

        self._update_input_counters()

    def _clear_input(self):
        self.input_textbox.delete("1.0", "end")
        self.output_textbox.delete("1.0", "end")
        self._update_input_counters()
        self.output_counter_label.configure(text="0 chars | 0 words")
        self.status_label.configure(text="Input cleared.")

    def _paste_input(self):
        try:
            clipboard_text = self.clipboard_get()
            self.input_textbox.insert("insert", clipboard_text)
            self._update_input_counters()
        except Exception:
            pass

    def _copy_output(self):
        out_text = self.output_textbox.get("1.0", "end-1c")
        if out_text.strip():
            self.clipboard_clear()
            self.clipboard_append(out_text)
            orig_text = self.copy_btn.cget("text")
            self.copy_btn.configure(text="✓ Copied!", fg_color="#10b981")
            self.after(2000, lambda: self.copy_btn.configure(text=orig_text, fg_color="#3b82f6"))
            self.status_label.configure(text="Translation copied to clipboard.")
        else:
            self.status_label.configure(text="Nothing to copy.")

    def _speak_text(self, text):
        if not HAS_TTS:
            messagebox.showwarning("TTS Not Available", "Text-to-speech library pyttsx3 is not installed.")
            return

        if not text.strip():
            return

        def run_speech():
            with self.tts_lock:
                try:
                    tts_engine = pyttsx3.init()
                    tts_engine.say(text)
                    tts_engine.runAndWait()
                except Exception as e:
                    print("TTS error:", e)

        thread = threading.Thread(target=run_speech, daemon=True)
        thread.start()

    def _start_translation_thread(self):
        text = self.input_textbox.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showwarning("Empty Text", "Please enter some text to translate.")
            return

        src_name = self.src_combo.get()
        tgt_name = self.tgt_combo.get()

        self.translate_btn.configure(state="disabled", text="Translating...")
        self.status_label.configure(text="Connecting to Google Translate API...")

        def worker():
            t0 = time.time()
            result = self.engine.translate(text, source_lang=src_name, target_lang=tgt_name)
            elapsed = round((time.time() - t0) * 1000, 1)

            # Update UI on main thread
            self.after(0, lambda: self._on_translation_finished(result, elapsed))

        threading.Thread(target=worker, daemon=True).start()

    def _on_translation_finished(self, result, elapsed_ms):
        self.translate_btn.configure(state="normal", text="🚀 Translate")

        if result.get("success"):
            translated_text = result["translated_text"]
            self.output_textbox.delete("1.0", "end")
            self.output_textbox.insert("1.0", translated_text)

            chars = len(translated_text)
            words = len(translated_text.split())
            self.output_counter_label.configure(text=f"{chars} chars | {words} words")

            detected = result.get("detected_source_name", "Detected")
            self.status_label.configure(
                text=f"✓ Translated successfully from {detected} to {result['target_name']} in {elapsed_ms}ms"
            )
        else:
            self.status_label.configure(text=f"❌ Translation failed: {result.get('error')}")
            messagebox.showerror("Translation Error", result.get("error", "Unknown error"))


if __name__ == "__main__":
    app = LanguageTranslatorApp()
    app.mainloop()
