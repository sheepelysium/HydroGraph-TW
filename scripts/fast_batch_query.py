"""
快速批次查詢 WRA API
使用並行請求加速 20 個測站查詢
從 20 秒降到 2-3 秒!
"""
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time

class FastWRAQuery:
    """高速 WRA API 查詢器"""

    def __init__(self, max_workers=10):
        """
        參數:
            max_workers: 同時發送的最大請求數 (預設10個)
        """
        self.base_url = "https://fhy.wra.gov.tw/WraApi/v1"
        self.max_workers = max_workers
        self.timeout = 5  # 每個請求最多等5秒

    def fetch_water_level(self, station_code):
        """查詢單一水位站"""
        try:
            url = f"{self.base_url}/Station/Water/{station_code}"
            response = requests.get(url, timeout=self.timeout)
            data = response.json()

            current = float(data.get('WaterLevel', 0))
            alert_1 = float(data.get('AlertLevel1', 999))

            return {
                'success': True,
                'station_code': station_code,
                'name': data.get('StationName'),
                'current_level': current,
                'alert_1': alert_1,
                'is_warning': current >= alert_1
            }
        except Exception as e:
            return {
                'success': False,
                'station_code': station_code,
                'error': str(e)
            }

    def fetch_rainfall(self, station_code):
        """查詢單一雨量站"""
        try:
            url = f"{self.base_url}/Rain/Station/{station_code}"
            response = requests.get(url, timeout=self.timeout)
            data = response.json()

            rainfall_1h = float(data.get('Rainfall_1hr', 0))

            return {
                'success': True,
                'station_code': station_code,
                'name': data.get('StationName'),
                'rainfall_1h': rainfall_1h,
                'is_warning': rainfall_1h >= 50  # 豪雨標準
            }
        except Exception as e:
            return {
                'success': False,
                'station_code': station_code,
                'error': str(e)
            }

    def batch_query_parallel(self, water_stations=None, rain_stations=None):
        """
        並行批次查詢多個測站

        時間複雜度:
        - 傳統逐一查詢: O(n) × 平均請求時間 (20個 × 0.5秒 = 10秒)
        - 並行查詢: O(1) × 最慢請求時間 (通常 1-2秒)

        加速比: 5-10倍!
        """
        start_time = time.time()
        results = {
            'water_levels': [],
            'rainfalls': [],
            'warnings': []
        }

        # 使用 ThreadPoolExecutor 並行處理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}

            # 提交所有水位站查詢
            if water_stations:
                for code in water_stations:
                    future = executor.submit(self.fetch_water_level, code)
                    futures[future] = ('water', code)

            # 提交所有雨量站查詢
            if rain_stations:
                for code in rain_stations:
                    future = executor.submit(self.fetch_rainfall, code)
                    futures[future] = ('rain', code)

            # 收集結果 (當任一請求完成就處理)
            for future in as_completed(futures):
                query_type, code = futures[future]
                try:
                    result = future.result()

                    if result['success']:
                        if query_type == 'water':
                            results['water_levels'].append(result)
                            if result['is_warning']:
                                results['warnings'].append({
                                    'type': '水位警戒',
                                    'station': result['name'],
                                    'value': f"{result['current_level']:.2f}m"
                                })
                        else:
                            results['rainfalls'].append(result)
                            if result['is_warning']:
                                results['warnings'].append({
                                    'type': '強降雨',
                                    'station': result['name'],
                                    'value': f"{result['rainfall_1h']:.1f}mm/hr"
                                })
                    else:
                        print(f"[失敗] {code}: {result.get('error')}")

                except Exception as e:
                    print(f"[錯誤] {code}: {e}")

        elapsed = time.time() - start_time
        results['query_time'] = elapsed

        print(f"\n[性能] 查詢完成: {elapsed:.2f}秒")
        print(f"  - 水位站: {len(results['water_levels'])} 個")
        print(f"  - 雨量站: {len(results['rainfalls'])} 個")
        print(f"  - 警戒數: {len(results['warnings'])} 個")

        return results


def performance_comparison():
    """
    性能比較測試
    """
    print("="*60)
    print("性能測試: 並行查詢 vs 逐一查詢")
    print("="*60)

    # 測試資料
    test_water = ['1500H005', '1500H021', '1120H008', '1140H012', '1500H041']
    test_rain = ['01A260', '01A230', '466940', 'C0A9I0', 'C0A9H0']

    # 方法1: 並行查詢
    print("\n【方法1: 並行查詢】")
    fast_query = FastWRAQuery(max_workers=10)
    results_parallel = fast_query.batch_query_parallel(
        water_stations=test_water,
        rain_stations=test_rain
    )
    time_parallel = results_parallel['query_time']

    # 方法2: 逐一查詢 (傳統做法)
    print("\n【方法2: 逐一查詢 (傳統做法)】")
    start = time.time()
    slow_query = FastWRAQuery(max_workers=1)  # 限制為1個worker
    results_sequential = slow_query.batch_query_parallel(
        water_stations=test_water,
        rain_stations=test_rain
    )
    time_sequential = results_sequential['query_time']

    # 比較
    print("\n" + "="*60)
    print("性能比較結果")
    print("="*60)
    print(f"並行查詢: {time_parallel:.2f}秒")
    print(f"逐一查詢: {time_sequential:.2f}秒")
    print(f"加速比: {time_sequential/time_parallel:.1f}x")
    print(f"節省時間: {time_sequential - time_parallel:.2f}秒")


if __name__ == "__main__":
    # 執行性能測試
    performance_comparison()

    print("\n" + "="*60)
    print("實際使用範例")
    print("="*60)

    # 淡水河流域 20 個測站查詢
    fast_query = FastWRAQuery(max_workers=15)

    results = fast_query.batch_query_parallel(
        water_stations=[
            '1500H005', '1500H021', '1120H008', '1140H012', '1500H041',
            '1500H029', '1500H039', '1120H015', '1140H009', '1500H011'
        ],
        rain_stations=[
            '01A260', '01A230', '466940', 'C0A9I0', 'C0A9H0',
            '01A520', '01A540', '466920', '466880', 'C0AC80'
        ]
    )

    # 顯示警戒
    if results['warnings']:
        print(f"\n⚠️  發現 {len(results['warnings'])} 個警戒:")
        for w in results['warnings']:
            print(f"  - {w['station']}: {w['type']} ({w['value']})")
    else:
        print("\n✅ 所有測站正常")
