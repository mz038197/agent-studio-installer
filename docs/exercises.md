# Agent Studio 左欄練習題

左欄：設計 Streamlit UI，組出 **Agent 摘要**（extra_context）。  
右欄：用摘要問 Agent，回答應隨左欄狀態改變。

不知道要用哪個 Streamlit 元件時，先到 App 裡的 **UI 元件詞彙表** 頁面玩看看，再把元件名稱寫進 Prompt。

---

## 練習 0 · 接線確認（Home 頁）

**左欄：** 暱稱、今日目標  
**右欄示例：** 「用暱稱跟我打招呼，兩句話就好。」

**驗收：** 改暱稱 → 右欄回答跟著變。

---

## 練習 1 · 心情儀表板（Playground 頁）

**左欄：** 心情 radio、能量 slider、今日事件（UI 已提供）  
**你要做：** 用 Prompt 請右欄 Agent 修改 `pages/2_Playground.py`，把左欄資訊透過 Extra Context 串接到右欄（可對照 Home 頁範例）  
**右欄示例：** 「根據我的心情和能量，給我三個放鬆建議。」

**驗收：** 接線後，改心情或能量 → 建議內容不同；接線前右欄不會讀到左欄狀態。

---

## 練習 2 · 點餐助手：雙向 Agent App

這一題分成兩個小任務。  
先練「左欄影響右欄」，再挑戰「右欄影響左欄」。

### 練習 2A · 我選餐，Agent 幫我確認

**目標：** 建立一個點餐頁面，左欄用 UI 選點餐內容，再用 Extra Context 傳給右欄 Agent。

**左欄建議元件：**

- `selectbox`：主餐，例如牛肉麵、雞腿飯、滷肉飯
- `multiselect`：加點，例如蛋、青菜、飲料
- `checkbox`：不要香菜
- `text_area`：備註
- `code` 或 `json`：顯示「給 Agent 的摘要」

**你可以對右欄 Agent 說：**

```text
請新增 `pages/4_Order.py`（必須 `數字_名稱.py`，不可用 `Order.py`）與 `data/order.json`，做一個點餐助手。

左欄要有：
- 主餐選擇
- 加點選擇
- 不要香菜 checkbox
- 備註
- 訂單摘要

請用 Extra Context 把左欄目前訂單傳給右欄 Agent，並顯示「給 Agent 的摘要」。
參考 `pages/1_Home.py`；不要改 `app.py`、`studio_shell/agent_panel.py` 或 `studio_shell/page_shell.py`。建完請 Rerun。
```

**驗收：** 改左欄主餐或加點後，在右欄問「像店員一樣唸出我的訂單摘要」，回答應該跟著改變。

### 練習 2B · 我說餐，左欄幫我整理

**目標：** 使用者在右欄用自然語言點餐，Agent 把訂單寫入 `studio_shell/workspace/order.json`，左欄讀取這個檔案並顯示目前訂單。

**你可以對右欄 Agent 說：**

```text
請改進 `pages/4_Order.py`，讓右欄 Agent 可以根據我的聊天內容更新左欄訂單。

當我在右欄說「我要牛肉麵，加蛋，不要香菜」時，請把訂單整理到：

`studio_shell/workspace/order.json`

JSON 欄位包含：
- main：主餐
- addons：加點
- no_cilantro：是否不要香菜
- note：備註

左欄頁面要讀取 `order.json`，並顯示目前訂單摘要。
請不要修改 `studio_shell/agent_panel.py` 或 `studio_shell/page_shell.py`。
```

**驗收：** 在右欄說「我要牛肉麵，加蛋，不要香菜」後，重新整理或切回點餐頁，左欄應顯示牛肉麵、加蛋、不要香菜。

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
6. 自訂頁檔名符合 `N_xxx.py`、Rerun 後側欄看得到？

---

## 好 prompt / 爛 prompt

**爛：** 幫我做一個很厲害的 App  

**好：** 在 `pages/2_Playground.py` 加 `-1` 按鈕；不要改 `studio_shell/agent_panel.py`。
