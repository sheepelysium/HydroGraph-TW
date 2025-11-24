# -*- coding: utf-8 -*-
"""
DIFY 自訂工具: WRA 即時監測資料查詢
可以在 DIFY 中註冊為 HTTP API 工具
"""
from flask import Flask, request, jsonify
from neo4j import GraphDatabase
import random
from datetime import datetime

app = Flask(__name__)

# Neo4j 連線
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "geoinfor"
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def get_station_info(station_name):
    """從 Neo4j 取得測站基本資訊"""
    with driver.session(database="neo4j") as session:
        result = session.run("""
            MATCH (s:Station)-[:LOCATED_ON]->(r:River)
            WHERE s.name CONTAINS $name
            RETURN s.name AS station_name,
                   s.code AS station_code,
                   s.type AS station_type,
                   r.name AS river_name,
                   labels(s) AS labels
            LIMIT 1
        """, name=station_name)
        return result.single()


def simulate_realtime_data(station_type):
    """
    模擬即時監測資料
    實際應用時,這裡應該呼叫真實的 WRA API
    """
    if "RainStation" in station_type:
        return {
            "current_value": round(random.uniform(0, 50), 1),
            "unit": "mm",
            "status": "正常" if random.random() > 0.2 else "警戒",
            "alert_level": random.choice(["安全", "注意", "警戒"]),
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    else:  # WaterStation
        return {
            "current_value": round(random.uniform(0.5, 5.0), 2),
            "unit": "m",
            "status": "正常" if random.random() > 0.3 else "警戒",
            "alert_level": random.choice(["安全", "一級警戒", "二級警戒"]),
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


@app.route('/query_realtime', methods=['POST'])
def query_realtime():
    """
    DIFY 工具 API 端點

    輸入:
    {
        "station_name": "中山橋"
    }

    輸出:
    {
        "station_name": "中山橋",
        "river": "基隆河",
        "type": "水位測站",
        "current_value": 2.3,
        "unit": "m",
        "status": "正常",
        "alert_level": "安全"
    }
    """
    try:
        data = request.json
        station_name = data.get('station_name')

        if not station_name:
            return jsonify({"error": "請提供測站名稱"}), 400

        # 1. 從 Neo4j 取得測站資訊
        station_info = get_station_info(station_name)

        if not station_info:
            return jsonify({"error": f"找不到測站: {station_name}"}), 404

        # 2. 模擬即時資料 (實際應該呼叫 WRA API)
        realtime_data = simulate_realtime_data(station_info['labels'])

        # 3. 整合返回
        result = {
            "station_name": station_info['station_name'].strip(),
            "station_code": station_info['station_code'],
            "river": station_info['river_name'],
            "type": station_info['station_type'],
            "current_value": realtime_data['current_value'],
            "unit": realtime_data['unit'],
            "status": realtime_data['status'],
            "alert_level": realtime_data['alert_level'],
            "last_update": realtime_data['last_update'],
            "message": f"{station_info['station_name'].strip()} 目前 {realtime_data['current_value']}{realtime_data['unit']}, 狀態: {realtime_data['status']}"
        }

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """健康檢查"""
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    print("="*80)
    print("WRA 即時監測工具 API 服務")
    print("="*80)
    print("\nAPI 端點:")
    print("  POST http://localhost:5000/query_realtime")
    print("\n範例請求:")
    print('  {"station_name": "中山橋"}')
    print("\n" + "="*80)

    app.run(host='0.0.0.0', port=5000, debug=True)
