"""
匯出 Neo4j 圖譜資料到 JSON
用於前端視覺化
"""
from neo4j import GraphDatabase
import json

class GraphExporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def export_all_data(self):
        """匯出所有節點和關係"""
        with self.driver.session() as session:
            # 1. 查詢主要水系（河川數 >= 5 的水系，約 30 個）
            water_systems = session.run("""
                MATCH (ws:WaterSystem)<-[:BELONGS_TO]-(r:River)
                WITH ws, count(r) as river_count
                WHERE river_count >= 5
                RETURN 'WS_' + replace(ws.name, ' ', '_') as id,
                       ws.name as name,
                       'WaterSystem' as group,
                       32 as radius,
                       toString(river_count) + ' 條河川' as region,
                       river_count
                ORDER BY river_count DESC
            """).data()

            print(f"  主要水系數量: {len(water_systems)} 個")

            # 移除 river_count 欄位（只用於排序）
            for ws in water_systems:
                if 'river_count' in ws:
                    del ws['river_count']

            # 2. 查詢所有河川
            rivers = session.run("""
                MATCH (r:River)
                RETURN 'R_' + r.code as id,
                       trim(r.name) as name,
                       'River' as group,
                       CASE
                         WHEN r.level = 1 THEN 24
                         WHEN r.level = 2 THEN 20
                         ELSE 16
                       END as radius,
                       CASE
                         WHEN r.level = 1 THEN '主幹河川'
                         ELSE '支流匯入'
                       END as flow
            """).data()

            # 3. 查詢所有集水區（過濾掉沒有 code 的節點）
            watersheds = session.run("""
                MATCH (w:Watershed)
                WHERE w.code IS NOT NULL
                RETURN 'W_' + w.code as id,
                       trim(w.name) as name,
                       'Watershed' as group,
                       13 as radius
            """).data()

            # 4. 查詢所有流域（過濾掉沒有 code 的節點）
            basins = session.run("""
                MATCH (b:Basin)
                WHERE b.code IS NOT NULL
                RETURN 'B_' + b.code as id,
                       trim(b.name) as name,
                       'Basin' as group,
                       18 as radius
            """).data()

            # 5. 查詢所有測站（包含水位站和雨量站，過濾掉沒有 code 的節點）
            stations = session.run("""
                MATCH (s)
                WHERE (s:WaterStation OR s:RainStation) AND s.code IS NOT NULL
                RETURN 'S_' + trim(s.code) as id,
                       trim(s.name) as name,
                       CASE
                         WHEN s:WaterStation THEN 'WaterStation'
                         ELSE 'RainStation'
                       END as group,
                       7 as radius,
                       s.latitude as lat,
                       s.longitude as lon
            """).data()

            # 合併所有節點
            nodes = water_systems + rivers + watersheds + basins + stations

            # 6. 查詢所有關係
            # BELONGS_TO: 河川歸屬水系
            belongs_to = session.run("""
                MATCH (r:River)-[:BELONGS_TO]->(ws:WaterSystem)
                RETURN 'R_' + r.code as source,
                       'WS_' + replace(ws.name, ' ', '_') as target,
                       'BELONGS_TO' as type,
                       5 as weight
            """).data()

            # FLOWS_INTO: 支流匯入主流
            flows_into = session.run("""
                MATCH (r1:River)-[:FLOWS_INTO]->(r2:River)
                RETURN 'R_' + r1.code as source,
                       'R_' + r2.code as target,
                       'FLOWS_INTO' as type,
                       4 as weight
            """).data()

            # DRAINS_TO: 集水區匯流到河川（過濾掉沒有 code 的節點）
            drains_to = session.run("""
                MATCH (w:Watershed)-[:DRAINS_TO]->(r:River)
                WHERE w.code IS NOT NULL AND r.code IS NOT NULL
                RETURN 'W_' + w.code as source,
                       'R_' + r.code as target,
                       'DRAINS_TO' as type,
                       3 as weight
            """).data()

            # PART_OF: 集水區屬於流域（過濾掉沒有 code 的節點）
            part_of = session.run("""
                MATCH (w:Watershed)-[:PART_OF]->(b:Basin)
                WHERE w.code IS NOT NULL AND b.code IS NOT NULL
                RETURN 'W_' + w.code as source,
                       'B_' + b.code as target,
                       'PART_OF' as type,
                       2 as weight
            """).data()

            # LOCATED_ON: 測站位於河川（過濾掉沒有 code 的節點）
            located_on = session.run("""
                MATCH (s)-[:LOCATED_ON]->(r:River)
                WHERE (s:WaterStation OR s:RainStation) AND s.code IS NOT NULL AND r.code IS NOT NULL
                RETURN 'S_' + trim(s.code) as source,
                       'R_' + r.code as target,
                       'LOCATED_ON' as type,
                       1 as weight
            """).data()

            # 合併所有關係
            links = belongs_to + flows_into + drains_to + part_of + located_on

            return {
                'nodes': nodes,
                'links': links
            }

def main():
    # Neo4j 連線設定
    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "geoinfor"

    print("連接 Neo4j...")
    exporter = GraphExporter(URI, USER, PASSWORD)

    try:
        print("匯出資料...")
        data = exporter.export_all_data()

        print(f"匯出完成：")
        print(f"  - 節點數量: {len(data['nodes'])}")
        print(f"  - 關係數量: {len(data['links'])}")

        # 統計各類型節點
        node_stats = {}
        for node in data['nodes']:
            group = node.get('group', 'Unknown')
            node_stats[group] = node_stats.get(group, 0) + 1

        print(f"\n節點統計：")
        for group, count in sorted(node_stats.items()):
            print(f"  - {group}: {count}")

        # 儲存為 JSON
        output_file = "frontend/src/data/neo4j_graph_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n[OK] 資料已儲存到: {output_file}")

    finally:
        exporter.close()
        print("\n連線已關閉")

if __name__ == "__main__":
    main()
