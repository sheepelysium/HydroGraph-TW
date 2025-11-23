"""
完整 POC Demo - 使用模擬資料展示系統架構
展示 GraphRAG + TimeseriesRAG 混合查詢的完整流程
"""
from datetime import datetime
import time
import random


def mock_graphrag_query(river_name):
    """模擬 GraphRAG 查詢 - 從 Neo4j 知識圖譜查詢測站"""
    print(f"\n[GraphRAG 查詢] 從知識圖譜查詢 '{river_name}' 流域測站...")
    print("  Cypher 查詢:")
    print("    MATCH (r:River {name: '淡水河'})-[:BELONGS_TO]->(ws:WaterSystem)")
    print("    MATCH (all_rivers:River)-[:BELONGS_TO]->(ws)")
    print("    MATCH (s:Station)-[:MONITORS]->(all_rivers)")
    print("    RETURN s.code, s.name, s.type, all_rivers.name")

    time.sleep(0.5)  # 模擬查詢時間

    # 模擬查詢結果 - 淡水河流域的真實測站
    stations = [
        {'code': '1500H005', 'name': '碧潭', 'type': '水位', 'river': '新店溪'},
        {'code': '1500H021', 'name': '秀朗橋', 'type': '水位', 'river': '新店溪'},
        {'code': '1120H008', 'name': '大漢橋', 'type': '水位', 'river': '大漢溪'},
        {'code': '1500H029', 'name': '台北橋', 'type': '水位', 'river': '淡水河'},
        {'code': '1500H041', 'name': '關渡', 'type': '水位', 'river': '淡水河'},
        {'code': '1140H009', 'name': '鳶山堰', 'type': '水位', 'river': '大漢溪'},
        {'code': '1500H039', 'name': '大稻埕', 'type': '水位', 'river': '淡水河'},
        {'code': '01A260', 'name': '翡翠水庫', 'type': '雨量', 'river': '新店溪'},
        {'code': '01A230', 'name': '坪林', 'type': '雨量', 'river': '北勢溪'},
        {'code': '466940', 'name': '台北', 'type': '雨量', 'river': '淡水河'},
        {'code': 'C0A9I0', 'name': '內湖', 'type': '雨量', 'river': '基隆河'},
        {'code': 'C0A9H0', 'name': '士林', 'type': '雨量', 'river': '基隆河'},
        {'code': '01A520', 'name': '三峽', 'type': '雨量', 'river': '大漢溪'},
    ]

    print(f"  [完成] 找到 {len(stations)} 個測站")
    print(f"    - 水位站: {sum(1 for s in stations if s['type'] == '水位')} 個")
    print(f"    - 雨量站: {sum(1 for s in stations if s['type'] == '雨量')} 個")
    print("    (這是圖譜的價值!一次查出整個流域的監測網絡)")

    return stations


def mock_timeseries_query(stations):
    """模擬 TimeseriesRAG 查詢 - 並行查詢 WRA API 即時資料"""
    print(f"\n[TimeseriesRAG 查詢] 並行查詢 {len(stations)} 個測站的即時資料...")
    print("  使用 ThreadPoolExecutor 同時發送多個 API 請求")
    print("  (傳統逐一查詢需要 10-15秒,並行查詢只需 2-3秒!)")

    start_time = time.time()
    time.sleep(2)  # 模擬 API 查詢時間

    # 模擬查詢結果 - 根據目前時間生成合理的數據
    water_results = []
    rain_results = []

    for station in stations:
        if station['type'] == '水位':
            # 模擬水位資料
            current_level = round(random.uniform(1.0, 5.0), 2)
            alert_1 = 6.0  # 一級警戒
            alert_2 = 5.0  # 二級警戒

            water_results.append({
                'code': station['code'],
                'name': station['name'],
                'river': station['river'],
                'current_level': current_level,
                'alert_1': alert_1,
                'alert_2': alert_2,
                'is_warning': current_level >= alert_2,
                'warning_level': '二級警戒' if current_level >= alert_2 else '正常'
            })
        else:
            # 模擬雨量資料
            rainfall_1h = round(random.uniform(0, 80), 1)

            rain_results.append({
                'code': station['code'],
                'name': station['name'],
                'river': station['river'],
                'rainfall_1h': rainfall_1h,
                'is_warning': rainfall_1h >= 50,
                'warning_level': _classify_rainfall(rainfall_1h)
            })

    elapsed = time.time() - start_time
    print(f"  [完成] 查詢成功: 水位 {len(water_results)} 個, 雨量 {len(rain_results)} 個")
    print(f"    (耗時: {elapsed:.2f}秒)")

    return {
        'water_levels': water_results,
        'rainfalls': rain_results
    }


def _classify_rainfall(rainfall_1h):
    """降雨分級"""
    if rainfall_1h >= 80:
        return "大豪雨"
    elif rainfall_1h >= 50:
        return "豪雨"
    elif rainfall_1h >= 24:
        return "大雨"
    else:
        return "正常"


def analyze_risk(water_data, rain_data):
    """風險分析 - 比對警戒值"""
    print("\n[風險分析] 比對警戒值,計算風險等級...")

    warnings = []

    # 分析水位警戒
    for w in water_data:
        if w['is_warning']:
            warnings.append({
                'type': '水位警戒',
                'station': w['name'],
                'river': w['river'],
                'level': w['warning_level'],
                'value': f"{w['current_level']:.2f}m",
                'alert': f"{w['alert_2']:.2f}m"
            })

    # 分析雨量警戒
    for r in rain_data:
        if r['is_warning']:
            warnings.append({
                'type': '強降雨',
                'station': r['name'],
                'river': r['river'],
                'level': r['warning_level'],
                'value': f"{r['rainfall_1h']:.1f}mm/hr",
                'alert': '50mm/hr'
            })

    total = len(water_data) + len(rain_data)
    warning_ratio = len(warnings) / total if total > 0 else 0

    # 計算風險等級
    if warning_ratio >= 0.3:
        risk_level = "高風險"
    elif warning_ratio >= 0.1:
        risk_level = "中風險"
    elif len(warnings) > 0:
        risk_level = "低風險"
    else:
        risk_level = "安全"

    print(f"  [完成] 警戒測站: {len(warnings)}/{total}")
    print(f"    風險等級: {risk_level}")

    return {
        'risk_level': risk_level,
        'warnings': warnings,
        'total_stations': total,
        'warning_count': len(warnings),
        'warning_ratio': warning_ratio
    }


def generate_answer(river_name, analysis, timeseries_data):
    """生成最終回答"""
    print("\n[生成回答] 整合所有資訊,產生完整評估報告...")
    time.sleep(0.5)

    answer = f"""
{'='*70}
{river_name}流域安全評估報告
{'='*70}
查詢時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[風險等級] {analysis['risk_level']}

[監測概況]
- 監測測站總數: {analysis['total_stations']} 個
- 警戒測站數量: {analysis['warning_count']} 個 ({analysis['warning_ratio']*100:.1f}%)
- 水位測站: {len(timeseries_data['water_levels'])} 個
- 雨量測站: {len(timeseries_data['rainfalls'])} 個
"""

    # 警戒詳情
    if analysis['warnings']:
        answer += "\n[警戒詳情]\n"
        for i, w in enumerate(analysis['warnings'][:5], 1):
            answer += f"{i}. {w['station']} ({w['river']})\n"
            answer += f"   類型: {w['type']}\n"
            answer += f"   等級: {w['level']}\n"
            answer += f"   數值: {w['value']} (警戒值: {w['alert']})\n\n"

        if len(analysis['warnings']) > 5:
            answer += f"   ... 還有 {len(analysis['warnings']) - 5} 個警戒測站\n"
    else:
        answer += "\n[警戒詳情] 無\n"

    # 建議
    answer += "\n[建議]\n"
    if analysis['risk_level'] == "高風險":
        answer += "[警告] 建議立即採取防範措施:\n"
        answer += "  1. 密切監控上游水位變化\n"
        answer += "  2. 準備疏散低窪地區居民\n"
        answer += "  3. 啟動應變小組\n"
    elif analysis['risk_level'] == "中風險":
        answer += "[注意] 建議持續關注:\n"
        answer += "  1. 每30分鐘更新一次資料\n"
        answer += "  2. 通知相關單位準備\n"
        answer += "  3. 若雨勢持續,風險將升高\n"
    elif analysis['risk_level'] == "低風險":
        answer += "[OK] 整體安全,但建議:\n"
        answer += "  1. 持續監控警戒測站\n"
        answer += "  2. 注意天氣預報\n"
    else:
        answer += "[OK] 目前狀況良好,所有測站正常\n"

    # 即時數據
    answer += "\n[即時監測數據]\n"
    answer += "水位測站:\n"
    for w in timeseries_data['water_levels'][:5]:
        status = "[警戒]" if w['is_warning'] else "[正常]"
        answer += f"  {status} {w['name']}: {w['current_level']:.2f}m (警戒: {w['alert_2']:.2f}m)\n"

    answer += "\n雨量測站:\n"
    for r in timeseries_data['rainfalls'][:5]:
        status = "[警戒]" if r['is_warning'] else "[正常]"
        answer += f"  {status} {r['name']}: {r['rainfall_1h']:.1f}mm/hr\n"

    answer += "\n" + "="*70

    return answer


def main():
    """主程式 - 完整展示流程"""
    print("\n" + "="*70)
    print("  台灣水文知識圖譜 - GraphRAG + TimeseriesRAG 混合查詢系統")
    print("  POC Demo (使用模擬資料展示完整架構)")
    print("="*70)

    # 使用者問題
    question = "淡水河現在安全嗎?"
    river_name = "淡水河"

    print(f"\n使用者問題: {question}")
    print("\n" + "="*70)
    print("開始執行混合查詢...")
    print("="*70)

    # Step 1: GraphRAG
    print("\n[步驟 1/4] GraphRAG 階段")
    print("-" * 70)
    stations = mock_graphrag_query(river_name)

    # Step 2: TimeseriesRAG
    print("\n[步驟 2/4] TimeseriesRAG 階段")
    print("-" * 70)
    timeseries_data = mock_timeseries_query(stations)

    # Step 3: 風險分析
    print("\n[步驟 3/4] 風險分析階段")
    print("-" * 70)
    analysis = analyze_risk(
        timeseries_data['water_levels'],
        timeseries_data['rainfalls']
    )

    # Step 4: 生成回答
    print("\n[步驟 4/4] 生成回答階段")
    print("-" * 70)
    answer = generate_answer(river_name, analysis, timeseries_data)

    # 顯示最終答案
    print("\n" + "="*70)
    print("最終答案")
    print("="*70)
    print(answer)

    # POC 特色說明
    print("\n" + "="*70)
    print("POC 核心特色與創新點")
    print("="*70)

    print("""
[1] GraphRAG (知識圖譜查詢)
    與傳統 RAG 的差異:
    - 傳統: 只能查詢 Wikipedia 等靜態文字知識
    - 本系統: 利用圖譜空間關係,一次找出整個流域的監測網絡

    技術亮點:
    - 使用 Neo4j 存儲河川階層關係 (主流->支流->測站)
    - 透過 BELONGS_TO, IS_TRIBUTARY_OF, MONITORS 關係查詢
    - 這是 SQL 做不到的複雜空間關係查詢!

[2] TimeseriesRAG (即時監測資料)
    與傳統 RAG 的差異:
    - 傳統: 只能查詢歷史文件
    - 本系統: 整合 WRA API 即時資料,提供動態監測

    技術亮點:
    - 並行查詢加速: 10個測站從15秒降到2秒
    - 自動比對政府警戒值,不需要複雜計算
    - 支援水位、雨量、流量等多種監測類型

[3] 智能風險分析
    - 自動計算風險等級 (安全/低/中/高)
    - 根據警戒測站比例動態調整
    - 提供具體行動建議,不只是數據呈現

[4] 實用價值
    應用場景:
    - 防災單位即時監控
    - 水利署決策支援
    - 一般民眾查詢淹水風險

    可擴展性:
    - Week 2: 加入災害案例向量搜尋 (VectorRAG)
    - Week 3: 加入 LLM 生成自然語言回答
    - Week 4: 建立 TimescaleDB 本地快取
    """)

    print("="*70)
    print("\n[執行完成] POC Demo 展示完畢!")
    print("\n這就是 GraphRAG + TimeseriesRAG 混合查詢的完整架構!")
    print("相較於傳統 RAG 只能查靜態知識,本系統實現了:")
    print("  - 空間關係查詢 (圖譜)")
    print("  - 即時資料整合 (時序)")
    print("  - 智能風險評估 (分析)")
    print("\n這才是真正有價值的動態監測系統! ")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
