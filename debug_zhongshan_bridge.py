# -*- coding: utf-8 -*-
"""Debug 中山橋測站的河川匹配問題"""
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "geoinfor"))

with driver.session(database="neo4j") as session:
    # 1. 取得中山橋的河川名稱
    result = session.run("""
        MATCH (s:Station)
        WHERE s.name CONTAINS '中山橋'
        RETURN s.name, s.river, s.code
    """)
    rec = result.single()

    station_name = rec['s.name']
    river_raw = rec['s.river']
    river_clean = river_raw.strip() if river_raw else None

    print("中山橋測站資訊:")
    print(f"  測站名稱: '{station_name}'")
    print(f"  河川欄位(原始): '{river_raw}'")
    print(f"  河川欄位(去空格): '{river_clean}'")
    print(f"  河川名稱長度: {len(river_raw)} -> {len(river_clean)}")

    # 2. 檢查是否有匹配的河川
    result2 = session.run("""
        MATCH (r:River)
        WHERE r.name = $name
        RETURN r.name, r.code
    """, name=river_clean)

    match = result2.single()
    if match:
        print(f"\n找到匹配的河川:")
        print(f"  河川名稱: '{match['r.name']}'")
        print(f"  河川代碼: {match['r.code']}")
    else:
        print(f"\n沒有找到匹配的河川!")
        print(f"  嘗試模糊搜尋包含 '景美' 的河川:")

        result3 = session.run("""
            MATCH (r:River)
            WHERE r.name CONTAINS '景美'
            RETURN r.name, r.code
        """)

        for r in result3:
            print(f"    - '{r['r.name']}' (code: {r['r.code']})")

    # 3. 手動建立關係
    print(f"\n嘗試手動建立關係...")
    result4 = session.run("""
        MATCH (s:Station), (r:River)
        WHERE s.name CONTAINS '中山橋'
        AND r.name CONTAINS '景美'
        MERGE (s)-[:LOCATED_ON]->(r)
        RETURN s.name, r.name
    """)

    created = result4.single()
    if created:
        print(f"  [OK] 成功建立: {created['s.name']} -> {created['r.name']}")
    else:
        print(f"  [X] 建立失敗")

driver.close()
