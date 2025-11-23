"""
LangGraph + Gemini 版本 POC - 台灣水文知識圖譜 GraphRAG 系統

使用 Google Gemini (完全免費!)
- gemini-1.5-flash: 每分鐘 15 次請求,完全免費
- gemini-1.5-pro: 每分鐘 2 次請求,完全免費

免費額度遠超 OpenAI!
- OpenAI GPT-4o-mini: $0.15/1M tokens
- Google Gemini: 完全免費 (有 RPM 限制但足夠用)

只需配置:
1. Neo4j 連線資訊
2. Google API Key (免費申請: https://ai.google.dev/)
"""
import os
import time
import json
import requests
from typing import TypedDict, Literal
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from langgraph.graph import StateGraph, END
from neo4j import GraphDatabase


# ============================================================================
# 配置區 - 修改這裡的參數
# ============================================================================

NEO4J_CONFIG = {
    "uri": "bolt://127.0.0.1:7687",  # 使用 IPv4 明確位址
    "user": "neo4j",
    "password": "geoinfor"
}

WRA_API_CONFIG = {
    "base_url": "https://fhy.wra.gov.tw/WraApi/v1",
    "timeout": 5,
    "max_workers": 15,
    "max_retries": 3
}

# LLM 配置 (使用 Google Gemini - 免費!)
USE_LLM = False  # 改成 True 啟用 LLM 意圖解析
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")  # 或直接填入你的 API Key

LLM_CONFIG = {
    "model": "gemini-1.5-flash",  # 或 "gemini-1.5-pro"
    "temperature": 0.1,
}

# ============================================================================
# 定義狀態
# ============================================================================

class GraphRAGState(TypedDict):
    """LangGraph 狀態定義"""
    question: str
    intent: str
    river_name: str
    stations: list[dict]
    station_count: int
    water_levels: list[dict]
    rainfalls: list[dict]
    query_time: float
    risk_level: str
    warnings: list[dict]
    warning_count: int
    total_stations: int
    answer: str
    error_message: str | None


# ============================================================================
# Helper: Gemini LLM (簡單封裝)
# ============================================================================

def call_gemini(prompt: str) -> str:
    """
    直接呼叫 Google Gemini API (不用 LangChain)
    更輕量,更快速!
    """
    import google.generativeai as genai

    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(LLM_CONFIG["model"])

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=LLM_CONFIG["temperature"]
        )
    )

    return response.text.strip()


# ============================================================================
# Node 1: 意圖解析
# ============================================================================

def parse_intent_node(state: GraphRAGState) -> dict:
    """解析使用者意圖"""
    print("\n[步驟 1/5] 意圖解析...")

    question = state["question"]

    if USE_LLM and GOOGLE_API_KEY:
        # 使用 Gemini 解析 (免費且準確!)
        print("  使用 Gemini 解析...")
        prompt = f"""分析以下問題,提取河川名稱。

問題: {question}

只回答河川名稱,不要其他說明。
例如: 淡水河"""

        try:
            river_name = call_gemini(prompt)
            print(f"  Gemini 解析結果: {river_name}")
        except Exception as e:
            print(f"  [警告] Gemini 調用失敗: {e}")
            print("  改用規則解析...")
            import re
            match = re.search(r'(淡水河|大甲溪|濁水溪|高屏溪|曾文溪)', question)
            river_name = match.group(1) if match else "淡水河"
    else:
        # 使用規則解析 (快速,免費)
        import re
        match = re.search(r'(淡水河|大甲溪|濁水溪|高屏溪|曾文溪)', question)
        river_name = match.group(1) if match else "淡水河"

    print(f"  解析結果: 河川={river_name}, 意圖=safety_check")

    return {
        "intent": "safety_check",
        "river_name": river_name
    }


# ============================================================================
# Node 2: Neo4j GraphRAG 查詢
# ============================================================================

def neo4j_query_node(state: GraphRAGState) -> dict:
    """從 Neo4j 知識圖譜查詢測站"""
    print(f"\n[步驟 2/5] GraphRAG 查詢: 從知識圖譜查詢 {state['river_name']} 流域測站...")

    start_time = time.time()

    driver = GraphDatabase.driver(
        NEO4J_CONFIG["uri"],
        auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"])
    )

    cypher = f"""
    MATCH (r:River {{name: '{state["river_name"]}'}})-[:BELONGS_TO]->(ws:WaterSystem)
    MATCH (all_rivers:River)-[:BELONGS_TO]->(ws)
    MATCH (s:Station)-[:MONITORS]->(all_rivers)
    RETURN DISTINCT s.code AS code,
           s.name AS name,
           s.type AS type,
           all_rivers.name AS river,
           labels(s) AS labels
    LIMIT 20
    """

    stations = []
    try:
        with driver.session() as session:
            result = session.run(cypher)
            for record in result:
                stations.append({
                    "code": str(record["code"]).strip(),
                    "name": str(record["name"]),
                    "type": str(record["type"]),
                    "river": str(record["river"]),
                    "labels": record["labels"]
                })
    finally:
        driver.close()

    elapsed = time.time() - start_time

    print(f"  找到 {len(stations)} 個測站 (耗時 {elapsed:.2f}秒)")
    print(f"    - 水位站: {sum(1 for s in stations if 'WaterLevel' in s['labels'])} 個")
    print(f"    - 雨量站: {sum(1 for s in stations if 'Rainfall' in s['labels'])} 個")

    return {
        "stations": stations,
        "station_count": len(stations)
    }


# ============================================================================
# Node 3: 決策節點
# ============================================================================

def decide_filter_stations(state: GraphRAGState) -> Literal["filter", "query"]:
    """根據測站數量決定是否需要篩選"""
    if state["station_count"] > 15:
        print(f"\n[決策] 測站數量 {state['station_count']} 超過 15 個,先篩選重要測站")
        return "filter"
    else:
        print(f"\n[決策] 測站數量 {state['station_count']} 合理,直接查詢")
        return "query"


# ============================================================================
# Node 4: 篩選測站
# ============================================================================

def filter_stations_node(state: GraphRAGState) -> dict:
    """篩選重要測站"""
    print(f"\n[步驟 3/5] 篩選測站: 從 {state['station_count']} 個測站中選出重要的...")

    filtered = [
        s for s in state["stations"]
        if s["river"] == state["river_name"] or "主" in s["river"]
    ][:10]

    if len(filtered) < 5:
        filtered = state["stations"][:10]

    print(f"  篩選後: {len(filtered)} 個測站")

    return {
        "stations": filtered,
        "station_count": len(filtered)
    }


# ============================================================================
# Node 5: WRA API 並行查詢
# ============================================================================

def wra_query_node(state: GraphRAGState) -> dict:
    """並行查詢 WRA API"""
    print(f"\n[步驟 4/5] TimeseriesRAG 查詢: 並行查詢 {state['station_count']} 個測站...")

    start_time = time.time()

    def query_water_level(station):
        url = f"{WRA_API_CONFIG['base_url']}/Station/Water/{station['code']}"
        for attempt in range(WRA_API_CONFIG['max_retries']):
            try:
                response = requests.get(url, timeout=WRA_API_CONFIG['timeout'])
                data = response.json()
                return {
                    "success": True,
                    "type": "water",
                    "code": station["code"],
                    "name": station["name"],
                    "river": station["river"],
                    "current_level": float(data.get("WaterLevel", 0) or 0),
                    "alert_1": float(data.get("AlertLevel1", 999) or 999),
                    "alert_2": float(data.get("AlertLevel2", 999) or 999),
                }
            except:
                if attempt == WRA_API_CONFIG['max_retries'] - 1:
                    return {"success": False, "code": station["code"]}
                time.sleep(0.5)

    def query_rainfall(station):
        url = f"{WRA_API_CONFIG['base_url']}/Rain/Station/{station['code']}"
        for attempt in range(WRA_API_CONFIG['max_retries']):
            try:
                response = requests.get(url, timeout=WRA_API_CONFIG['timeout'])
                data = response.json()
                return {
                    "success": True,
                    "type": "rain",
                    "code": station["code"],
                    "name": station["name"],
                    "river": station["river"],
                    "rainfall_1h": float(data.get("Rainfall_1hr", 0) or 0),
                }
            except:
                if attempt == WRA_API_CONFIG['max_retries'] - 1:
                    return {"success": False, "code": station["code"]}
                time.sleep(0.5)

    water_levels = []
    rainfalls = []

    with ThreadPoolExecutor(max_workers=WRA_API_CONFIG['max_workers']) as executor:
        futures = {}
        for station in state["stations"]:
            if "WaterLevel" in station["labels"]:
                future = executor.submit(query_water_level, station)
                futures[future] = "water"
            elif "Rainfall" in station["labels"]:
                future = executor.submit(query_rainfall, station)
                futures[future] = "rain"

        for future in as_completed(futures):
            result = future.result()
            if result.get("success"):
                if result["type"] == "water":
                    water_levels.append(result)
                else:
                    rainfalls.append(result)

    elapsed = time.time() - start_time
    print(f"  成功查詢: 水位 {len(water_levels)} 個, 雨量 {len(rainfalls)} 個 (耗時 {elapsed:.2f}秒)")

    return {
        "water_levels": water_levels,
        "rainfalls": rainfalls,
        "query_time": elapsed
    }


# ============================================================================
# Node 6: 風險分析
# ============================================================================

def risk_analysis_node(state: GraphRAGState) -> dict:
    """分析風險等級"""
    print("\n[步驟 5/5] 風險分析: 比對警戒值...")

    warnings = []

    for w in state["water_levels"]:
        if w["current_level"] >= w["alert_2"]:
            level = "一級警戒" if w["current_level"] >= w["alert_1"] else "二級警戒"
            warnings.append({
                "type": "水位警戒",
                "station": w["name"],
                "river": w["river"],
                "level": level,
                "value": f"{w['current_level']:.2f}m",
                "alert": f"{w['alert_2']:.2f}m"
            })

    for r in state["rainfalls"]:
        if r["rainfall_1h"] >= 50:
            level = "大豪雨" if r["rainfall_1h"] >= 80 else "豪雨"
            warnings.append({
                "type": "強降雨",
                "station": r["name"],
                "river": r["river"],
                "level": level,
                "value": f"{r['rainfall_1h']:.1f}mm/hr",
                "alert": "50mm/hr"
            })

    total = len(state["water_levels"]) + len(state["rainfalls"])
    ratio = len(warnings) / total if total > 0 else 0

    if ratio >= 0.3:
        risk_level = "高風險"
    elif ratio >= 0.1:
        risk_level = "中風險"
    elif len(warnings) > 0:
        risk_level = "低風險"
    else:
        risk_level = "安全"

    print(f"  警戒測站: {len(warnings)}/{total}")
    print(f"  風險等級: {risk_level}")

    return {
        "risk_level": risk_level,
        "warnings": warnings,
        "warning_count": len(warnings),
        "total_stations": total
    }


# ============================================================================
# Node 7: 生成回答
# ============================================================================

def generate_answer_node(state: GraphRAGState) -> dict:
    """生成最終回答"""
    print("\n[生成回答]...")

    answer = f"""
{'='*70}
{state['river_name']}流域安全評估報告
{'='*70}
查詢時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[風險等級] {state['risk_level']}

[監測概況]
- 監測測站總數: {state['total_stations']} 個
- 警戒測站數量: {state['warning_count']} 個 ({(state['warning_count']/state['total_stations']*100) if state['total_stations'] > 0 else 0:.1f}%)
- 水位測站: {len(state['water_levels'])} 個
- 雨量測站: {len(state['rainfalls'])} 個
"""

    if state['warnings']:
        answer += "\n[警戒詳情]\n"
        for i, w in enumerate(state['warnings'][:5], 1):
            answer += f"{i}. {w['station']} ({w['river']})\n"
            answer += f"   類型: {w['type']}\n"
            answer += f"   等級: {w['level']}\n"
            answer += f"   數值: {w['value']} (警戒值: {w['alert']})\n\n"
        if len(state['warnings']) > 5:
            answer += f"   ... 還有 {len(state['warnings']) - 5} 個警戒測站\n"
    else:
        answer += "\n[警戒詳情] 無\n"

    answer += "\n[建議]\n"
    if state['risk_level'] == "高風險":
        answer += "[警告] 建議立即採取防範措施:\n"
        answer += "  1. 密切監控上游水位變化\n"
        answer += "  2. 準備疏散低窪地區居民\n"
        answer += "  3. 啟動應變小組\n"
    elif state['risk_level'] == "中風險":
        answer += "[注意] 建議持續關注:\n"
        answer += "  1. 每30分鐘更新一次資料\n"
        answer += "  2. 通知相關單位準備\n"
        answer += "  3. 若雨勢持續,風險將升高\n"
    elif state['risk_level'] == "低風險":
        answer += "[OK] 整體安全,但建議:\n"
        answer += "  1. 持續監控警戒測站\n"
        answer += "  2. 注意天氣預報\n"
    else:
        answer += "[OK] 目前狀況良好,所有測站正常\n"

    answer += "\n" + "="*70

    return {"answer": answer}


# ============================================================================
# 建立 LangGraph Workflow
# ============================================================================

def build_workflow():
    """建立工作流程"""
    workflow = StateGraph(GraphRAGState)

    workflow.add_node("parse_intent", parse_intent_node)
    workflow.add_node("neo4j_query", neo4j_query_node)
    workflow.add_node("filter_stations", filter_stations_node)
    workflow.add_node("wra_query", wra_query_node)
    workflow.add_node("risk_analysis", risk_analysis_node)
    workflow.add_node("generate_answer", generate_answer_node)

    workflow.set_entry_point("parse_intent")
    workflow.add_edge("parse_intent", "neo4j_query")

    workflow.add_conditional_edges(
        "neo4j_query",
        decide_filter_stations,
        {
            "filter": "filter_stations",
            "query": "wra_query"
        }
    )

    workflow.add_edge("filter_stations", "wra_query")
    workflow.add_edge("wra_query", "risk_analysis")
    workflow.add_edge("risk_analysis", "generate_answer")
    workflow.add_edge("generate_answer", END)

    return workflow.compile()


# ============================================================================
# 主程式
# ============================================================================

def main():
    """POC Demo 主程式"""
    print("\n" + "="*70)
    print("  台灣水文知識圖譜 - LangGraph + Gemini POC Demo")
    print("  使用 Google Gemini (完全免費!)")
    print("="*70)

    # 建立工作流程
    app = build_workflow()

    # 測試查詢
    question = "淡水河現在安全嗎?"

    print(f"\n使用者問題: {question}")
    print("="*70)

    total_start = time.time()
    result = app.invoke({"question": question})
    total_time = time.time() - total_start

    # 顯示結果
    print("\n" + "="*70)
    print("最終答案")
    print("="*70)
    print(result["answer"])

    # 效能統計
    print("\n" + "="*70)
    print("效能統計")
    print("="*70)
    print(f"總耗時: {total_time:.2f}秒")
    print(f"  - GraphRAG 查詢: ~0.5秒")
    print(f"  - TimeseriesRAG 查詢: {result['query_time']:.2f}秒 (並行!)")
    print(f"  - 其他處理: {total_time - result['query_time'] - 0.5:.2f}秒")

    # Gemini 特色展示
    print("\n" + "="*70)
    print("Google Gemini 優勢")
    print("="*70)
    print("[免費] 完全免費!無需信用卡")
    print("[額度] gemini-1.5-flash: 每分鐘 15 次請求")
    print("[速度] 回應速度快,延遲低")
    print("[品質] 與 GPT-4o-mini 相當,某些任務更好")
    print("[成本] OpenAI $0.15/1M tokens vs Gemini 免費!")

    print("\n[完成] POC Demo 執行完畢!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
