# -*- coding: utf-8 -*-
"""
直接從測站基本資料建立MONITORS關係
(使用測站資料中的河川名稱)
"""
from neo4j import GraphDatabase
import pandas as pd

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "geoinfor"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# 讀取測站資料
df_rainfall = pd.read_excel('data/測站基本資料2025.xlsx', sheet_name=0)
df_water = pd.read_excel('data/測站基本資料2025.xlsx', sheet_name=1)

with driver.session() as session:
    print("=== 從測站基本資料建立MONITORS關係 ===\n")

    total_count = 0
    success_count = 0
    station_not_found = 0
    river_not_found = 0
    no_river_info = 0

    # 處理雨量測站
    print(f"處理 {len(df_rainfall)} 個雨量測站...")
    for idx, row in df_rainfall.iterrows():
        station_code = str(row.iloc[2]).strip()  # cols[2] = 測站代號
        river_name = str(row.iloc[7]).strip() if pd.notna(row.iloc[7]) else None  # cols[7] = 河川

        if not river_name or river_name == '' or river_name == 'nan':
            no_river_info += 1
            continue

        total_count += 1

        # 檢查測站是否存在
        result_s = session.run("""
            MATCH (s:Station)
            WHERE trim(s.code) = $code
            RETURN s
        """, code=station_code)

        station = result_s.single()
        if not station:
            station_not_found += 1
            continue

        # 檢查河川是否存在 (使用河川名稱)
        result_r = session.run("""
            MATCH (r:River {name: $name})
            RETURN r
        """, name=river_name)

        river = result_r.single()
        if not river:
            river_not_found += 1
            if river_not_found <= 10:
                print(f"  找不到河川: '{river_name}' (測站: {row.iloc[4]})")
            continue

        # 建立MONITORS關係
        session.run("""
            MATCH (s:Station)
            WHERE trim(s.code) = $station_code
            MATCH (r:River {name: $river_name})
            MERGE (s)-[rel:MONITORS]->(r)
            SET rel.match_type = '直接匹配',
                rel.source = '測站基本資料'
        """, station_code=station_code, river_name=river_name)

        success_count += 1

        if (idx + 1) % 50 == 0:
            print(f"  已處理 {idx + 1}/{len(df_rainfall)} 個雨量測站...")

    print(f"雨量測站完成: 成功建立 {success_count} 條關係\n")

    # 處理水位測站
    print(f"處理 {len(df_water)} 個水位測站...")
    rainfall_success = success_count  # 記錄雨量測站的成功數

    for idx, row in df_water.iterrows():
        station_code = str(row.iloc[2]).strip()  # cols[2] = 站號
        river_name = str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) else None  # cols[6] = 河川

        if not river_name or river_name == '' or river_name == 'nan':
            no_river_info += 1
            continue

        total_count += 1

        # 檢查測站是否存在
        result_s = session.run("""
            MATCH (s:Station)
            WHERE trim(s.code) = $code
            RETURN s
        """, code=station_code)

        station = result_s.single()
        if not station:
            station_not_found += 1
            continue

        # 檢查河川是否存在
        result_r = session.run("""
            MATCH (r:River {name: $name})
            RETURN r
        """, name=river_name)

        river = result_r.single()
        if not river:
            river_not_found += 1
            if river_not_found <= 20:
                print(f"  找不到河川: '{river_name}' (測站: {row.iloc[3]})")
            continue

        # 建立MONITORS關係
        session.run("""
            MATCH (s:Station)
            WHERE trim(s.code) = $station_code
            MATCH (r:River {name: $river_name})
            MERGE (s)-[rel:MONITORS]->(r)
            SET rel.match_type = '直接匹配',
                rel.source = '測站基本資料'
        """, station_code=station_code, river_name=river_name)

        success_count += 1

        if (idx + 1) % 100 == 0:
            print(f"  已處理 {idx + 1}/{len(df_water)} 個水位測站...")

    water_success = success_count - rainfall_success
    print(f"水位測站完成: 成功建立 {water_success} 條關係\n")

    print("="*60)
    print(f"總結:")
    print(f"  測站總數: {len(df_rainfall) + len(df_water)}")
    print(f"  有河川資訊: {total_count}")
    print(f"  沒有河川資訊: {no_river_info}")
    print(f"  成功建立關係: {success_count}")
    print(f"  測站找不到: {station_not_found}")
    print(f"  河川找不到: {river_not_found}")
    print("="*60)

    # 驗證最終結果
    result = session.run("""
        MATCH (s:Station)-[r:MONITORS]->(river:River)
        RETURN count(DISTINCT r) as total
    """)
    total_monitors = result.single()['total']
    print(f"\n最終MONITORS關係總數: {total_monitors} 條")

driver.close()
