# 專案規則 - 請嚴格遵守

## 檔案組織規則

### ❌ 禁止事項
1. **禁止在根目錄創建測試/調試檔案**
   - 不要創建 `test_*.py`, `debug_*.py`, `check_*.py`, `verify_*.py`
   - 不要創建任何 `.txt` 輸出檔案在根目錄

2. **禁止在根目錄創建臨時腳本**
   - 所有腳本都應該放在適當的目錄

### ✅ 正確的檔案位置

**正式腳本** → `scripts/`
- 資料處理腳本: `scripts/1_*.py`, `scripts/2_*.py` 等
- Neo4j 匯入腳本: `scripts/5_*.py`, `scripts/6_*.py` 等

**測試腳本** → `test/`
- 單元測試: `test/test_*.py`
- 整合測試: `test/integration_*.py`
- 探索性腳本: `test/explore_*.py`

**範例/工具** → 根目錄(僅限必要)
- 查詢範例: `example_queries.py`
- 工具腳本: `create_monitors_from_station_data.py`

**臨時調試** → `test/debug/` (創建後使用)
- 所有 debug_*.py
- 所有輸出 .txt 檔案

## 工作流程

### 開始工作前
1. 閱讀此規則
2. 確認檔案應該放在哪個目錄
3. 如果是調試,使用 `test/debug/` 目錄

### 創建檔案時
1. 先思考:這是什麼類型的檔案?
2. 選擇正確的目錄
3. 使用描述性的檔案名稱

### 完成工作後
1. 清理所有臨時檔案
2. 將有用的腳本移到正確位置
3. 更新文檔

## 命名規範

**正式腳本**: 有編號和清楚描述
- ✅ `1_extract_rivers_from_pdf.py`
- ❌ `extract.py`

**測試腳本**: 有 test_ 前綴
- ✅ `test/test_connection.py`
- ❌ `connection_test.py`

**調試腳本**: 放在 test/debug/
- ✅ `test/debug/debug_station_codes.py`
- ❌ `debug_station_codes.py` (在根目錄)

---

**記住**: 當您需要創建調試腳本時,請立即問自己:
"這個檔案應該放在哪裡?" 不是 "我現在可以快速創建它嗎?"
