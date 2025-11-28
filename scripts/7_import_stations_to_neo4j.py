# -*- coding: utf-8 -*-
"""將測站資料匯入 Neo4j 知識圖譜 (使用最詳細的原始資料)"""
import pandas as pd
from neo4j import GraphDatabase
from pathlib import Path


class StationImporter:
    """測站資料匯入器"""

    def __init__(self, uri, user, password):
        """初始化 Neo4j 連線"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """關閉連線"""
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
        """匯入雨量測站 (第一個工作表)

        Args:
            excel_path: 測站基本資料2025.xlsx 的路徑
        """
        print(f"\n讀取雨量測站資料 (詳細版): {excel_path}")

        # 讀取第一個工作表 (雨量測站)
        df = pd.read_excel(excel_path, sheet_name=0)
        print(f"  共 {len(df)} 個雨量測站")
        print(f"  欄位: {list(df.columns)}")

        # 建立雨量測站節點
        print("\n建立雨量測站節點 (Station:Rainfall)...")

        # 取得實際欄位
        cols = list(df.columns)

        with self.driver.session(database="neo4j") as session:
            for idx, row in df.iterrows():
                # 雨量測站欄位對應:
                # cols[0] = 類別
                # cols[1] = 存廢狀態
                # cols[2] = 測站代號 (站號, 如 2560P008)
                # cols[3] = 氣象署站號 (如 01U050)
                # cols[4] = 測站名稱 (如 士場(1))
                # cols[5] = 管理單位
                # cols[6] = 水系
                # cols[7] = 河川
                # cols[8] = 高程(m)
                # cols[9] = 縣市
                # cols[10] = 地址
                # cols[11-12] = TWD97 座標
                # cols[13] = 替代站號
                # cols[14] = 分雨量 (有資料的年份)
                # cols[15] = 時雨量 (有資料的年份)
                # cols[16] = 日雨量 (有資料的年份)
                # cols[17] = 月雨量 (有資料的年份)
                session.run("""
                    MERGE (s:Station:Rainfall {code: $code})
                    SET s.name = $name,
                        s.type = '雨量測站',
                        s.category = $category,
                        s.status = $status,
                        s.cwa_station_code = $cwa_station_code,
                        s.management_unit = $management_unit,
                        s.water_system = $water_system,
                        s.river = $river,
                        s.elevation = $elevation,
                        s.city = $city,
                        s.address = $address,
                        s.x_twd97 = $x,
                        s.y_twd97 = $y,
                        s.backup_station_code = $backup_station_code,
                        s.rainfall_minute_years = $rainfall_minute_years,
                        s.rainfall_hour_years = $rainfall_hour_years,
                        s.rainfall_daily_years = $rainfall_daily_years,
                        s.rainfall_monthly_years = $rainfall_monthly_years
                """,
                    code=str(row[cols[2]]) if pd.notna(row[cols[2]]) else None,  # 測站代號
                    name=str(row[cols[4]]) if pd.notna(row[cols[4]]) else None,  # 測站名稱
                    category=str(row[cols[0]]) if pd.notna(row[cols[0]]) else None,  # 類別
                    status=str(row[cols[1]]) if pd.notna(row[cols[1]]) else None,  # 存廢狀態
                    cwa_station_code=str(row[cols[3]]) if pd.notna(row[cols[3]]) else None,  # 氣象署站號
                    management_unit=str(row[cols[5]]) if pd.notna(row[cols[5]]) else None,  # 管理單位
                    water_system=str(row[cols[6]]) if pd.notna(row[cols[6]]) else None,  # 水系
                    river=str(row[cols[7]]) if pd.notna(row[cols[7]]) else None,  # 河川
                    elevation=float(row[cols[8]]) if pd.notna(row[cols[8]]) else None,  # 高程(m)
                    city=str(row[cols[9]]) if pd.notna(row[cols[9]]) else None,  # 縣市
                    address=str(row[cols[10]]) if pd.notna(row[cols[10]]) else None,  # 地址
                    x=float(row[cols[11]]) if pd.notna(row[cols[11]]) else None,  # TWD97M2(X坐標)
                    y=float(row[cols[12]]) if pd.notna(row[cols[12]]) else None,  # TWD97M2(Y坐標)
                    backup_station_code=str(row[cols[13]]) if pd.notna(row[cols[13]]) else None,  # 替代站號
                    rainfall_minute_years=str(row[cols[14]]) if pd.notna(row[cols[14]]) else None,  # 分雨量
                    rainfall_hour_years=str(row[cols[15]]) if pd.notna(row[cols[15]]) else None,  # 時雨量
                    rainfall_daily_years=str(row[cols[16]]) if pd.notna(row[cols[16]]) else None,  # 日雨量
                    rainfall_monthly_years=str(row[cols[17]]) if pd.notna(row[cols[17]]) else None  # 月雨量
                )

                if (idx + 1) % 50 == 0:
                    print(f"  已匯入 {idx + 1}/{len(df)} 個雨量測站...")

        print(f"[OK] 已匯入 {len(df)} 個雨量測站")

    def import_water_level_stations(self, excel_path):
        """匯入水位測站 (第二個工作表)

        Args:
            excel_path: 測站基本資料2025.xlsx 的路徑
        """
        print(f"\n讀取水位測站資料 (詳細版)...")

        # 讀取第二個工作表 (水位測站)
        df = pd.read_excel(excel_path, sheet_name=1)
        print(f"  共 {len(df)} 個水位測站")
        print(f"  欄位: {list(df.columns)}")

        # 建立水位測站節點
        print("\n建立水位測站節點 (Station:WaterLevel)...")

        # 取得實際欄位
        cols = list(df.columns)

        with self.driver.session(database="neo4j") as session:
            for idx, row in df.iterrows():
                # 水位測站欄位對應 (沒有氣象署站號,比雨量站少1欄):
                # cols[0] = 類別
                # cols[1] = 存廢狀態
                # cols[2] = 站號 (測站代號)
                # cols[3] = 站名 (測站名稱)
                # cols[4] = 管理單位
                # cols[5] = 流域
                # cols[6] = 河川
                # cols[7] = 高程(m)
                # cols[8] = 縣市
                # cols[9] = 地址
                # cols[10-11] = TWD97 座標
                # cols[12] = 替代站號
                # cols[13] = 時水位 (有資料的年份)
                # cols[14] = 日水位 (有資料的年份)
                # cols[15] = 月水位 (有資料的年份)
                # cols[16] = 時流量 (有資料的年份)
                # cols[17] = 日流量 (有資料的年份)
                # cols[18] = 月流量 (有資料的年份)
                # cols[19] = 含砂量及實測流量 (有資料的年份)
                session.run("""
                    MERGE (s:Station:WaterLevel {code: $code})
                    SET s.name = $name,
                        s.type = '水位測站',
                        s.category = $category,
                        s.status = $status,
                        s.management_unit = $management_unit,
                        s.water_system = $water_system,
                        s.river = $river,
                        s.elevation = $elevation,
                        s.city = $city,
                        s.address = $address,
                        s.x_twd97 = $x,
                        s.y_twd97 = $y,
                        s.backup_station_code = $backup_station_code,
                        s.water_level_hour_years = $water_level_hour_years,
                        s.water_level_daily_years = $water_level_daily_years,
                        s.water_level_monthly_years = $water_level_monthly_years,
                        s.flow_hour_years = $flow_hour_years,
                        s.flow_daily_years = $flow_daily_years,
                        s.flow_monthly_years = $flow_monthly_years,
                        s.sediment_years = $sediment_years
                """,
                    code=str(row[cols[2]]) if pd.notna(row[cols[2]]) else None,  # 站號
                    name=str(row[cols[3]]) if pd.notna(row[cols[3]]) else None,  # 站名
                    category=str(row[cols[0]]) if pd.notna(row[cols[0]]) else None,  # 類別
                    status=str(row[cols[1]]) if pd.notna(row[cols[1]]) else None,  # 存廢狀態
                    management_unit=str(row[cols[4]]) if pd.notna(row[cols[4]]) else None,  # 管理單位
                    water_system=str(row[cols[5]]) if pd.notna(row[cols[5]]) else None,  # 流域
                    river=str(row[cols[6]]) if pd.notna(row[cols[6]]) else None,  # 河川
                    elevation=float(row[cols[7]]) if pd.notna(row[cols[7]]) else None,  # 高程(m)
                    city=str(row[cols[8]]) if pd.notna(row[cols[8]]) else None,  # 縣市
                    address=str(row[cols[9]]) if pd.notna(row[cols[9]]) else None,  # 地址
                    x=float(row[cols[10]]) if pd.notna(row[cols[10]]) else None,  # TWD97M2(X坐標)
                    y=float(row[cols[11]]) if pd.notna(row[cols[11]]) else None,  # TWD97M2(Y坐標)
                    backup_station_code=str(row[cols[12]]) if pd.notna(row[cols[12]]) else None,  # 替代站號
                    water_level_hour_years=str(row[cols[13]]) if pd.notna(row[cols[13]]) else None,  # 時水位
                    water_level_daily_years=str(row[cols[14]]) if pd.notna(row[cols[14]]) else None,  # 日水位
                    water_level_monthly_years=str(row[cols[15]]) if pd.notna(row[cols[15]]) else None,  # 月水位
                    flow_hour_years=str(row[cols[16]]) if pd.notna(row[cols[16]]) else None,  # 時流量
                    flow_daily_years=str(row[cols[17]]) if pd.notna(row[cols[17]]) else None,  # 日流量
                    flow_monthly_years=str(row[cols[18]]) if pd.notna(row[cols[18]]) else None,  # 月流量
                    sediment_years=str(row[cols[19]]) if pd.notna(row[cols[19]]) else None  # 含砂量及實測流量
                )

                if (idx + 1) % 50 == 0:
                    print(f"  已匯入 {idx + 1}/{len(df)} 個水位測站...")

        print(f"[OK] 已匯入 {len(df)} 個水位測站")

    def link_stations_to_rivers(self, matching_report_path):
        """建立測站 -> 河川關係 (使用配對報表，加入代碼驗證避免同名河川錯誤配對)

        Args:
            matching_report_path: 測站河川配對分析報表.xlsx 的路徑
        """
        print(f"\n建立測站 MONITORS 河川關係...")

        # 讀取「能配對的測站」工作表
        df = pd.read_excel(matching_report_path, sheet_name='能配對的測站')
        print(f"  共 {len(df)} 個能配對的測站")

        # 取得欄位列表
        cols = list(df.columns)

        with self.driver.session(database="neo4j") as session:
            count = 0
            skipped = 0
            code_mismatch = 0

            for idx, row in df.iterrows():
                # 更新後的欄位結構:
                # cols[0] = 測站類型
                # cols[1] = 測站代號
                # cols[2] = 測站名稱
                # cols[3] = 河川
                # cols[4] = 匹配的河川
                # cols[5] = 河川代碼
                # cols[6] = 匹配方式
                # cols[7] = 管理單位
                # cols[8] = 高程(m)

                station_code = str(row[cols[1]]).strip() if pd.notna(row[cols[1]]) and str(row[cols[1]]).strip() != '' else None
                river_code = str(row[cols[5]]) if pd.notna(row[cols[5]]) else None

                if station_code and river_code:
                    # ★ 代碼驗證: 測站代碼前綴應與河川代碼前綴匹配
                    # 避免同名河川錯誤配對 (例如: 北港溪在淡水河和雲林都有)
                    station_prefix_4 = station_code[:4]
                    river_prefix_4 = river_code[:4]
                    station_prefix_3 = station_code[:3]
                    river_prefix_3 = river_code[:3]

                    if station_prefix_4 != river_prefix_4 and station_prefix_3 != river_prefix_3:
                        # 代碼不匹配，跳過此配對
                        code_mismatch += 1
                        continue

                    # 使用測站代號來匹配,需要處理Neo4j中可能的尾隨空格
                    session.run("""
                        MATCH (s:Station)
                        WHERE trim(s.code) = $station_code
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
            print(f"[INFO] 過濾 {code_mismatch} 條代碼不匹配 (避免同名河川錯誤配對)")

    def link_stations_to_watersheds(self):
        """建立測站 -> 集水區關係 (根據集水區名稱)"""
        print("\n建立測站 LOCATED_IN 集水區關係...")

        with self.driver.session(database="neo4j") as session:
            # 使用測站的 watershed 屬性與集水區的 name 屬性配對
            result = session.run("""
                MATCH (s:Station)
                WHERE s.watershed IS NOT NULL
                MATCH (w:Watershed)
                WHERE w.name = s.watershed
                MERGE (s)-[:LOCATED_IN]->(w)
                RETURN count(*) as count
            """)

            count = result.single()["count"]

        print(f"[OK] 已建立 {count} 條測站-集水區關係")

    def verify_import(self):
        """驗證匯入結果"""
        print("\n" + "="*80)
        print("驗證測站匯入結果")
        print("="*80)

        with self.driver.session(database="neo4j") as session:
            # 統計節點數量
            total_stations = session.run(
                "MATCH (s:Station) RETURN count(s) as count"
            ).single()["count"]

            rainfall = session.run(
                "MATCH (s:Rainfall) RETURN count(s) as count"
            ).single()["count"]

            water_level = session.run(
                "MATCH (s:WaterLevel) RETURN count(s) as count"
            ).single()["count"]

            print(f"\n節點統計:")
            print(f"  Station 總數: {total_stations}")
            print(f"    - Rainfall (雨量測站): {rainfall}")
            print(f"    - WaterLevel (水位測站): {water_level}")

            # 統計關係數量
            monitors_count = session.run(
                "MATCH ()-[r:MONITORS]->() RETURN count(r) as count"
            ).single()["count"]

            located_in_count = session.run(
                "MATCH ()-[r:LOCATED_IN]->() RETURN count(r) as count"
            ).single()["count"]

            print(f"\n關係統計:")
            print(f"  MONITORS (監測河川): {monitors_count}")
            print(f"  LOCATED_IN (位於集水區): {located_in_count}")

            # 按管理單位統計
            print(f"\n測站管理單位分布 (前10):")
            result = session.run("""
                MATCH (s:Station)
                WHERE s.management_unit IS NOT NULL
                RETURN s.management_unit as unit, count(s) as count
                ORDER BY count DESC
                LIMIT 10
            """)

            for record in result:
                print(f"  - {record['unit']}: {record['count']} 個測站")

            # 顯示有座標的測站比例
            with_coords = session.run("""
                MATCH (s:Station)
                WHERE s.x_twd97 IS NOT NULL AND s.y_twd97 IS NOT NULL
                RETURN count(s) as count
            """).single()["count"]

            print(f"\n座標資料完整度:")
            print(f"  有座標的測站: {with_coords}/{total_stations} "
                  f"({with_coords/total_stations*100:.1f}%)")

            # 顯示範例雨量測站
            print(f"\n範例雨量測站 (前5個):")
            result = session.run("""
                MATCH (s:Rainfall)-[:MONITORS]->(r:River)
                RETURN s.name as station, s.river as river_in_station,
                       r.name as matched_river, s.elevation as elevation
                LIMIT 5
            """)

            for record in result:
                print(f"  - {record['station']} (高程{record['elevation']}m) → "
                      f"{record['matched_river']}")

            # 顯示範例水位測站
            print(f"\n範例水位測站 (前5個):")
            result = session.run("""
                MATCH (s:WaterLevel)
                RETURN s.name as station, s.watershed as watershed,
                       s.city as city, s.elevation as elevation
                LIMIT 5
            """)

            for record in result:
                print(f"  - {record['station']} ({record['city']}, "
                      f"高程{record['elevation']}m) → {record['watershed']}")


def main():
    """主程式"""
    print("="*80)
    print("測站資料匯入 Neo4j (詳細版)")
    print("="*80)

    # Neo4j 連線設定
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "geoinfor"  # 請改成您的密碼

    # 資料檔案路徑
    STATION_DATA_PATH = Path("data/測站基本資料2025.xlsx")
    MATCHING_REPORT_PATH = Path("data/測站河川配對分析報表.xlsx")

    # 確認檔案存在
    if not STATION_DATA_PATH.exists():
        print(f"[X] 找不到檔案: {STATION_DATA_PATH}")
        return

    if not MATCHING_REPORT_PATH.exists():
        print(f"[X] 找不到檔案: {MATCHING_REPORT_PATH}")
        return

    # 建立匯入器
    importer = StationImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        # 建立索引
        importer.create_indexes()

        # 匯入雨量測站 (第一個工作表)
        importer.import_rainfall_stations(STATION_DATA_PATH)

        # 匯入水位測站 (第二個工作表)
        importer.import_water_level_stations(STATION_DATA_PATH)

        # 建立測站 -> 河川關係
        importer.link_stations_to_rivers(MATCHING_REPORT_PATH)

        # 建立測站 -> 集水區關係
        importer.link_stations_to_watersheds()

        # 驗證結果
        importer.verify_import()

        print("\n" + "="*80)
        print("[OK] 測站資料匯入完成!")
        print("="*80)
        print("\n💡 提示: 請確保已先執行:")
        print("   - 5_import_rivers_to_neo4j.py (河川資料)")
        print("   - 6_import_watersheds_to_neo4j.py (集水區資料)")

    except Exception as e:
        print(f"\n[X] 發生錯誤: {e}")
        import traceback
        traceback.print_exc()

    finally:
        importer.close()
        print("\n已關閉 Neo4j 連線")


if __name__ == "__main__":
    main()
