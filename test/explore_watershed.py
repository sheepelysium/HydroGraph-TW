# -*- coding: utf-8 -*-
"""探索集水區 Shapefile 資料結構"""
import geopandas as gpd
import pandas as pd

print("=" * 80)
print("讀取集水區 Shapefile")
print("=" * 80)

# 讀取 Shapefile
gdf = gpd.read_file('file/110年度全臺839子集水區範圍圖_UTF8.shp')

print(f"\n集水區數量: {len(gdf)}")
print(f"\n欄位名稱:")
for i, col in enumerate(gdf.columns):
    print(f"  [{i}] {col} - {gdf[col].dtype}")

print(f"\n前5筆資料:")
print(gdf.head().to_string())

print(f"\n統計資訊:")
print(f"  BASIN_ID 唯一值數量: {gdf['BASIN_ID'].nunique()}")
print(f"  WS_ID 唯一值數量: {gdf['WS_ID'].nunique()}")
print(f"  BASIN_NAME 範例: {gdf['BASIN_NAME'].unique()[:5]}")
print(f"  WS_NAME 範例: {gdf['WS_NAME'].unique()[:10]}")

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

# 提取集水區代碼的前4碼
ws_prefixes = set()
for ws_id in gdf['WS_ID'].unique():
    if pd.notna(ws_id):
        prefix = str(ws_id)[:4] if len(str(ws_id)) >= 4 else str(ws_id)
        ws_prefixes.add(prefix)

print(f"集水區代碼前4碼唯一值數量: {len(ws_prefixes)}")

# 找出交集
common_prefixes = river_prefixes & ws_prefixes
print(f"共同的前4碼數量: {len(common_prefixes)}")
print(f"範例: {list(common_prefixes)[:10]}")

print(f"\n集水區面積統計:")
print(f"  最小面積: {gdf['AREA_M2'].min():.2f} m²")
print(f"  最大面積: {gdf['AREA_M2'].max():.2f} m²")
print(f"  平均面積: {gdf['AREA_M2'].mean():.2f} m²")
print(f"  總面積: {gdf['AREA_M2'].sum():.2f} m² = {gdf['AREA_M2'].sum()/1e6:.2f} km²")

print(f"\n按流域(BASIN)統計:")
basin_counts = gdf.groupby('BASIN_NAME').size().sort_values(ascending=False)
print(basin_counts.head(10))

print("\n=" * 80)
print("探索完成！")
print("=" * 80)
