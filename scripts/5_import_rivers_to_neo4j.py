# -*- coding: utf-8 -*-
"""將河川資料匯入 Neo4j 知識圖譜"""
import pandas as pd
from neo4j import GraphDatabase
from pathlib import Path
from data_utils import clean_dataframe  # 匯入資料清理工具


class RiverImporter:
    """河川資料匯入器"""

    def __init__(self, uri, user, password):
        """初始化 Neo4j 連線

        Args:
            uri: Neo4j 連線位址 (例如: bolt://localhost:7687)
            user: 使用者名稱
            password: 密碼
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """關閉連線"""
        self.driver.close()

    def clear_database(self):
        """清空資料庫 (謹慎使用!)"""
        print("[WARNING]  清空 Neo4j 資料庫...")
        with self.driver.session(database="neo4j") as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("[OK] 資料庫已清空")

    def create_indexes(self):
        """建立索引以提升查詢效能"""
        print("\n建立索引...")

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
        """匯入河川節點

        Args:
            excel_path: 河川關係_完整版.xlsx 的路徑
        """
        print(f"\n讀取河川資料: {excel_path}")
        df = pd.read_excel(excel_path)
        df = clean_dataframe(df)  # 清理資料（去除空格）
        print(f"  共 {len(df)} 條河川")

        # 建立河川節點
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
        """匯入水系節點並建立河川與水系的關係

        Args:
            excel_path: 河川關係_完整版.xlsx 的路徑
        """
        print(f"\n建立水系節點與關係...")
        df = pd.read_excel(excel_path)
        df = clean_dataframe(df)  # 清理資料（去除空格）

        # 取得所有唯一的水系
        water_systems = df['主流水系'].dropna().unique()
        print(f"  發現 {len(water_systems)} 個水系")

        # 建立水系節點
        with self.driver.session(database="neo4j") as session:
            for ws in water_systems:
                session.run("""
                    MERGE (w:WaterSystem {name: $name})
                """, name=str(ws))

        print(f"[OK] 已建立 {len(water_systems)} 個水系節點")

        # 建立河川 -> 水系關係
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
        """匯入河川階層關係 (支流 -> 主流)

        Args:
            excel_path: 河川關係_完整版.xlsx 的路徑
        """
        print("\n建立河川階層關係 (IS_TRIBUTARY_OF)...")
        df = pd.read_excel(excel_path)
        df = clean_dataframe(df)  # 清理資料（去除空格）

        # 建立河川名稱到代碼的映射
        river_name_to_code = dict(zip(df['河川名稱'], df['河川代碼']))

        with self.driver.session(database="neo4j") as session:
            count = 0
            for idx, row in df.iterrows():
                # 如果有上游河川 (parent)
                if pd.notna(row['上游河川']):
                    parent_name = str(row['上游河川'])

                    # 從映射中找到上游河川代碼
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
                            level_diff=1  # 階層差距
                        )
                        count += 1

                if (idx + 1) % 100 == 0:
                    print(f"  已處理 {idx + 1}/{len(df)} 條河川...")

        print(f"[OK] 已建立 {count} 條河川階層關係")

    def verify_import(self):
        """驗證匯入結果"""
        print("\n" + "="*80)
        print("驗證匯入結果")
        print("="*80)

        with self.driver.session(database="neo4j") as session:
            # 統計節點數量
            river_count = session.run("MATCH (r:River) RETURN count(r) as count").single()["count"]
            ws_count = session.run("MATCH (w:WaterSystem) RETURN count(w) as count").single()["count"]

            print(f"\n節點統計:")
            print(f"  River (河川): {river_count}")
            print(f"  WaterSystem (水系): {ws_count}")

            # 統計關係數量
            belongs_count = session.run(
                "MATCH ()-[r:BELONGS_TO]->() RETURN count(r) as count"
            ).single()["count"]

            tributary_count = session.run(
                "MATCH ()-[r:IS_TRIBUTARY_OF]->() RETURN count(r) as count"
            ).single()["count"]

            print(f"\n關係統計:")
            print(f"  BELONGS_TO (屬於水系): {belongs_count}")
            print(f"  IS_TRIBUTARY_OF (支流關係): {tributary_count}")

            # 按階層統計河川
            print(f"\n河川階層分布:")
            result = session.run("""
                MATCH (r:River)
                RETURN r.level as level, count(r) as count
                ORDER BY level
            """)

            for record in result:
                level = record["level"]
                count = record["count"]
                level_name = {1: "主流", 2: "支流", 3: "次支流", 4: "次次支流", 5: "次次次支流"}
                print(f"  階層 {level} ({level_name.get(level, '未知')}): {count} 條")

            # 顯示範例河川
            print(f"\n範例河川 (前5條主流):")
            result = session.run("""
                MATCH (r:River {level: 1})-[:BELONGS_TO]->(w:WaterSystem)
                RETURN r.name as name, r.code as code, w.name as water_system
                LIMIT 5
            """)

            for record in result:
                print(f"  - {record['name']} ({record['code']}) → {record['water_system']}")

            # 顯示範例階層關係
            print(f"\n範例階層關係 (前5條):")
            result = session.run("""
                MATCH (tributary:River)-[:IS_TRIBUTARY_OF]->(main:River)
                RETURN tributary.name as tributary, main.name as main,
                       tributary.level as t_level, main.level as m_level
                LIMIT 5
            """)

            for record in result:
                print(f"  - {record['tributary']} (階層{record['t_level']}) → "
                      f"{record['main']} (階層{record['m_level']})")


def main():
    """主程式"""
    print("="*80)
    print("河川資料匯入 Neo4j")
    print("="*80)

    # Neo4j 連線設定
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "geoinfor"  # 請改成您的密碼

    # 資料檔案路徑
    RIVER_DATA_PATH = Path("data/河川關係_完整版.xlsx")

    # 確認檔案存在
    if not RIVER_DATA_PATH.exists():
        print(f"[X] 找不到檔案: {RIVER_DATA_PATH}")
        return

    # 建立匯入器
    importer = RiverImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        # 詢問是否清空資料庫
        print("\n[WARNING]  警告: 此操作會清空 Neo4j 資料庫!")
        response = input("是否繼續? (yes/no): ")

        if response.lower() == 'yes':
            importer.clear_database()
        else:
            print("取消清空資料庫，將在現有資料上新增/更新")

        # 建立索引
        importer.create_indexes()

        # 匯入河川節點
        importer.import_rivers(RIVER_DATA_PATH)

        # 匯入水系與關係
        importer.import_water_systems(RIVER_DATA_PATH)

        # 匯入河川階層關係
        importer.import_river_hierarchy(RIVER_DATA_PATH)

        # 驗證結果
        importer.verify_import()

        print("\n" + "="*80)
        print("[OK] 河川資料匯入完成!")
        print("="*80)

    except Exception as e:
        print(f"\n[X] 發生錯誤: {e}")
        import traceback
        traceback.print_exc()

    finally:
        importer.close()
        print("\n已關閉 Neo4j 連線")


if __name__ == "__main__":
    main()
