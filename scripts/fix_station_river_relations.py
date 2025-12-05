# -*- coding: utf-8 -*-
"""
修復測站-河川關係 (LOCATED_ON)

問題：很多測站有 s.river 屬性（如「濁水溪」），但沒有 LOCATED_ON 關係連到 River 節點
原因：原始匯入只用配對報表，且有嚴格的代碼驗證過濾掉很多

解法：用 s.river 屬性 + 代碼前綴匹配，補建缺失的 LOCATED_ON 關係

使用方式：
  python fix_station_river_relations.py        # 交互模式，需確認
  python fix_station_river_relations.py --auto # 自動模式，直接執行
"""
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import sys

load_dotenv()

AUTO_MODE = '--auto' in sys.argv

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

print("=" * 80)
print("修復測站-河川關係 (LOCATED_ON)")
print("=" * 80)

with driver.session(database="neo4j") as session:
    # 1. 統計現況
    print("\n[統計] 現況分析...\n")

    total_stations = session.run(
        "MATCH (s:Station) RETURN count(s) as cnt"
    ).single()['cnt']

    with_located_on = session.run(
        "MATCH (s:Station)-[:LOCATED_ON]->(:River) RETURN count(DISTINCT s) as cnt"
    ).single()['cnt']

    with_river_attr = session.run(
        "MATCH (s:Station) WHERE s.river IS NOT NULL AND s.river <> '' RETURN count(s) as cnt"
    ).single()['cnt']

    missing_relation = session.run("""
        MATCH (s:Station)
        WHERE s.river IS NOT NULL AND s.river <> ''
          AND NOT (s)-[:LOCATED_ON]->(:River)
        RETURN count(s) as cnt
    """).single()['cnt']

    print(f"  測站總數：{total_stations}")
    print(f"  有 LOCATED_ON 關係：{with_located_on}")
    print(f"  有 river 屬性：{with_river_attr}")
    print(f"  有 river 但無 LOCATED_ON：{missing_relation} ← 需要修復")

    if missing_relation == 0:
        print("\n[OK] 沒有需要修復的資料")
        driver.close()
        exit()

    # 2. 顯示範例（將被修復的測站）
    print(f"\n[範例] 將被修復的測站（前10個）：\n")
    result = session.run("""
        MATCH (s:Station)
        WHERE s.river IS NOT NULL AND s.river <> ''
          AND NOT (s)-[:LOCATED_ON]->(:River)
        RETURN s.code AS code, s.name AS name, s.river AS river
        LIMIT 10
    """)
    for r in result:
        print(f"  {r['code']} {r['name']} → 河川：{r['river']}")

    # 3. 詢問確認
    print(f"\n將為 {missing_relation} 個測站建立 LOCATED_ON 關係")
    if AUTO_MODE:
        print("[自動模式] 跳過確認，直接執行...")
    else:
        confirm = input("是否繼續？(yes/no): ")
        if confirm.lower() not in ['yes', 'y']:
            print("[取消] 未執行任何修改")
            driver.close()
            exit()

    # 4. 執行修復 - 方法1：精確匹配（河川名稱 + 代碼前綴）
    print("\n[修復] 方法1：精確匹配（河川名稱 + 代碼前綴4位）...")
    result = session.run("""
        MATCH (s:Station)
        WHERE s.river IS NOT NULL AND s.river <> ''
          AND NOT (s)-[:LOCATED_ON]->(:River)
        MATCH (r:River)
        WHERE r.name = s.river
          AND left(s.code, 4) = left(r.code, 4)
        MERGE (s)-[rel:LOCATED_ON]->(r)
        SET rel.match_type = 'river_attr_prefix4',
            rel.created_by = 'fix_script'
        RETURN count(*) as cnt
    """)
    exact_match = result.single()['cnt']
    print(f"  → 建立 {exact_match} 條關係")

    # 5. 執行修復 - 方法2：寬鬆匹配（只看河川名稱，用於代碼前綴3位匹配）
    print("\n[修復] 方法2：寬鬆匹配（河川名稱 + 代碼前綴3位）...")
    result = session.run("""
        MATCH (s:Station)
        WHERE s.river IS NOT NULL AND s.river <> ''
          AND NOT (s)-[:LOCATED_ON]->(:River)
        MATCH (r:River)
        WHERE r.name = s.river
          AND left(s.code, 3) = left(r.code, 3)
        MERGE (s)-[rel:LOCATED_ON]->(r)
        SET rel.match_type = 'river_attr_prefix3',
            rel.created_by = 'fix_script'
        RETURN count(*) as cnt
    """)
    loose_match = result.single()['cnt']
    print(f"  → 建立 {loose_match} 條關係")

    # 6. 執行修復 - 方法3：最寬鬆（只看河川名稱，限制唯一匹配）
    print("\n[修復] 方法3：唯一名稱匹配（河川名稱唯一時直接匹配）...")
    result = session.run("""
        MATCH (s:Station)
        WHERE s.river IS NOT NULL AND s.river <> ''
          AND NOT (s)-[:LOCATED_ON]->(:River)
        MATCH (r:River)
        WHERE r.name = s.river
        WITH s, collect(r) AS rivers
        WHERE size(rivers) = 1
        WITH s, rivers[0] AS r
        MERGE (s)-[rel:LOCATED_ON]->(r)
        SET rel.match_type = 'river_attr_unique',
            rel.created_by = 'fix_script'
        RETURN count(*) as cnt
    """)
    unique_match = result.single()['cnt']
    print(f"  → 建立 {unique_match} 條關係")

    # 7. 統計結果
    print("\n" + "=" * 80)
    print("[結果] 修復完成")
    print("=" * 80)

    total_created = exact_match + loose_match + unique_match
    print(f"\n  新建關係總數：{total_created}")
    print(f"    - 精確匹配(prefix4)：{exact_match}")
    print(f"    - 寬鬆匹配(prefix3)：{loose_match}")
    print(f"    - 唯一名稱匹配：{unique_match}")

    # 8. 檢查還有多少沒配對到
    still_missing = session.run("""
        MATCH (s:Station)
        WHERE s.river IS NOT NULL AND s.river <> ''
          AND NOT (s)-[:LOCATED_ON]->(:River)
        RETURN count(s) as cnt
    """).single()['cnt']

    if still_missing > 0:
        print(f"\n  仍無法配對：{still_missing} 個測站")
        print("\n  [範例] 無法配對的測站：")
        result = session.run("""
            MATCH (s:Station)
            WHERE s.river IS NOT NULL AND s.river <> ''
              AND NOT (s)-[:LOCATED_ON]->(:River)
            RETURN s.code AS code, s.name AS name, s.river AS river
            LIMIT 5
        """)
        for r in result:
            print(f"    {r['code']} {r['name']} → {r['river']} (找不到對應River節點)")
    else:
        print(f"\n  [OK] 所有有 river 屬性的測站都已配對完成！")

    # 9. 最終統計
    final_located_on = session.run(
        "MATCH (s:Station)-[:LOCATED_ON]->(:River) RETURN count(DISTINCT s) as cnt"
    ).single()['cnt']

    print(f"\n  最終有 LOCATED_ON 關係的測站：{final_located_on}/{total_stations}")

driver.close()
print("\n已關閉 Neo4j 連線")
