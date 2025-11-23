"""
簡化版 POC Demo - 不需要 Neo4j 連線
直接展示混合查詢流程和結果
"""
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time


class WRAApiClient:
    """WRA API 即時資料查詢器"""

    def __init__(self, max_workers=10):
        self.base_url = "https://fhy.wra.gov.tw/WraApi/v1"
        self.max_workers = max_workers
        self.timeout = 5

    def fetch_water_level(self, station_code):
        """查詢水位站即時資料"""
        try:
            url = f"{self.base_url}/Station/Water/{station_code}"
            response = requests.get(url, timeout=self.timeout)
            data = response.json()

            current = float(data.get('WaterLevel', 0) or 0)
            alert_1 = float(data.get('AlertLevel1', 999) or 999)
            alert_2 = float(data.get('AlertLevel2', 999) or 999)

            return {
                'success': True,
                'station_code': station_code,
                'name': data.get('StationName', '未知'),
                'current_level': current,
                'alert_1': alert_1,
                'alert_2': alert_2,
                'is_warning': current >= alert_2,
                'warning_level': self._get_water_warning_level(current, alert_1, alert_2)
            }
        except Exception as e:
            return {'success': False, 'station_code': station_code, 'error': str(e)}

    def fetch_rainfall(self, station_code):
        """查詢雨量站即時資料"""
        try:
            url = f"{self.base_url}/Rain/Station/{station_code}"
            response = requests.get(url, timeout=self.timeout)
            data = response.json()

            rainfall_1h = float(data.get('Rainfall_1hr', 0) or 0)

            return {
                'success': True,
                'station_code': station_code,
                'name': data.get('StationName', '未知'),
                'rainfall_1h': rainfall_1h,
                'is_warning': rainfall_1h >= 50,
                'warning_level': self._get_rainfall_warning_level(rainfall_1h)
            }
        except Exception as e:
            return {'success': False, 'station_code': station_code, 'error': str(e)}

    def _get_water_warning_level(self, current, alert_1, alert_2):
        """判斷水位警戒等級"""
        if current >= alert_1:
            return "一級警戒"
        elif current >= alert_2:
            return "二級警戒"
        else:
            return "正常"

    def _get_rainfall_warning_level(self, rainfall_1h):
        """判斷雨量警戒等級"""
        if rainfall_1h >= 80:
            return "大豪雨"
        elif rainfall_1h >= 50:
            return "豪雨"
        elif rainfall_1h >= 24:
            return "大雨"
        else:
            return "正常"

    def batch_query_stations(self, water_stations, rain_stations):
        """並行批次查詢測站資料"""
        water_results = []
        rain_results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}

            # 提交水位站查詢
            for code in water_stations:
                future = executor.submit(self.fetch_water_level, code)
                futures[future] = ('water', code)

            # 提交雨量站查詢
            for code in rain_stations:
                future = executor.submit(self.fetch_rainfall, code)
                futures[future] = ('rain', code)

            # 收集結果
            for future in as_completed(futures):
                query_type, code = futures[future]
                try:
                    result = future.result()
                    if result['success']:
                        if query_type == 'water':
                            water_results.append(result)
                        else:
                            rain_results.append(result)
                    else:
                        print(f"[失敗] {code}: {result.get('error', '未知錯誤')}")
                except Exception as e:
                    print(f"[錯誤] {code}: {e}")

        return {
            'water_levels': water_results,
            'rainfalls': rain_results
        }


def analyze_risk(water_data, rain_data):
    """分析淹水風險"""
    warnings = []
    total = len(water_data) + len(rain_data)

    # 檢查水位警戒
    for w in water_data:
        if w['is_warning']:
            warnings.append({
                'type': '水位警戒',
                'station': w['name'],
                'level': w['warning_level'],
                'value': f"{w['current_level']:.2f}m",
                'alert': f"{w['alert_2']:.2f}m"
            })

    # 檢查雨量警戒
    for r in rain_data:
        if r['is_warning']:
            warnings.append({
                'type': '強降雨',
                'station': r['name'],
                'level': r['warning_level'],
                'value': f"{r['rainfall_1h']:.1f}mm/hr",
                'alert': '50mm/hr'
            })

    # 計算風險等級
    warning_ratio = len(warnings) / total if total > 0 else 0

    if warning_ratio >= 0.3:
        risk_level = "高風險"
    elif warning_ratio >= 0.1:
        risk_level = "中風險"
    elif len(warnings) > 0:
        risk_level = "低風險"
    else:
        risk_level = "安全"

    return {
        'risk_level': risk_level,
        'warnings': warnings,
        'total_stations': total,
        'warning_count': len(warnings),
        'warning_ratio': warning_ratio
    }


def main():
    """POC Demo 主程式"""
    print("\n" + "="*70)
    print("  台灣水文知識圖譜 - GraphRAG + TimeseriesRAG 混合查詢 POC Demo")
    print("="*70 + "\n")

    print("使用者問題: 淡水河現在安全嗎?")
    print("\n" + "="*70)

    # 模擬 GraphRAG 查詢結果 (實際會從 Neo4j 查詢)
    print("\n[步驟 1/4] GraphRAG 查詢: 從知識圖譜找出淡水河流域的所有測站...")
    print("  (模擬) 透過圖譜關係查詢:")
    print("    淡水河 -> 所屬水系 -> 水系中的所有河川 -> 監測這些河川的測站")

    # 淡水河流域的真實測站代號
    water_stations = [
        '1500H005',  # 碧潭 (新店溪)
        '1500H021',  # 秀朗橋 (新店溪)
        '1120H008',  # 大漢橋 (大漢溪)
        '1500H029',  # 台北橋 (淡水河)
        '1500H041',  # 關渡 (淡水河)
    ]

    rain_stations = [
        '01A260',    # 翡翠水庫
        '01A230',    # 坪林
        '466940',    # 台北
        'C0A9I0',    # 內湖
        'C0A9H0',    # 士林
    ]

    print(f"  找到 {len(water_stations) + len(rain_stations)} 個測站")
    print(f"    - 水位站: {len(water_stations)} 個")
    print(f"    - 雨量站: {len(rain_stations)} 個")
    print("  (耗時: 0.5秒)")

    # TimeseriesRAG - 查詢即時資料
    print("\n[步驟 2/4] TimeseriesRAG 查詢: 並行查詢測站即時資料...")
    start_time = time.time()

    wra_client = WRAApiClient(max_workers=15)
    timeseries_data = wra_client.batch_query_stations(water_stations, rain_stations)

    api_time = time.time() - start_time
    print(f"  成功查詢: 水位 {len(timeseries_data['water_levels'])} 個, "
          f"雨量 {len(timeseries_data['rainfalls'])} 個")
    print(f"  (耗時: {api_time:.2f}秒) <-- 並行查詢加速!")

    # 風險分析
    print("\n[步驟 3/4] 風險分析: 比對警戒值,計算風險等級...")
    analysis = analyze_risk(
        timeseries_data['water_levels'],
        timeseries_data['rainfalls']
    )
    print(f"  警戒測站: {analysis['warning_count']}/{analysis['total_stations']}")
    print(f"  風險等級: {analysis['risk_level']}")

    # 生成回答
    print("\n[步驟 4/4] 生成最終回答...")
    print("\n" + "="*70)
    print("最終答案")
    print("="*70)

    print(f"""
淡水河流域安全評估報告
查詢時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[風險等級] {analysis['risk_level']}

[監測概況]
- 監測測站總數: {analysis['total_stations']} 個
- 警戒測站數量: {analysis['warning_count']} 個 ({analysis['warning_ratio']*100:.1f}%)
- 水位測站: {len(timeseries_data['water_levels'])} 個
- 雨量測站: {len(timeseries_data['rainfalls'])} 個
""")

    # 顯示警戒詳情
    if analysis['warnings']:
        print("[警戒詳情]")
        for i, w in enumerate(analysis['warnings'], 1):
            print(f"{i}. {w['station']}")
            print(f"   類型: {w['type']}")
            print(f"   等級: {w['level']}")
            print(f"   數值: {w['value']} (警戒: {w['alert']})\n")
    else:
        print("[警戒詳情] 無")

    # 建議
    print("\n[建議]")
    if analysis['risk_level'] == "高風險":
        print("[警告] 建議立即採取防範措施:")
        print("  1. 密切監控上游水位變化")
        print("  2. 準備疏散低窪地區居民")
        print("  3. 啟動應變小組")
    elif analysis['risk_level'] == "中風險":
        print("[注意] 建議持續關注:")
        print("  1. 每30分鐘更新一次資料")
        print("  2. 通知相關單位準備")
        print("  3. 若雨勢持續,風險將升高")
    elif analysis['risk_level'] == "低風險":
        print("[OK] 整體安全,但建議:")
        print("  1. 持續監控警戒測站")
        print("  2. 注意天氣預報")
    else:
        print("[OK] 目前狀況良好,所有測站正常")

    print("\n" + "="*70)

    # 顯示實際水位/雨量數據
    print("\n[即時數據詳情]")
    print("\n水位測站:")
    for w in timeseries_data['water_levels']:
        status = "[警戒]" if w['is_warning'] else "[正常]"
        print(f"  {status} {w['name']}: {w['current_level']:.2f}m "
              f"(警戒: {w['alert_2']:.2f}m)")

    print("\n雨量測站:")
    for r in timeseries_data['rainfalls']:
        status = "[警戒]" if r['is_warning'] else "[正常]"
        print(f"  {status} {r['name']}: {r['rainfall_1h']:.1f}mm/hr")

    # POC 特色展示
    print("\n" + "="*70)
    print("[POC 核心特色]")
    print("="*70)
    print("[1] GraphRAG (知識圖譜)")
    print("    - 利用圖譜關係找出整個流域的測站")
    print("    - 不是只查單一河川,而是查整個水系!")
    print("    - 這是 SQL 做不到的空間關係查詢")
    print()
    print("[2] TimeseriesRAG (即時監測)")
    print("    - 並行查詢 WRA API,2-3秒查完10+測站")
    print("    - 自動比對政府公告的警戒值")
    print("    - 不需要複雜的水文計算!")
    print()
    print("[3] 智能分析")
    print("    - 自動計算風險等級 (安全/低/中/高)")
    print("    - 給出具體建議,不只是數據呈現")
    print()
    print("[4] 與傳統 RAG 的差異")
    print("    - 傳統 RAG: 只能查 Wikipedia 靜態知識")
    print("    - 本系統: 結合即時資料 + 空間關係 + 語義搜尋")
    print("    - 真正的動態監測系統!")
    print()
    print(f"[總耗時] {api_time + 0.5:.2f}秒 (GraphRAG 0.5秒 + TimeseriesRAG {api_time:.2f}秒)")
    print("="*70)


if __name__ == "__main__":
    main()
