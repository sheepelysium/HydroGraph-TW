# -*- coding: utf-8 -*-
"""測試查詢指定測站的資料"""
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "geoinfor"))

print("="*80)
print("測試查詢指定測站資料")
print("="*80)

with driver.session(database="neo4j") as session:

    # 1. 查詢中山橋測站的完整資料
    print("\n[查詢 1] 中山橋測站的完整資料")
    result = session.run("""
        MATCH (s:Station {name: '中山橋'})
        OPTIONAL MATCH (s)-[:LOCATED_ON]->(r:River)
        OPTIONAL MATCH (r)-[:BELONGS_TO]->(ws:WaterSystem)
        RETURN
            s.name AS 測站名稱,
            s.code AS 測站代碼,
            s.type AS 測站類型,
            s.elevation AS 海拔,
            s.management_unit AS 管理單位,
            s.address AS 地址,
            s.x_twd97 AS TWD97_X,
            s.y_twd97 AS TWD97_Y,
            r.name AS 所在河川,
            ws.name AS 所屬水系,
            labels(s) AS 標籤
    """)

    record = result.single()
    if record:
        print("\n  測站資訊:")
        for key in record.keys():
            print(f"    {key}: {record[key]}")
    else:
        print("  找不到中山橋測站!")

    # 2. 模糊搜尋測站 (DIFY 應該用的查詢方式)
    print("\n[查詢 2] 模糊搜尋包含'中山橋'的測站")
    result = session.run("""
        MATCH (s:Station)
        WHERE s.name CONTAINS '中山橋'
        OPTIONAL MATCH (s)-[:LOCATED_ON]->(r:River)
        RETURN s.name AS 測站名稱, s.type AS 類型, r.name AS 河川
    """)

    stations = list(result)
    print(f"  找到 {len(stations)} 個測站:")
    for st in stations:
        print(f"    - {st['測站名稱']} ({st['類型']}) 位於 {st['河川']}")

    # 3. 檢查是否是水位測站
    print("\n[查詢 3] 確認中山橋是否為水位測站")
    result = session.run("""
        MATCH (s:WaterStation {name: '中山橋'})
        RETURN s.name AS name
    """)

    if result.single():
        print("  ✓ 中山橋確實是水位測站 (WaterStation)")
    else:
        print("  ✗ 中山橋不是水位測站")

    # 4. 列出所有水位測站範例
    print("\n[查詢 4] 所有水位測站範例 (前10個)")
    result = session.run("""
        MATCH (s:WaterStation)-[:LOCATED_ON]->(r:River)
        RETURN s.name AS 測站名稱, r.name AS 河川
        LIMIT 10
    """)

    for st in result:
        print(f"    - {st['測站名稱']} (位於 {st['河川']})")

driver.close()

print("\n" + "="*80)
print("測試完成")
print("="*80)

print("\n結論:")
print("  如果 DIFY 查不到中山橋,可能的原因:")
print("  1. Cypher 查詢語法問題 (例如:沒有精確匹配測站名稱)")
print("  2. DIFY Agent Prompt 中的查詢邏輯有誤")
print("  3. Neo4j 連線設定問題")
