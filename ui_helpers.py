"""Small helpers for safely rendering dynamic UI content."""

import html
from collections.abc import MutableMapping
from typing import Any


def escape_html(value: object) -> str:
    return html.escape(str(value), quote=True)


def format_history_item(source: object, target: object, text: object) -> str:
    original_text = str(text)
    preview = escape_html(original_text[:55])
    if len(original_text) > 55:
        preview += "..."
    return f"""
    <div class='history-item'>
        <div class='history-arrow'>▸ {escape_html(source)} → {escape_html(target)}</div>
        <div style='color:#94a3b8;font-size:0.78rem;margin-top:2px;'>{preview}</div>
    </div>
    """


def swap_language_values(state: MutableMapping[str, Any]) -> bool:
    source = state.get("sel_src", "Auto Detect")
    if source == "Auto Detect":
        return False

    target = state["sel_tgt"]
    state["sel_src"] = target
    state["sel_tgt"] = source

    result = state.get("result")
    if result and result.get("translated_text"):
        translated_text = result["translated_text"]
        state["input_text"] = translated_text
        state["txt_input"] = translated_text
        state["result"] = None
    return True
