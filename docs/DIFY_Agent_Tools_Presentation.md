# 水文圖資知識庫工具介紹

## 一、前言

### 專案目標
建立台灣水文圖資知識庫，整合測站、河川、水系等資料，透過自然語言問答方式查詢水文資訊。

### 技術架構
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   使用者    │────▶│  DIFY Agent │────▶│   Neo4j     │
│  自然語言   │     │    + LLM    │     │  圖資料庫   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  水利署 API │     │  Neo4j 預存 │
                    │  (觀測資料) │     │    程序     │
                    └─────────────┘     └─────────────┘
```

### Neo4j 預存程序（類似 SQL Stored Procedure）

工具封裝為 Neo4j 預存程序，DIFY Agent 直接呼叫：

```cypher
-- Agent 呼叫方式（類似 SQL: EXEC sp_searchStation '中正橋'）
CALL custom.searchStation("中正橋")
CALL custom.getStationsByRiver("蘭陽溪")
CALL custom.getRiverTributaries("蘭陽溪")
```

**建立方式**：使用 APOC 套件的 `apoc.custom.installProcedure()`

**優點**：
- 封裝複雜 Cypher 邏輯，Agent 只需傳參數
- 動態註冊，易於維護更新
- 參數化查詢，防止注入攻擊

---

## 二、圖資結構（Graph Schema）

### 節點類型（Nodes）

| 節點 | 標籤 | 說明 | 數量 |
|------|------|------|------|
| Station | Rainfall / WaterLevel | 測站（雨量站/水位站） | 826 |
| River | - | 河川 | 數百條 |
| WaterSystem | - | 水系 | 數十個 |
| Watershed | - | 集水區 | - |

### 關係類型（Relationships）

```
┌──────────┐                    ┌──────────┐
│ Station  │───LOCATED_ON──────▶│  River   │
│  測站    │                    │   河川   │
└──────────┘                    └────┬─────┘
      │                              │
      │                              │ BELONGS_TO
      │ LOCATED_IN                   │
      ▼                              ▼
┌──────────┐                    ┌──────────┐
│Watershed │                    │WaterSystem│
│  集水區  │                    │   水系   │
└──────────┘                    └──────────┘

河川流向關係：
┌──────────┐                    ┌──────────┐
│  支流    │───FLOWS_INTO──────▶│  主流    │
│ (上游)   │                    │  (下游)  │
└──────────┘                    └──────────┘
```

### 關係說明

| 關係 | 方向 | 說明 |
|------|------|------|
| `LOCATED_ON` | Station → River | 測站位於河川上 |
| `LOCATED_IN` | Station → Watershed | 測站位於集水區內 |
| `BELONGS_TO` | River → WaterSystem | 河川屬於水系 |
| `FLOWS_INTO` | River → River | 河川流入（上游→下游） |

---

## 三、九大工具總覽

### 工具分類

```
九大工具
├── 測站查詢類（5 個）
│   ├── 1. searchStation          - 模糊搜尋測站
│   ├── 2. getStationsByRiver     - 河川沿線測站
│   ├── 3. getStationsByWaterSystem - 水系內測站
│   ├── 4. getStationsByCity      - 縣市內測站
│   └── 5. getStationStats        - 測站統計
│
├── 河川查詢類（3 個）
│   ├── 6. getRiverTributaries    - 河川支流（遞迴）
│   ├── 7. getRiversInWaterSystem - 水系內河川
│   └── 8. getRiverFlowPath       - 河川流向路徑
│
└── 觀測資料類（1 個）
    └── 9. searchStationObservation - 歷史觀測資料
```

---

## 四、測站查詢類工具（4 個）

### 1. searchStation - 模糊搜尋測站

**功能**：輸入站名或站號，模糊搜尋測站詳細資料

**核心語法**：
```cypher
-- 1. 全文索引搜尋（一次搜尋 5 個欄位）
CALL db.index.fulltext.queryNodes("stationSearch", $keyword)
YIELD node AS s, score  -- 返回相關性分數

-- 2. 額外模糊處理（移除「站」字）
WHERE s.name CONTAINS $keyword
   OR s.code CONTAINS $keyword
   OR s.name CONTAINS replace($keyword, '站', '')

-- 3. 關聯河川資訊
OPTIONAL MATCH (s)-[:LOCATED_ON]->(r:River)

-- 4. 按相關性分數排序
RETURN s.code, s.name, s.city, r.name AS river
ORDER BY score DESC
```

**類 RAG 模糊搜尋機制**：

| 特性 | RAG（向量搜尋） | Neo4j Fulltext Index |
|------|----------------|---------------------|
| 原理 | Embedding 向量相似度 | 關鍵字 BM25 演算法 |
| 模糊匹配 | ✅ 語意相似 | ✅ 文字相似 |
| 相關性排序 | ✅ cosine similarity | ✅ score 分數 |
| 多欄位搜尋 | ❌ 需分別建索引 | ✅ 一次搜多欄位 |
| 即時性 | 需重建向量 | 即時更新 |

**效果展示**：
- 輸入「牛鬥站」→ 找到「牛鬥(1)」「牛鬥(3)」
- 輸入「中正橋」→ 找到台北、台南、嘉義的中正橋（按相關性排序）

**技術亮點**：
- 使用 Fulltext Index 實現類 RAG 模糊搜尋
- 自動計算相關性分數並排序
- 同時搜尋站名、站號、縣市、河川等多個欄位
- 自動移除「站」「測站」等後綴
- 比傳統 SQL LIKE 查詢更智慧

---

### 2. getStationsByRiver - 河川沿線測站

**功能**：列出某河川上的所有測站

**核心語法**：
```cypher
MATCH (s:Station)-[:LOCATED_ON]->(r:River)
WHERE r.name = $riverName
   OR r.name STARTS WITH $riverName           -- 前綴匹配
   OR r.name STARTS WITH ($riverName + '(')   -- 半形括號
   OR r.name STARTS WITH ($riverName + '（')  -- 全形括號
   OR r.name STARTS WITH ($riverName + '【')  -- 方括號
RETURN s.name, s.type, r.name AS river
```

**技術亮點**：
- 支援河川別名（如「馬太鞍溪【馬鞍溪】」）
- 支援三種括號格式：`()` `（）` `【】`

---

### 3. getStationsByWaterSystem - 水系內測站

**功能**：列出某水系/流域內所有河川的測站

**核心語法**：
```cypher
MATCH (s:Station)-[:LOCATED_ON]->(r:River)-[:BELONGS_TO]->(ws:WaterSystem)
WHERE ws.name = $waterSystemName
   OR ws.name = replace($waterSystemName, '水系', '')
   OR ws.name = replace($waterSystemName, '流域', '')
RETURN s.name, s.type, r.name AS river
```

**技術亮點**：
- 兩層關係查詢：測站→河川→水系
- 同義詞處理：「水系」=「流域」

---

### 4. getStationsByCity - 縣市內測站

**功能**：列出某縣市的所有測站

**核心語法**：
```cypher
MATCH (s:Station)
WHERE s.city CONTAINS $city
   OR replace(s.city, '臺', '台') CONTAINS $city
WITH s, CASE WHEN s:Rainfall THEN "雨量" ELSE "水位" END AS stationType
WHERE $filterType = "全部" OR stationType = $filterType
RETURN s.name, stationType, s.city
```

**技術亮點**：
- 臺/台自動轉換
- 支援類型篩選（雨量/水位/全部）

---

## 五、河川網絡空間邏輯（Graph 能力展示）

> **設計重點**：強調 SQL 做不到的事（遞迴查詢、路徑追蹤）

### SQL vs Graph 遞迴查詢比較

| 需求 | SQL 做法 | Graph 做法 |
|------|----------|-----------|
| 查一層支流 | JOIN 一次 | `[:FLOWS_INTO]` |
| 查兩層支流 | JOIN 兩次 | `[:FLOWS_INTO*2]` |
| 查 N 層支流 | 寫 N 個 JOIN 或 CTE 遞迴 | `[:FLOWS_INTO*1..N]` |
| 不知道幾層 | 😱 無法處理 | `[:FLOWS_INTO*]` 自動追蹤 |

---

### 6. getRiverTributaries - 遞迴支流查詢

**功能**：列出某河川的所有上游支流，自動計算層級

**核心語法**：
```cypher
MATCH (main:River) WHERE main.name = $riverName
MATCH (tributary:River)-[:FLOWS_INTO*1..10]->(main)
WITH tributary, main,
     tributary.level - main.level AS relativeLevel
RETURN tributary.name,
       CASE relativeLevel
           WHEN 1 THEN '支流'
           WHEN 2 THEN '二級支流'
           WHEN 3 THEN '三級支流'
           ELSE '四級支流'
       END AS levelName
ORDER BY relativeLevel, tributary.name
```

**技術亮點**：
- **遞迴語法**：`[:FLOWS_INTO*1..10]` 一行搞定 1~10 層關係追蹤
- **相對層級**：動態計算支流相對於查詢主流的層級差
- **分組呈現**：依 levelName 分組顯示（支流 → 二級支流 → 三級支流）

**河川別名處理**：
```cypher
WHERE r.name = $riverName
   OR r.name STARTS WITH ($riverName + '(')   -- 半形括號
   OR r.name STARTS WITH ($riverName + '（')  -- 全形括號
   OR r.name STARTS WITH ($riverName + '【')  -- 方括號
```
- 效果：輸入「馬太鞍溪」→ 自動匹配「馬太鞍溪【馬鞍溪】」

---

### 7. getRiversInWaterSystem - 水系內河川清單

**功能**：列出某水系內的所有河川及其層級關係

**核心語法**：
```cypher
MATCH (r:River)-[:BELONGS_TO]->(ws:WaterSystem)
WHERE ws.name = $waterSystemName
OPTIONAL MATCH (r)-[:FLOWS_INTO]->(downstream:River)
RETURN r.name,
       downstream.name AS flowsInto,
       CASE r.level
           WHEN 1 THEN '主流'
           WHEN 2 THEN '支流'
           WHEN 3 THEN '二級支流'
           ELSE '三級支流'
       END AS levelName
ORDER BY r.level, r.name
```

**技術亮點**：
- **絕對層級**：使用預先計算的 `r.level` 屬性
- **流向資訊**：`OPTIONAL MATCH` 顯示每條河流入的下游河川

---

### 8. getRiverFlowPath - 流向路徑追蹤

**功能**：追蹤河川從源頭到出海口的完整路徑

**核心語法**：
```cypher
MATCH (start:River) WHERE start.name = $riverName
MATCH path = (start)-[:FLOWS_INTO*0..10]->(end:River)
WHERE NOT (end)-[:FLOWS_INTO]->()  -- 終點：無下游的河川
WITH [node IN nodes(path) | node.name] AS riverPath
RETURN riverPath
```

**技術亮點**：
- **路徑追蹤**：`*0..10` 包含起點，自動追蹤到終點
- **終點判斷**：`NOT (end)-[:FLOWS_INTO]->()` 找到無出流的河川（入海口）
- **路徑展開**：`nodes(path)` 取得完整路徑

**效果展示**：
```
輸入：番社坑溪
輸出：番社坑溪 → 宜蘭河 → 蘭陽溪
```

---

## 六、資料整合與統計（API 能力展示）

> **設計重點**：展示系統的擴充性，整合外部 API 與聚合統計

---

### 9. searchStationObservation - 歷史觀測資料

**功能**：查詢測站的歷史觀測資料（雨量、水位、流量）

**實作方式**：DIFY CODE（Python）+ 水利署 API

**處理流程**：
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  使用者輸入  │────▶│ Agent 解析  │────▶│  水利署 API │
│「去年五月」  │     │ → 2024-05   │     │  取得數據   │
└─────────────┘     └─────────────┘     └─────────────┘
```

**API 來源**：
| 資料類型 | API 端點 |
|---------|---------|
| 雨量 | `https://gweb.wra.gov.tw/HydroInfo/StDataInfo/StDataInfo?RA&{站碼}` |
| 水位 | `https://gweb.wra.gov.tw/HydroInfo/StDataInfo/StDataInfo?LE&{站碼}` |

**語意時間解析**：
| 使用者輸入 | 自動轉換 |
|-----------|---------|
| 「去年」 | 2024 |
| 「今年五月」 | 2025-05 |
| 「上個月」 | 2025-11 |

---

### 5. getStationStats - 多維度統計分析

**功能**：統計全台測站數量，按縣市和類型分組

**核心語法**：
```cypher
MATCH (s:Station)
WITH CASE WHEN s:Rainfall THEN "雨量" ELSE "水位" END AS stationType,
     s.city AS city,
     count(*) AS cnt
WITH collect({type: stationType, city: city, count: cnt}) AS details,
     sum(CASE WHEN stationType = "雨量" THEN cnt ELSE 0 END) AS rainfallTotal,
     sum(CASE WHEN stationType = "水位" THEN cnt ELSE 0 END) AS waterLevelTotal
RETURN rainfallTotal, waterLevelTotal, details
```

**技術亮點**：
- **聚合統計**：`collect()` + `sum()` 一次查詢完成多維度統計
- **條件計數**：`CASE WHEN` 動態分類
- **結構化輸出**：直接返回 JSON 格式，Agent 可直接使用

**效益**：取代人工 Excel 統計，即時產出各縣市/各類型測站分佈表

---

## 七、技術亮點總結

| 問題 | 傳統做法 | 本專案解法 | 效果 |
|------|----------|-----------|------|
| 用戶輸入不精確 | SQL LIKE 精確比對，找不到 | Fulltext Index + BM25 排序 | 「牛鬥站」→ 找到「牛鬥(1)」 |
| 河川有別名 | 需維護對照表 | 動態解析 `()（）【】` 括號 | 「馬太鞍溪」→ 匹配「馬太鞍溪【馬鞍溪】」 |
| 支流層級不固定 | 寫死 JOIN 幾層 | 遞迴查詢 `*1..10` | 自動追蹤 1~10 層支流 |
| 臺/台混用 | 建兩筆資料或對照表 | 即時轉換 `replace()` | 「台北」=「臺北」 |
| 水系/流域混稱 | 建同義詞表 | 查詢時動態 replace | 「蘭陽溪流域」=「蘭陽溪水系」 |
| 統計需多次查詢 | 多個 SQL + 程式彙整 | Cypher `collect()` 一次完成 | 單一查詢返回完整統計 |

---

## 八、上周報告修正

### 1. 水系與河川測站數量差異

**問題**：為何「蘭陽溪水系測站」比「蘭陽溪測站」多？

**解答**：
- `getStationsByRiver` - 只查詢**單一河川**上的測站
- `getStationsByWaterSystem` - 查詢**整個水系所有河川**的測站

```
蘭陽溪水系
├── 蘭陽溪（主流）     ← getStationsByRiver 只查這條
├── 宜蘭河（支流）     ┐
├── 羅東溪（支流）     │← getStationsByWaterSystem
├── 冬山河（支流）     │  包含所有這些河川
└── 其他支流...        ┘
```

### 2. POC 範圍：蘭陽溪水系

本次 POC 以**蘭陽溪水系**為驗證範圍，涵蓋：
- 主流：蘭陽溪
- 主要支流：宜蘭河、羅東溪、冬山河等
- 測站類型：雨量站、水位站

### 3. 名詞修正：海拔 → 高程

測站屬性欄位 `elevation` 統一使用「**高程**」一詞，符合水利專業術語。

### 4. 測站樹狀呈現方式

河川支流查詢結果改為按 `levelName` 分組呈現：

```
蘭陽溪支流（共 X 條）
├── 支流（一級）
│   ├── 宜蘭河
│   ├── 羅東溪
│   └── 冬山河
├── 二級支流
│   ├── xxx溪
│   └── xxx溪
└── 三級支流
    └── xxx溪
```

### 5. 整合觀測資料 API

新增 `searchStationObservation` 工具，整合水利署 API：
- 支援查詢歷史雨量、水位、流量資料
- 支援相對日期（去年、今年、上個月）
- 自動解析測站代碼並呼叫對應 API

### 6. 管理單位與縣市查詢

**現狀**：透過 `searchStation` 工具即可查詢，輸出欄位包含：

| 欄位 | 說明 | 範例 |
|------|------|------|
| `city` | 縣市 | 臺北市 |
| `managementUnit` | 管理單位 | 第十河川分署 |
| `address` | 地址 | 臺北市中正區水源路... |

**不需新增工具**，現有 searchStation 已滿足需求。

### 7. 複合條件查詢修正

**問題**：「花蓮縣河川雨量有哪些」無法正確回應

**解決方式**：透過 PROMPT 調優
- 明確工具選擇邏輯：當問題包含「縣市 + 類型」時，使用 `getStationsByCity`
- 重置對話記憶，避免上下文干擾

**驗證結果**：
- ❌ 修正前：「花蓮縣河川雨量有哪些」→ 無回應
- ✅ 修正後：「花蓮縣河川雨量有哪些」→ 正確回傳 21 個雨量站

---

## 九、Demo 展示

| # | 工具 | 問題範例 |
|---|------|----------|
| 1 | searchStation | 「中正橋雨量站」 |
| 2 | getStationsByRiver | 「馬太鞍溪有哪些測站？」 |
| 3 | getStationsByWaterSystem | 「蘭陽溪水系有哪些測站？」 |
| 4 | getStationsByCity | 「宜蘭縣有幾個雨量站？」 |
| 5 | getStationStats | 「哪個縣市的測站最多？」 |
| 6 | getRiverTributaries | 「蘭陽溪有哪些支流？」 |
| 7 | getRiversInWaterSystem | 「蘭陽溪水系有哪些河川？」 |
| 8 | getRiverFlowPath | 「冬山河流到哪裡？」 |
| 9 | searchStationObservation | 「中正橋 2023 年雨量資料」 |

---

## 十、Q&A

歡迎提問！
