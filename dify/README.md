# Dify Workflow - 台灣水文知識圖譜 GraphRAG

## 📋 目錄
- [系統架構](#系統架構)
- [快速開始](#快速開始)
- [詳細配置](#詳細配置)
- [測試範例](#測試範例)
- [常見問題](#常見問題)

---

## 🏗️ 系統架構

### 完整流程圖

```
使用者問題
    ↓
[LLM] 意圖解析
    ↓
[IF/ELSE] 條件路由
    ├─ safety_check → [Code] Neo4j GraphRAG
    └─ find_alerts  → [Code] 查詢所有測站
    ↓
[Code] TimeseriesRAG (並行查詢 WRA API)
    ↓
[Code] 風險分析
    ↓
[LLM] 生成自然語言回答
    ↓
回傳給使用者
```

### 核心節點說明

| 節點 | 類型 | 功能 | 關鍵技術 |
|-----|------|------|----------|
| **意圖解析** | LLM | 理解使用者問題,提取意圖和參數 | GPT-4o-mini, JSON 輸出 |
| **條件路由** | IF/ELSE | 根據意圖決定查詢路徑 | 條件分支 |
| **Neo4j GraphRAG** | Code | 從知識圖譜查詢河川流域測站 | Neo4j Cypher, 圖譜查詢 |
| **TimeseriesRAG** | Code | 並行查詢 WRA API 即時資料 | ThreadPoolExecutor, 並行加速 |
| **風險分析** | Code | 比對警戒值,計算風險等級 | 警戒邏輯 |
| **生成回答** | LLM | 自然語言輸出 | GPT-4o, 結構化 Prompt |

---

## 🚀 快速開始

### 步驟 1: 導入 Workflow

1. 登入你的 Dify 平台
2. 點擊「創建應用」→「工作流程」
3. 點擊右上角「導入 DSL」
4. 上傳 `workflow_graphrag.yml` 檔案
5. 完成導入!

### 步驟 2: 配置環境

#### 2.1 配置 Neo4j 連線

編輯以下節點中的 Neo4j 連線資訊:
- `graph_query_neo4j` (Code 節點)
- `find_all_stations` (Code 節點)

```python
# 修改這部分
driver = GraphDatabase.driver(
    "bolt://localhost:7687",  # ← 改成你的 Neo4j 位址
    auth=("neo4j", "12345678")  # ← 改成你的帳密
)
```

**建議**: 使用 Dify 環境變數管理敏感資訊

#### 2.2 配置 LLM

確認以下節點使用正確的 LLM:
- `parse_intent`: GPT-4o-mini (意圖解析,快速便宜)
- `generate_answer`: GPT-4o (生成回答,品質較好)

可以根據成本和效能需求調整模型。

### 步驟 3: 測試運行

在 Dify 測試介面輸入:
```
淡水河現在安全嗎?
```

預期輸出:
```
【風險評估】
目前 淡水河流域 處於「安全」狀態。

【監測概況】
系統正在監測 13 個測站,所有測站均正常運作。

【建議】
目前狀況良好,建議:
- 持續關注天氣預報
- 若有豪雨預報,請再次查詢
```

---

## ⚙️ 詳細配置

### 節點配置詳解

#### 1. 意圖解析 (LLM 節點)

**用途**: 理解使用者自然語言問題

**System Prompt**:
```
你是台灣水文監測系統的意圖解析器。

請分析使用者問題,提取以下資訊:
1. intent: 查詢意圖
   - safety_check: 查詢特定河川安全狀況
   - find_alerts: 查詢所有警戒測站
   - station_query: 查詢特定測站

2. river_name: 河川名稱 (如果有的話)
3. station_name: 測站名稱 (如果有的話)

請以 JSON 格式回答。
```

**輸入**: `{{#start.query#}}`
**輸出**: JSON 格式的意圖資料

**模型建議**: GPT-4o-mini (Temperature: 0.1)

---

#### 2. 條件路由 (IF/ELSE 節點)

**用途**: 根據意圖決定查詢路徑

**條件設定**:

| 條件 | 邏輯 | 目標節點 |
|-----|------|---------|
| `parse_intent.text` contains "safety_check" | AND | graph_query_neo4j |
| `parse_intent.text` contains "find_alerts" | AND | find_all_stations |

---

#### 3. Neo4j GraphRAG 查詢 (Code 節點)

**用途**: 從知識圖譜查詢河川流域的所有測站

**核心程式碼**:
```python
cypher = f"""
MATCH (r:River {{name: '{river_name}'}})-[:BELONGS_TO]->(ws:WaterSystem)
MATCH (all_rivers:River)-[:BELONGS_TO]->(ws)
MATCH (s:Station)-[:MONITORS]->(all_rivers)
RETURN DISTINCT s.code, s.name, s.type, labels(s)
LIMIT 20
"""
```

**這就是 GraphRAG 的核心!**
- 透過圖譜關係查詢整個流域
- 一次找出所有相關測站
- 這是 SQL 做不到的!

**輸入變數**:
- `intent_json`: 意圖解析結果

**輸出變數**:
- `stations`: 測站列表 (array[object])
- `count`: 測站數量 (number)
- `river_name`: 河川名稱 (string)

**依賴套件**:
- `neo4j`

---

#### 4. TimeseriesRAG 查詢 (Code 節點)

**用途**: 並行查詢 WRA API 取得即時監測資料

**核心程式碼**:
```python
with ThreadPoolExecutor(max_workers=15) as executor:
    futures = {}

    for station in stations:
        if "WaterLevel" in station["labels"]:
            future = executor.submit(query_water_level, station)
        elif "Rainfall" in station["labels"]:
            future = executor.submit(query_rainfall, station)

    # 收集結果
    for future in as_completed(futures):
        result = future.result()
        ...
```

**並行加速效果**:
- 逐一查詢: 10-15秒
- 並行查詢: 2-3秒
- **加速 5-7倍!**

**輸入變數**:
- `stations_json`: Neo4j 查詢結果

**輸出變數**:
- `water_levels`: 水位資料 (array[object])
- `rainfalls`: 雨量資料 (array[object])
- `total_queried`: 查詢成功數量 (number)

**依賴套件**:
- `requests`
- `concurrent.futures` (內建)

---

#### 5. 風險分析 (Code 節點)

**用途**: 比對警戒值,計算風險等級

**風險分級邏輯**:
```python
warning_ratio = 警戒測站數 / 總測站數

if warning_ratio >= 0.3:
    risk_level = "高風險"     # ≥30% 測站警戒
elif warning_ratio >= 0.1:
    risk_level = "中風險"     # ≥10% 測站警戒
elif warning_count > 0:
    risk_level = "低風險"     # 有警戒,但比例低
else:
    risk_level = "安全"       # 無警戒
```

**警戒標準**:
- 水位: `current_level >= alert_2` (二級警戒)
- 雨量: `rainfall_1h >= 50mm/hr` (豪雨)

**輸入變數**:
- `timeseries_json`: TimeseriesRAG 查詢結果

**輸出變數**:
- `risk_level`: 風險等級 (string)
- `warnings`: 警戒列表 (array[object])
- `warning_count`: 警戒數量 (number)
- `total_stations`: 總測站數 (number)

---

#### 6. 生成回答 (LLM 節點)

**用途**: 將結構化資料轉換成自然語言

**System Prompt**:
```
你是台灣水文監測系統的專業助手。

根據以下監測資料回答使用者問題:

河川/區域: {{#graph_query_neo4j.river_name#}}
風險等級: {{#risk_analysis.risk_level#}}
監測測站總數: {{#risk_analysis.total_stations#}} 個
警戒測站數量: {{#risk_analysis.warning_count#}} 個

請用自然、易懂、專業的語言回答。
```

**模型建議**: GPT-4o (Temperature: 0.7)

---

## 📝 測試範例

### 範例 1: 查詢特定河川

**輸入**:
```
淡水河現在安全嗎?
```

**流程**:
1. 意圖解析 → `safety_check`, `river_name: "淡水河"`
2. Neo4j GraphRAG → 找到 13 個測站
3. TimeseriesRAG → 查詢即時資料 (2.5秒)
4. 風險分析 → 低風險 (1/13 警戒)
5. 生成回答 → 自然語言輸出

**輸出**:
```
【風險評估】
目前 淡水河流域 處於「低風險」狀態。

【監測概況】
系統正在監測 13 個測站,其中 1 個測站發出警戒。

【警戒詳情】
1. 內湖雨量站 (基隆河)
   - 類型: 強降雨
   - 等級: 豪雨
   - 數值: 79.3mm/hr (警戒值: 50mm/hr)

【建議】
整體安全,但建議:
- 持續監控內湖站的雨量變化
- 若雨勢持續增強,可能影響基隆河水位
```

---

### 範例 2: 全域警戒查詢

**輸入**:
```
哪些河川有警戒?
```

**流程**:
1. 意圖解析 → `find_alerts`
2. 查詢所有測站 → 找到 50 個測站
3. TimeseriesRAG → 並行查詢
4. 風險分析 → 找出警戒測站
5. 生成回答 → 列出所有警戒

**輸出**:
```
【全台警戒概況】
目前全台共監測 50 個測站,其中 3 個測站發出警戒:

1. 內湖雨量站 (基隆河) - 豪雨 79.3mm/hr
2. 石門水庫 (大漢溪) - 二級警戒 水位 245.2m
3. 翡翠水庫 (新店溪) - 大雨 28.5mm/hr

【建議】
- 基隆河流域: 注意內湖地區積水
- 大漢溪流域: 石門水庫接近警戒,持續觀察
```

---

### 範例 3: 上游分析

**輸入**:
```
淡水河上游雨量如何?
```

**流程**:
1. 意圖解析 → `upstream_analysis`, `river_name: "淡水河"`
2. Neo4j GraphRAG → 查詢上游支流測站
3. TimeseriesRAG → 查詢雨量資料
4. 分析回答

---

## 🔧 進階配置

### 環境變數管理

建議將敏感資訊設為環境變數:

1. 在 Dify 中設定環境變數:
   - `NEO4J_URI`: bolt://localhost:7687
   - `NEO4J_USER`: neo4j
   - `NEO4J_PASSWORD`: your_password

2. 修改 Code 節點:
```python
import os

driver = GraphDatabase.driver(
    os.environ.get("NEO4J_URI"),
    auth=(os.environ.get("NEO4J_USER"), os.environ.get("NEO4J_PASSWORD"))
)
```

---

### 加入 VectorRAG (災害案例搜尋)

可以在「風險分析」和「生成回答」之間加入 **Knowledge 節點**:

1. 建立知識庫:
   - 上傳歷史災害報告
   - 索引災害案例

2. 加入 Knowledge 節點:
   - 查詢向量: 當前風險描述
   - 返回: 類似災害案例

3. 整合到回答:
```
根據歷史案例,類似情況曾在 2015年蘇迪勒颱風 發生...
```

---

### 效能優化

#### 1. 減少 API 請求次數

```python
# 在 TimeseriesRAG 節點中
LIMIT = 10  # 限制最多查詢 10 個測站

# 優先查詢重要測站
stations_sorted = sorted(stations, key=lambda x: priority(x), reverse=True)
stations_to_query = stations_sorted[:LIMIT]
```

#### 2. 加入快取機制

```python
import time

cache = {}
CACHE_TTL = 300  # 5分鐘快取

def get_cached_or_fetch(station_code):
    now = time.time()
    if station_code in cache:
        data, timestamp = cache[station_code]
        if now - timestamp < CACHE_TTL:
            return data

    # 查詢 API
    data = query_api(station_code)
    cache[station_code] = (data, now)
    return data
```

---

## ❓ 常見問題

### Q1: Neo4j 連線失敗怎麼辦?

**A**: 檢查以下項目:
1. Neo4j 是否啟動? (`systemctl status neo4j`)
2. 連線位址正確? (預設 `bolt://localhost:7687`)
3. 帳密正確?
4. 防火牆是否阻擋?

**測試連線**:
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
with driver.session() as session:
    result = session.run("RETURN 1")
    print(result.single()[0])  # 應該輸出 1
driver.close()
```

---

### Q2: WRA API 查詢失敗怎麼辦?

**A**: 可能原因:
1. 測站代號錯誤 (檢查 Neo4j 資料)
2. API 暫時無法連線
3. 網路問題

**解決方案**:
```python
# 加入重試機制
import time

def query_with_retry(url, max_retries=3):
    for i in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            return response.json()
        except Exception as e:
            if i == max_retries - 1:
                raise
            time.sleep(1)  # 等待1秒後重試
```

---

### Q3: Code 節點執行超時?

**A**: Dify Code 節點有執行時間限制 (通常 30-60秒)

**解決方案**:
1. 減少查詢的測站數量
2. 增加 `ThreadPoolExecutor` 的 `max_workers`
3. 降低 API timeout 時間
4. 將複雜邏輯改用 HTTP API

---

### Q4: 如何加入新的河川?

**A**: 在 Neo4j 中新增資料:
```cypher
// 新增河川
CREATE (r:River {
    name: '新河川',
    code: 'NEW001',
    level: 1
})

// 建立關係
MATCH (r:River {name: '新河川'})
MATCH (ws:WaterSystem {name: '某水系'})
CREATE (r)-[:BELONGS_TO]->(ws)
```

---

### Q5: 回答品質不好怎麼辦?

**A**: 優化 LLM Prompt:

1. **增加範例**:
```
以下是優質回答範例:

【範例 1】
風險評估: ...
監測概況: ...
```

2. **明確指令**:
```
請務必包含:
1. 風險等級 (高/中/低/安全)
2. 具體數據 (幾個測站,幾個警戒)
3. 實用建議 (民眾該怎麼做)
```

3. **調整 Temperature**:
- 0.3: 保守、一致
- 0.7: 平衡 (推薦)
- 1.0: 創意、多樣

---

## 📊 系統監控

### 效能指標

| 指標 | 目標值 | 監控方式 |
|-----|-------|---------|
| GraphRAG 查詢時間 | < 1秒 | Neo4j 日誌 |
| TimeseriesRAG 查詢時間 | < 3秒 | Code 節點輸出 |
| 總回應時間 | < 10秒 | Dify 監控面板 |
| API 成功率 | > 95% | 錯誤日誌 |

### 日誌監控

在 Code 節點中加入日誌:
```python
import logging

logger = logging.getLogger(__name__)

def main(args):
    logger.info(f"開始查詢,測站數: {len(stations)}")

    # 執行查詢
    ...

    logger.info(f"查詢完成,成功: {success_count}, 失敗: {fail_count}")
```

---

## 🚀 部署上線

### 檢查清單

- [ ] Neo4j 連線測試通過
- [ ] WRA API 查詢測試通過
- [ ] 所有測試範例通過
- [ ] LLM 模型配置正確
- [ ] 環境變數設定完成
- [ ] 錯誤處理機制就緒
- [ ] 效能測試達標

### 發布流程

1. 在 Dify 中點擊「發布」
2. 選擇發布管道:
   - API 端點
   - 網頁嵌入
   - Slack/Teams 整合
3. 配置訪問權限
4. 啟動!

---

## 📞 支援

如有問題,請聯繫:
- 專案負責人: [你的名字]
- Email: [your-email@example.com]
- 文件: 本 README.md

---

**恭喜!你已經在 Dify 上建立了完整的 GraphRAG 系統!** 🎉

這個系統結合了:
- ✅ GraphRAG (Neo4j 知識圖譜)
- ✅ TimeseriesRAG (WRA API 即時資料)
- ✅ 智能分析 (風險評估)
- ✅ LLM 自然語言輸出

**這才是真正有價值的動態監測系統!** 🚀
