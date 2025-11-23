# -*- coding: utf-8 -*-
"""讀取集水區 DBF 檔案（不需要 geopandas）"""
import pandas as pd
from dbfread import DBF

print("=" * 80)
print("讀取集水區屬性資料 (DBF)")
print("=" * 80)

# 讀取 DBF 檔案
dbf_path = 'file/110年度全臺839子集水區範圍圖_UTF8.dbf'
table = DBF(dbf_path, encoding='utf-8')

# 轉換為 DataFrame
df = pd.DataFrame(iter(table))

print(f"\n集水區數量: {len(df)}")
print(f"\n欄位名稱:")
for i, col in enumerate(df.columns):
    print(f"  [{i}] {col} - {df[col].dtype}")

print(f"\n前10筆資料:")
print(df.head(10).to_string())

print(f"\n統計資訊:")
print(f"  BASIN_ID 唯一值數量: {df['BASIN_ID'].nunique()}")
print(f"  WS_ID 唯一值數量: {df['WS_ID'].nunique()}")
print(f"  BASIN_NAME 範例: {df['BASIN_NAME'].unique()[:5]}")
print(f"  WS_NAME 範例: {df['WS_NAME'].unique()[:10]}")

print(f"\n檢查與河川代碼的關係:")
# 河川代碼範例：256000, 114000, 130000 等（6位數）
# 集水區代碼可能：2560xx（前4碼對應河川前4碼）

# 讀取河川資料
rivers = pd.read_excel('data/河川關係_完整版.xlsx')
print(f"河川數量: {len(rivers)}")

# 提取河川代碼的前4碼
river_prefixes = set()
for code in rivers['河川代碼'].unique():
    if pd.notna(code):
        prefix = str(code)[:4] if len(str(code)) >= 4 else str(code)
        river_prefixes.add(prefix)

print(f"河川代碼前4碼唯一值數量: {len(river_prefixes)}")
print(f"河川代碼前4碼範例: {sorted(list(river_prefixes))[:10]}")

# 提取集水區代碼的前4碼
ws_prefixes = set()
for ws_id in df['WS_ID'].unique():
    if pd.notna(ws_id):
        prefix = str(ws_id)[:4] if len(str(ws_id)) >= 4 else str(ws_id)
        ws_prefixes.add(prefix)

print(f"集水區代碼前4碼唯一值數量: {len(ws_prefixes)}")
print(f"集水區代碼前4碼範例: {sorted(list(ws_prefixes))[:10]}")

# 找出交集
common_prefixes = river_prefixes & ws_prefixes
print(f"\n共同的前4碼數量: {len(common_prefixes)}")
print(f"共同前4碼範例: {sorted(list(common_prefixes))[:10]}")

if 'AREA_M2' in df.columns:
    print(f"\n集水區面積統計:")
    print(f"  最小面積: {df['AREA_M2'].min():.2f} m²")
    print(f"  最大面積: {df['AREA_M2'].max():.2f} m²")
    print(f"  平均面積: {df['AREA_M2'].mean():.2f} m²")
    print(f"  總面積: {df['AREA_M2'].sum():.2f} m² = {df['AREA_M2'].sum()/1e6:.2f} km²")

print(f"\n按流域(BASIN)統計:")
basin_counts = df.groupby('BASIN_NAME').size().sort_values(ascending=False)
print(basin_counts.head(10))

print("\n=" * 80)
print("探索完成！")
print("=" * 80)
