#!/bin/bash
# 檢查是否在根目錄創建測試檔案

# 檢查最近的寫入操作
if echo "$PROMPT" | grep -E "(test|debug|check|verify).*\.py" | grep -v "scripts/" | grep -v "test/"; then
    echo "⚠️ 警告: 請將測試檔案放在 test/ 或 scripts/ 目錄中,不要放在根目錄"
    exit 1
fi
