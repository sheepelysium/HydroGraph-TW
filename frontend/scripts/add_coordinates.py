#!/usr/bin/env python3
"""
為 neo4j_graph_data.json 中的水系節點添加地理座標
"""
import json
import os

# 台灣主要水系的地理座標 (lat, lon) - 根據實際河川出海口位置
WATER_SYSTEM_COORDS = {
    # 北部
    "淡水河": (25.18, 121.43),
    "南崁溪": (25.08, 121.22),
    "社子溪": (24.98, 121.08),

    # 東北部（宜蘭）
    "蘭陽溪": (24.68, 121.82),
    "冬山河": (24.62, 121.85),
    "得子口溪": (24.58, 121.88),

    # 新竹苗栗
    "頭前溪": (24.82, 120.95),
    "鳳山溪": (24.88, 121.02),
    "客雅溪排水": (24.78, 120.90),
    "新豐溪": (24.92, 121.00),
    "中港溪": (24.65, 120.82),
    "後龍溪": (24.58, 120.78),
    "西湖溪": (24.52, 120.72),

    # 中部
    "大安溪": (24.42, 120.68),
    "大甲溪": (24.32, 120.62),
    "烏溪": (24.15, 120.50),
    "濁水溪": (23.85, 120.22),
    "溫寮溪": (24.22, 120.55),

    # 雲嘉南
    "北港溪": (23.55, 120.12),
    "朴子溪": (23.42, 120.15),
    "八掌溪": (23.35, 120.18),
    "急水溪": (23.22, 120.15),
    "曾文溪": (23.05, 120.08),
    "鹽水溪": (22.98, 120.12),
    "鹿耳門溪(鹿耳門排水)": (23.02, 120.05),

    # 高屏
    "二仁溪": (22.88, 120.18),
    "阿公店溪": (22.78, 120.25),
    "高屏溪": (22.48, 120.42),
    "東港溪": (22.42, 120.45),
    "林邊溪": (22.38, 120.50),
    "四重溪": (22.02, 120.72),
    "枋山溪": (22.18, 120.65),

    # 東部
    "花蓮溪": (23.95, 121.58),
    "秀姑巒溪": (23.48, 121.52),
    "卑南溪": (22.75, 121.15),
    "知本溪": (22.68, 121.05),
    "太麻里溪": (22.62, 121.02),
    "港口溪": (22.05, 120.88),

    # 其他小河川（估算位置）
    "老街溪": (24.98, 121.12),
    "大堀溪": (24.95, 121.05),
}

def get_river_coords(river_name):
    """根據河川名稱獲取座標，如果沒有則根據相似名稱推測"""
    # 直接匹配
    if river_name in WATER_SYSTEM_COORDS:
        return WATER_SYSTEM_COORDS[river_name]

    # 嘗試部分匹配
    for key, coords in WATER_SYSTEM_COORDS.items():
        if key in river_name or river_name in key:
            return coords

    # 根據河川名稱中的地名推測位置
    location_hints = {
        # 北部
        "台北": (25.05, 121.50),
        "基隆": (25.12, 121.72),
        "桃園": (25.00, 121.25),
        # 新竹苗栗
        "新竹": (24.80, 120.95),
        "苗栗": (24.55, 120.80),
        # 中部
        "台中": (24.15, 120.65),
        "彰化": (24.08, 120.52),
        "南投": (23.92, 120.68),
        # 雲嘉南
        "雲林": (23.70, 120.35),
        "嘉義": (23.48, 120.42),
        "台南": (23.00, 120.18),
        # 高屏
        "高雄": (22.62, 120.32),
        "屏東": (22.52, 120.48),
        # 東部
        "宜蘭": (24.65, 121.75),
        "花蓮": (23.98, 121.58),
        "台東": (22.75, 121.12),
    }

    for hint, coords in location_hints.items():
        if hint in river_name:
            return coords

    return None

def add_coordinates_to_json():
    """讀取 JSON 並添加座標"""
    json_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'data', 'neo4j_graph_data.json')

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    updated_count = 0
    missing = []

    for node in data['nodes']:
        if node['group'] == 'WaterSystem':
            name = node['name']
            coords = get_river_coords(name)

            if coords:
                node['lat'] = coords[0]
                node['lon'] = coords[1]
                updated_count += 1
            else:
                missing.append(name)
                # 給一個默認的中部位置
                node['lat'] = 23.50
                node['lon'] = 120.50

    # 保存更新後的 JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"已更新 {updated_count} 個水系節點的座標")
    if missing:
        print(f"以下水系未找到座標（使用默認值）：{missing}")

if __name__ == '__main__':
    add_coordinates_to_json()
