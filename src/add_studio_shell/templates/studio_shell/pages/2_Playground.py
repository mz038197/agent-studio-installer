from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from studio_shell.page_shell import page_shell
from studio_shell.shell_ui import inject_style

st.set_page_config(page_title="Playground", page_icon="🎛️", layout="wide")
inject_style()

MOOD_OPTIONS = ["😀 開心", "😐 普通", "😢 低落"]


def render_main() -> str:
    st.markdown("#### 練習 1 · 心情儀表板")

    col1, col2 = st.columns(2)
    with col1:
        nickname = st.text_input("暱稱", key="playground_nickname", placeholder="例如：小明")
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
    st.markdown("#### 接線練習 · extra context")
    st.info(
        "右欄 Agent **看不到**左欄的 widget，只會收到你在 `render_main()` **最後 `return` 的字串**。"
        "請把左欄選擇組成摘要，傳給右欄。完整範例可對照 `pages/1_Home.py`。"
    )

    with st.expander("需要提示？接線三步驟", expanded=True):
        st.markdown(
            """
1. 在檔案上方加入：`from studio_shell.shell_ui import format_extra_context`
2. 在 `render_main()` 裡用 `format_extra_context("Playground", 心情=..., 能量=..., ...)` 組摘要
3. 用 `st.code(extra)` 顯示「給 Agent 的摘要」，並 **`return extra`**

接線骨架（請貼到本函式下方、取代最後的 `return ""`）：

```python
extra = format_extra_context(
    "Playground",
    暱稱=nickname or "（未填）",
    心情=mood,
    能量=f"{energy}/10",
    今日事件=event or "（未填）",
    計數器=st.session_state.playground_count,
)
st.code(extra, language="text")
return extra
```
"""
        )

    st.markdown("#### 左欄狀態預覽（尚未傳給 Agent）")
    st.caption("先確認 widget 有在運作；接線完成後，改由下方的「給 Agent 的摘要」顯示。")
    st.json(
        {
            "暱稱": nickname or "（未填）",
            "心情": mood,
            "能量": f"{energy}/10",
            "今日事件": event or "（未填）",
            "計數器": st.session_state.playground_count,
        }
    )

    st.markdown("#### 給 Agent 的摘要")
    st.code("（尚未接線 — 完成 extra context 後，這裡會顯示你的摘要）", language="text")

    st.markdown("#### 右欄可以這樣問")
    st.markdown(
        """
- 「根據我的心情和能量，給我三個今晚可以放鬆的建議。」
- 「用鼓勵的語氣寫一段 50 字給我，不要說教。」

**驗收：** 接線後，改心情或能量 → 用同一句話問右欄 → 回答應跟著變。
"""
    )

    # TODO: 練習 1 — 接上 extra context（參考 1_Home.py），再 return 摘要字串
    return ""


page_shell(
    "Playground",
    "練習把左欄狀態用 extra context 傳給右欄 Agent（請在本頁 `render_main` 完成接線）。",
    render_main,
    page_name="Playground",
)
