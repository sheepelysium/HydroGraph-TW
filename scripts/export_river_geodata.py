# -*- coding: utf-8 -*-
"""
河川空間資料匯出腳本
=====================

功能：
    將水利署的河川邊界點資料（TWD97 座標）轉換為前端地圖可用的 GeoJSON 格式

資料來源：
    D:/Users/User/Downloads/圖資下載/圖資資料彙整.xlsx
    - Sheet: boundarypoint_邊界點
    - 532 筆河川邊界點資料

座標轉換：
    TWD97 (EPSG:3826) → WGS84 (EPSG:4326)
    - TWD97: 台灣常用的投影座標系統（公尺）
    - WGS84: 全球通用的經緯度座標系統（Leaflet/MapLibre 使用）

輸出：
    frontend/src/data/riverBoundaryPoints.json - GeoJSON 格式

使用方式：
    python scripts/export_river_geodata.py
"""

import pandas as pd
import json
import os
import math

# ============================================================
# 第一部分：座標轉換函數
# ============================================================

def twd97_to_wgs84(x, y):
    """
    將 TWD97 座標轉換為 WGS84 經緯度

    TWD97 是台灣使用的橫麥卡托投影座標系統：
    - 中央經線: 121°E
    - 原點緯度: 0°
    - 東偏移: 250,000 公尺
    - 北偏移: 0 公尺

    參數:
        x (float): TWD97 X 座標（東向，單位：公尺）
        y (float): TWD97 Y 座標（北向，單位：公尺）

    回傳:
        tuple: (經度, 緯度) WGS84 座標

    範例:
        >>> twd97_to_wgs84(250000, 2500000)
        (121.0, 22.59...)
    """
    # 檢查輸入值是否有效
    if x is None or y is None or math.isnan(x) or math.isnan(y):
        return None, None

    # TWD97 參數
    a = 6378137.0              # 長半軸（公尺）
    b = 6356752.314245         # 短半軸（公尺）
    lon0 = 121.0 * math.pi / 180  # 中央經線（弧度）
    k0 = 0.9999                # 尺度因子
    dx = 250000                # 東偏移（公尺）
    dy = 0                     # 北偏移（公尺）

    # 橢球參數計算
    e = math.sqrt(1 - (b / a) ** 2)  # 第一偏心率
    e2 = e ** 2 / (1 - e ** 2)       # 第二偏心率的平方

    # 移除偏移
    x = x - dx
    y = y - dy

    # 計算底點緯度 (Footpoint Latitude)
    M = y / k0  # 子午線弧長
    mu = M / (a * (1 - e ** 2 / 4 - 3 * e ** 4 / 64 - 5 * e ** 6 / 256))

    # 使用級數展開計算底點緯度
    e1 = (1 - math.sqrt(1 - e ** 2)) / (1 + math.sqrt(1 - e ** 2))
    J1 = 3 * e1 / 2 - 27 * e1 ** 3 / 32
    J2 = 21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32
    J3 = 151 * e1 ** 3 / 96
    J4 = 1097 * e1 ** 4 / 512

    fp = mu + J1 * math.sin(2 * mu) + J2 * math.sin(4 * mu) + J3 * math.sin(6 * mu) + J4 * math.sin(8 * mu)

    # 計算經緯度
    C1 = e2 * math.cos(fp) ** 2
    T1 = math.tan(fp) ** 2
    R1 = a * (1 - e ** 2) / (1 - e ** 2 * math.sin(fp) ** 2) ** 1.5
    N1 = a / math.sqrt(1 - e ** 2 * math.sin(fp) ** 2)
    D = x / (N1 * k0)

    # 計算緯度
    Q1 = N1 * math.tan(fp) / R1
    Q2 = D ** 2 / 2
    Q3 = (5 + 3 * T1 + 10 * C1 - 4 * C1 ** 2 - 9 * e2) * D ** 4 / 24
    Q4 = (61 + 90 * T1 + 298 * C1 + 45 * T1 ** 2 - 3 * C1 ** 2 - 252 * e2) * D ** 6 / 720
    lat = fp - Q1 * (Q2 - Q3 + Q4)

    # 計算經度
    Q5 = D
    Q6 = (1 + 2 * T1 + C1) * D ** 3 / 6
    Q7 = (5 - 2 * C1 + 28 * T1 - 3 * C1 ** 2 + 8 * e2 + 24 * T1 ** 2) * D ** 5 / 120
    lon = lon0 + (Q5 - Q6 + Q7) / math.cos(fp)

    # 轉換為度
    lat_deg = lat * 180 / math.pi
    lon_deg = lon * 180 / math.pi

    return round(lon_deg, 6), round(lat_deg, 6)


# ============================================================
# 第二部分：讀取 Excel 資料
# ============================================================

def read_boundary_points(excel_path):
    """
    讀取河川邊界點資料

    Excel 欄位說明：
        - BASIN: 所屬水系（如「蘭陽溪」）
        - CLASS: 河川分類（如「蘭陽溪主流」「蘭陽溪支流」）
        - RIVER: 河川名稱
        - NAME: 邊界點名稱（如「米摩登溪匯流口」）
        - BANK: 岸別（左/右）
        - TWD97_X_L: 左岸 X 座標
        - TWD97_Y_L: 左岸 Y 座標
        - TWD97_X_R: 右岸 X 座標
        - TWD97_Y_R: 右岸 Y 座標

    參數:
        excel_path (str): Excel 檔案路徑

    回傳:
        pandas.DataFrame: 邊界點資料
    """
    print(f"[1/4] 讀取 Excel 檔案...")
    print(f"      路徑: {excel_path}")

    # 讀取指定的 Sheet
    df = pd.read_excel(excel_path, sheet_name='boundarypoint_邊界點')

    print(f"      成功讀取 {len(df)} 筆邊界點資料")
    print(f"      欄位: {list(df.columns)}")
    print(f"      水系: {df['BASIN'].nunique()} 個")
    print(f"      河川: {df['RIVER'].nunique()} 條")

    return df


# ============================================================
# 第三部分：轉換為 GeoJSON
# ============================================================

def convert_to_geojson(df):
    """
    將邊界點資料轉換為 GeoJSON 格式

    GeoJSON 結構：
    {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [經度, 緯度]
                },
                "properties": {
                    "basin": "蘭陽溪",
                    "river": "蘭陽溪",
                    "name": "米摩登溪匯流口",
                    "class": "蘭陽溪主流"
                }
            },
            ...
        ]
    }

    參數:
        df (pandas.DataFrame): 邊界點資料

    回傳:
        dict: GeoJSON 格式的資料
    """
    print(f"\n[2/4] 轉換座標系統...")
    print(f"      TWD97 (EPSG:3826) → WGS84 (EPSG:4326)")

    features = []
    converted_count = 0
    error_count = 0

    for idx, row in df.iterrows():
        # 取得 TWD97 座標（使用左岸座標為主要點位）
        x = row['TWD97_X_L']
        y = row['TWD97_Y_L']

        # 轉換座標
        lon, lat = twd97_to_wgs84(x, y)

        if lon is None or lat is None:
            error_count += 1
            continue

        # 建立 GeoJSON Feature
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "properties": {
                "basin": row['BASIN'],           # 水系
                "river": row['RIVER'],           # 河川
                "name": row['NAME'],             # 邊界點名稱
                "class": row['CLASS'],           # 河川分類
                "bank": row['BANK'],             # 岸別
                "twd97_x": x,                    # 原始 X 座標
                "twd97_y": y                     # 原始 Y 座標
            }
        }
        features.append(feature)
        converted_count += 1

    print(f"      成功轉換: {converted_count} 筆")
    if error_count > 0:
        print(f"      轉換失敗: {error_count} 筆（座標無效）")

    # 組合成 FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "source": "水利署河川邊界點資料",
            "coordinate_system": "WGS84 (EPSG:4326)",
            "total_points": len(features),
            "basins": df['BASIN'].nunique(),
            "rivers": df['RIVER'].nunique()
        }
    }

    return geojson


# ============================================================
# 第四部分：按水系分組匯出
# ============================================================

def group_by_basin(geojson):
    """
    將 GeoJSON 按水系分組，方便前端按需載入

    輸出結構：
    {
        "淡水河": {
            "points": [...],
            "rivers": ["淡水河", "基隆河", ...]
        },
        "蘭陽溪": {
            "points": [...],
            "rivers": [...]
        }
    }

    參數:
        geojson (dict): GeoJSON FeatureCollection

    回傳:
        dict: 按水系分組的資料
    """
    print(f"\n[3/4] 按水系分組...")

    grouped = {}

    for feature in geojson['features']:
        basin = feature['properties']['basin']
        river = feature['properties']['river']

        if basin not in grouped:
            grouped[basin] = {
                "points": [],
                "rivers": set()
            }

        grouped[basin]['points'].append(feature)
        grouped[basin]['rivers'].add(river)

    # 將 rivers 從 set 轉為 list
    for basin in grouped:
        grouped[basin]['rivers'] = sorted(list(grouped[basin]['rivers']))
        print(f"      {basin}: {len(grouped[basin]['points'])} 個點, {len(grouped[basin]['rivers'])} 條河川")

    return grouped


# ============================================================
# 第五部分：儲存檔案
# ============================================================

def save_files(geojson, grouped, output_dir):
    """
    儲存輸出檔案

    會產生以下檔案：
    1. riverBoundaryPoints.json - 完整的 GeoJSON（所有水系）
    2. riverBoundaryByBasin.json - 按水系分組的資料

    參數:
        geojson (dict): 完整的 GeoJSON
        grouped (dict): 按水系分組的資料
        output_dir (str): 輸出目錄
    """
    print(f"\n[4/4] 儲存檔案...")

    # 確保輸出目錄存在
    os.makedirs(output_dir, exist_ok=True)

    # 1. 儲存完整 GeoJSON
    geojson_path = os.path.join(output_dir, 'riverBoundaryPoints.json')
    with open(geojson_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    print(f"      [OK] {geojson_path}")
    print(f"        - 共 {len(geojson['features'])} 個點")

    # 2. 儲存按水系分組的資料
    grouped_path = os.path.join(output_dir, 'riverBoundaryByBasin.json')

    # 轉換格式以便 JSON 序列化
    grouped_serializable = {}
    for basin, data in grouped.items():
        grouped_serializable[basin] = {
            "pointCount": len(data['points']),
            "rivers": data['rivers'],
            "points": data['points']
        }

    with open(grouped_path, 'w', encoding='utf-8') as f:
        json.dump(grouped_serializable, f, ensure_ascii=False, indent=2)
    print(f"      [OK] {grouped_path}")
    print(f"        - 共 {len(grouped_serializable)} 個水系")

    # 3. 輸出摘要
    summary_path = os.path.join(output_dir, 'riverBoundary_summary.json')
    summary = {
        "totalPoints": len(geojson['features']),
        "basins": list(grouped_serializable.keys()),
        "basinCount": len(grouped_serializable),
        "riverCount": geojson['metadata']['rivers'],
        "files": [
            "riverBoundaryPoints.json - 完整 GeoJSON",
            "riverBoundaryByBasin.json - 按水系分組"
        ]
    }
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"      [OK] {summary_path}")


# ============================================================
# 主程式
# ============================================================

def main():
    """
    主程式入口

    執行流程：
    1. 讀取 Excel 中的 boundarypoint_邊界點 資料
    2. 將 TWD97 座標轉換為 WGS84
    3. 轉換為 GeoJSON 格式
    4. 按水系分組
    5. 儲存到 frontend/src/data/ 目錄
    """
    print("=" * 60)
    print("河川空間資料匯出腳本")
    print("=" * 60)

    # 設定路徑
    excel_path = r"D:\Users\User\Downloads\圖資下載\圖資資料彙整.xlsx"
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'src', 'data')

    # 檢查 Excel 檔案是否存在
    if not os.path.exists(excel_path):
        print(f"\n[錯誤] 找不到 Excel 檔案: {excel_path}")
        print("請確認檔案路徑是否正確")
        return

    # 執行轉換流程
    try:
        # Step 1: 讀取資料
        df = read_boundary_points(excel_path)

        # Step 2 & 3: 轉換為 GeoJSON
        geojson = convert_to_geojson(df)

        # Step 4: 按水系分組
        grouped = group_by_basin(geojson)

        # Step 5: 儲存檔案
        save_files(geojson, grouped, output_dir)

        print("\n" + "=" * 60)
        print("完成！")
        print("=" * 60)
        print(f"\n輸出目錄: {os.path.abspath(output_dir)}")
        print("\n前端使用方式:")
        print("  import riverData from './data/riverBoundaryPoints.json'")
        print("  import basinData from './data/riverBoundaryByBasin.json'")

    except Exception as e:
        print(f"\n[錯誤] {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
