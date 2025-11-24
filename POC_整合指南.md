# 台灣水文 GraphRAG 系統 - POC 整合指南

## 系統架構

```
台灣水文 GraphRAG 系統
│
├─ [1] Neo4j 知識圖譜 ✅ (已完成)
│   └─ 831 條河川, 826 個測站, 839 個集水區
│
├─ [2] WRA 即時監測工具 ⚙️ (本文件實作)
│   └─ dify_tools/wra_realtime_tool.py
│
├─ [3] 災害知識庫 📚 (本文件建立)
│   ├─ knowledge_base/災害案例.md
│   └─ knowledge_base/防災手冊.md
│
└─ [4] DIFY Agent 🤖 (需整合)
    ├─ 靜態查詢 → Neo4j (neo4j_query 工具)
    ├─ 即時查詢 → WRA 工具 (HTTP API)
    └─ 知識問答 → 知識庫 RAG
```

---

## 整合步驟

### 步驟 1: 啟動 WRA 工具 API

```bash
cd d:/Project/HydroGraph-TW
hydro_env/Scripts/python.exe dify_tools/wra_realtime_tool.py
```

**驗證:**
```bash
curl -X POST http://localhost:5000/query_realtime \
  -H "Content-Type: application/json" \
  -d '{"station_name": "中山橋"}'
```

### 步驟 2: 在 DIFY 註冊 WRA 工具

1. 進入 DIFY 後台
2. 工具 → 新增自訂工具 → HTTP API
3. 設定:
   - **名稱**: query_realtime_data
   - **URL**: http://localhost:5000/query_realtime
   - **方法**: POST
   - **參數**:
     - station_name (string, required)
   - **描述**: "查詢測站即時監測資料"

### 步驟 3: 建立 DIFY 知識庫

1. 進入 DIFY 後台
2. 知識庫 → 新增知識庫 → "水文災害知識庫"
3. 上傳文件:
   - `knowledge_base/災害案例.md`
   - `knowledge_base/防災手冊.md`
4. 選擇嵌入模型 (例如: text-embedding-ada-002)
5. 開始向量化

### 步驟 4: 更新 DIFY Agent Prompt

```markdown
# 台灣水文監測助手

你有以下能力:

1. **靜態查詢** (neo4j_query 工具)
   - 測站基本資訊
   - 河川拓撲關係
   - 流域統計

2. **即時監測** (query_realtime_data 工具)
   - 測站即時水位/雨量
   - 警戒狀態
   - 更新時間

3. **災害知識** (知識庫 RAG)
   - 歷史災害案例
   - 防災應變手冊
   - 測站維護紀錄

## 查詢邏輯

當用戶詢問:
- "中山橋的資料" → 先查 Neo4j (基本資訊) → 再查即時資料
- "淡水河曾發生哪些災害" → 查知識庫
- "測站雷擊怎麼處理" → 查知識庫 (防災手冊)
```

---

## 使用範例

### 範例 1: 綜合查詢
**用戶**: "中山橋現在安全嗎?"

**Agent 執行:**
1. 呼叫 `neo4j_query` 取得中山橋基本資訊
2. 呼叫 `query_realtime_data` 取得即時水位
3. 查知識庫找警戒標準
4. 綜合回答: "中山橋目前水位 2.3m,低於二級警戒 2.5m,狀態安全"

### 範例 2: 災害查詢
**用戶**: "淡水河流域歷年有哪些重大災害?"

**Agent 執行:**
1. 查知識庫 (災害案例.md)
2. 回答: "2024年颱風凱米、2023年豪雨事件..."

### 範例 3: 防災諮詢
**用戶**: "高海拔測站容易受什麼災害?"

**Agent 執行:**
1. 查知識庫 (防災手冊.md)
2. 回答: "雷擊、土石流,建議加強防雷設施..."

---

## 測試清單

### ✅ 基本功能測試
- [ ] Neo4j 查詢測站基本資訊
- [ ] Neo4j 查詢河川拓撲
- [ ] WRA 工具查詢即時資料
- [ ] 知識庫 RAG 查詢災害案例

### ✅ 整合測試
- [ ] 綜合查詢 (靜態+即時)
- [ ] 災害風險分析 (圖譜+知識庫)
- [ ] 防災建議 (即時資料+知識庫)

### ✅ 壓力測試
- [ ] 連續 10 次查詢
- [ ] 並發查詢 (5 個用戶)
- [ ] 錯誤處理 (測站不存在)

---

## 擴展建議

### 短期 (1 週)
- ✅ 完成基本整合
- ✅ 測試主要功能
- ✅ 準備 Demo

### 中期 (1 個月)
- 🔄 真實 WRA API 整合 (若可用)
- 🔄 加入更多災害案例
- 🔄 NeoDash 儀表板

### 長期 (3 個月)
- 🔄 歷史資料分析
- 🔄 災害預測模型
- 🔄 WebSocket 即時推播

---

## 常見問題

### Q: WRA API 無法使用怎麼辦?
A: 目前使用模擬資料,足以展示概念。未來可整合其他公開 API。

### Q: 知識庫如何更新?
A: 在 DIFY 後台直接上傳新文件,系統會自動重新向量化。

### Q: 如何客製化 Agent 回答?
A: 調整 Agent Prompt 中的"查詢邏輯"和"回答格式"部分。

---

## 部署清單

### 開發環境
- [x] Neo4j 資料庫
- [x] Python 虛擬環境 (hydro_env)
- [x] WRA 工具 API (Flask)
- [ ] DIFY 平台設定

### 生產環境 (未來)
- [ ] Neo4j 雲端部署
- [ ] WRA 工具容器化 (Docker)
- [ ] DIFY 正式版部署
- [ ] 前端整合

---

**這就是一個完整的 GraphRAG POC!** 🎉

結合了:
- ✅ 知識圖譜 (結構化資料)
- ✅ 即時監測 (動態資料)
- ✅ 知識庫 (非結構化知識)
- ✅ LLM Agent (智能推理)
