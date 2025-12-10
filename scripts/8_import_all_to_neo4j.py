# -*- coding: utf-8 -*-
"""
一鍵匯入所有資料到 Neo4j
整合河川、集水區、測站匯入功能

使用方式:
    python 8_import_all_to_neo4j.py              # 互動模式
    python 8_import_all_to_neo4j.py --auto-clear # 自動清空重建
"""
import sys
import pandas as pd
from pathlib import Path
from neo4j import GraphDatabase


# =============================================================================
# 資料清理工具
# =============================================================================

def clean_dataframe(df):
    """清理 DataFrame：去除欄位名稱和字串值的空格"""
    df.columns = df.columns.str.strip()
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    return df


# =============================================================================
# 河川資料匯入器
# =============================================================================

class RiverImporter:
    """河川資料匯入器"""

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_indexes(self):
        """建立索引"""
        print("\n建立河川索引...")
        indexes = [
            "CREATE INDEX river_code IF NOT EXISTS FOR (r:River) ON (r.code)",
            "CREATE INDEX river_name IF NOT EXISTS FOR (r:River) ON (r.name)",
            "CREATE INDEX water_system IF NOT EXISTS FOR (w:WaterSystem) ON (w.name)",
        ]
        with self.driver.session(database="neo4j") as session:
            for idx_query in indexes:
                session.run(idx_query)
                print(f"  [OK] {idx_query.split('FOR')[0].strip()}")

    def import_rivers(self, excel_path):
        """匯入河川節點"""
        print(f"\n讀取河川資料: {excel_path}")
        df = pd.read_excel(excel_path)
        df = clean_dataframe(df)
        print(f"  共 {len(df)} 條河川")

        print("\n建立河川節點 (River)...")
        with self.driver.session(database="neo4j") as session:
            for idx, row in df.iterrows():
                session.run("""
                    MERGE (r:River {code: $code})
                    SET r.name = $name,
                        r.level = $level,
                        r.main_stream = $main_stream,
                        r.seq_no = $seq_no
                """,
                    code=str(row['河川代碼']),
                    name=str(row['河川名稱']),
                    level=int(row['階層']),
                    main_stream=str(row['主流水系']) if pd.notna(row['主流水系']) else None,
                    seq_no=str(row['序號']) if pd.notna(row['序號']) else None
                )
                if (idx + 1) % 100 == 0:
                    print(f"  已匯入 {idx + 1}/{len(df)} 條河川...")
        print(f"[OK] 完成! 共匯入 {len(df)} 個河川節點")

    def import_water_systems(self, excel_path):
        """匯入水系節點並建立河川與水系的關係"""
        print(f"\n建立水系節點與關係...")
        df = pd.read_excel(excel_path)
        df = clean_dataframe(df)

        water_systems = df['主流水系'].dropna().unique()
        print(f"  發現 {len(water_systems)} 個水系")

        with self.driver.session(database="neo4j") as session:
            for ws in water_systems:
                session.run("MERGE (w:WaterSystem {name: $name})", name=str(ws))
        print(f"[OK] 已建立 {len(water_systems)} 個水系節點")

        print("\n建立河川 BELONGS_TO 水系關係...")
        with self.driver.session(database="neo4j") as session:
            count = 0
            for idx, row in df.iterrows():
                if pd.notna(row['主流水系']):
                    session.run("""
                        MATCH (r:River {code: $river_code})
                        MATCH (w:WaterSystem {name: $water_system})
                        MERGE (r)-[:BELONGS_TO]->(w)
                    """,
                        river_code=str(row['河川代碼']),
                        water_system=str(row['主流水系'])
                    )
                    count += 1
        print(f"[OK] 已建立 {count} 條河川-水系關係")

    def import_river_hierarchy(self, excel_path):
        """匯入河川階層關係 (支流 -> 主流)"""
        print("\n建立河川階層關係 (IS_TRIBUTARY_OF)...")
        df = pd.read_excel(excel_path)
        df = clean_dataframe(df)

        river_name_to_code = dict(zip(df['河川名稱'], df['河川代碼']))

        with self.driver.session(database="neo4j") as session:
            count = 0
            for idx, row in df.iterrows():
                if pd.notna(row['上游河川']):
                    parent_name = str(row['上游河川'])
                    if parent_name in river_name_to_code:
                        parent_code = river_name_to_code[parent_name]
                        session.run("""
                            MATCH (tributary:River {code: $tributary_code})
                            MATCH (main:River {code: $main_code})
                            MERGE (tributary)-[r:IS_TRIBUTARY_OF]->(main)
                            SET r.level_diff = $level_diff
                        """,
                            tributary_code=str(row['河川代碼']),
                            main_code=str(parent_code),
                            level_diff=1
                        )
                        count += 1
                if (idx + 1) % 100 == 0:
                    print(f"  已處理 {idx + 1}/{len(df)} 條河川...")
        print(f"[OK] 已建立 {count} 條河川階層關係")


# =============================================================================
# 集水區資料匯入器
# =============================================================================

class WatershedImporter:
    """集水區資料匯入器"""

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_indexes(self):
        """建立索引"""
        print("\n建立集水區索引...")
        indexes = [
            "CREATE INDEX watershed_id IF NOT EXISTS FOR (w:Watershed) ON (w.id)",
            "CREATE INDEX watershed_name IF NOT EXISTS FOR (w:Watershed) ON (w.name)",
            "CREATE INDEX basin_id IF NOT EXISTS FOR (b:Basin) ON (b.id)",
            "CREATE INDEX basin_name IF NOT EXISTS FOR (b:Basin) ON (b.name)",
        ]
        with self.driver.session(database="neo4j") as session:
            for idx_query in indexes:
                session.run(idx_query)
                print(f"  [OK] {idx_query.split('FOR')[0].strip()}")

    def import_basins(self, excel_path):
        """匯入流域節點"""
        print(f"\n讀取流域統計資料: {excel_path}")
        df = pd.read_excel(excel_path, sheet_name='流域統計')
        df = clean_dataframe(df)
        print(f"  共 {len(df)} 個流域")

        print("\n建立流域節點 (Basin)...")
        cols = list(df.columns)
        with self.driver.session(database="neo4j") as session:
            for idx, row in df.iterrows():
                basin_name = str(row[cols[0]]) if pd.notna(row[cols[0]]) else None
                if basin_name:
                    session.run("""
                        MERGE (b:Basin {name: $name})
                        SET b.watershed_count = $watershed_count,
                            b.river_count = $river_count,
                            b.area_km2 = $area_km2,
                            b.avg_area_km2 = $avg_area_km2
                    """,
                        name=basin_name,
                        watershed_count=int(row[cols[1]]) if pd.notna(row[cols[1]]) else 0,
                        river_count=int(row[cols[2]]) if pd.notna(row[cols[2]]) else 0,
                        area_km2=float(row[cols[4]]) if pd.notna(row[cols[4]]) else 0.0,
                        avg_area_km2=float(row[cols[3]]) if pd.notna(row[cols[3]]) else 0.0
                    )
        print(f"[OK] 已匯入 {len(df)} 個流域節點")

    def import_watersheds(self, excel_path):
        """匯入集水區節點"""
        print(f"\n讀取集水區資料...")
        df = pd.read_excel(excel_path, sheet_name='集水區列表')
        df = clean_dataframe(df)
        print(f"  共 {len(df)} 個集水區")

        print("\n建立集水區節點 (Watershed)...")
        with self.driver.session(database="neo4j") as session:
            for idx, row in df.iterrows():
                session.run("""
                    MERGE (w:Watershed {id: $id})
                    SET w.name = $name,
                        w.basin_id = $basin_id,
                        w.basin_name = $basin_name,
                        w.area_m2 = $area_m2,
                        w.area_km2 = $area_km2,
                        w.basin_code = $basin_code,
                        w.river_count = $river_count,
                        w.main_river = $main_river,
                        w.branch = $branch
                """,
                    id=str(row['WS_ID']),
                    name=str(row['WS_NAME']) if pd.notna(row['WS_NAME']) else None,
                    basin_id=str(row['BASIN_ID']) if pd.notna(row['BASIN_ID']) else None,
                    basin_name=str(row['BASIN_NAME']) if pd.notna(row['BASIN_NAME']) else None,
                    area_m2=float(row['AREA_M2']) if pd.notna(row['AREA_M2']) else 0.0,
                    area_km2=float(row['AREA_M2']) / 1e6 if pd.notna(row['AREA_M2']) else 0.0,
                    basin_code=str(row['流域代碼']) if pd.notna(row['流域代碼']) else None,
                    river_count=int(row['關聯河川數量']) if pd.notna(row['關聯河川數量']) else 0,
                    main_river=str(row['主要河川']) if pd.notna(row['主要河川']) else None,
                    branch=str(row['BRANCH']) if pd.notna(row['BRANCH']) else None
                )
                if (idx + 1) % 100 == 0:
                    print(f"  已匯入 {idx + 1}/{len(df)} 個集水區...")
        print(f"[OK] 已匯入 {len(df)} 個集水區節點")

    def link_watersheds_to_basins(self, excel_path):
        """建立集水區 -> 流域關係"""
        print("\n建立集水區 PART_OF 流域關係...")
        df = pd.read_excel(excel_path, sheet_name='集水區列表')
        df = clean_dataframe(df)

        with self.driver.session(database="neo4j") as session:
            count = 0
            for idx, row in df.iterrows():
                if pd.notna(row['BASIN_NAME']):
                    session.run("""
                        MATCH (w:Watershed {id: $ws_id})
                        MATCH (b:Basin {name: $basin_name})
                        MERGE (w)-[:PART_OF]->(b)
                    """,
                        ws_id=str(row['WS_ID']),
                        basin_name=str(row['BASIN_NAME'])
                    )
                    count += 1
        print(f"[OK] 已建立 {count} 條集水區-流域關係")

    def link_watersheds_to_rivers(self, excel_path):
        """建立集水區 -> 河川關係"""
        print("\n建立集水區 CONTAINS_RIVER 河川關係...")
        df = pd.read_excel(excel_path, sheet_name='集水區-河川關聯')
        df = clean_dataframe(df)
        print(f"  共 {len(df)} 條關聯記錄")

        with self.driver.session(database="neo4j") as session:
            count = 0
            for idx, row in df.iterrows():
                session.run("""
                    MATCH (w:Watershed {id: $ws_id})
                    MATCH (r:River {code: $river_code})
                    MERGE (w)-[rel:CONTAINS_RIVER]->(r)
                    SET rel.river_level = $river_level
                """,
                    ws_id=str(row['集水區ID']),
                    river_code=str(row['河川代碼']),
                    river_level=int(row['河川階層']) if pd.notna(row['河川階層']) else None
                )
                count += 1
                if (idx + 1) % 500 == 0:
                    print(f"  已建立 {idx + 1}/{len(df)} 條關係...")
        print(f"[OK] 已建立 {count} 條集水區-河川關係")


# =============================================================================
# 測站資料匯入器
# =============================================================================

class StationImporter:
    """測站資料匯入器"""

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_indexes(self):
        """建立索引"""
        print("\n建立測站索引...")
        indexes = [
            "CREATE INDEX station_code IF NOT EXISTS FOR (s:Station) ON (s.code)",
            "CREATE INDEX station_name IF NOT EXISTS FOR (s:Station) ON (s.name)",
            "CREATE INDEX station_type IF NOT EXISTS FOR (s:Station) ON (s.type)",
        ]
        with self.driver.session(database="neo4j") as session:
            for idx_query in indexes:
                session.run(idx_query)
                print(f"  [OK] {idx_query.split('FOR')[0].strip()}")

    def import_rainfall_stations(self, excel_path):
        """匯入雨量測站"""
        print(f"\n讀取雨量測站資料: {excel_path}")
        df = pd.read_excel(excel_path, sheet_name=0)
        df = clean_dataframe(df)
        print(f"  共 {len(df)} 個雨量測站")

        print("\n建立雨量測站節點 (Station:Rainfall)...")
        cols = list(df.columns)
        with self.driver.session(database="neo4j") as session:
            for idx, row in df.iterrows():
                session.run("""
                    MERGE (s:Station:Rainfall {code: $code})
                    SET s.name = $name, s.type = '雨量測站',
                        s.category = $category, s.status = $status,
                        s.cwa_code = $cwa_code, s.management_unit = $management_unit,
                        s.water_system = $water_system, s.river = $river,
                        s.elevation = $elevation, s.city = $city, s.address = $address,
                        s.x_twd97 = $x, s.y_twd97 = $y,
                        s.backup_station_code = $backup_station_code,
                        s.rainfall_minute_years = $rainfall_minute_years,
                        s.rainfall_hour_years = $rainfall_hour_years,
                        s.rainfall_daily_years = $rainfall_daily_years,
                        s.rainfall_monthly_years = $rainfall_monthly_years
                """,
                    code=str(row[cols[2]]) if pd.notna(row[cols[2]]) else None,
                    name=str(row[cols[4]]) if pd.notna(row[cols[4]]) else None,
                    category=str(row[cols[0]]) if pd.notna(row[cols[0]]) else None,
                    status=str(row[cols[1]]) if pd.notna(row[cols[1]]) else None,
                    cwa_code=str(row[cols[3]]) if pd.notna(row[cols[3]]) else None,
                    management_unit=str(row[cols[5]]) if pd.notna(row[cols[5]]) else None,
                    water_system=str(row[cols[6]]) if pd.notna(row[cols[6]]) else None,
                    river=str(row[cols[7]]) if pd.notna(row[cols[7]]) else None,
                    elevation=float(row[cols[8]]) if pd.notna(row[cols[8]]) else None,
                    city=str(row[cols[9]]) if pd.notna(row[cols[9]]) else None,
                    address=str(row[cols[10]]) if pd.notna(row[cols[10]]) else None,
                    x=float(row[cols[11]]) if pd.notna(row[cols[11]]) else None,
                    y=float(row[cols[12]]) if pd.notna(row[cols[12]]) else None,
                    backup_station_code=str(row[cols[13]]) if pd.notna(row[cols[13]]) else None,
                    rainfall_minute_years=str(row[cols[14]]) if pd.notna(row[cols[14]]) else None,
                    rainfall_hour_years=str(row[cols[15]]) if pd.notna(row[cols[15]]) else None,
                    rainfall_daily_years=str(row[cols[16]]) if pd.notna(row[cols[16]]) else None,
                    rainfall_monthly_years=str(row[cols[17]]) if pd.notna(row[cols[17]]) else None
                )
                if (idx + 1) % 50 == 0:
                    print(f"  已匯入 {idx + 1}/{len(df)} 個雨量測站...")
        print(f"[OK] 已匯入 {len(df)} 個雨量測站")

    def import_water_level_stations(self, excel_path):
        """匯入水位測站"""
        print(f"\n讀取水位測站資料...")
        df = pd.read_excel(excel_path, sheet_name=1)
        df = clean_dataframe(df)
        print(f"  共 {len(df)} 個水位測站")

        print("\n建立水位測站節點 (Station:WaterLevel)...")
        cols = list(df.columns)
        with self.driver.session(database="neo4j") as session:
            for idx, row in df.iterrows():
                session.run("""
                    MERGE (s:Station:WaterLevel {code: $code})
                    SET s.name = $name, s.type = '水位測站',
                        s.category = $category, s.status = $status,
                        s.management_unit = $management_unit,
                        s.water_system = $water_system, s.river = $river,
                        s.elevation = $elevation, s.city = $city, s.address = $address,
                        s.x_twd97 = $x, s.y_twd97 = $y,
                        s.backup_station_code = $backup_station_code,
                        s.water_level_hour_years = $water_level_hour_years,
                        s.water_level_daily_years = $water_level_daily_years,
                        s.water_level_monthly_years = $water_level_monthly_years,
                        s.flow_hour_years = $flow_hour_years,
                        s.flow_daily_years = $flow_daily_years,
                        s.flow_monthly_years = $flow_monthly_years,
                        s.sediment_years = $sediment_years
                """,
                    code=str(row[cols[2]]) if pd.notna(row[cols[2]]) else None,
                    name=str(row[cols[3]]) if pd.notna(row[cols[3]]) else None,
                    category=str(row[cols[0]]) if pd.notna(row[cols[0]]) else None,
                    status=str(row[cols[1]]) if pd.notna(row[cols[1]]) else None,
                    management_unit=str(row[cols[4]]) if pd.notna(row[cols[4]]) else None,
                    water_system=str(row[cols[5]]) if pd.notna(row[cols[5]]) else None,
                    river=str(row[cols[6]]) if pd.notna(row[cols[6]]) else None,
                    elevation=float(row[cols[7]]) if pd.notna(row[cols[7]]) else None,
                    city=str(row[cols[8]]) if pd.notna(row[cols[8]]) else None,
                    address=str(row[cols[9]]) if pd.notna(row[cols[9]]) else None,
                    x=float(row[cols[10]]) if pd.notna(row[cols[10]]) else None,
                    y=float(row[cols[11]]) if pd.notna(row[cols[11]]) else None,
                    backup_station_code=str(row[cols[12]]) if pd.notna(row[cols[12]]) else None,
                    water_level_hour_years=str(row[cols[13]]) if pd.notna(row[cols[13]]) else None,
                    water_level_daily_years=str(row[cols[14]]) if pd.notna(row[cols[14]]) else None,
                    water_level_monthly_years=str(row[cols[15]]) if pd.notna(row[cols[15]]) else None,
                    flow_hour_years=str(row[cols[16]]) if pd.notna(row[cols[16]]) else None,
                    flow_daily_years=str(row[cols[17]]) if pd.notna(row[cols[17]]) else None,
                    flow_monthly_years=str(row[cols[18]]) if pd.notna(row[cols[18]]) else None,
                    sediment_years=str(row[cols[19]]) if pd.notna(row[cols[19]]) else None
                )
                if (idx + 1) % 50 == 0:
                    print(f"  已匯入 {idx + 1}/{len(df)} 個水位測站...")
        print(f"[OK] 已匯入 {len(df)} 個水位測站")

    def link_stations_to_rivers(self, matching_report_path):
        """建立測站 -> 河川關係"""
        print(f"\n建立測站 MONITORS 河川關係...")
        df = pd.read_excel(matching_report_path, sheet_name='能配對的測站')
        df = clean_dataframe(df)
        print(f"  共 {len(df)} 個能配對的測站")

        cols = list(df.columns)
        with self.driver.session(database="neo4j") as session:
            count = 0
            skipped = 0
            code_mismatch = 0

            for idx, row in df.iterrows():
                station_code = str(row[cols[1]]).strip() if pd.notna(row[cols[1]]) and str(row[cols[1]]).strip() != '' else None
                river_code = str(row[cols[5]]) if pd.notna(row[cols[5]]) else None

                if station_code and river_code:
                    station_prefix_4 = station_code[:4]
                    river_prefix_4 = river_code[:4]
                    station_prefix_3 = station_code[:3]
                    river_prefix_3 = river_code[:3]

                    if station_prefix_4 != river_prefix_4 and station_prefix_3 != river_prefix_3:
                        code_mismatch += 1
                        continue

                    session.run("""
                        MATCH (s:Station) WHERE trim(s.code) = $station_code
                        MATCH (r:River {code: $river_code})
                        MERGE (s)-[rel:MONITORS]->(r)
                        SET rel.match_type = $match_type,
                            rel.original_river_name = $original_river,
                            rel.matched_river_name = $matched_river
                    """,
                        station_code=station_code,
                        river_code=river_code,
                        match_type=str(row[cols[6]]) if pd.notna(row[cols[6]]) else 'unknown',
                        original_river=str(row[cols[3]]) if pd.notna(row[cols[3]]) else None,
                        matched_river=str(row[cols[4]]) if pd.notna(row[cols[4]]) else None
                    )
                    count += 1
                else:
                    skipped += 1

                if (idx + 1) % 100 == 0:
                    print(f"  已處理 {idx + 1}/{len(df)} 條...")

        print(f"[OK] 已建立 {count} 條測站-河川關係")
        if skipped > 0:
            print(f"[INFO] 跳過 {skipped} 條 (缺少測站代號或河川代碼)")
        if code_mismatch > 0:
            print(f"[INFO] 過濾 {code_mismatch} 條代碼不匹配")


# =============================================================================
# 主匯入器與 Schema 遷移
# =============================================================================

def migrate_schema(uri, user, password):
    """Schema 遷移: 轉換為 DIFY 兼容格式
    - IS_TRIBUTARY_OF -> FLOWS_INTO
    - MONITORS -> LOCATED_ON
    """
    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session(database="neo4j") as session:
        print("  轉換 IS_TRIBUTARY_OF -> FLOWS_INTO...")
        result = session.run("""
            MATCH (child:River)-[r:IS_TRIBUTARY_OF]->(parent:River)
            MERGE (child)-[:FLOWS_INTO]->(parent)
            DELETE r
            RETURN count(r) as count
        """)
        count = result.single()['count']
        print(f"    [OK] 轉換 {count} 條河川支流關係")

        print("  轉換 MONITORS -> LOCATED_ON...")
        result = session.run("""
            MATCH (s:Station)-[r:MONITORS]->(river:River)
            MERGE (s)-[:LOCATED_ON]->(river)
            DELETE r
            RETURN count(r) as count
        """)
        count = result.single()['count']
        print(f"    [OK] 轉換 {count} 條測站監測關係")

        print("  驗證資料完整性...")
        result = session.run("""
            MATCH (s:Station)-[:LOCATED_ON]->(r:River)
            WITH s, r, trim(s.code) as station_code, r.code as river_code
            WHERE station_code IS NOT NULL AND river_code IS NOT NULL
              AND left(station_code, 4) <> left(river_code, 4)
              AND left(station_code, 3) <> left(river_code, 3)
            RETURN count(*) as mismatch_count
        """)
        mismatch = result.single()['mismatch_count']
        if mismatch == 0:
            print(f"    [OK] 無代碼不匹配的錯誤")
        else:
            print(f"    [WARNING] 發現 {mismatch} 個代碼不匹配，正在清理...")
            session.run("""
                MATCH (s:Station)-[r:LOCATED_ON]->(river:River)
                WITH s, r, river, trim(s.code) as station_code, river.code as river_code
                WHERE station_code IS NOT NULL AND river_code IS NOT NULL
                  AND left(station_code, 4) <> left(river_code, 4)
                  AND left(station_code, 3) <> left(river_code, 3)
                DELETE r
            """)
            print(f"    [OK] 已清理代碼不匹配的關係")

    driver.close()
    print("  [OK] Schema 遷移完成")


class MasterImporter:
    """主匯入器 - 統一執行所有匯入流程"""

    def __init__(self, uri, user, password):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def test_connection(self):
        """測試連線"""
        print("\n測試 Neo4j 連線...")
        try:
            with self.driver.session(database="neo4j") as session:
                result = session.run("RETURN 1 as test")
                result.single()
            print("[OK] 連線成功!")
            return True
        except Exception as e:
            print(f"[錯誤] 連線失敗: {e}")
            return False

    def clear_database(self, auto_confirm=False):
        """清空資料庫"""
        print("\n[警告] 清空 Neo4j 資料庫...")

        if auto_confirm:
            response = 'yes'
            print("[自動模式] 自動確認清空資料庫")
        else:
            response = input("確定要清空所有資料嗎? 此操作無法復原! (yes/no): ")

        if response.lower() == 'yes':
            with self.driver.session(database="neo4j") as session:
                session.run("MATCH (n) DETACH DELETE n")
            print("[OK] 資料庫已清空")
            return True
        else:
            print("[提示] 取消清空，將在現有資料上新增/更新")
            return False

    def show_final_statistics(self):
        """顯示最終統計資料"""
        print("\n" + "="*80)
        print("完整知識圖譜統計")
        print("="*80)

        with self.driver.session(database="neo4j") as session:
            print("\n【節點統計】")
            node_types = [
                ("River", "河川"), ("WaterSystem", "水系"), ("Basin", "流域"),
                ("Watershed", "集水區"), ("Station", "測站 (總數)"),
                ("Rainfall", "  - 雨量測站"), ("WaterLevel", "  - 水位測站"),
            ]
            for node_type, desc in node_types:
                count = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count").single()["count"]
                print(f"  {desc}: {count}")

            print("\n【關係統計】")
            rel_types = [
                ("FLOWS_INTO", "河川流向關係"), ("BELONGS_TO", "河川屬於水系"),
                ("PART_OF", "集水區屬於流域"), ("LOCATED_ON", "測站位於河川"),
            ]
            for rel_type, desc in rel_types:
                count = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count").single()["count"]
                print(f"  {desc}: {count}")


def main():
    """主程式 - 一鍵匯入所有資料"""
    auto_clear = '--auto-clear' in sys.argv

    print("="*80)
    print("HydroGraph-TW 完整資料匯入 Neo4j")
    print("台灣水文知識圖譜建置")
    print("="*80)
    if auto_clear:
        print("[自動模式] 將自動清空並重建資料庫")

    # Neo4j 連線設定
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "geoinfor"

    # 檢查必要檔案
    required_files = [
        Path("data/河川關係_完整版.xlsx"),
        Path("data/集水區分析報表.xlsx"),
        Path("data/測站基本資料2025.xlsx"),
        Path("data/測站河川配對分析報表.xlsx"),
    ]

    print("\n檢查必要檔案...")
    all_exist = True
    for file_path in required_files:
        if file_path.exists():
            print(f"  [OK] {file_path.name}")
        else:
            print(f"  [X] 找不到: {file_path}")
            all_exist = False

    if not all_exist:
        print("\n[錯誤] 缺少必要檔案，請先執行 1-4 號腳本產生資料檔案")
        return

    master = MasterImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    if not master.test_connection():
        print("\n[錯誤] 無法連線到 Neo4j")
        master.close()
        return

    try:
        cleared = master.clear_database(auto_confirm=auto_clear)

        print("\n" + "="*80)
        print("開始匯入資料...")
        print("="*80)

        # 步驟 1: 匯入河川資料
        print("\n【步驟 1/3】匯入河川與水系資料")
        print("-" * 80)
        river_importer = RiverImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        if cleared:
            river_importer.create_indexes()
        river_importer.import_rivers(Path("data/河川關係_完整版.xlsx"))
        river_importer.import_water_systems(Path("data/河川關係_完整版.xlsx"))
        river_importer.import_river_hierarchy(Path("data/河川關係_完整版.xlsx"))
        river_importer.close()

        # 步驟 2: 匯入集水區資料
        print("\n【步驟 2/3】匯入集水區與流域資料")
        print("-" * 80)
        watershed_importer = WatershedImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        watershed_importer.create_indexes()
        watershed_importer.import_basins(Path("data/集水區分析報表.xlsx"))
        watershed_importer.import_watersheds(Path("data/集水區分析報表.xlsx"))
        watershed_importer.link_watersheds_to_basins(Path("data/集水區分析報表.xlsx"))
        watershed_importer.link_watersheds_to_rivers(Path("data/集水區分析報表.xlsx"))
        watershed_importer.close()

        # 步驟 3: 匯入測站資料
        print("\n【步驟 3/3】匯入測站資料")
        print("-" * 80)
        station_importer = StationImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        station_importer.create_indexes()
        station_importer.import_rainfall_stations(Path("data/測站基本資料2025.xlsx"))
        station_importer.import_water_level_stations(Path("data/測站基本資料2025.xlsx"))
        station_importer.link_stations_to_rivers(Path("data/測站河川配對分析報表.xlsx"))
        station_importer.close()

        # 步驟 4: Schema 遷移
        print("\n【步驟 4/4】Schema 遷移")
        print("-" * 80)
        migrate_schema(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

        master.show_final_statistics()

        print("\n" + "="*80)
        print("[完成] 所有資料匯入完成!")
        print("="*80)

    except Exception as e:
        print(f"\n[錯誤] 匯入過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()

    finally:
        master.close()
        print("\n已關閉 Neo4j 連線")


if __name__ == "__main__":
    main()
