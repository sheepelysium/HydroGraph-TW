# -*- coding: utf-8 -*-
"""
台灣水文知識圖譜 - 實用查詢範例
"""
from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "geoinfor"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

with driver.session() as session:
    print("="*80)
    print("台灣水文知識圖譜 - 查詢範例")
    print("="*80)

    # 1. 查詢淡水河水系的所有監測站
    print("\n【查詢1】淡水河水系的監測站 (前15個)")
    print("-" * 80)
    result = session.run("""
        MATCH (ws:WaterSystem {name: '淡水河'})
        MATCH (r:River)-[:BELONGS_TO]->(ws)
        MATCH (s:Station)-[:MONITORS]->(r)
        RETURN s.name as station, r.name as river, s.type as type
        LIMIT 15
    """)

    for i, record in enumerate(result, 1):
        print(f"  {i}. {record['station']:20s} -> {record['river']:15s} ({record['type']})")

    # 2. 查詢蘭陽溪有多少個測站
    print("\n【查詢2】蘭陽溪的監測站統計")
    print("-" * 80)
    result = session.run("""
        MATCH (r:River {name: '蘭陽溪'})
        MATCH (s:Station)-[:MONITORS]->(r)
        RETURN count(s) as total,
               count(DISTINCT CASE WHEN s:Rainfall THEN s END) as rainfall,
               count(DISTINCT CASE WHEN s:WaterLevel THEN s END) as water_level
    """)

    record = result.single()
    print(f"  總測站數: {record['total']}")
    print(f"  雨量測站: {record['rainfall']}")
    print(f"  水位測站: {record['water_level']}")

    # 3. 查詢高程最高的10個測站
    print("\n【查詢3】高程最高的10個測站")
    print("-" * 80)
    result = session.run("""
        MATCH (s:Station)
        WHERE s.elevation IS NOT NULL
        RETURN s.name as station, s.elevation as elevation, s.type as type
        ORDER BY s.elevation DESC
        LIMIT 10
    """)

    for i, record in enumerate(result, 1):
        print(f"  {i}. {record['station']:25s} {record['elevation']:8.1f}m ({record['type']})")

    # 4. 查詢哪條河川的監測站最多
    print("\n【查詢4】監測站數量最多的河川 (前10名)")
    print("-" * 80)
    result = session.run("""
        MATCH (r:River)<-[:MONITORS]-(s:Station)
        WITH r, count(s) as station_count
        ORDER BY station_count DESC
        LIMIT 10
        RETURN r.name as river, station_count
    """)

    for i, record in enumerate(result, 1):
        print(f"  {i}. {record['river']:20s} {record['station_count']:3d} 個測站")

    # 5. 查詢某個縣市的測站數量
    print("\n【查詢5】各縣市的測站數量 (前10名)")
    print("-" * 80)
    result = session.run("""
        MATCH (s:Station)
        WHERE s.city IS NOT NULL
        WITH s.city as city, count(s) as station_count
        ORDER BY station_count DESC
        LIMIT 10
        RETURN city, station_count
    """)

    for i, record in enumerate(result, 1):
        print(f"  {i}. {record['city']:15s} {record['station_count']:3d} 個測站")

    # 6. 查詢濁水溪的支流
    print("\n【查詢6】濁水溪的直接支流")
    print("-" * 80)
    result = session.run("""
        MATCH (main:River {name: '濁水溪'})
        MATCH (tributary:River)-[:IS_TRIBUTARY_OF]->(main)
        RETURN tributary.name as tributary_name, tributary.code as code
        LIMIT 15
    """)

    for i, record in enumerate(result, 1):
        print(f"  {i}. {record['tributary_name']:25s} ({record['code']})")

    # 7. 查詢某個測站的詳細資訊
    print("\n【查詢7】查詢「清泉」測站的詳細資訊")
    print("-" * 80)
    result = session.run("""
        MATCH (s:Station)
        WHERE s.name CONTAINS '清泉'
        OPTIONAL MATCH (s)-[:MONITORS]->(r:River)
        RETURN s.name as station, s.code as code, s.type as type,
               s.elevation as elevation, s.city as city,
               s.management_unit as unit,
               r.name as river
        LIMIT 1
    """)

    record = result.single()
    if record:
        print(f"  測站名稱: {record['station']}")
        print(f"  測站代號: {record['code']}")
        print(f"  測站類型: {record['type']}")
        print(f"  監測河川: {record['river']}")
        print(f"  高程: {record['elevation']} m")
        print(f"  縣市: {record['city']}")
        print(f"  管理單位: {record['unit']}")

    # 8. 查詢淡水河流域面積最大的集水區
    print("\n【查詢8】淡水河流域面積最大的5個集水區")
    print("-" * 80)
    result = session.run("""
        MATCH (b:Basin {name: '淡水河流域'})
        MATCH (w:Watershed)-[:PART_OF]->(b)
        WHERE w.area_km2 IS NOT NULL
        RETURN w.name as watershed, w.area_km2 as area
        ORDER BY area DESC
        LIMIT 5
    """)

    for i, record in enumerate(result, 1):
        print(f"  {i}. {record['watershed']:30s} {record['area']:8.2f} km²")

    # 9. 查詢第十河川分署管理的測站
    print("\n【查詢9】第十河川分署管理的測站 (前10個)")
    print("-" * 80)
    result = session.run("""
        MATCH (s:Station)
        WHERE s.management_unit = '第十河川分署'
        OPTIONAL MATCH (s)-[:MONITORS]->(r:River)
        RETURN s.name as station, s.type as type, r.name as river
        LIMIT 10
    """)

    for i, record in enumerate(result, 1):
        river = record['river'] if record['river'] else '(未配對)'
        print(f"  {i}. {record['station']:20s} {record['type']:10s} -> {river}")

    # 10. 統計整個知識圖譜
    print("\n【查詢10】知識圖譜整體統計")
    print("-" * 80)

    # 節點統計
    result = session.run("""
        MATCH (r:River) RETURN count(r) as cnt
    """)
    rivers = result.single()['cnt']

    result = session.run("""
        MATCH (s:Station) RETURN count(s) as cnt
    """)
    stations = result.single()['cnt']

    result = session.run("""
        MATCH (w:Watershed) RETURN count(w) as cnt
    """)
    watersheds = result.single()['cnt']

    result = session.run("""
        MATCH (ws:WaterSystem) RETURN count(ws) as cnt
    """)
    water_systems = result.single()['cnt']

    # 關係統計
    result = session.run("""
        MATCH ()-[r:MONITORS]->() RETURN count(r) as cnt
    """)
    monitors = result.single()['cnt']

    result = session.run("""
        MATCH ()-[r:IS_TRIBUTARY_OF]->() RETURN count(r) as cnt
    """)
    tributaries = result.single()['cnt']

    print(f"  河川: {rivers} 條")
    print(f"  測站: {stations} 個")
    print(f"  集水區: {watersheds} 個")
    print(f"  水系: {water_systems} 個")
    print(f"  MONITORS關係: {monitors} 條")
    print(f"  IS_TRIBUTARY_OF關係: {tributaries} 條")

    print("\n" + "="*80)

driver.close()
