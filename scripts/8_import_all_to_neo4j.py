# -*- coding: utf-8 -*-
"""一鍵匯入所有資料到 Neo4j"""
import sys
from pathlib import Path

# 匯入各個匯入器
sys.path.append(str(Path(__file__).parent))

from neo4j import GraphDatabase
from data_utils import clean_dataframe  # 匯入資料清理工具


def migrate_schema(uri, user, password):
    """Schema 遷移: 轉換為 DIFY 兼容格式"""
    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session(database="neo4j") as session:
        # 1. IS_TRIBUTARY_OF → FLOWS_INTO (反向)
        print("  轉換 IS_TRIBUTARY_OF → FLOWS_INTO...")
        result = session.run("""
            MATCH (child:River)-[r:IS_TRIBUTARY_OF]->(parent:River)
            MERGE (child)-[:FLOWS_INTO]->(parent)
            DELETE r
            RETURN count(r) as count
        """)
        count = result.single()['count']
        print(f"    [OK] 轉換 {count} 條河川支流關係")

        # 2. MONITORS → LOCATED_ON
        print("  轉換 MONITORS → LOCATED_ON...")
        result = session.run("""
            MATCH (s:Station)-[r:MONITORS]->(river:River)
            MERGE (s)-[:LOCATED_ON]->(river)
            DELETE r
            RETURN count(r) as count
        """)
        count = result.single()['count']
        print(f"    [OK] 轉換 {count} 條測站監測關係")

        # 3. 驗證無代碼不匹配的錯誤
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

    def __init__(self, uri, user, password, database="hydrograph-tw"):
        """初始化 Neo4j 連線"""
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """關閉連線"""
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

    def clear_database(self):
        """清空資料庫"""
        print("\n[警告] 清空 Neo4j 資料庫...")
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
            # 節點統計
            print("\n【節點統計】")

            node_types = [
                ("River", "河川"),
                ("WaterSystem", "水系"),
                ("Basin", "流域"),
                ("Watershed", "集水區"),
                ("Station", "測站 (總數)"),
                ("Rainfall", "  - 雨量測站"),
                ("WaterLevel", "  - 水位測站"),
            ]

            for node_type, desc in node_types:
                count = session.run(
                    f"MATCH (n:{node_type}) RETURN count(n) as count"
                ).single()["count"]
                print(f"  {desc}: {count}")

            # 關係統計
            print("\n【關係統計】")

            rel_types = [
                ("FLOWS_INTO", "河川流向關係 (DIFY Schema)"),
                ("BELONGS_TO", "河川屬於水系"),
                ("PART_OF", "集水區屬於流域"),
                ("DRAINS_TO", "集水區排入河川"),
                ("LOCATED_ON", "測站位於河川 (DIFY Schema)"),
                # ("LOCATED_IN", "測站位於集水區"),  # 未實作，透過河川間接查詢
            ]

            for rel_type, desc in rel_types:
                count = session.run(
                    f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
                ).single()["count"]
                print(f"  {desc}: {count}")

            # 資料完整度
            print("\n【資料完整度】")

            # 有測站監測的河川比例
            result = session.run("""
                MATCH (r:River)
                OPTIONAL MATCH (s:Station)-[:LOCATED_ON]->(r)
                WITH r, count(s) as station_count
                RETURN
                    sum(CASE WHEN station_count > 0 THEN 1 ELSE 0 END) as with_stations,
                    count(r) as total
            """).single()

            with_stations = result["with_stations"]
            total_rivers = result["total"]
            print(f"  有測站監測的河川: {with_stations}/{total_rivers} "
                  f"({with_stations/total_rivers*100:.1f}%)")

            # 有座標的測站比例
            result = session.run("""
                MATCH (s:Station)
                WITH count(s) as total,
                     sum(CASE WHEN s.x_twd97 IS NOT NULL AND s.y_twd97 IS NOT NULL
                         THEN 1 ELSE 0 END) as with_coords
                RETURN total, with_coords
            """).single()

            with_coords = result["with_coords"]
            total_stations = result["total"]
            print(f"  有座標的測站: {with_coords}/{total_stations} "
                  f"({with_coords/total_stations*100:.1f}%)")

            # 複雜查詢範例
            print("\n【知識圖譜能力展示】")

            # 範例1: 找出淡水河流域的所有測站
            print("\n1. 淡水河水系的監測網路:")
            result = session.run("""
                MATCH (ws:WaterSystem {name: '淡水河'})
                MATCH (r:River)-[:BELONGS_TO]->(ws)
                MATCH (s:Station)-[:LOCATED_ON]->(r)
                RETURN ws.name as water_system,
                       count(DISTINCT r) as river_count,
                       count(DISTINCT s) as station_count
            """).single()

            if result:
                print(f"   水系: {result['water_system']}")
                print(f"   包含河川: {result['river_count']} 條")
                print(f"   監測站數: {result['station_count']} 個")

            # 範例2: 找出監測站最多的前5條河川
            print("\n2. 監測站最多的河川 (前5名):")
            result = session.run("""
                MATCH (s:Station)-[:LOCATED_ON]->(r:River)
                WITH r, count(s) as station_count
                ORDER BY station_count DESC
                LIMIT 5
                RETURN r.name as river, r.level as level, station_count
            """)

            for record in result:
                level_name = {1: "主流", 2: "支流", 3: "次支流", 4: "次次支流", 5: "次次次支流"}
                print(f"   - {record['river']} ({level_name.get(record['level'], '未知')}): "
                      f"{record['station_count']} 個測站")

            # 範例3: 河川階層深度統計
            print("\n3. 河川網路結構:")
            result = session.run("""
                MATCH (r:River)
                RETURN r.level as level, count(r) as count
                ORDER BY level
            """)

            level_names = {1: "主流", 2: "支流", 3: "次支流", 4: "次次支流", 5: "次次次支流"}
            for record in result:
                level = record['level']
                count = record['count']
                print(f"   階層{level} ({level_names.get(level, '未知')}): {count} 條")

            # 範例4: 集水區覆蓋度
            print("\n4. 集水區監測覆蓋度 (前5大流域):")
            result = session.run("""
                MATCH (b:Basin)<-[:PART_OF]-(w:Watershed)
                OPTIONAL MATCH (s:Station)-[:LOCATED_IN]->(w)
                WITH b, count(DISTINCT w) as ws_count, count(DISTINCT s) as station_count
                ORDER BY b.area_km2 DESC
                LIMIT 5
                RETURN b.name as basin, ws_count, station_count, b.area_km2 as area
            """)

            for record in result:
                print(f"   - {record['basin']}: {record['ws_count']} 個集水區, "
                      f"{record['station_count']} 個測站, {record['area']:.1f} km²")


def main():
    """主程式 - 一鍵匯入所有資料"""
    print("="*80)
    print("HydroGraph-TW 完整資料匯入 Neo4j")
    print("台灣水文知識圖譜建置")
    print("="*80)

    # Neo4j 連線設定
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "geoinfor"  # 請改成您的密碼

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

    # 建立主匯入器
    master = MasterImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    # 測試連線
    if not master.test_connection():
        print("\n[錯誤] 無法連線到 Neo4j，請檢查:")
        print("  1. Neo4j 是否已啟動")
        print("  2. 連線位址是否正確 (預設: bolt://localhost:7687)")
        print("  3. 帳號密碼是否正確")
        master.close()
        return

    try:
        # 清空資料庫 (可選)
        cleared = master.clear_database()

        print("\n" + "="*80)
        print("開始匯入資料...")
        print("="*80)

        # 步驟 1: 匯入河川資料
        print("\n【步驟 1/3】匯入河川與水系資料")
        print("-" * 80)
        from importlib import import_module
        river_module = import_module('5_import_rivers_to_neo4j')
        river_importer = river_module.RiverImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

        if not cleared:
            # 如果沒有清空，就不需要再建立索引
            pass
        else:
            river_importer.create_indexes()

        river_importer.import_rivers(Path("data/河川關係_完整版.xlsx"))
        river_importer.import_water_systems(Path("data/河川關係_完整版.xlsx"))
        river_importer.import_river_hierarchy(Path("data/河川關係_完整版.xlsx"))
        river_importer.close()

        # 步驟 2: 匯入集水區資料
        print("\n【步驟 2/3】匯入集水區與流域資料")
        print("-" * 80)
        watershed_module = import_module('6_import_watersheds_to_neo4j')
        watershed_importer = watershed_module.WatershedImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

        watershed_importer.create_indexes()
        watershed_importer.import_basins(Path("data/集水區分析報表.xlsx"))
        watershed_importer.import_watersheds(Path("data/集水區分析報表.xlsx"))
        watershed_importer.link_watersheds_to_basins(Path("data/集水區分析報表.xlsx"))
        watershed_importer.link_watersheds_to_rivers(Path("data/集水區分析報表.xlsx"))
        watershed_importer.close()

        # 步驟 3: 匯入測站資料
        print("\n【步驟 3/3】匯入測站資料 (雨量站 + 水位站)")
        print("-" * 80)
        station_module = import_module('7_import_stations_to_neo4j')
        station_importer = station_module.StationImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

        station_importer.create_indexes()
        station_importer.import_rainfall_stations(Path("data/測站基本資料2025.xlsx"))
        station_importer.import_water_level_stations(Path("data/測站基本資料2025.xlsx"))
        station_importer.link_stations_to_rivers(Path("data/測站河川配對分析報表.xlsx"))
        # station_importer.link_stations_to_watersheds()
        # ↑ 未實作原因：
        # 1. 測站資料(水利署)沒有集水區欄位，只有「流域」(=水系名稱，如淡水河)
        # 2. 集水區資料(水保署)的命名方式不同，無法直接配對
        # 3. 可透過河川間接查詢：Station-[:LOCATED_ON]->River<-[:DRAINS_TO]-Watershed
        station_importer.close()

        # 步驟 4: Schema 遷移 (DIFY 兼容格式)
        print("\n【步驟 4/4】Schema 遷移 (MONITORS→LOCATED_ON, IS_TRIBUTARY_OF→FLOWS_INTO)")
        print("-" * 80)
        migrate_schema(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

        # 顯示最終統計
        master.show_final_statistics()

        print("\n" + "="*80)
        print("[完成] 所有資料匯入完成!")
        print("="*80)

        print("\n台灣水文知識圖譜已成功建置!")
        print("\n您現在可以:")
        print("  1. 使用 Neo4j Browser 查看圖譜: http://localhost:7474")
        print("  2. 執行 Cypher 查詢分析水文資料")
        print("  3. 開發 GraphRAG 應用")
        print("  4. 使用 NeoDash 視覺化: docker start neodash → http://localhost:5005")

        print("\n💡 查詢範例 (使用 DIFY Schema):")
        print("  - 找出淡水河流域所有測站:")
        print("    MATCH (ws:WaterSystem {name: '淡水河'})")
        print("    MATCH (r:River)-[:BELONGS_TO]->(ws)")
        print("    MATCH (s:Station)-[:LOCATED_ON]->(r)")
        print("    RETURN s.name, r.name")

    except Exception as e:
        print(f"\n[錯誤] 匯入過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()

    finally:
        master.close()
        print("\n已關閉 Neo4j 連線")


if __name__ == "__main__":
    main()
