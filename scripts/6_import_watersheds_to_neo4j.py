# -*- coding: utf-8 -*-
"""將集水區資料匯入 Neo4j 知識圖譜"""
import pandas as pd
from neo4j import GraphDatabase
from pathlib import Path
from data_utils import clean_dataframe  # 匯入資料清理工具


class WatershedImporter:
    """集水區資料匯入器"""

    def __init__(self, uri, user, password):
        """初始化 Neo4j 連線"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """關閉連線"""
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
        """匯入流域節點

        Args:
            excel_path: 集水區分析報表.xlsx 的路徑
        """
        print(f"\n讀取流域統計資料: {excel_path}")

        # 讀取「流域統計」工作表
        df = pd.read_excel(excel_path, sheet_name='流域統計')
        df = clean_dataframe(df)  # 清理資料（去除空格）
        print(f"  共 {len(df)} 個流域")

        # 建立流域節點
        print("\n建立流域節點 (Basin)...")

        # 取得欄位列表
        cols = list(df.columns)

        with self.driver.session(database="neo4j") as session:
            for idx, row in df.iterrows():
                # 流域名稱在 BASIN_NAME 欄位
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
                        watershed_count=int(row[cols[1]]) if pd.notna(row[cols[1]]) else 0,  # 集水區數量
                        river_count=int(row[cols[2]]) if pd.notna(row[cols[2]]) else 0,  # 關聯河川總數
                        area_km2=float(row[cols[4]]) if pd.notna(row[cols[4]]) else 0.0,  # 總面積(km2)
                        avg_area_km2=float(row[cols[3]]) if pd.notna(row[cols[3]]) else 0.0  # 平均集水區面積(km2)
                    )

        print(f"[OK] 已匯入 {len(df)} 個流域節點")

    def import_watersheds(self, excel_path):
        """匯入集水區節點

        Args:
            excel_path: 集水區分析報表.xlsx 的路徑
        """
        print(f"\n讀取集水區資料...")

        # 讀取「集水區列表」工作表
        df = pd.read_excel(excel_path, sheet_name='集水區列表')
        df = clean_dataframe(df)  # 清理資料（去除空格）
        print(f"  共 {len(df)} 個集水區")

        # 建立集水區節點
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
        """建立集水區 -> 流域關係

        Args:
            excel_path: 集水區分析報表.xlsx 的路徑
        """
        print("\n建立集水區 PART_OF 流域關係...")

        df = pd.read_excel(excel_path, sheet_name='集水區列表')
        df = clean_dataframe(df)  # 清理資料（去除空格）

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
        """建立集水區 -> 河川關係

        Args:
            excel_path: 集水區分析報表.xlsx 的路徑
        """
        print("\n建立集水區 CONTAINS_RIVER 河川關係...")

        # 讀取「集水區-河川關聯」工作表
        df = pd.read_excel(excel_path, sheet_name='集水區-河川關聯')
        df = clean_dataframe(df)  # 清理資料（去除空格）
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

    def verify_import(self):
        """驗證匯入結果"""
        print("\n" + "="*80)
        print("驗證集水區匯入結果")
        print("="*80)

        with self.driver.session(database="neo4j") as session:
            # 統計節點數量
            basin_count = session.run(
                "MATCH (b:Basin) RETURN count(b) as count"
            ).single()["count"]

            watershed_count = session.run(
                "MATCH (w:Watershed) RETURN count(w) as count"
            ).single()["count"]

            print(f"\n節點統計:")
            print(f"  Basin (流域): {basin_count}")
            print(f"  Watershed (集水區): {watershed_count}")

            # 統計關係數量
            part_of_count = session.run(
                "MATCH ()-[r:PART_OF]->() RETURN count(r) as count"
            ).single()["count"]

            contains_count = session.run(
                "MATCH ()-[r:CONTAINS_RIVER]->() RETURN count(r) as count"
            ).single()["count"]

            print(f"\n關係統計:")
            print(f"  PART_OF (集水區屬於流域): {part_of_count}")
            print(f"  CONTAINS_RIVER (集水區包含河川): {contains_count}")

            # 顯示前5大流域
            print(f"\n前5大流域 (按集水區數量):")
            result = session.run("""
                MATCH (b:Basin)
                RETURN b.name as name,
                       b.watershed_count as ws_count,
                       b.area_km2 as area
                ORDER BY b.watershed_count DESC
                LIMIT 5
            """)

            for record in result:
                print(f"  - {record['name']}: {record['ws_count']} 個集水區, "
                      f"{record['area']:.1f} km²")

            # 顯示範例集水區
            print(f"\n範例集水區 (前5個):")
            result = session.run("""
                MATCH (w:Watershed)-[:PART_OF]->(b:Basin)
                RETURN w.name as ws_name, w.area_km2 as area,
                       b.name as basin_name, w.river_count as river_count
                LIMIT 5
            """)

            for record in result:
                print(f"  - {record['ws_name']} ({record['area']:.2f} km²) → "
                      f"{record['basin_name']}, 包含 {record['river_count']} 條河川")

            # 顯示集水區-河川關聯範例
            print(f"\n集水區-河川關聯範例 (前5條):")
            result = session.run("""
                MATCH (w:Watershed)-[rel:CONTAINS_RIVER]->(r:River)
                RETURN w.name as watershed, r.name as river,
                       rel.river_level as level, r.main_stream as water_system
                LIMIT 5
            """)

            for record in result:
                print(f"  - {record['watershed']} ⊃ {record['river']} "
                      f"(階層{record['level']}, {record['water_system']})")


def main():
    """主程式"""
    print("="*80)
    print("集水區資料匯入 Neo4j")
    print("="*80)

    # Neo4j 連線設定
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "geoinfor"  # 請改成您的密碼

    # 資料檔案路徑
    WATERSHED_DATA_PATH = Path("data/集水區分析報表.xlsx")

    # 確認檔案存在
    if not WATERSHED_DATA_PATH.exists():
        print(f"[X] 找不到檔案: {WATERSHED_DATA_PATH}")
        return

    # 建立匯入器
    importer = WatershedImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        # 建立索引
        importer.create_indexes()

        # 匯入流域節點
        importer.import_basins(WATERSHED_DATA_PATH)

        # 匯入集水區節點
        importer.import_watersheds(WATERSHED_DATA_PATH)

        # 建立集水區 -> 流域關係
        importer.link_watersheds_to_basins(WATERSHED_DATA_PATH)

        # 建立集水區 -> 河川關係
        importer.link_watersheds_to_rivers(WATERSHED_DATA_PATH)

        # 驗證結果
        importer.verify_import()

        print("\n" + "="*80)
        print("[OK] 集水區資料匯入完成!")
        print("="*80)
        print("\n💡 提示: 請確保已先執行 5_import_rivers_to_neo4j.py 匯入河川資料")

    except Exception as e:
        print(f"\n[X] 發生錯誤: {e}")
        import traceback
        traceback.print_exc()

    finally:
        importer.close()
        print("\n已關閉 Neo4j 連線")


if __name__ == "__main__":
    main()
