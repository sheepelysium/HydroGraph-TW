"""
水位雨量警戒監控系統
使用 WRA API 即時資料 + 警戒值判斷
不需要複雜的水文計算!
"""
import requests
import pandas as pd
from datetime import datetime

class FloodAlertMonitor:
    """淹水警戒監控"""

    def __init__(self):
        self.wra_base_url = "https://fhy.wra.gov.tw/WraApi/v1"

    def get_water_level_alert(self, station_code):
        """
        取得水位站警戒狀態
        """
        try:
            url = f"{self.wra_base_url}/Station/Water/{station_code}"
            response = requests.get(url, timeout=10)
            data = response.json()

            current = float(data.get('WaterLevel', 0))
            alert_1 = float(data.get('AlertLevel1', 999))  # 一級警戒
            alert_2 = float(data.get('AlertLevel2', 999))  # 二級警戒
            alert_3 = float(data.get('AlertLevel3', 999))  # 三級警戒

            # 判斷警戒等級
            if current >= alert_1:
                level = "一級警戒"
                emoji = "🔴"
            elif current >= alert_2:
                level = "二級警戒"
                emoji = "🟠"
            elif current >= alert_3:
                level = "三級警戒"
                emoji = "🟡"
            else:
                level = "安全"
                emoji = "🟢"

            return {
                'station_code': station_code,
                'station_name': data.get('StationName'),
                'current_level': current,
                'alert_1': alert_1,
                'alert_2': alert_2,
                'alert_3': alert_3,
                'alert_status': level,
                'emoji': emoji,
                'is_warning': level != "安全",
                'timestamp': datetime.now()
            }

        except Exception as e:
            print(f"[錯誤] 查詢測站 {station_code} 失敗: {e}")
            return None

    def classify_rainfall(self, rainfall_1h):
        """
        依據氣象局標準分類降雨強度

        參數:
            rainfall_1h: 1小時雨量 (mm)
        """
        if rainfall_1h >= 130:
            return "超大豪雨", "🔴", True
        elif rainfall_1h >= 80:
            return "大豪雨", "🟠", True
        elif rainfall_1h >= 50:
            return "豪雨", "🟡", True
        elif rainfall_1h >= 24:
            return "大雨", "🟢", False
        else:
            return "正常", "⚪", False

    def get_rainfall_alert(self, station_code):
        """
        取得雨量站警戒狀態
        """
        try:
            # 查詢最近1小時雨量
            url = f"{self.wra_base_url}/Rain/Station/{station_code}"
            response = requests.get(url, timeout=10)
            data = response.json()

            rainfall_1h = float(data.get('Rainfall_1hr', 0))

            # 分類
            category, emoji, is_warning = self.classify_rainfall(rainfall_1h)

            return {
                'station_code': station_code,
                'station_name': data.get('StationName'),
                'rainfall_1h': rainfall_1h,
                'category': category,
                'emoji': emoji,
                'is_warning': is_warning,
                'timestamp': datetime.now()
            }

        except Exception as e:
            print(f"[錯誤] 查詢雨量站 {station_code} 失敗: {e}")
            return None

    def monitor_stations(self, water_stations=None, rain_stations=None):
        """
        批次監控多個測站

        參數:
            water_stations: 水位站代號列表
            rain_stations: 雨量站代號列表
        """
        print(f"\n{'='*60}")
        print(f"水文警戒監控系統 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        warnings = []

        # 監控水位站
        if water_stations:
            print("【水位監控】")
            for code in water_stations:
                result = self.get_water_level_alert(code)
                if result:
                    print(f"{result['emoji']} {result['station_name']} ({code})")
                    print(f"   目前水位: {result['current_level']:.2f}m")
                    print(f"   警戒水位: 一級 {result['alert_1']:.2f}m / "
                          f"二級 {result['alert_2']:.2f}m / "
                          f"三級 {result['alert_3']:.2f}m")
                    print(f"   狀態: {result['alert_status']}\n")

                    if result['is_warning']:
                        warnings.append(result)

        # 監控雨量站
        if rain_stations:
            print("\n【雨量監控】")
            for code in rain_stations:
                result = self.get_rainfall_alert(code)
                if result:
                    print(f"{result['emoji']} {result['station_name']} ({code})")
                    print(f"   1小時雨量: {result['rainfall_1h']:.1f}mm")
                    print(f"   等級: {result['category']}\n")

                    if result['is_warning']:
                        warnings.append(result)

        # 警告摘要
        if warnings:
            print(f"\n{'='*60}")
            print(f"⚠️  共有 {len(warnings)} 個測站發出警戒!")
            print(f"{'='*60}")
            for w in warnings:
                if 'alert_status' in w:
                    print(f"- {w['station_name']}: {w['alert_status']} "
                          f"(水位 {w['current_level']:.2f}m)")
                else:
                    print(f"- {w['station_name']}: {w['category']} "
                          f"(雨量 {w['rainfall_1h']:.1f}mm/hr)")
        else:
            print("\n✅ 所有測站目前安全")

        return warnings


if __name__ == "__main__":
    # 使用範例
    monitor = FloodAlertMonitor()

    # 淡水河流域重點測站 (範例)
    water_stations = [
        '1500H005',  # 碧潭 (新店溪)
        '1500H021',  # 秀朗橋 (新店溪)
        '1120H008',  # 大漢橋 (大漢溪)
    ]

    rain_stations = [
        '01A260',    # 翡翠水庫
        '01A230',    # 坪林
        '466940',    # 台北
    ]

    # 執行監控
    warnings = monitor.monitor_stations(
        water_stations=water_stations,
        rain_stations=rain_stations
    )
