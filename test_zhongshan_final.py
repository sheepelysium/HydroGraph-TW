# -*- coding: utf-8 -*-
"""最終測試: 中山橋測站查詢 (模擬 DIFY Agent 的查詢)"""
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "geoinfor"))

print("="*80)
print("測試: 中山橋的水位測站資料 (DIFY Agent 查詢)")
print("="*80)

with driver.session(database="neo4j") as session:

    # DIFY Agent 應該使用的查詢 (CONTAINS 模糊搜尋)
    result = session.run("""
        MATCH (s:WaterStation)-[:LOCATED_ON]->(r:River)
        WHERE s.name CONTAINS '中山橋'
        RETURN
            s.name AS 測站名稱,
            s.code AS 測站代碼,
            s.type AS 測站類型,
            s.elevation AS 海拔,
            s.management_unit AS 管理單位,
            s.address AS 地址,
            r.name AS 所在河川
    """)

    records = list(result)

    if records:
        print(f"\n找到 {len(records)} 個中山橋水位測站:")
        print()
        for rec in records:
            print(f"  測站名稱: {rec['測站名稱'].strip()}")
            print(f"  測站代碼: {rec['測站代碼']}")
            print(f"  測站類型: {rec['測站類型']}")
            print(f"  所在河川: {rec['所在河川']}")
            print(f"  海拔: {rec['海拔']}m")
            print(f"  管理單位: {rec['管理單位']}")
            print(f"  地址: {rec['地址']}")
    else:
        print("\n  [X] 查詢失敗: 找不到中山橋水位測站")
        print("  可能原因:")
        print("    1. 測站沒有 LOCATED_ON 關係")
        print("    2. 測站不是 WaterStation 類型")

driver.close()

print("\n" + "="*80)
print("這個查詢就是 DIFY Agent 應該執行的 Cypher")
print("="*80)
