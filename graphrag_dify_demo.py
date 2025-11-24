# -*- coding: utf-8 -*-
"""
HydroGraph-TW GraphRAG 演示腳本 (DIFY Schema 版)
使用關係: FLOWS_INTO, LOCATED_ON, DRAINS_TO, BELONGS_TO
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class HydroGraphDifyDemo:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "geoinfor")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        self.driver.close()

    def demo_pollution_trace(self, river_name):
        """
        [情境 1] 汙染溯源與擴散分析
        使用關係: FLOWS_INTO (支流流入主流)
        """
        print(f"\n{'='*80}")
        print(f"[情境 1] 汙染溯源 - 假設【{river_name}】發生汙染")
        print("="*80)

        with self.driver.session(database="neo4j") as session:
            # 查詢下游 (汙染會流到哪裡)
            print(f"\n[下游分析] 汙染會影響哪些河川?")
            result = session.run("""
                MATCH (start:River {name: $name})
                MATCH path = (start)-[:FLOWS_INTO*1..5]->(downstream:River)
                RETURN downstream.name AS river,
                       length(path) AS steps
                ORDER BY steps
            """, name=river_name)

            downstream = list(result)
            if downstream:
                print(f"  汙染將依序流向:")
                for r in downstream:
                    print(f"    -> {r['river']} (距離 {r['steps']} 步)")
            else:
                print(f"  (沒有下游河川,可能是主流末端或出海口)")

            # 查詢上游 (汙染可能來自哪裡)
            print(f"\n[上游分析] 汙染可能來自哪些支流?")
            result = session.run("""
                MATCH (main:River {name: $name})
                MATCH (tributary:River)-[:FLOWS_INTO]->(main)
                RETURN tributary.name AS river, tributary.level AS level
                ORDER BY level
                LIMIT 10
            """, name=river_name)

            upstream = list(result)
            if upstream:
                print(f"  可能的汙染源 (直接支流):")
                for r in upstream:
                    print(f"    <- {r['river']} (level {r['level']})")
            else:
                print(f"  (沒有直接支流)")

    def demo_station_lookup(self, river_name):
        """
        [情境 2] 監測站點查找
        使用關係: LOCATED_ON (測站位於河川)
        """
        print(f"\n{'='*80}")
        print(f"[情境 2] 監測站查詢 - 【{river_name}】上的測站")
        print("="*80)

        with self.driver.session(database="neo4j") as session:
            result = session.run("""
                MATCH (r:River {name: $name})
                MATCH (s:Station)-[:LOCATED_ON]->(r)
                RETURN s.name AS station_name,
                       s.type AS station_type,
                       s.management_unit AS agency,
                       s.elevation AS elevation,
                       labels(s) AS labels
                ORDER BY s.elevation DESC
            """, name=river_name)

            stations = list(result)
            if not stations:
                print(f"  (目前資料庫中 {river_name} 上沒有登記測站)")
            else:
                print(f"\n  找到 {len(stations)} 個監測站:")
                print(f"  {'站名':<30} {'類型':<15} {'海拔':<10} {'管理單位'}")
                print("  " + "-"*75)

                for r in stations:
                    # 判斷圖示
                    if 'RainStation' in r['labels']:
                        icon = "[雨量]"
                    elif 'WaterStation' in r['labels']:
                        icon = "[水位]"
                    else:
                        icon = "[測站]"

                    name = r['station_name'][:28]
                    station_type = (r['station_type'] or 'N/A')[:13]
                    elev = f"{r['elevation']:.1f}m" if r['elevation'] else "N/A"
                    agency = (r['agency'] or 'N/A')[:20]

                    print(f"  {icon} {name:<26} {station_type:<13} {elev:<10} {agency}")

    def demo_watershed_analysis(self, river_name):
        """
        [情境 3] 集水區與地理空間分析
        使用關係: DRAINS_TO (集水區排入河川)
        """
        print(f"\n{'='*80}")
        print(f"[情境 3] 集水區分析 - 哪些集水區排入【{river_name}】?")
        print("="*80)

        with self.driver.session(database="neo4j") as session:
            result = session.run("""
                MATCH (r:River {name: $name})
                MATCH (w:Watershed)-[:DRAINS_TO]->(r)
                OPTIONAL MATCH (w)-[:PART_OF]->(b:Basin)
                RETURN w.name AS watershed_name,
                       w.area_km2 AS area,
                       b.name AS basin_name
                ORDER BY w.area_km2 DESC
                LIMIT 10
            """, name=river_name)

            watersheds = list(result)
            if not watersheds:
                print(f"  (資料庫中未建立 {river_name} 的集水區關聯)")
            else:
                print(f"\n  排入此河川的主要集水區 (前10大):")
                print(f"  {'集水區名稱':<30} {'面積 (km2)':<15} {'所屬流域'}")
                print("  " + "-"*70)

                for r in watersheds:
                    ws_name = (r['watershed_name'] or 'N/A')[:28]
                    area = f"{r['area']:.2f}" if r['area'] else "N/A"
                    basin = (r['basin_name'] or 'N/A')[:25]
                    print(f"  {ws_name:<30} {area:<15} {basin}")

    def demo_water_system_network(self, water_system_name):
        """
        [情境 4] 水系網絡分析
        使用關係: BELONGS_TO (河川屬於水系)
        """
        print(f"\n{'='*80}")
        print(f"[情境 4] 水系網絡 - 【{water_system_name}】的完整監測網")
        print("="*80)

        with self.driver.session(database="neo4j") as session:
            # 統計資訊
            result = session.run("""
                MATCH (ws:WaterSystem {name: $name})
                MATCH (r:River)-[:BELONGS_TO]->(ws)
                OPTIONAL MATCH (s:RainStation)-[:LOCATED_ON]->(r)
                OPTIONAL MATCH (w:WaterStation)-[:LOCATED_ON]->(r)
                RETURN count(DISTINCT r) AS river_count,
                       count(DISTINCT s) AS rain_station_count,
                       count(DISTINCT w) AS water_station_count
            """, name=water_system_name)

            stats = result.single()
            if stats and stats['river_count'] > 0:
                print(f"\n  [統計資訊]")
                print(f"    河川數量: {stats['river_count']} 條")
                print(f"    雨量測站: {stats['rain_station_count']} 個")
                print(f"    水位測站: {stats['water_station_count']} 個")
                print(f"    總測站數: {stats['rain_station_count'] + stats['water_station_count']} 個")
            else:
                print(f"  (找不到 {water_system_name} 水系)")

            # 主要河川列表
            result = session.run("""
                MATCH (ws:WaterSystem {name: $name})
                MATCH (r:River)-[:BELONGS_TO]->(ws)
                WHERE r.level = 1 OR r.level = 2
                OPTIONAL MATCH (s:Station)-[:LOCATED_ON]->(r)
                RETURN r.name AS river,
                       r.level AS level,
                       count(s) AS station_count
                ORDER BY r.level, station_count DESC
                LIMIT 10
            """, name=water_system_name)

            rivers = list(result)
            if rivers:
                print(f"\n  [主要河川與測站分布]")
                for r in rivers:
                    level_str = "主流" if r['level'] == 1 else f"支流(L{r['level']})"
                    print(f"    {r['river']:<15} {level_str:<12} {r['station_count']} 個測站")

    def demo_complex_graphrag(self, keyword):
        """
        [情境 5] 複雜路徑查詢 (GraphRAG)
        結合多種關係: Station -> LOCATED_ON -> River -> BELONGS_TO -> WaterSystem
        """
        print(f"\n{'='*80}")
        print(f"[情境 5] GraphRAG 查詢 - 搜尋關鍵字【{keyword}】")
        print("="*80)

        with self.driver.session(database="neo4j") as session:
            # 搜尋包含關鍵字的河川
            result = session.run("""
                MATCH (r:River)
                WHERE r.name CONTAINS $keyword
                OPTIONAL MATCH (r)-[:BELONGS_TO]->(ws:WaterSystem)
                OPTIONAL MATCH (s:Station)-[:LOCATED_ON]->(r)
                RETURN r.name AS river,
                       ws.name AS water_system,
                       count(DISTINCT s) AS station_count,
                       r.level AS level
                ORDER BY station_count DESC
                LIMIT 10
            """, keyword=keyword)

            rivers = list(result)
            if rivers:
                print(f"\n  找到 {len(rivers)} 條相關河川:")
                for r in rivers:
                    ws_str = f"[{r['water_system']}]" if r['water_system'] else "[未知水系]"
                    level_str = f"L{r['level']}" if r['level'] else "N/A"
                    print(f"    {r['river']:<20} {ws_str:<15} {level_str:<5} {r['station_count']} 個測站")
            else:
                print(f"  (沒有找到包含 '{keyword}' 的河川)")

def main():
    print("\n" + "="*80)
    print("HydroGraph-TW GraphRAG Demo (DIFY Schema 版)")
    print("="*80)
    print("\n使用關係:")
    print("  - FLOWS_INTO: 支流流入主流")
    print("  - LOCATED_ON: 測站位於河川")
    print("  - DRAINS_TO: 集水區排入河川")
    print("  - BELONGS_TO: 河川屬於水系")

    app = HydroGraphDifyDemo()

    try:
        # 測試各種情境
        app.demo_pollution_trace("大漢溪")
        app.demo_station_lookup("大漢溪")
        app.demo_watershed_analysis("大漢溪")
        app.demo_water_system_network("淡水河")
        app.demo_complex_graphrag("景美")

    except Exception as e:
        print(f"\n[ERROR] 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        app.close()
        print("\n" + "="*80)
        print("演示結束")
        print("="*80)

if __name__ == "__main__":
    main()
