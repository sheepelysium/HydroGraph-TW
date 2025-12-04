# -*- coding: utf-8 -*-
"""將測站的 TWD97 座標轉換為 WGS84 經緯度,供 NeoDash 地圖使用"""
from neo4j import GraphDatabase
import math


class CoordinateConverter:
    """TWD97 轉 WGS84 座標轉換器"""

    @staticmethod
    def twd97_to_wgs84(x, y):
        """
        TWD97 (TWD97 TM2) 轉 WGS84 經緯度

        參考: https://github.com/snksos3/twd97-to-wgs84

        Args:
            x: TWD97 X 座標 (橫座標)
            y: TWD97 Y 座標 (縱座標)

        Returns:
            (latitude, longitude) WGS84 經緯度
        """
        # TWD97 TM2 投影參數
        a = 6378137.0  # 長半軸
        b = 6356752.314245  # 短半軸
        lon0 = 121.0 * math.pi / 180.0  # 中央子午線 121°E
        k0 = 0.9999  # 比例因子
        dx = 250000  # 東偏移

        # 計算 e^2 (第一離心率平方)
        e = math.pow((1 - math.pow(b, 2) / math.pow(a, 2)), 0.5)

        # 計算 x, y
        x_real = x - dx
        y_real = y

        # 計算 M (子午線弧長)
        M = y_real / k0
        mu = M / (a * (1.0 - math.pow(e, 2) / 4.0 - 3 * math.pow(e, 4) / 64.0 - 5 * math.pow(e, 6) / 256.0))

        # 計算 e1
        e1 = (1.0 - math.pow((1.0 - math.pow(e, 2)), 0.5)) / (1.0 + math.pow((1.0 - math.pow(e, 2)), 0.5))

        # 計算 J1-J4
        J1 = (3 * e1 / 2 - 27 * math.pow(e1, 3) / 32.0)
        J2 = (21 * math.pow(e1, 2) / 16 - 55 * math.pow(e1, 4) / 32.0)
        J3 = (151 * math.pow(e1, 3) / 96.0)
        J4 = (1097 * math.pow(e1, 4) / 512.0)

        # 計算 footprint latitude
        fp = mu + J1 * math.sin(2 * mu) + J2 * math.sin(4 * mu) + J3 * math.sin(6 * mu) + J4 * math.sin(8 * mu)

        # 計算 e', N, T, C, R, D
        e_prime = (e * a / b)
        C1 = math.pow(e_prime, 2) * math.pow(math.cos(fp), 2)
        T1 = math.pow(math.tan(fp), 2)
        R1 = a * (1 - math.pow(e, 2)) / math.pow((1 - math.pow(e, 2) * math.pow(math.sin(fp), 2)), (3.0 / 2.0))
        N1 = a / math.pow((1 - math.pow(e, 2) * math.pow(math.sin(fp), 2)), 0.5)
        D = x_real / (N1 * k0)

        # 計算 Q1-Q7
        Q1 = N1 * math.tan(fp) / R1
        Q2 = (math.pow(D, 2) / 2.0)
        Q3 = (5 + 3 * T1 + 10 * C1 - 4 * math.pow(C1, 2) - 9 * math.pow(e_prime, 2)) * math.pow(D, 4) / 24.0
        Q4 = (61 + 90 * T1 + 298 * C1 + 45 * math.pow(T1, 2) - 3 * math.pow(C1, 2) - 252 * math.pow(e_prime, 2)) * math.pow(D, 6) / 720.0
        Q5 = D
        Q6 = (1 + 2 * T1 + C1) * math.pow(D, 3) / 6
        Q7 = (5 - 2 * C1 + 28 * T1 - 3 * math.pow(C1, 2) + 8 * math.pow(e_prime, 2) + 24 * math.pow(T1, 2)) * math.pow(D, 5) / 120.0

        # 計算經緯度 (弧度)
        lat_rad = fp - Q1 * (Q2 - Q3 + Q4)
        lon_rad = lon0 + (Q5 - Q6 + Q7) / math.cos(fp)

        # 轉換為度
        latitude = lat_rad * 180.0 / math.pi
        longitude = lon_rad * 180.0 / math.pi

        return latitude, longitude


def convert_all_stations():
    """將所有測站的座標轉換為 WGS84 並儲存到 Neo4j"""

    print("="*80)
    print("TWD97 → WGS84 座標轉換")
    print("="*80)

    # Neo4j 連線
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "geoinfor"

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    converter = CoordinateConverter()

    try:
        with driver.session(database="neo4j") as session:
            # 取得所有有座標的測站
            print("\n讀取測站座標...")
            result = session.run("""
                MATCH (s:Station)
                WHERE s.x_twd97 IS NOT NULL
                  AND s.y_twd97 IS NOT NULL
                RETURN id(s) as id,
                       s.name as name,
                       s.x_twd97 as x,
                       s.y_twd97 as y
            """)

            stations = list(result)
            print(f"  找到 {len(stations)} 個有座標的測站")

            # 轉換座標
            print("\n開始轉換座標...")
            success_count = 0
            error_count = 0

            for idx, record in enumerate(stations):
                try:
                    station_id = record['id']
                    name = record['name']
                    x = float(record['x'])
                    y = float(record['y'])

                    # 轉換座標
                    lat, lon = converter.twd97_to_wgs84(x, y)

                    # 更新 Neo4j
                    session.run("""
                        MATCH (s:Station)
                        WHERE id(s) = $id
                        SET s.latitude = $lat,
                            s.longitude = $lon
                    """, id=station_id, lat=lat, lon=lon)

                    success_count += 1

                    if (idx + 1) % 100 == 0:
                        print(f"  已轉換 {idx + 1}/{len(stations)} 個測站...")

                except Exception as e:
                    print(f"  [錯誤] 轉換失敗: {name} - {e}")
                    error_count += 1

            print(f"\n[完成] 座標轉換完成!")
            print(f"  成功: {success_count} 個")
            print(f"  失敗: {error_count} 個")

            # 驗證結果
            print("\n驗證轉換結果...")
            result = session.run("""
                MATCH (s:Station)
                WHERE s.latitude IS NOT NULL AND s.longitude IS NOT NULL
                RETURN count(s) as count
            """).single()

            print(f"  有 WGS84 座標的測站: {result['count']} 個")

            # 顯示範例
            print("\n範例座標 (前5個):")
            result = session.run("""
                MATCH (s:Station)
                WHERE s.latitude IS NOT NULL
                RETURN s.name as name,
                       s.x_twd97 as x_twd97,
                       s.y_twd97 as y_twd97,
                       s.latitude as lat,
                       s.longitude as lon
                LIMIT 5
            """)

            print(f"\n{'測站名稱':<15} {'TWD97_X':<12} {'TWD97_Y':<12} {'緯度':<12} {'經度':<12}")
            print("-" * 70)
            for record in result:
                print(f"{record['name']:<15} "
                      f"{record['x_twd97']:<12.2f} "
                      f"{record['y_twd97']:<12.2f} "
                      f"{record['lat']:<12.6f} "
                      f"{record['lon']:<12.6f}")

            print("\n" + "="*80)
            print("現在可以在 NeoDash 使用地圖視覺化了!")
            print("="*80)
            print("\nCypher 查詢範例:")
            print("""
MATCH (s:Station)
WHERE s.latitude IS NOT NULL
  AND (s.status IS NULL OR NOT s.status CONTAINS '廢')
RETURN s.name as name,
       s.latitude as latitude,
       s.longitude as longitude,
       labels(s) as type
LIMIT 100
            """)

    except Exception as e:
        print(f"\n[錯誤] 發生錯誤: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.close()
        print("\n已關閉 Neo4j 連線")


if __name__ == "__main__":
    convert_all_stations()
