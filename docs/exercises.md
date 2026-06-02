# Agent Studio 左欄練習題

左欄：設計 Streamlit UI，組出 **Agent 摘要**（extra_context）。  
右欄：用摘要問 Agent，回答應隨左欄狀態改變。

---

## 練習 0 · 接線確認（Home 頁）

**左欄：** 暱稱、今日目標  
**右欄示例：** 「用暱稱跟我打招呼，兩句話就好。」

**驗收：** 改暱稱 → 右欄回答跟著變。

---

## 練習 1 · 心情儀表板（Playground 頁）

**左欄：** 心情 radio、能量 slider、今日事件（UI 已提供）  
**你要做：** 在 `pages/2_Playground.py` 的 `render_main()` 用 `format_extra_context` 組摘要並 `return`（對照 Home 頁範例）  
**右欄示例：** 「根據我的心情和能量，給我三個放鬆建議。」

**驗收：** 接線後，改心情或能量 → 建議內容不同；接線前右欄不會讀到左欄狀態。

---

## 練習 2 · 點餐助手

**左欄：** multiselect 主餐 / 加點、checkbox 不要香菜、訂單摘要  
**extra_context 示例：**

```json
{"page":"點餐","main":["麵"],"addons":["蛋"],"no_cilantro":true}
```

**右欄示例：** 「像店員一樣唸出訂單摘要。」

---

## 練習 3 · 學習小助手

**左欄：** 科目、程度、卡關描述  
**右欄示例：** 「用生活例子解釋，100 字內，不要直接給作業答案。」

---

## 練習 4 · 故事接龍

**左欄：** 世界觀、個性、故事 textarea（可越寫越長）  
**右欄示例：** 「接寫 3 句，維持原本語氣。」

---

## 左欄設計檢查表

1. 至少 2 種 widget？
2. 有「給 Agent 的摘要」區（`st.code`）？
3. 摘要含頁面名稱 + 使用者選擇？
4. 改左欄 → 右欄回答會變？
5. prompt 有寫規則（語氣、長度）？

---

## 好 prompt / 爛 prompt

**爛：** 幫我做一個很厲害的 App  

**好：** 在 `pages/2_Playground.py` 加 `-1` 按鈕；不要改 `studio_shell/agent_panel.py`。
