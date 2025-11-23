# HydroGraph-TW Neo4j 資料匯入指南

> **台灣水文知識圖譜建置專案**

---

## 📋 目錄

1. [專案概述](#專案概述)
2. [資料結構](#資料結構)
3. [匯入腳本說明](#匯入腳本說明)
4. [執行步驟](#執行步驟)
5. [驗證與查詢](#驗證與查詢)
6. [常見問題](#常見問題)

---

## 專案概述

本專案將台灣水文資料匯入 Neo4j 圖資料庫,建立完整的知識圖譜,包含:

- **832條河川** + 階層關係
- **839個集水區** + 136個流域
- **826個測站** (242個水位測站 + 584個氣象測站)
- **多種關係** (支流、屬於、包含、監測、位於等)

---

## 資料結構

### 節點類型 (Nodes)

| 節點類型 | 標籤 | 數量 | 主要屬性 |
|---------|------|------|---------|
| 河川 | `River` | 832 | code, name, level, main_stream |
| 水系 | `WaterSystem` | 26 | name |
| 流域 | `Basin` | 136 | name, area_km2, watershed_count |
| 集水區 | `Watershed` | 839 | id, name, basin_name, area_m2 |
| 雨量測站 | `Station:Rainfall` | 242 | code, name, x_twd97, y_twd97, elevation |
| 水位測站 | `Station:WaterLevel` | 584 | code, name, x_twd97, y_twd97, elevation |

### 關係類型 (Relationships)

| 關係 | FROM | TO | 說明 | 數量 |
|------|------|-----|------|------|
| `IS_TRIBUTARY_OF` | River | River | 支流指向主流 | ~700 |
| `BELONGS_TO` | River | WaterSystem | 河川屬於水系 | ~800 |
| `PART_OF` | Watershed | Basin | 集水區屬於流域 | 839 |
| `CONTAINS_RIVER` | Watershed | River | 集水區包含河川 | ~2000 |
| `MONITORS` | Station | River | 測站監測河川 | 737 |
| `LOCATED_IN` | Station | Watershed | 測站位於集水區 | ~700 |

---

## 匯入腳本說明

### 腳本檔案

| 檔案名稱 | 功能 | 輸入資料 |
|---------|------|---------|
| `5_import_rivers_to_neo4j.py` | 匯入河川與水系 | `河川關係_完整版.xlsx` |
| `6_import_watersheds_to_neo4j.py` | 匯入集水區與流域 | `集水區分析報表.xlsx` |
| `7_import_stations_to_neo4j.py` | 匯入測站 (詳細資料) | `測站基本資料2025.xlsx` + `測站河川配對分析報表.xlsx` |
| `8_import_all_to_neo4j.py` | **一鍵匯入所有資料** | 上述所有檔案 |

### 各腳本功能詳解

#### 5_import_rivers_to_neo4j.py

**功能**:
1. 建立 River 節點 (832條河川)
2. 建立 WaterSystem 節點 (26個水系)
3. 建立 IS_TRIBUTARY_OF 關係 (河川階層)
4. 建立 BELONGS_TO 關係 (河川屬於水系)

**輸出**:
- River 節點屬性: `code`, `name`, `level`, `main_stream`, `seq_no`
- WaterSystem 節點屬性: `name`

#### 6_import_watersheds_to_neo4j.py

**功能**:
1. 建立 Basin 節點 (136個流域)
2. 建立 Watershed 節點 (839個集水區)
3. 建立 PART_OF 關係 (集水區屬於流域)
4. 建立 CONTAINS_RIVER 關係 (集水區包含河川)

**輸出**:
- Basin 節點屬性: `name`, `area_km2`, `watershed_count`, `river_count`
- Watershed 節點屬性: `id`, `name`, `basin_name`, `area_m2`, `river_count`

#### 7_import_stations_to_neo4j.py

**功能**:
1. 建立 WaterLevel 測站節點 (242個)
2. 建立 Weather 測站節點 (584個)
3. 建立 MONITORS 關係 (測站監測河川)
4. 建立 LOCATED_IN 關係 (測站位於集水區)

**特色**: 使用 `測站基本資料2025.xlsx` 的**詳細資料**:
- **第一個工作表**: 雨量測站 (242個, 18欄位)
- **第二個工作表**: 水位測站 (584個, 20欄位)
- **第三個工作表**: 地下水位測站 (不匯入)

包含完整資訊:
- 完整座標 (TWD97)
- 管理單位
- 設置年份
- 測站功能屬性 (現有/測設/預備/流量)

**輸出**:
- Rainfall 節點屬性: `code`, `name`, `type`, `river`, `watershed`, `elevation`, `x_twd97`, `y_twd97`, `city`, `address`, `management_unit`, 雨量功能屬性
- WaterLevel 節點屬性: `code`, `name`, `type`, `river`, `watershed`, `elevation`, `x_twd97`, `y_twd97`, `city`, `address`, `management_unit`, 流量功能屬性, 關聯雨量站

#### 8_import_all_to_neo4j.py (推薦)

**功能**: 一鍵執行完整匯入流程

**執行順序**:
1. 測試連線
2. 清空資料庫 (可選)
3. 匯入河川與水系
4. 匯入集水區與流域
5. 匯入測站資料
6. 顯示完整統計

---

## 執行步驟

### 前置準備

#### 1. 啟動 Neo4j

確保 Neo4j 已啟動並可連線:
- 預設位址: `bolt://localhost:7687`
- 預設帳號: `neo4j`
- 預設密碼: 請在腳本中修改

#### 2. 確認資料檔案存在

```bash
data/
├── 河川關係_完整版.xlsx
├── 集水區分析報表.xlsx
├── 測站基本資料2025.xlsx
└── 測站河川配對分析報表.xlsx
```

如果缺少這些檔案,請先執行:
```bash
python scripts/1_extract_rivers_from_pdf.py
python scripts/2_extract_stations.py
python scripts/3_generate_final_report.py
python scripts/4_extract_watersheds.py
```

#### 3. 安裝相依套件

```bash
# 啟用虛擬環境
hydro_env\Scripts\activate

# 確認已安裝 neo4j 套件
pip install neo4j pandas openpyxl
```

### 執行匯入

#### 方式一: 一鍵匯入 (推薦)

```bash
python scripts/8_import_all_to_neo4j.py
```

**互動提示**:
- 是否清空資料庫? (yes/no)
  - `yes`: 清空後重新匯入 (建議第一次使用)
  - `no`: 在現有資料上新增/更新

**執行時間**: 約 2-5 分鐘

#### 方式二: 分步執行

```bash
# 步驟 1: 匯入河川資料
python scripts/5_import_rivers_to_neo4j.py

# 步驟 2: 匯入集水區資料
python scripts/6_import_watersheds_to_neo4j.py

# 步驟 3: 匯入測站資料
python scripts/7_import_stations_to_neo4j.py
```

---

## 驗證與查詢

### 在 Neo4j Browser 中驗證

開啟 Neo4j Browser: http://localhost:7474

#### 查詢所有節點類型

```cypher
MATCH (n)
RETURN DISTINCT labels(n) as NodeType, count(n) as Count
ORDER BY Count DESC
```

#### 查詢所有關係類型

```cypher
MATCH ()-[r]->()
RETURN DISTINCT type(r) as RelationType, count(r) as Count
ORDER BY Count DESC
```

### 範例查詢

#### 1. 找出淡水河流域的所有測站

```cypher
MATCH (ws:WaterSystem {name: '淡水河'})
MATCH (r:River)-[:BELONGS_TO]->(ws)
MATCH (s:Station)-[:MONITORS]->(r)
RETURN ws.name as 水系,
       r.name as 河川,
       s.name as 測站,
       s.type as 測站類型
ORDER BY r.name, s.name
```

#### 2. 查詢某條河川的完整支流階層

```cypher
MATCH path = (tributary:River)-[:IS_TRIBUTARY_OF*]->(main:River {name: '淡水河'})
RETURN path
LIMIT 50
```

#### 3. 找出監測站最多的前10條河川

```cypher
MATCH (s:Station)-[:MONITORS]->(r:River)
WITH r, count(s) as station_count
ORDER BY station_count DESC
LIMIT 10
RETURN r.name as 河川名稱,
       r.level as 階層,
       r.main_stream as 主流水系,
       station_count as 測站數量
```

#### 4. 查詢某集水區的所有河川與測站

```cypher
MATCH (w:Watershed {name: '淡水河集水區'})
MATCH (w)-[:CONTAINS_RIVER]->(r:River)
OPTIONAL MATCH (s:Station)-[:MONITORS]->(r)
RETURN w.name as 集水區,
       r.name as 河川,
       collect(s.name) as 測站清單
```

#### 5. 找出有座標的測站並顯示在地圖上

```cypher
MATCH (s:Station)
WHERE s.x_twd97 IS NOT NULL AND s.y_twd97 IS NOT NULL
RETURN s.name as 測站名稱,
       s.type as 類型,
       s.x_twd97 as X座標,
       s.y_twd97 as Y座標,
       s.elevation as 高程
LIMIT 100
```

#### 6. 找出某測站上游的所有測站

```cypher
MATCH (s1:Station {name: '中正橋'})-[:MONITORS]->(r1:River)
MATCH (r2:River)-[:IS_TRIBUTARY_OF*]->(r1)
MATCH (s2:Station)-[:MONITORS]->(r2)
RETURN s1.name as 下游測站,
       r1.name as 下游河川,
       collect(DISTINCT s2.name) as 上游測站,
       collect(DISTINCT r2.name) as 上游河川
```

---

## 知識圖譜統計 (預期結果)

執行成功後,應該看到以下統計:

### 節點統計

```
River (河川): 832
WaterSystem (水系): 26
Basin (流域): 136
Watershed (集水區): 839
Station (測站總數): 826
  - Rainfall (雨量測站): 242
  - WaterLevel (水位測站): 584
```

### 關係統計

```
IS_TRIBUTARY_OF (河川支流關係): ~700
BELONGS_TO (河川屬於水系): ~800
PART_OF (集水區屬於流域): 839
CONTAINS_RIVER (集水區包含河川): ~2000
MONITORS (測站監測河川): 737
LOCATED_IN (測站位於集水區): ~700
```

### 資料完整度

```
有測站監測的河川: 181/832 (21.8%)
有座標的測站: ~800/826 (96.8%)
能配對到河川的測站: 737/826 (89.2%)
```

---

## 常見問題

### Q1: 連線錯誤 "Unable to connect to localhost:7687"

**解決方法**:
1. 確認 Neo4j 已啟動
2. 檢查 Neo4j 設定檔中的 bolt 連接埠
3. 確認防火牆沒有阻擋 7687 port

### Q2: 認證失敗 "Authentication failed"

**解決方法**:
- 修改腳本中的密碼: `NEO4J_PASSWORD = "your_password"`
- 或在 Neo4j Browser 重設密碼

### Q3: 找不到資料檔案

**解決方法**:
```bash
# 先執行資料提取腳本
python scripts/1_extract_rivers_from_pdf.py
python scripts/2_extract_stations.py
python scripts/3_generate_final_report.py
python scripts/4_extract_watersheds.py
```

### Q4: 執行到一半中斷怎麼辦?

**解決方法**:
- 如果是分步執行,可以從中斷的步驟繼續
- 如果使用 `8_import_all_to_neo4j.py`,建議選擇清空資料庫後重新執行

### Q5: 如何更新部分資料?

**解決方法**:
- Neo4j 使用 `MERGE` 語法,會自動更新現有節點
- 可以直接重新執行對應的匯入腳本
- 例如只更新測站: `python scripts/7_import_stations_to_neo4j.py`

### Q6: 記憶體不足怎麼辦?

**解決方法**:
1. 調整 Neo4j 記憶體設定 (neo4j.conf)
2. 分批匯入資料 (修改腳本使用批次處理)
3. 增加系統記憶體

---

## 下一步

### GraphRAG 應用開發

匯入完成後,您可以:

1. **建立向量資料庫**
   - 為河川、測站建立描述性文字
   - 使用 OpenAI/HuggingFace 產生向量嵌入
   - 儲存到 Chroma/Pinecone/Weaviate

2. **開發混合查詢 API**
   - GraphRAG: 從 Neo4j 查詢結構化關係
   - VectorRAG: 從向量 DB 檢索相似內容
   - 整合兩者提供完整答案

3. **整合即時資料**
   - 串接水利署 API 取得即時水位
   - 串接氣象署 API 取得降雨資料
   - 建立時間序列節點

4. **災害事件圖譜**
   - 新增 DisasterEvent 節點
   - 連結災害與河川、測站、集水區
   - 分析災害影響範圍

---

## 技術支援

- **專案 GitHub**: (請補充您的 repo 連結)
- **Neo4j 官方文件**: https://neo4j.com/docs/
- **Cypher 查詢語言**: https://neo4j.com/docs/cypher-manual/

---

**文件版本**: v1.0
**最後更新**: 2025-01-23
**作者**: HydroGraph-TW Team
