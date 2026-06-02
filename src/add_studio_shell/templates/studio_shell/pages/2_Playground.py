from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from studio_shell.page_shell import page_shell
from studio_shell.shell_ui import format_extra_context, inject_style


st.set_page_config(page_title="Playground", page_icon="🎛️", layout="wide")
inject_style()

MOOD_OPTIONS = ["😀 開心", "😐 普通", "😢 低落"]


def render_main() -> str:
    st.markdown("#### 練習 1 · 心情儀表板")

    col1, col2 = st.columns(2)
    with col1:
        nickname = st.text_input("暱稱", key="playground_nickname", placeholder="接線測試用")
    with col2:
        mood = st.radio("今天心情", MOOD_OPTIONS, horizontal=True, key="playground_mood")

    energy = st.slider("能量", min_value=1, max_value=10, value=5, key="playground_energy")
    event = st.text_area(
        "今天發生一件事（一句話）",
        placeholder="例如：段考結束了",
        key="playground_event",
    )

    st.divider()
    st.markdown("#### 計數器（AI coding 小練習）")
    if "playground_count" not in st.session_state:
        st.session_state.playground_count = 0

    metric_col, btn_col = st.columns([2, 1])
    metric_col.metric("Count", st.session_state.playground_count)
    if btn_col.button("+1", use_container_width=True):
        st.session_state.playground_count += 1
        st.rerun()

    st.caption("試著請 Agent 在 `pages/2_Playground.py` 加一個「-1」按鈕。")

    st.divider()
    st.markdown("#### 給 Agent 的摘要")
    extra = format_extra_context(
        "Playground",
        暱稱=nickname or "（未填）",
        心情=mood,
        能量=f"{energy}/10",
        今日事件=event or "（未填）",
        計數器=st.session_state.playground_count,
    )
    st.code(extra, language="text")

    st.markdown("#### 右欄可以這樣問")
    st.markdown(
        """
- 「根據我的心情和能量，給我三個今晚可以放鬆的建議。」
- 「用鼓勵的語氣寫一段 50 字給我，不要說教。」
"""
    )
    return extra


page_shell(
    "Playground",
    "左欄設計 UI → 摘要傳給右欄 Agent。改左欄選項，右欄回答應跟著變。",
    render_main,
    page_name="Playground",
)
