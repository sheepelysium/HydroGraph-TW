# -*- coding: utf-8 -*-
"""
從 Neo4j 匯出圖資料為前端可用的 JavaScript 檔案
用來取代 mockData.js
"""
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import json

load_dotenv()

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def export_graph_data(water_system_name=None, limit_rivers=50):
    """
    匯出圖資料

    Args:
        water_system_name: 指定水系名稱（如 "淡水河"），None 則匯出全部
        limit_rivers: 限制河川數量（避免太多）
    """
    nodes = []
    links = []
    node_ids = set()

    with driver.session() as session:
        # 1. 取得水系
        if water_system_name:
            ws_query = """
                MATCH (ws:WaterSystem)
                WHERE ws.name CONTAINS $name
                RETURN ws.name AS name, 'WS_' + id(ws) AS id
            """
            result = session.run(ws_query, name=water_system_name)
        else:
            ws_query = """
                MATCH (ws:WaterSystem)
                RETURN ws.name AS name, 'WS_' + id(ws) AS id
                LIMIT 20
            """
            result = session.run(ws_query)

        for record in result:
            node_id = record['id']
            if node_id not in node_ids:
                nodes.append({
                    'id': node_id,
                    'name': record['name'],
                    'group': 'WaterSystem',
                    'radius': 30
                })
                node_ids.add(node_id)

        # 2. 取得河川和流向關係
        if water_system_name:
            river_query = """
                MATCH (r:River)-[:BELONGS_TO]->(ws:WaterSystem)
                WHERE ws.name CONTAINS $name
                OPTIONAL MATCH (r)-[:FLOWS_INTO]->(downstream:River)
                RETURN r.name AS name, 'R_' + id(r) AS id, r.level AS level,
                       'R_' + id(downstream) AS downstream_id, downstream.name AS downstream_name,
                       'WS_' + id(ws) AS ws_id
                ORDER BY r.level
                LIMIT $limit
            """
            result = session.run(river_query, name=water_system_name, limit=limit_rivers)
        else:
            river_query = """
                MATCH (r:River)
                OPTIONAL MATCH (r)-[:FLOWS_INTO]->(downstream:River)
                OPTIONAL MATCH (r)-[:BELONGS_TO]->(ws:WaterSystem)
                RETURN r.name AS name, 'R_' + id(r) AS id, r.level AS level,
                       'R_' + id(downstream) AS downstream_id, downstream.name AS downstream_name,
                       'WS_' + id(ws) AS ws_id
                ORDER BY r.level
                LIMIT $limit
            """
            result = session.run(river_query, limit=limit_rivers)

        for record in result:
            node_id = record['id']
            if node_id not in node_ids:
                level = record['level'] or 2
                radius = max(25 - (level * 3), 10)  # 主流較大，支流較小
                nodes.append({
                    'id': node_id,
                    'name': record['name'],
                    'group': 'River',
                    'radius': radius
                })
                node_ids.add(node_id)

            # FLOWS_INTO 關係
            if record['downstream_id'] and record['downstream_id'] != 'R_None':
                # 確保下游節點存在
                if record['downstream_id'] not in node_ids:
                    nodes.append({
                        'id': record['downstream_id'],
                        'name': record['downstream_name'],
                        'group': 'River',
                        'radius': 20
                    })
                    node_ids.add(record['downstream_id'])

                links.append({
                    'source': node_id,
                    'target': record['downstream_id'],
                    'type': 'FLOWS_INTO'
                })

            # BELONGS_TO 關係（可選）
            # if record['ws_id'] and record['ws_id'] != 'WS_None':
            #     links.append({
            #         'source': node_id,
            #         'target': record['ws_id'],
            #         'type': 'BELONGS_TO'
            #     })

        # 3. 取得測站
        if water_system_name:
            station_query = """
                MATCH (s:Station)-[:LOCATED_ON]->(r:River)-[:BELONGS_TO]->(ws:WaterSystem)
                WHERE ws.name CONTAINS $name
                RETURN s.name AS name, 'S_' + id(s) AS id,
                       CASE WHEN s:Rainfall THEN '雨量' ELSE '水位' END AS type,
                       'R_' + id(r) AS river_id
                LIMIT 30
            """
            result = session.run(station_query, name=water_system_name)
        else:
            station_query = """
                MATCH (s:Station)-[:LOCATED_ON]->(r:River)
                RETURN s.name AS name, 'S_' + id(s) AS id,
                       CASE WHEN s:Rainfall THEN '雨量' ELSE '水位' END AS type,
                       'R_' + id(r) AS river_id
                LIMIT 30
            """
            result = session.run(station_query)

        for record in result:
            node_id = record['id']
            if node_id not in node_ids:
                nodes.append({
                    'id': node_id,
                    'name': f"{record['name']}（{record['type']}站）",
                    'group': 'Station',
                    'radius': 8
                })
                node_ids.add(node_id)

            # LOCATED_ON 關係
            if record['river_id'] in node_ids:
                links.append({
                    'source': node_id,
                    'target': record['river_id'],
                    'type': 'LOCATED_ON'
                })

    return {'nodes': nodes, 'links': links}


def save_as_js(data, output_path):
    """儲存為 JavaScript 檔案"""
    js_content = f"export const mockData = {json.dumps(data, ensure_ascii=False, indent=4)};\n"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(js_content)

    print(f"已儲存至 {output_path}")
    print(f"  - 節點數: {len(data['nodes'])}")
    print(f"  - 關係數: {len(data['links'])}")


if __name__ == '__main__':
    import sys

    # 可指定水系名稱，例如：python export_graph_data.py 淡水河
    water_system = sys.argv[1] if len(sys.argv) > 1 else None

    if water_system:
        print(f"匯出水系: {water_system}")
    else:
        print("匯出全部資料（限制數量）")

    data = export_graph_data(water_system_name=water_system, limit_rivers=100)

    output_path = os.path.join(
        os.path.dirname(__file__),
        '..', 'frontend', 'src', 'data', 'mockData.js'
    )

    save_as_js(data, output_path)

    driver.close()
