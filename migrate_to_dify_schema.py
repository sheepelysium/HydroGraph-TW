# -*- coding: utf-8 -*-
"""Neo4j Schema 遷移: 從原始 Schema 轉換為 DIFY 兼容 Schema

原始 Schema:
- River -[:IS_TRIBUTARY_OF]-> River (支流關係)
- Station -[:MONITORS]-> River (監測關係)

DIFY Schema (更直觀):
- River -[:FLOWS_INTO]-> River (流向關係,反向更直觀)
- Station -[:LOCATED_ON]-> River (位置關係,更清楚)

重要: 使用河川代碼 (code) 而非名稱,避免同名河川配對錯誤!
"""

from neo4j import GraphDatabase
import pandas as pd
from pathlib import Path

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "geoinfor"
NEO4J_DATABASE = "neo4j"


class SchemaM migrator:
    """Schema 遷移器"""

    def __init__(self, uri, user, password, database="neo4j"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        self.driver.close()

    def backup_current_schema(self):
        """備份當前 Schema 資訊"""
        print("=" * 80)
        print("備份當前 Schema")
        print("=" * 80)
        print()

        with self.driver.session(database=self.database) as session:
            # 統計現有關係
            print("現有關係統計:")

            for rel_type in ['IS_TRIBUTARY_OF', 'MONITORS', 'FLOWS_INTO', 'LOCATED_ON']:
                result = session.run(f"""
                    MATCH ()-[r:{rel_type}]->()
                    RETURN count(r) as count
                """)
                count = result.single()['count']
                print(f"  {rel_type}: {count} 條")

            print()

    def migrate_tributary_to_flows(self):
        """遷移: IS_TRIBUTARY_OF -> FLOWS_INTO

        邏輯: A -[:IS_TRIBUTARY_OF]-> B
             轉換為: A -[:FLOWS_INTO]-> B

        注意: 方向相同,只是語意更清楚
        """
        print("=" * 80)
        print("步驟 1: 遷移河川關係 IS_TRIBUTARY_OF -> FLOWS_INTO")
        print("=" * 80)
        print()

        with self.driver.session(database=self.database) as session:
            # 檢查是否已有 FLOWS_INTO
            result = session.run("""
                MATCH ()-[r:FLOWS_INTO]->()
                RETURN count(r) as count
            """)
            existing = result.single()['count']

            if existing > 0:
                print(f"[INFO] 已存在 {existing} 條 FLOWS_INTO 關係")
                confirm = input("是否刪除並重建? (yes/no): ")
                if confirm.lower() not in ['yes', 'y']:
                    print("[SKIP] 跳過此步驟")
                    return

                # 刪除現有的 FLOWS_INTO
                session.run("MATCH ()-[r:FLOWS_INTO]->() DELETE r")
                print(f"[OK] 已刪除 {existing} 條舊的 FLOWS_INTO 關係")

            # 從 IS_TRIBUTARY_OF 複製到 FLOWS_INTO
            print("\n從 IS_TRIBUTARY_OF 建立 FLOWS_INTO...")
            result = session.run("""
                MATCH (tributary:River)-[old:IS_TRIBUTARY_OF]->(main:River)
                MERGE (tributary)-[new:FLOWS_INTO]->(main)
                SET new.level_diff = old.level_diff
                RETURN count(new) as created
            """)

            created = result.single()['created']
            print(f"[OK] 建立了 {created} 條 FLOWS_INTO 關係")

            # 驗證: 檢查是否有跨水系錯誤
            print("\n驗證: 檢查跨水系錯誤...")
            result = session.run("""
                MATCH (from:River)-[r:FLOWS_INTO]->(to:River)
                WHERE from.main_stream <> to.main_stream
                  AND from.main_stream <> to.name
                RETURN count(r) as wrong_count
            """)

            wrong_count = result.single()['wrong_count']
            if wrong_count > 0:
                print(f"[WARNING] 發現 {wrong_count} 條跨水系錯誤!")
                print("          稍後將自動修正...")
            else:
                print("[OK] 無跨水系錯誤")

            print()

    def migrate_monitors_to_located_on(self):
        """遷移: MONITORS -> LOCATED_ON

        邏輯: Station -[:MONITORS]-> River
             轉換為: Station -[:LOCATED_ON]-> River

        注意: 使用河川代碼配對,避免同名河川問題!
        """
        print("=" * 80)
        print("步驟 2: 遷移測站關係 MONITORS -> LOCATED_ON")
        print("=" * 80)
        print()

        with self.driver.session(database=self.database) as session:
            # 檢查是否已有 LOCATED_ON
            result = session.run("""
                MATCH ()-[r:LOCATED_ON]->()
                RETURN count(r) as count
            """)
            existing = result.single()['count']

            if existing > 0:
                print(f"[INFO] 已存在 {existing} 條 LOCATED_ON 關係")
                confirm = input("是否刪除並重建? (yes/no): ")
                if confirm.lower() not in ['yes', 'y']:
                    print("[SKIP] 跳過此步驟")
                    return

                # 刪除現有的 LOCATED_ON
                session.run("MATCH ()-[r:LOCATED_ON]->() DELETE r")
                print(f"[OK] 已刪除 {existing} 條舊的 LOCATED_ON 關係")

            # 從 MONITORS 複製到 LOCATED_ON
            print("\n從 MONITORS 建立 LOCATED_ON...")
            result = session.run("""
                MATCH (station:Station)-[old:MONITORS]->(river:River)
                MERGE (station)-[new:LOCATED_ON]->(river)
                SET new.match_type = old.match_type,
                    new.original_river_name = old.original_river_name,
                    new.matched_river_name = old.matched_river_name
                RETURN count(new) as created
            """)

            created = result.single()['created']
            print(f"[OK] 建立了 {created} 條 LOCATED_ON 關係")

            print()

    def fix_cross_water_system_flows(self):
        """修正跨水系的 FLOWS_INTO 錯誤"""
        print("=" * 80)
        print("步驟 3: 修正跨水系錯誤")
        print("=" * 80)
        print()

        with self.driver.session(database=self.database) as session:
            # 找出所有跨水系錯誤
            result = session.run("""
                MATCH (from:River)-[r:FLOWS_INTO]->(to:River)
                WHERE from.main_stream <> to.main_stream
                  AND from.main_stream <> to.name
                RETURN count(r) as total
            """)

            total = result.single()['total']
            if total == 0:
                print("[OK] 無跨水系錯誤")
                return

            print(f"發現 {total} 條跨水系錯誤關係")
            print("\n刪除這些錯誤關係...")

            result = session.run("""
                MATCH (from:River)-[r:FLOWS_INTO]->(to:River)
                WHERE from.main_stream <> to.main_stream
                  AND from.main_stream <> to.name
                DELETE r
                RETURN count(r) as deleted
            """)

            deleted = result.single()['deleted']
            print(f"[OK] 已刪除 {deleted} 條錯誤關係")

            print()

    def fix_duplicate_located_on(self):
        """修正測站連到多條同名河川的錯誤"""
        print("=" * 80)
        print("步驟 4: 修正測站重複配對")
        print("=" * 80)
        print()

        with self.driver.session(database=self.database) as session:
            # 找出連到多條同名河川的測站
            result = session.run("""
                MATCH (s:Station)-[:LOCATED_ON]->(r:River)
                WITH s, r.name as river_name, count(*) as rel_count
                WHERE rel_count > 1
                RETURN count(s) as duplicate_count
            """)

            duplicate_count = result.single()['duplicate_count']
            if duplicate_count == 0:
                print("[OK] 無重複配對")
                return

            print(f"發現 {duplicate_count} 個測站連到多條同名河川")

            # 找出所有這樣的測站
            result = session.run("""
                MATCH (s:Station)-[:LOCATED_ON]->(r:River)
                WITH s, r.name as river_name, count(*) as rel_count
                WHERE rel_count > 1
                RETURN s.name as station_name, s.river as station_river, river_name
            """)

            multi_connections = list(result)
            deleted_count = 0

            print("\n刪除錯誤配對 (保留 main_stream 與測站 river 欄位相符的)...")

            for mc in multi_connections:
                station_name = mc['station_name']
                station_river = mc['station_river']
                river_name = mc['river_name']

                # 刪除不符合的連接
                result = session.run("""
                    MATCH (s:Station {name: $station_name})-[r:LOCATED_ON]->(river:River {name: $river_name})
                    WHERE NOT (
                        $station_river CONTAINS river.main_stream
                        OR river.main_stream CONTAINS $station_river
                        OR $station_river = river.name
                    )
                    DELETE r
                    RETURN count(r) as deleted
                """, station_name=station_name, river_name=river_name, station_river=station_river)

                deleted = result.single()['deleted']
                deleted_count += deleted

            print(f"[OK] 已刪除 {deleted_count} 條錯誤配對")

            print()

    def add_missing_flows(self, excel_path):
        """補充缺失的 FLOWS_INTO 關係

        使用原始 Excel 資料,根據「上游河川代碼」欄位建立關係
        """
        print("=" * 80)
        print("步驟 5: 補充缺失的流向關係")
        print("=" * 80)
        print()

        if not Path(excel_path).exists():
            print(f"[SKIP] 找不到檔案: {excel_path}")
            return

        print(f"讀取原始河川資料: {excel_path}")
        df = pd.read_excel(excel_path)

        with self.driver.session(database=self.database) as session:
            added_count = 0
            skipped_count = 0

            for idx, row in df.iterrows():
                # 檢查是否有「上游河川代碼」欄位
                if '上游河川代碼' not in df.columns or pd.isna(row.get('上游河川代碼')):
                    continue

                from_code = str(row['河川代碼']).strip()
                to_code = str(row['上游河川代碼']).strip()

                # 使用 code 配對,確保唯一性
                result = session.run("""
                    MATCH (from:River {code: $from_code})
                    MATCH (to:River {code: $to_code})
                    WHERE from.main_stream = to.main_stream OR from.main_stream = to.name
                    MERGE (from)-[:FLOWS_INTO]->(to)
                    RETURN count(*) as created
                """, from_code=from_code, to_code=to_code)

                if result.single()['created'] > 0:
                    added_count += 1
                else:
                    skipped_count += 1

                if (idx + 1) % 100 == 0:
                    print(f"  已處理 {idx + 1}/{len(df)} 條...")

        print(f"[OK] 新增了 {added_count} 條 FLOWS_INTO 關係")
        if skipped_count > 0:
            print(f"[INFO] 略過 {skipped_count} 條 (已存在或資料不完整)")

        print()

    def verify_migration(self):
        """驗證遷移結果"""
        print("=" * 80)
        print("驗證遷移結果")
        print("=" * 80)
        print()

        with self.driver.session(database=self.database) as session:
            # 統計所有關係
            print("關係統計:")
            for rel_type in ['IS_TRIBUTARY_OF', 'MONITORS', 'FLOWS_INTO', 'LOCATED_ON']:
                result = session.run(f"""
                    MATCH ()-[r:{rel_type}]->()
                    RETURN count(r) as count
                """)
                count = result.single()['count']
                symbol = "[OLD]" if rel_type in ['IS_TRIBUTARY_OF', 'MONITORS'] else "[NEW]"
                print(f"  {symbol} {rel_type}: {count} 條")

            print()

            # 檢查錯誤
            print("錯誤檢查:")

            # 1. 跨水系錯誤
            result = session.run("""
                MATCH (from:River)-[r:FLOWS_INTO]->(to:River)
                WHERE from.main_stream <> to.main_stream
                  AND from.main_stream <> to.name
                RETURN count(r) as count
            """)
            cross_system = result.single()['count']
            status = "[OK]" if cross_system == 0 else "[ERROR]"
            print(f"  {status} 跨水系 FLOWS_INTO: {cross_system} 條")

            # 2. 重複配對
            result = session.run("""
                MATCH (s:Station)-[:LOCATED_ON]->(r:River)
                WITH s, r.name as river_name, count(*) as rel_count
                WHERE rel_count > 1
                RETURN count(s) as count
            """)
            duplicate = result.single()['count']
            status = "[OK]" if duplicate == 0 else "[ERROR]"
            print(f"  {status} 測站重複配對: {duplicate} 個")

            print()

            # 驗證淡水河流域
            print("淡水河流域驗證:")
            test_rivers = [
                ('北勢溪', '114022'),
                ('南勢溪', '114021'),
                ('新店溪', '114020'),
                ('大漢溪', '114010'),
                ('基隆河', '114030'),
            ]

            for river_name, river_code in test_rivers:
                # 測站數量
                result = session.run("""
                    MATCH (s:Station)-[:LOCATED_ON]->(r:River {name: $name, code: $code})
                    RETURN count(s) as station_count
                """, name=river_name, code=river_code)
                station_count = result.single()['station_count']

                # 流向
                result = session.run("""
                    MATCH (r:River {name: $name, code: $code})-[:FLOWS_INTO]->(target)
                    RETURN target.name as flows_to
                """, name=river_name, code=river_code)

                flows_to_record = result.single()
                flows_to = flows_to_record['flows_to'] if flows_to_record else '(無)'

                print(f"  {river_name} ({river_code}): {station_count} 個測站, 流向 {flows_to}")

            print()


def main():
    print("=" * 80)
    print("Neo4j Schema 遷移工具")
    print("從原始 Schema 轉換為 DIFY 兼容 Schema")
    print("=" * 80)
    print()

    print("目標:")
    print("  IS_TRIBUTARY_OF -> FLOWS_INTO (流向關係)")
    print("  MONITORS -> LOCATED_ON (位置關係)")
    print()

    print("注意事項:")
    print("  1. 使用河川代碼 (code) 配對,避免同名河川錯誤")
    print("  2. 自動修正跨水系錯誤")
    print("  3. 自動修正測站重複配對")
    print("  4. 可選擇保留舊關係或刪除")
    print()

    confirm = input("確認開始遷移? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("取消遷移")
        return

    migrator = SchemaMigrator(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE)

    try:
        # 步驟 0: 備份當前狀態
        migrator.backup_current_schema()

        # 步驟 1: IS_TRIBUTARY_OF -> FLOWS_INTO
        migrator.migrate_tributary_to_flows()

        # 步驟 2: MONITORS -> LOCATED_ON
        migrator.migrate_monitors_to_located_on()

        # 步驟 3: 修正跨水系錯誤
        migrator.fix_cross_water_system_flows()

        # 步驟 4: 修正重複配對
        migrator.fix_duplicate_located_on()

        # 步驟 5: 補充缺失的流向
        excel_path = "data/河川關係_完整版.xlsx"
        migrator.add_missing_flows(excel_path)

        # 步驟 6: 驗證結果
        migrator.verify_migration()

        print("=" * 80)
        print("遷移完成!")
        print("=" * 80)
        print()

        # 詢問是否刪除舊關係
        print("是否刪除舊關係 (IS_TRIBUTARY_OF, MONITORS)?")
        delete_old = input("刪除後無法復原! (yes/no): ")

        if delete_old.lower() in ['yes', 'y']:
            with migrator.driver.session(database=migrator.database) as session:
                result = session.run("MATCH ()-[r:IS_TRIBUTARY_OF]->() DELETE r RETURN count(r) as deleted")
                deleted1 = result.single()['deleted']

                result = session.run("MATCH ()-[r:MONITORS]->() DELETE r RETURN count(r) as deleted")
                deleted2 = result.single()['deleted']

                print(f"[OK] 已刪除 IS_TRIBUTARY_OF: {deleted1} 條")
                print(f"[OK] 已刪除 MONITORS: {deleted2} 條")
        else:
            print("[INFO] 保留舊關係 (可用於驗證或回滾)")

        print()
        print("建議:")
        print("  1. 在 Neo4j Browser 驗證結果")
        print("  2. 更新 LangGraph/DIFY 查詢腳本")
        print("  3. 測試所有 Demo 問題")
        print("  4. 重新整理 NeoDash Dashboard")

    except Exception as e:
        print(f"\n[ERROR] 發生錯誤: {e}")
        import traceback
        traceback.print_exc()

    finally:
        migrator.close()


if __name__ == "__main__":
    main()
