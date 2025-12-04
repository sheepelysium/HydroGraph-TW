# Neo4j 台灣水文知識圖譜 - 關係類型與查詢範例

> 最後更新：2025-12-01
> 總關係數：24,250 個
> 關係類型：5 種

---

## 📊 關係統計總覽

| 關係類型 | 數量 | 佔比 | 說明 |
|---------|------|------|------|
| DRAINS_TO | 21,281 | 87.8% | 集水區 → 河川（排水到） |
| PART_OF | 839 | 3.5% | 集水區 → 流域（屬於） |
| BELONGS_TO | 831 | 3.4% | 河川 → 水系（隸屬於） |
| FLOWS_INTO | 654 | 2.7% | 河川 → 河川（流入） |
| LOCATED_ON | 645 | 2.7% | 測站 → 河川（位於） |

---

## 🔗 關係類型詳細說明與查詢範例

### 1. BELONGS_TO（河川隸屬於水系）

**關係模式**：`(River) -[BELONGS_TO]-> (WaterSystem)`

**說明**：表示河川隸屬於哪個水系

**常見查詢案例**：

#### 查詢某水系下的所有河川
```cypher
// 查詢淡水河水系的所有河川
MATCH (r:River)-[:BELONGS_TO]->(ws:WaterSystem {name: "淡水河"})
RETURN r.name as 河川名稱
ORDER BY r.name
```

#### 查詢某河川屬於哪個水系
```cypher
// 查詢新店溪屬於哪個水系
MATCH (r:River {name: "新店溪"})-[:BELONGS_TO]->(ws:WaterSystem)
RETURN ws.name as 水系名稱
```

#### 統計每個水系有多少河川
```cypher
MATCH (r:River)-[:BELONGS_TO]->(ws:WaterSystem)
RETURN ws.name as 水系名稱, count(r) as 河川數量
ORDER BY 河川數量 DESC
```

#### 查詢有最多河川的前 10 個水系
```cypher
MATCH (r:River)-[:BELONGS_TO]->(ws:WaterSystem)
RETURN ws.name as 水系名稱, count(r) as 河川數量
ORDER BY 河川數量 DESC
LIMIT 10
```

---

### 2. PART_OF（集水區屬於流域）

**關係模式**：`(Watershed) -[PART_OF]-> (Basin)`

**說明**：表示集水區屬於哪個流域

**常見查詢案例**：

#### 查詢某流域下的所有集水區
```cypher
// 查詢北部流域的所有集水區
MATCH (w:Watershed)-[:PART_OF]->(b:Basin {name: "北部"})
RETURN w.name as 集水區名稱
ORDER BY w.name
```

#### 查詢某集水區屬於哪個流域
```cypher
// 查詢淡水河集水區屬於哪個流域
MATCH (w:Watershed {name: "淡水河"})-[:PART_OF]->(b:Basin)
RETURN b.name as 流域名稱
```

#### 統計每個流域有多少集水區
```cypher
MATCH (w:Watershed)-[:PART_OF]->(b:Basin)
RETURN b.name as 流域名稱, count(w) as 集水區數量
ORDER BY 集水區數量 DESC
```

#### 查詢台灣所有流域及其集水區數量
```cypher
MATCH (w:Watershed)-[:PART_OF]->(b:Basin)
RETURN b.name as 流域, count(w) as 集水區數量, collect(w.name)[0..5] as 範例集水區
ORDER BY 集水區數量 DESC
```

---

### 3. FLOWS_INTO（河川流入河川）

**關係模式**：`(River) -[FLOWS_INTO]-> (River)`

**說明**：表示河川的流向關係（支流流入主流）

**常見查詢案例**：

#### 查詢某河川的所有支流
```cypher
// 查詢淡水河的所有直接支流
MATCH (tributary:River)-[:FLOWS_INTO]->(main:River {name: "淡水河"})
RETURN tributary.name as 支流名稱
ORDER BY tributary.name
```

#### 查詢某河川流入哪條河川
```cypher
// 查詢新店溪流入哪條河川
MATCH (r:River {name: "新店溪"})-[:FLOWS_INTO]->(main:River)
RETURN main.name as 流入河川
```

#### 查詢完整的河川流向路徑
```cypher
// 查詢從大北溪到海的完整流向路徑
MATCH path = (r:River {name: "大北溪"})-[:FLOWS_INTO*]->(end:River)
WHERE NOT (end)-[:FLOWS_INTO]->()
RETURN [node in nodes(path) | node.name] as 流向路徑
```

#### 找出所有最終流向（沒有再流入其他河川的河川）
```cypher
MATCH (r:River)
WHERE NOT (r)-[:FLOWS_INTO]->()
RETURN r.name as 最終河川
ORDER BY r.name
```

#### 查詢某河川的所有上游河川（遞迴查詢）
```cypher
// 查詢淡水河的所有上游河川
MATCH (upstream:River)-[:FLOWS_INTO*]->(main:River {name: "淡水河"})
RETURN DISTINCT upstream.name as 上游河川
ORDER BY upstream.name
```

#### 查詢河川流向的層級深度
```cypher
// 查詢每條河川到最終流向的深度
MATCH (r:River)
OPTIONAL MATCH path = (r)-[:FLOWS_INTO*]->(end:River)
WHERE NOT (end)-[:FLOWS_INTO]->()
RETURN r.name as 河川名稱,
       length(path) as 流向深度,
       end.name as 最終流向
ORDER BY 流向深度 DESC
```

---

### 4. LOCATED_ON（測站位於河川）

**關係模式**：`(Station) -[LOCATED_ON]-> (River)`

**說明**：表示水文測站位於哪條河川上

**常見查詢案例**：

#### 查詢某河川上的所有測站
```cypher
// 查詢淡水河上的所有測站
MATCH (s:Station)-[:LOCATED_ON]->(r:River {name: "淡水河"})
RETURN s.name as 測站名稱, s.station_no as 測站編號
ORDER BY s.name
```

#### 查詢某測站位於哪條河川
```cypher
// 查詢關渡測站位於哪條河川
MATCH (s:Station {name: "關渡"})-[:LOCATED_ON]->(r:River)
RETURN r.name as 河川名稱
```

#### 統計每條河川有多少測站
```cypher
MATCH (s:Station)-[:LOCATED_ON]->(r:River)
RETURN r.name as 河川名稱, count(s) as 測站數量
ORDER BY 測站數量 DESC
```

#### 找出沒有測站的河川
```cypher
MATCH (r:River)
WHERE NOT (r)<-[:LOCATED_ON]-(:Station)
RETURN r.name as 無測站河川
ORDER BY r.name
```

#### 查詢某水系下所有河川的測站
```cypher
// 查詢淡水河水系的所有測站
MATCH (s:Station)-[:LOCATED_ON]->(r:River)-[:BELONGS_TO]->(ws:WaterSystem {name: "淡水河"})
RETURN r.name as 河川名稱, collect(s.name) as 測站列表
ORDER BY r.name
```

#### 找出測站最多的前 10 條河川
```cypher
MATCH (s:Station)-[:LOCATED_ON]->(r:River)
RETURN r.name as 河川名稱, count(s) as 測站數量
ORDER BY 測站數量 DESC
LIMIT 10
```

---

### 5. DRAINS_TO（集水區排水到河川）⭐ 最多！

**關係模式**：`(Watershed) -[DRAINS_TO]-> (River)`

**說明**：表示集水區的排水流向哪條河川

**常見查詢案例**：

#### 查詢某河川的所有集水區
```cypher
// 查詢淡水河的所有集水區
MATCH (w:Watershed)-[:DRAINS_TO]->(r:River {name: "淡水河"})
RETURN w.name as 集水區名稱
ORDER BY w.name
```

#### 查詢某集水區排水到哪條河川
```cypher
// 查詢翡翠集水區排水到哪條河川
MATCH (w:Watershed {name: "翡翠"})-[:DRAINS_TO]->(r:River)
RETURN r.name as 河川名稱
```

#### 統計每條河川有多少集水區
```cypher
MATCH (w:Watershed)-[:DRAINS_TO]->(r:River)
RETURN r.name as 河川名稱, count(w) as 集水區數量
ORDER BY 集水區數量 DESC
```

#### 查詢某流域的集水區及其排水河川
```cypher
// 查詢北部流域的集水區及其排水河川
MATCH (w:Watershed)-[:PART_OF]->(b:Basin {name: "北部"}),
      (w)-[:DRAINS_TO]->(r:River)
RETURN w.name as 集水區, r.name as 排水河川
ORDER BY w.name
```

#### 找出集水區最多的前 10 條河川
```cypher
MATCH (w:Watershed)-[:DRAINS_TO]->(r:River)
RETURN r.name as 河川名稱, count(w) as 集水區數量
ORDER BY 集水區數量 DESC
LIMIT 10
```

---

## 🔍 綜合查詢範例

### 查詢某水系的完整資訊
```cypher
// 查詢淡水河水系的完整資訊
MATCH (ws:WaterSystem {name: "淡水河"})
OPTIONAL MATCH (r:River)-[:BELONGS_TO]->(ws)
OPTIONAL MATCH (s:Station)-[:LOCATED_ON]->(r)
OPTIONAL MATCH (w:Watershed)-[:DRAINS_TO]->(r)
RETURN ws.name as 水系名稱,
       count(DISTINCT r) as 河川數量,
       count(DISTINCT s) as 測站數量,
       count(DISTINCT w) as 集水區數量
```

### 查詢某河川的完整資訊鏈
```cypher
// 查詢新店溪的完整資訊
MATCH (r:River {name: "新店溪"})
OPTIONAL MATCH (r)-[:BELONGS_TO]->(ws:WaterSystem)
OPTIONAL MATCH (tributary:River)-[:FLOWS_INTO]->(r)
OPTIONAL MATCH (r)-[:FLOWS_INTO]->(main:River)
OPTIONAL MATCH (s:Station)-[:LOCATED_ON]->(r)
OPTIONAL MATCH (w:Watershed)-[:DRAINS_TO]->(r)
RETURN r.name as 河川名稱,
       ws.name as 所屬水系,
       collect(DISTINCT tributary.name) as 支流,
       main.name as 流入河川,
       collect(DISTINCT s.name) as 測站列表,
       count(DISTINCT w) as 集水區數量
```

### 查詢跨越多個關係的複雜路徑
```cypher
// 從集水區到水系的完整路徑
MATCH path = (w:Watershed)-[:DRAINS_TO]->(r:River)-[:BELONGS_TO]->(ws:WaterSystem)
WHERE w.name = "翡翠"
RETURN [node in nodes(path) | node.name] as 完整路徑
```

### 統計整個知識圖譜
```cypher
// 統計所有節點和關係
MATCH (n)
OPTIONAL MATCH (n)-[r]->()
RETURN labels(n)[0] as 節點類型,
       count(DISTINCT n) as 節點數量,
       count(r) as 關係數量
```

### 找出某流域的水系網絡
```cypher
// 查詢北部流域的完整水系網絡
MATCH (b:Basin {name: "北部"})<-[:PART_OF]-(w:Watershed),
      (w)-[:DRAINS_TO]->(r:River),
      (r)-[:BELONGS_TO]->(ws:WaterSystem)
RETURN ws.name as 水系,
       count(DISTINCT r) as 河川數,
       count(DISTINCT w) as 集水區數
ORDER BY 河川數 DESC
```

---

## 💡 實用查詢技巧

### 1. 使用 LIMIT 限制結果數量
```cypher
// 只查詢前 10 筆結果
MATCH (r:River)
RETURN r.name
LIMIT 10
```

### 2. 使用 WHERE 過濾條件
```cypher
// 查詢名稱包含「溪」的河川
MATCH (r:River)
WHERE r.name CONTAINS "溪"
RETURN r.name
```

### 3. 使用聚合函數
```cypher
// count(), collect(), sum(), avg(), max(), min()
MATCH (r:River)-[:BELONGS_TO]->(ws:WaterSystem)
RETURN ws.name,
       count(r) as 數量,
       collect(r.name) as 清單
```

### 4. 使用路徑變數
```cypher
// 儲存路徑並分析
MATCH path = (r:River)-[:FLOWS_INTO*]->(end:River)
RETURN length(path) as 深度,
       [node in nodes(path) | node.name] as 路徑
```

### 5. 使用 OPTIONAL MATCH（左外連接）
```cypher
// 即使沒有關係也會返回節點
MATCH (r:River)
OPTIONAL MATCH (s:Station)-[:LOCATED_ON]->(r)
RETURN r.name, collect(s.name) as 測站
```

---

## 📚 常用參考資料

### 節點類型
- `WaterSystem`：水系
- `Basin`：流域
- `River`：河川
- `Station`：測站
- `Watershed`：集水區

### 關係類型
- `BELONGS_TO`：隸屬於
- `PART_OF`：屬於
- `FLOWS_INTO`：流入
- `LOCATED_ON`：位於
- `DRAINS_TO`：排水到

### Neo4j 常用函數
- `count()`：計數
- `collect()`：收集成列表
- `length()`：路徑長度
- `nodes()`：路徑中的節點
- `relationships()`：路徑中的關係
- `DISTINCT`：去重
- `ORDER BY`：排序
- `LIMIT`：限制數量

---

## 🔧 在 Python 中執行查詢

```python
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
)

with driver.session() as session:
    result = session.run("""
        MATCH (r:River)-[:BELONGS_TO]->(ws:WaterSystem {name: "淡水河"})
        RETURN r.name as river
    """)

    for record in result:
        print(record['river'])

driver.close()
```

---

*此文檔會隨著資料庫更新而更新*
