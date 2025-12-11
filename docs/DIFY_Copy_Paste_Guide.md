# DIFY 工具更新：複製貼上指南（樹狀階層排序版）

## 輸出格式說明

**所有工具統一使用以下輸出變數（不可更改）：**

| 工具 | 輸出變數 |
|------|----------|
| searchStation | `count` (Number), `stations` (String) |
| getStationsByRiver | `count` (Number), `rainfall_count` (Number), `water_level_count` (Number), `stations_json` (String) |
| getStationsByWaterSystem | `count` (Number), `stations_json` (String), `message` (String) |
| getStationsByCity | `count` (Number), `rainfall_count` (Number), `water_level_count` (Number), `stations_json` (String) |
| getStationStats | `success` (Boolean), `rainfallTotal` (Number), `waterLevelTotal` (Number), `totalStations` (Number), `details_json` (String), `top_cities_json` (String), `message` (String) |
| getRiverTributaries | `count` (Number), `rivers_json` (String), `message` (String) |
| getRiversInWaterSystem | `count` (Number), `rivers_json` (String), `message` (String) |
| getRiverFlowPath | `found` (Boolean), `path` (String), `message` (String) |
| searchStationObservation | `count` (Number), `stations` (String) |

---

## 全部 9 個工具

1. **searchStation** - 搜尋測站（模糊搜尋）
2. **getStationsByRiver** - 依河川查詢測站
3. **getStationsByWaterSystem** - 依水系查詢測站
4. **getStationsByCity** - 依縣市查詢測站
5. **getStationStats** - 測站統計
6. **getRiverTributaries** - 河川支流查詢（樹狀排序）
7. **getRiversInWaterSystem** - 水系河川查詢（樹狀排序）
8. **getRiverFlowPath** - 河川流向查詢
9. **searchStationObservation** - 查詢測站觀測資料（呼叫 DIFY API）

---

## 🔧 工具 1：searchStation（測站搜尋）

### 輸出變數
- `count`: Number
- `stations`: String (JSON，按雨量/水位分組)

### 完整代碼（直接複製）

```python
import json
import urllib.request
import urllib.error
import base64

def main(keyword: str, filterType: str = "全部") -> dict:
    """搜尋測站（模糊搜尋，自動分類雨量/水位）

    DIFY 輸出變數：
    - count: Number
    - stations: String (JSON格式，按雨量站/水位站分組)

    智慧過濾：
    - 關鍵字含「水位」→ 只顯示水位站
    - 關鍵字含「雨量」→ 只顯示雨量站
    - filterType 指定 → 只顯示該類型
    - 其他 → 顯示全部，按類型分組
    """
    NEO4J_URLS = [
        "http://localhost:7474/db/neo4j/tx/commit",
        "http://host.docker.internal:7474/db/neo4j/tx/commit",
        "http://127.0.0.1:7474/db/neo4j/tx/commit"
    ]
    NEO4J_AUTH = base64.b64encode(b"neo4j:geoinfor").decode()

    # 判斷過濾類型
    filter_type = None
    search_keyword = keyword
    if "水位" in keyword:
        filter_type = "水位"
        search_keyword = keyword.replace("水位站", "").replace("水位", "").strip()
    elif "雨量" in keyword:
        filter_type = "雨量"
        search_keyword = keyword.replace("雨量站", "").replace("雨量", "").strip()

    # 如果去掉類型後關鍵字為空，使用原關鍵字
    if not search_keyword:
        search_keyword = keyword

    # 決定最終過濾類型（優先使用智慧判斷，其次使用傳入參數）
    final_filter = filter_type if filter_type else filterType

    query_body = {
        "statements": [{
            "statement": """
                CALL custom.searchStation($keyword, $filterType)
                YIELD code, name, type, city, riverName, status
                RETURN code, name, type, city, riverName AS river, status
            """,
            "parameters": {"keyword": search_keyword, "filterType": final_filter}
        }]
    }

    for url in NEO4J_URLS:
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(query_body).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {NEO4J_AUTH}"
                }
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))

                if result.get("errors"):
                    return {"count": 0, "stations": "{}"}

                rainfall_stations = []
                waterlevel_stations = []

                if result.get("results") and result["results"][0].get("data"):
                    for row in result["results"][0]["data"]:
                        code, name, stype, city, river, status = row["row"]
                        station = {
                            "code": code,
                            "name": name,
                            "city": city,
                            "river": river,
                            "status": status
                        }
                        if stype == "雨量":
                            rainfall_stations.append(station)
                        else:
                            waterlevel_stations.append(station)

                # 根據過濾類型返回結果
                if filter_type == "水位":
                    grouped = {"水位站": waterlevel_stations}
                    return {
                        "count": len(waterlevel_stations),
                        "stations": json.dumps(grouped, ensure_ascii=False)
                    }
                elif filter_type == "雨量":
                    grouped = {"雨量站": rainfall_stations}
                    return {
                        "count": len(rainfall_stations),
                        "stations": json.dumps(grouped, ensure_ascii=False)
                    }
                else:
                    grouped = {"雨量站": rainfall_stations, "水位站": waterlevel_stations}
                    total = len(rainfall_stations) + len(waterlevel_stations)
                    return {
                        "count": total,
                        "stations": json.dumps(grouped, ensure_ascii=False)
                    }
        except:
            continue

    return {"count": 0, "stations": "{}"}
```

---

## 🔧 工具 2：getStationsByRiver（依河川查詢測站）

### 輸出變數
- `count`: Number
- `rainfall_count`: Number
- `water_level_count`: Number
- `stations_json`: String (JSON)

### 完整代碼（直接複製）

```python
import json
import urllib.request
import urllib.error
import base64

def main(riverName: str, filterType: str = "全部") -> dict:
    """依河川查詢測站

    DIFY 輸出變數：
    - count: Number
    - rainfall_count: Number
    - water_level_count: Number
    - stations_json: String (JSON格式，按類型分組)
    """
    NEO4J_URLS = [
        "http://localhost:7474/db/neo4j/tx/commit",
        "http://host.docker.internal:7474/db/neo4j/tx/commit",
        "http://127.0.0.1:7474/db/neo4j/tx/commit"
    ]
    NEO4J_AUTH = base64.b64encode(b"neo4j:geoinfor").decode()

    query_body = {
        "statements": [{
            "statement": """
                CALL custom.getStationsByRiver($riverName)
                YIELD code, name, type, city, river, status
                RETURN code, name, type, city, river, status
            """,
            "parameters": {"riverName": riverName}
        }]
    }

    for url in NEO4J_URLS:
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(query_body).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {NEO4J_AUTH}"
                }
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))

                if result.get("errors"):
                    return {"count": 0, "rainfall_count": 0, "water_level_count": 0, "stations_json": "[]"}

                rainfall_stations = []
                waterlevel_stations = []

                if result.get("results") and result["results"][0].get("data"):
                    for row in result["results"][0]["data"]:
                        code, name, stype, city, river, status = row["row"]
                        station = {"code": code, "name": name, "city": city, "river": river}
                        if stype == "雨量":
                            rainfall_stations.append(station)
                        else:
                            waterlevel_stations.append(station)

                # 根據 filterType 過濾
                if filterType == "雨量站":
                    grouped = {"雨量站": rainfall_stations}
                    return {
                        "count": len(rainfall_stations),
                        "rainfall_count": len(rainfall_stations),
                        "water_level_count": 0,
                        "stations_json": json.dumps(grouped, ensure_ascii=False)
                    }
                elif filterType == "水位站":
                    grouped = {"水位站": waterlevel_stations}
                    return {
                        "count": len(waterlevel_stations),
                        "rainfall_count": 0,
                        "water_level_count": len(waterlevel_stations),
                        "stations_json": json.dumps(grouped, ensure_ascii=False)
                    }
                else:
                    grouped = {"雨量站": rainfall_stations, "水位站": waterlevel_stations}
                    total = len(rainfall_stations) + len(waterlevel_stations)
                    return {
                        "count": total,
                        "rainfall_count": len(rainfall_stations),
                        "water_level_count": len(waterlevel_stations),
                        "stations_json": json.dumps(grouped, ensure_ascii=False)
                    }
        except:
            continue

    return {"count": 0, "rainfall_count": 0, "water_level_count": 0, "stations_json": "[]"}
```

---

## 🔧 工具 3：getStationsByWaterSystem（依水系查詢測站）

### 輸出變數
- `count`: Number
- `stations_json`: String (JSON)
- `message`: String

### 完整代碼（直接複製）

```python
import json
import urllib.request
import urllib.error
import base64

def main(waterSystemName: str) -> dict:
    """查詢水系內所有測站（按雨量/水位分組）

    DIFY 輸出變數：
    - count: Number
    - stations_json: String (JSON格式，按類型分組)
    - message: String
    """
    NEO4J_URLS = [
        "http://localhost:7474/db/neo4j/tx/commit",
        "http://host.docker.internal:7474/db/neo4j/tx/commit",
        "http://127.0.0.1:7474/db/neo4j/tx/commit"
    ]
    NEO4J_AUTH = base64.b64encode(b"neo4j:geoinfor").decode()

    query_body = {
        "statements": [{
            "statement": """
                CALL custom.getStationsByWaterSystem($waterSystemName)
                YIELD code, name, type, city, river, status
                RETURN code, name, type, river
            """,
            "parameters": {"waterSystemName": waterSystemName}
        }]
    }

    for url in NEO4J_URLS:
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(query_body).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {NEO4J_AUTH}"
                }
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))

                if result.get("errors"):
                    return {"count": 0, "stations_json": "[]", "message": "查詢錯誤"}

                rainfall_stations = []
                waterlevel_stations = []

                if result.get("results") and result["results"][0].get("data"):
                    for row in result["results"][0]["data"]:
                        code, name, stype, river = row["row"]
                        station = {"name": name, "code": code, "river": river}
                        if stype == "雨量":
                            rainfall_stations.append(station)
                        else:
                            waterlevel_stations.append(station)

                total = len(rainfall_stations) + len(waterlevel_stations)
                if total == 0:
                    return {"count": 0, "stations_json": "[]", "message": f"「{waterSystemName}」水系沒有測站"}

                grouped = {"雨量站": rainfall_stations, "水位站": waterlevel_stations}
                return {
                    "count": total,
                    "stations_json": json.dumps(grouped, ensure_ascii=False),
                    "message": f"找到 {len(rainfall_stations)} 個雨量站、{len(waterlevel_stations)} 個水位站"
                }
        except:
            continue

    return {"count": 0, "stations_json": "[]", "message": "無法連接資料庫"}
```

---

## 🔧 工具 4：getStationsByCity（依縣市查詢測站）

### 輸出變數
- `count`: Number
- `rainfall_count`: Number
- `water_level_count`: Number
- `stations_json`: String (JSON)

### 完整代碼（直接複製）

```python
import json
import urllib.request
import urllib.error
import base64

def main(city: str, filterType: str = "全部") -> dict:
    """依縣市查詢測站

    DIFY 輸出變數：
    - count: Number
    - rainfall_count: Number
    - water_level_count: Number
    - stations_json: String (JSON格式，按類型分組)
    """
    NEO4J_URLS = [
        "http://localhost:7474/db/neo4j/tx/commit",
        "http://host.docker.internal:7474/db/neo4j/tx/commit",
        "http://127.0.0.1:7474/db/neo4j/tx/commit"
    ]
    NEO4J_AUTH = base64.b64encode(b"neo4j:geoinfor").decode()

    query_body = {
        "statements": [{
            "statement": """
                CALL custom.getStationsByCity($city)
                YIELD code, name, type, city, river, status
                RETURN code, name, type, city, river, status
            """,
            "parameters": {"city": city}
        }]
    }

    for url in NEO4J_URLS:
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(query_body).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {NEO4J_AUTH}"
                }
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))

                if result.get("errors"):
                    return {"count": 0, "rainfall_count": 0, "water_level_count": 0, "stations_json": "[]"}

                rainfall_stations = []
                waterlevel_stations = []

                if result.get("results") and result["results"][0].get("data"):
                    for row in result["results"][0]["data"]:
                        code, name, stype, city, river, status = row["row"]
                        station = {"code": code, "name": name, "city": city, "river": river}
                        if stype == "雨量":
                            rainfall_stations.append(station)
                        else:
                            waterlevel_stations.append(station)

                # 根據 filterType 過濾
                if filterType == "雨量站":
                    grouped = {"雨量站": rainfall_stations}
                    return {
                        "count": len(rainfall_stations),
                        "rainfall_count": len(rainfall_stations),
                        "water_level_count": 0,
                        "stations_json": json.dumps(grouped, ensure_ascii=False)
                    }
                elif filterType == "水位站":
                    grouped = {"水位站": waterlevel_stations}
                    return {
                        "count": len(waterlevel_stations),
                        "rainfall_count": 0,
                        "water_level_count": len(waterlevel_stations),
                        "stations_json": json.dumps(grouped, ensure_ascii=False)
                    }
                else:
                    grouped = {"雨量站": rainfall_stations, "水位站": waterlevel_stations}
                    total = len(rainfall_stations) + len(waterlevel_stations)
                    return {
                        "count": total,
                        "rainfall_count": len(rainfall_stations),
                        "water_level_count": len(waterlevel_stations),
                        "stations_json": json.dumps(grouped, ensure_ascii=False)
                    }
        except:
            continue

    return {"count": 0, "rainfall_count": 0, "water_level_count": 0, "stations_json": "[]"}
```

---

## 🔧 工具 5：getStationStats（測站統計）

### 輸出變數
- `success`: Boolean
- `rainfallTotal`: Number
- `waterLevelTotal`: Number
- `totalStations`: Number
- `details_json`: String (JSON)
- `top_cities_json`: String (JSON)
- `message`: String

### 完整代碼（直接複製）

```python
import json
import urllib.request
import urllib.error
import base64

def main() -> dict:
    """測站統計

    DIFY 輸出變數：
    - success: Boolean
    - rainfallTotal: Number
    - waterLevelTotal: Number
    - totalStations: Number
    - details_json: String (JSON)
    - top_cities_json: String (JSON)
    - message: String
    """
    NEO4J_URLS = [
        "http://localhost:7474/db/neo4j/tx/commit",
        "http://host.docker.internal:7474/db/neo4j/tx/commit",
        "http://127.0.0.1:7474/db/neo4j/tx/commit"
    ]
    NEO4J_AUTH = base64.b64encode(b"neo4j:geoinfor").decode()

    query_body = {
        "statements": [{
            "statement": """
                CALL custom.getStationStats()
                YIELD rainfallTotal, waterLevelTotal, totalStations, cityStats
                RETURN rainfallTotal, waterLevelTotal, totalStations, cityStats
            """
        }]
    }

    for url in NEO4J_URLS:
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(query_body).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {NEO4J_AUTH}"
                }
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))

                if result.get("errors"):
                    return {
                        "success": False,
                        "rainfallTotal": 0,
                        "waterLevelTotal": 0,
                        "totalStations": 0,
                        "details_json": "[]",
                        "top_cities_json": "[]",
                        "message": "查詢錯誤"
                    }

                if result.get("results") and result["results"][0].get("data"):
                    row = result["results"][0]["data"][0]["row"]
                    rainfall_total, water_level_total, total_stations, city_stats = row

                    # 排序城市統計（測站數最多的前5名）
                    sorted_cities = sorted(city_stats, key=lambda x: x.get("total", 0), reverse=True)
                    top_cities = sorted_cities[:5]

                    return {
                        "success": True,
                        "rainfallTotal": rainfall_total,
                        "waterLevelTotal": water_level_total,
                        "totalStations": total_stations,
                        "details_json": json.dumps(city_stats, ensure_ascii=False),
                        "top_cities_json": json.dumps(top_cities, ensure_ascii=False),
                        "message": f"總計 {total_stations} 個測站（雨量站 {rainfall_total}、水位站 {water_level_total}）"
                    }

                return {
                    "success": False,
                    "rainfallTotal": 0,
                    "waterLevelTotal": 0,
                    "totalStations": 0,
                    "details_json": "[]",
                    "top_cities_json": "[]",
                    "message": "沒有統計資料"
                }
        except:
            continue

    return {
        "success": False,
        "rainfallTotal": 0,
        "waterLevelTotal": 0,
        "totalStations": 0,
        "details_json": "[]",
        "top_cities_json": "[]",
        "message": "無法連接資料庫"
    }
```

---

## 🔧 工具 6：getRiverTributaries（河川支流查詢，樹狀排序）

### 輸出變數
- `count`: Number
- `rivers_json`: String (JSON)
- `message`: String（樹狀階層格式）

### 完整代碼（直接複製）

```python
import json
import urllib.request
import urllib.error
import base64

def main(riverName: str) -> dict:
    """查詢河川的所有支流（遞迴，樹狀排序）

    DIFY 輸出變數：
    - count: Number
    - rivers_json: String (JSON格式的支流列表)
    - message: String (樹狀階層格式化文字)
    """
    NEO4J_URLS = [
        "http://localhost:7474/db/neo4j/tx/commit",
        "http://host.docker.internal:7474/db/neo4j/tx/commit",
        "http://127.0.0.1:7474/db/neo4j/tx/commit"
    ]
    NEO4J_AUTH = base64.b64encode(b"neo4j:geoinfor").decode()

    query_body = {
        "statements": [{
            "statement": """
                CALL custom.getRiverTributaries($riverName)
                YIELD count, rivers_json, message
                RETURN count, rivers_json, message
            """,
            "parameters": {"riverName": riverName}
        }]
    }

    for url in NEO4J_URLS:
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(query_body).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {NEO4J_AUTH}"
                }
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))

                if result.get("errors"):
                    return {"count": 0, "rivers_json": "[]", "message": "查詢錯誤"}

                if result.get("results") and result["results"][0].get("data"):
                    row = result["results"][0]["data"][0]["row"]
                    count = row[0]
                    rivers_json = row[1]

                    if count == 0:
                        return {"count": 0, "rivers_json": "[]", "message": f"「{riverName}」沒有支流資料"}

                    # 格式化為樹狀結構
                    tree_text = format_tributaries_tree(rivers_json, riverName, count)
                    return {
                        "count": count,
                        "rivers_json": rivers_json,
                        "message": tree_text
                    }

                return {"count": 0, "rivers_json": "[]", "message": f"「{riverName}」沒有支流資料"}
        except:
            continue

    return {"count": 0, "rivers_json": "[]", "message": "無法連接資料庫"}


def format_tributaries_tree(rivers_json: str, main_river: str, count: int) -> str:
    """將支流資料格式化為樹狀結構"""
    rivers = json.loads(rivers_json)

    # 按 flowsInto 分組
    by_parent = {}
    for r in rivers:
        parent = r.get('flowsInto')
        if parent not in by_parent:
            by_parent[parent] = []
        by_parent[parent].append(r)

    def add_children(lines, parent, depth):
        children = by_parent.get(parent, [])
        indent = "    " * depth
        for child in sorted(children, key=lambda x: x['name']):
            lines.append(f"{indent}{child['name']}（{child['flowsInto']}）")
            add_children(lines, child['name'], depth + 1)

    lines = [f"{main_river}的所有支流如下，共有{count}條：", ""]

    # 直接支流（流入主河川的）
    direct = by_parent.get(main_river, [])
    if direct:
        lines.append("支流：")
        for i, trib in enumerate(sorted(direct, key=lambda x: x['name']), 1):
            lines.append(f"{i}. {trib['name']}")
            add_children(lines, trib['name'], 1)

    return "\n".join(lines)
```

---

## 🔧 工具 7：getRiversInWaterSystem（水系河川查詢，樹狀排序）

### 輸出變數
- `count`: Number
- `rivers_json`: String (JSON)
- `message`: String（樹狀階層格式）

### 完整代碼（直接複製）

```python
import json
import urllib.request
import urllib.error
import base64

def main(waterSystemName: str) -> dict:
    """查詢水系內所有河川（樹狀階層排序）

    DIFY 輸出變數：
    - count: Number
    - rivers_json: String (JSON格式的河川列表)
    - message: String (樹狀階層格式化文字)
    """
    NEO4J_URLS = [
        "http://localhost:7474/db/neo4j/tx/commit",
        "http://host.docker.internal:7474/db/neo4j/tx/commit",
        "http://127.0.0.1:7474/db/neo4j/tx/commit"
    ]
    NEO4J_AUTH = base64.b64encode(b"neo4j:geoinfor").decode()

    query_body = {
        "statements": [{
            "statement": """
                CALL custom.getRiversInWaterSystem($waterSystemName)
                YIELD count, rivers_json, message
                RETURN count, rivers_json, message
            """,
            "parameters": {"waterSystemName": waterSystemName}
        }]
    }

    for url in NEO4J_URLS:
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(query_body).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {NEO4J_AUTH}"
                }
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))

                if result.get("errors"):
                    return {"count": 0, "rivers_json": "[]", "message": "查詢錯誤"}

                if result.get("results") and result["results"][0].get("data"):
                    row = result["results"][0]["data"][0]["row"]
                    count = row[0]
                    rivers_json = row[1]

                    if count == 0:
                        return {"count": 0, "rivers_json": "[]", "message": f"「{waterSystemName}」水系沒有河川資料"}

                    # 格式化為樹狀結構
                    tree_text = format_tree(rivers_json, waterSystemName, count)
                    return {
                        "count": count,
                        "rivers_json": rivers_json,
                        "message": tree_text
                    }

                return {"count": 0, "rivers_json": "[]", "message": f"「{waterSystemName}」水系沒有河川資料"}
        except:
            continue

    return {"count": 0, "rivers_json": "[]", "message": "無法連接資料庫"}


def format_tree(rivers_json: str, water_system: str, count: int) -> str:
    """將河川資料格式化為樹狀結構"""
    rivers = json.loads(rivers_json)

    # 找主流
    main_river = None
    for r in rivers:
        if r.get('levelName') == '主流':
            main_river = r['name']
            break

    # 按 flowsInto 分組
    by_parent = {}
    for r in rivers:
        parent = r.get('flowsInto')
        if parent not in by_parent:
            by_parent[parent] = []
        by_parent[parent].append(r)

    def add_children(lines, parent, depth):
        children = by_parent.get(parent, [])
        indent = "    " * depth
        for child in sorted(children, key=lambda x: x['name']):
            lines.append(f"{indent}{child['name']}（{child['flowsInto']}）")
            add_children(lines, child['name'], depth + 1)

    lines = [f"屬於{water_system}範圍內的所有河川如下，共有{count}條：", ""]

    if main_river:
        lines.append(f"主流：{main_river}")
        lines.append("")

    direct = by_parent.get(main_river, [])
    if direct:
        lines.append("支流：")
        for i, trib in enumerate(sorted(direct, key=lambda x: x['name']), 1):
            lines.append(f"{i}. {trib['name']}")
            add_children(lines, trib['name'], 1)

    return "\n".join(lines)
```

---

## 🔧 工具 8：getRiverFlowPath（河川流向查詢）

### 輸出變數
- `found`: Boolean
- `path`: String
- `message`: String

### 完整代碼（直接複製）

```python
import json
import urllib.request
import urllib.error
import base64

def main(riverName: str) -> dict:
    """查詢河川流向路徑

    DIFY 輸出變數：
    - found: Boolean
    - path: String (流向路徑，如 "羅東溪 → 蘭陽溪")
    - message: String
    """
    NEO4J_URLS = [
        "http://localhost:7474/db/neo4j/tx/commit",
        "http://host.docker.internal:7474/db/neo4j/tx/commit",
        "http://127.0.0.1:7474/db/neo4j/tx/commit"
    ]
    NEO4J_AUTH = base64.b64encode(b"neo4j:geoinfor").decode()

    query_body = {
        "statements": [{
            "statement": """
                CALL custom.getRiverFlowPath($riverName)
                YIELD riverPath
                RETURN riverPath
            """,
            "parameters": {"riverName": riverName}
        }]
    }

    for url in NEO4J_URLS:
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(query_body).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {NEO4J_AUTH}"
                }
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))

                if result.get("errors"):
                    return {"found": False, "path": "", "message": "查詢錯誤"}

                if result.get("results") and result["results"][0].get("data"):
                    if result["results"][0]["data"]:
                        path_list = result["results"][0]["data"][0]["row"][0]

                        if path_list and len(path_list) > 0:
                            path_str = " → ".join(path_list)
                            return {
                                "found": True,
                                "path": path_str,
                                "message": f"流向：{path_str}"
                            }

                return {"found": False, "path": "", "message": f"「{riverName}」沒有流向資料"}
        except:
            continue

    return {"found": False, "path": "", "message": "無法連接資料庫"}
```

---

## 🔧 工具 9：searchStationObservation（測站觀測資料查詢）

### 輸出變數
- `count`: Number
- `stations`: String (JSON)

### 說明
此工具呼叫 DIFY 外部 API 查詢測站的即時觀測資料。

### 完整代碼（直接複製）

```python
import json
import urllib.request
import urllib.error

def main(station_codes: str) -> dict:
    """查詢測站觀測資料

    DIFY 輸出變數：
    - count: Number
    - stations: String (JSON格式的觀測資料)
    """
    DIFY_API_URL = "http://localhost/v1/workflows/run"
    DIFY_API_KEY = "app-your-api-key-here"  # 請替換為實際的 API Key

    # 解析測站代碼（支援逗號分隔）
    codes = [c.strip() for c in station_codes.split(",") if c.strip()]

    if not codes:
        return {"count": 0, "stations": "[]"}

    try:
        request_body = {
            "inputs": {"station_codes": ",".join(codes)},
            "response_mode": "blocking",
            "user": "dify-agent"
        }

        req = urllib.request.Request(
            DIFY_API_URL,
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DIFY_API_KEY}"
            }
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))

            if result.get("data") and result["data"].get("outputs"):
                outputs = result["data"]["outputs"]
                stations = outputs.get("stations", [])

                return {
                    "count": len(stations),
                    "stations": json.dumps(stations, ensure_ascii=False)
                }

        return {"count": 0, "stations": "[]"}
    except Exception as e:
        return {"count": 0, "stations": "[]"}
```

---

## ✅ 部署檢查清單

更新完成後，在 DIFY 中依序測試所有 9 個工具：

### 測站工具
- [ ] searchStation("蘭陽") → 應返回包含「蘭陽」的測站
- [ ] getStationsByRiver("蘭陽溪") → 應返回蘭陽溪的測站
- [ ] getStationsByWaterSystem("蘭陽溪") → 應返回蘭陽溪水系的測站
- [ ] getStationsByCity("宜蘭縣") → 應返回宜蘭縣的測站
- [ ] getStationStats() → 應返回測站統計

### 河川工具
- [ ] getRiverTributaries("蘭陽溪") → 應返回蘭陽溪的支流（樹狀排序）
- [ ] getRiversInWaterSystem("蘭陽溪") → 應返回蘭陽溪水系的河川
- [ ] getRiverFlowPath("羅東溪") → 應返回「羅東溪 → 蘭陽溪」

### 觀測資料工具
- [ ] searchStationObservation("H0A660") → 應返回測站觀測資料

---

## 📞 遇到問題？

### 常見問題

**Q1：貼上後顯示語法錯誤**
- 確認完整複製了整個 `main()` 函數
- 檢查縮排是否正確

**Q2：測試時返回 "連線失敗"**
- 確認 Neo4j 服務正在運行
- 檢查 DIFY 能否訪問 localhost:7474

**Q3：返回 "Neo4j 查詢錯誤"**
- 確認 Neo4j Procedures 已正確安裝
- 執行：`CALL apoc.custom.list()` 確認程序存在

**Q4：searchStationObservation 無法連接**
- 確認 DIFY API URL 和 API Key 正確
- 檢查網路連線

---

## 📚 相關文件

- [完整修復總結](DIFY_Tools_Fix_Summary.md)
- [問題分析報告](../tests/test_report_analysis.md)
- [測試結果](../tests/two_improved_tools_test_report.txt)
