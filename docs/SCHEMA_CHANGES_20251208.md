# Neo4j Schema 變更記錄

## 2025-12-08 - DIFY 兼容格式更新

### 關係變更

為了確保與 DIFY Agent 工具的 Neo4j Procedure 一致，今天進行了以下 Schema 遷移：

#### 1. 河川支流關係：IS_TRIBUTARY_OF → FLOWS_INTO

**原始關係**：
```cypher
(支流:River)-[:IS_TRIBUTARY_OF]->(主流:River)
```

**新關係**：
```cypher
(支流:River)-[:FLOWS_INTO]->(主流:River)
```

**原因**：
- 統一為更直觀的「流向」語義
- 與 DIFY Agent 工具的 Neo4j Procedure 保持一致
- 簡化查詢邏輯（例如：查詢河川流向路徑）

**影響範圍**：
- 所有河川階層關係（約數千條）
- DIFY 工具：`getRiverFlowPath`, `getRiverTributaries`, `getUpstreamRivers`

#### 2. 測站監測關係：MONITORS → LOCATED_ON

**原始關係**：
```cypher
(測站:Station)-[:MONITORS]->(河川:River)
```

**新關係**：
```cypher
(測站:Station)-[:LOCATED_ON]->(河川:River)
```

**原因**：
- 更準確描述測站與河川的空間關係
- 「位於」比「監測」更符合物理位置的語義
- 與 DIFY Agent 工具的 Neo4j Procedure 保持一致

**影響範圍**：
- 所有測站-河川關係（約 826 個測站）
- DIFY 工具：`searchStation`, `getStationsByRiver`, `getStationsByWaterSystem`, `getStationsByCity`

---

### 實施方式

Schema 遷移在 `scripts/8_import_all_to_neo4j.py` 的 `migrate_schema()` 函數中自動執行：

```python
def migrate_schema(uri, user, password):
    """Schema 遷移: 轉換為 DIFY 兼容格式

    2025-12-08 更新：
    - IS_TRIBUTARY_OF → FLOWS_INTO (河川支流關係統一為流向)
    - MONITORS → LOCATED_ON (測站監測關係統一為位置)
    """
    # 1. IS_TRIBUTARY_OF → FLOWS_INTO
    MATCH (child:River)-[r:IS_TRIBUTARY_OF]->(parent:River)
    MERGE (child)-[:FLOWS_INTO]->(parent)
    DELETE r

    # 2. MONITORS → LOCATED_ON
    MATCH (s:Station)-[r:MONITORS]->(river:River)
    MERGE (s)-[:LOCATED_ON]->(river)
    DELETE r
```

---

### 相關文件更新

所有導入腳本已添加說明註解：

1. **scripts/5_import_rivers_to_neo4j.py**
   - `import_river_hierarchy()` 方法中添加註解
   - 說明創建的 IS_TRIBUTARY_OF 會被轉換為 FLOWS_INTO

2. **scripts/7_import_stations_to_neo4j.py**
   - `link_stations_to_rivers()` 方法中添加註解
   - `link_stations_to_rivers_by_attribute()` 方法中添加註解
   - 說明創建的 MONITORS 會被轉換為 LOCATED_ON

3. **scripts/8_import_all_to_neo4j.py**
   - `migrate_schema()` 函數中添加完整說明
   - 移除未使用的 `clean_dataframe` import

---

### DIFY 工具更新

同時更新了 5 個 DIFY Agent 工具，修復了完全失效的問題：

1. ✅ **getStationsByWaterSystem** - 水系測站查詢
2. ✅ **getRiversInWaterSystem** - 水系河川查詢
3. ✅ **getRiverFlowPath** - 河川流向查詢
4. ✅ **getStationsByCity** - 縣市測站查詢
5. ✅ **getStationStats** - 全台測站統計

所有改進版工具代碼保存在 `tests/improved_*.py`，並已部署到 DIFY。

---

### 專案清理

同時清理了 tests 目錄，刪除了 13 個臨時測試文件：

**刪除的檔案**：
- `test_dify_code.py`
- `improved_dify_code.py`
- `test_getStationsByWaterSystem.py`
- `test_getStationsByWaterSystem_diverse.py`
- `getRiverTributaries_formatted.py`
- `test_two_improved_tools.py`
- 7 個臨時 .txt 輸出文件

**保留的檔案**：
- `test_dify_agent.py` (主測試腳本)
- `test_report_analysis.md` (分析報告)
- 4 個 `improved_*.py` 工具 + 對應的 `*_test.txt` 輸出

---

### 查詢範例更新

**舊查詢**（已廢棄）：
```cypher
// 查詢蘭陽溪的支流
MATCH (tributary:River)-[:IS_TRIBUTARY_OF]->(main:River {name: '蘭陽溪'})
RETURN tributary.name

// 查詢測站監測的河川
MATCH (s:Station)-[:MONITORS]->(r:River)
RETURN s.name, r.name
```

**新查詢**（推薦）：
```cypher
// 查詢流入蘭陽溪的河川
MATCH (tributary:River)-[:FLOWS_INTO]->(main:River {name: '蘭陽溪'})
RETURN tributary.name

// 查詢測站位於的河川
MATCH (s:Station)-[:LOCATED_ON]->(r:River)
RETURN s.name, r.name
```

---

### 向後兼容性

⚠️ **重要**：此次變更**不保證向後兼容**

- 舊的關係名稱（IS_TRIBUTARY_OF, MONITORS）將被完全移除
- 所有依賴這些關係的查詢和應用都需要更新
- 建議在重新導入資料前備份現有 Neo4j 資料庫

---

### 驗證方式

Schema 遷移後會自動驗證：
1. 檢查是否有代碼不匹配的錯誤配對
2. 統計轉換的關係數量
3. 確保無資料遺失

執行完整導入：
```bash
hydro_env/Scripts/python.exe scripts/8_import_all_to_neo4j.py --auto-clear
```

---

**變更日期**：2025-12-08
**變更人員**：Claude Code
**測試狀態**：✅ 已完成
