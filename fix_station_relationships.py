# -*- coding: utf-8 -*-
"""
修復測站與河川的關係
問題: 測站的 river 欄位包含空格,導致無法匹配到 River 節點
解決: 用 TRIM() 去除空格後重新建立 LOCATED_ON 關係
"""
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "geoinfor"))

print("="*80)
print("修復測站與河川的 LOCATED_ON 關係")
print("="*80)

with driver.session(database="neo4j") as session:

    # 1. 檢查有多少測站沒有 LOCATED_ON 關係
    print("\n[步驟 1] 檢查缺少關係的測站...")
    result = session.run("""
        MATCH (s:Station)
        WHERE NOT (s)-[:LOCATED_ON]->(:River)
        AND s.river IS NOT NULL
        RETURN count(s) as count
    """)
    missing_count = result.single()['count']
    print(f"  缺少 LOCATED_ON 關係的測站: {missing_count} 個")

    if missing_count == 0:
        print("\n  所有測站都已正確連接!")
    else:
        # 2. 重新建立關係 (使用 TRIM 去除空格)
        print("\n[步驟 2] 重新建立 LOCATED_ON 關係...")
        result = session.run("""
            MATCH (s:Station)
            WHERE NOT (s)-[:LOCATED_ON]->(:River)
            AND s.river IS NOT NULL
            WITH s, trim(s.river) AS clean_river_name
            MATCH (r:River)
            WHERE r.name = clean_river_name
            MERGE (s)-[:LOCATED_ON]->(r)
            RETURN count(*) as fixed_count
        """)
        fixed = result.single()['fixed_count']
        print(f"  成功建立關係: {fixed} 條")

    # 3. 驗證修復結果
    print("\n[步驟 3] 驗證修復結果...")
    result = session.run("""
        MATCH (s:Station)
        WHERE NOT (s)-[:LOCATED_ON]->(:River)
        AND s.river IS NOT NULL
        RETURN count(s) as still_missing
    """)
    still_missing = result.single()['still_missing']

    if still_missing > 0:
        print(f"  [WARNING] 仍有 {still_missing} 個測站無法匹配到河川")

        # 列出無法匹配的測站
        result = session.run("""
            MATCH (s:Station)
            WHERE NOT (s)-[:LOCATED_ON]->(:River)
            AND s.river IS NOT NULL
            RETURN s.name as station, s.river as river
            LIMIT 10
        """)
        print("\n  無法匹配的測站範例:")
        for r in result:
            print(f"    - {r['station']} -> 河川: '{r['river']}'")
    else:
        print("  [OK] 所有測站都已成功連接!")

    # 4. 測試中山橋
    print("\n[步驟 4] 測試中山橋測站...")
    result = session.run("""
        MATCH (s:Station {name: '中山橋'})-[:LOCATED_ON]->(r:River)
        RETURN s.name as station, r.name as river
    """)
    record = result.single()
    if record:
        print(f"  [OK] 中山橋 -> {record['river']}")
    else:
        print("  [X] 中山橋仍然沒有連接到河川")

    # 5. 統計所有 LOCATED_ON 關係
    print("\n[步驟 5] 最終統計...")
    result = session.run("""
        MATCH ()-[r:LOCATED_ON]->()
        RETURN count(r) as total
    """)
    total = result.single()['total']
    print(f"  LOCATED_ON 關係總數: {total} 條")

driver.close()

print("\n" + "="*80)
print("修復完成!")
print("="*80)
