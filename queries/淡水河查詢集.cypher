// ============================================
// 淡水河水系查詢集
// 使用方式: 複製單個查詢到 Neo4j Browser 執行
// ============================================

// ----------------------------------------
// 1. 淡水河水系基本統計
// ----------------------------------------
MATCH (ws:WaterSystem {name: '淡水河'})
MATCH (r:River)-[:BELONGS_TO]->(ws)
RETURN ws.name AS 水系名稱,
       count(r) AS 河川總數


// ----------------------------------------
// 2. 淡水河的直接支流 (按階層排序)
// ----------------------------------------
MATCH (t:River)-[:IS_TRIBUTARY_OF]->(m:River {name: '淡水河'})
RETURN t.name AS 支流名稱,
       t.code AS 河川代碼,
       t.level AS 階層
ORDER BY t.level, t.name


// ----------------------------------------
// 3. 淡水河水系所有測站統計
// ----------------------------------------
MATCH (ws:WaterSystem {name: '淡水河'})
MATCH (r:River)-[:BELONGS_TO]->(ws)
MATCH (s:Station)-[:MONITORS]->(r)
RETURN count(DISTINCT s) AS 測站總數,
       count(DISTINCT CASE WHEN s:Rainfall THEN s END) AS 雨量測站,
       count(DISTINCT CASE WHEN s:WaterLevel THEN s END) AS 水位測站


// ----------------------------------------
// 4. 淡水河水系各河川的測站數量 (前10名)
// ----------------------------------------
MATCH (ws:WaterSystem {name: '淡水河'})
MATCH (r:River)-[:BELONGS_TO]->(ws)
MATCH (s:Station)-[:MONITORS]->(r)
WITH r, count(s) AS 測站數
ORDER BY 測站數 DESC
LIMIT 10
RETURN r.name AS 河川名稱, 測站數


// ----------------------------------------
// 5. 淡水河本流的測站列表
// ----------------------------------------
MATCH (r:River {name: '淡水河'})
MATCH (s:Station)-[:MONITORS]->(r)
RETURN s.name AS 測站名稱,
       s.type AS 測站類型,
       s.elevation AS 高程,
       s.city AS 縣市
ORDER BY s.elevation DESC


// ----------------------------------------
// 6. 淡水河水系的河川階層分布
// ----------------------------------------
MATCH (ws:WaterSystem {name: '淡水河'})
MATCH (r:River)-[:BELONGS_TO]->(ws)
WITH r.level AS 階層, count(r) AS 河川數
ORDER BY 階層
RETURN 階層, 河川數


// ----------------------------------------
// 7. 淡水河水系各縣市的測站分布
// ----------------------------------------
MATCH (ws:WaterSystem {name: '淡水河'})
MATCH (r:River)-[:BELONGS_TO]->(ws)
MATCH (s:Station)-[:MONITORS]->(r)
WHERE s.city IS NOT NULL
WITH s.city AS 縣市, count(s) AS 測站數
ORDER BY 測站數 DESC
RETURN 縣市, 測站數


// ----------------------------------------
// 8. 淡水河水系完整階層結構 (樹狀展示)
// ----------------------------------------
MATCH path = (main:River {name: '淡水河'})<-[:IS_TRIBUTARY_OF*0..4]-(r:River)
RETURN r.name AS 河川名稱,
       r.level AS 階層,
       length(path) AS 深度,
       [rel in relationships(path) | startNode(rel).name] AS 路徑
ORDER BY 深度, r.name


// ----------------------------------------
// 9. 淡水河水系綜合統計 (一次查詢)
// ----------------------------------------
CALL {
    MATCH (ws:WaterSystem {name: '淡水河'})
    MATCH (r:River)-[:BELONGS_TO]->(ws)
    RETURN '河川總數' AS 項目, count(r) AS 數量

    UNION

    MATCH (ws:WaterSystem {name: '淡水河'})
    MATCH (r:River)-[:BELONGS_TO]->(ws)
    MATCH (s:Station)-[:MONITORS]->(r)
    RETURN '測站總數' AS 項目, count(DISTINCT s) AS 數量

    UNION

    MATCH (ws:WaterSystem {name: '淡水河'})
    MATCH (r:River)-[:BELONGS_TO]->(ws)
    WHERE r.level = 1
    RETURN '主流數量' AS 項目, count(r) AS 數量

    UNION

    MATCH (ws:WaterSystem {name: '淡水河'})
    MATCH (r:River)-[:BELONGS_TO]->(ws)
    WHERE r.level = 2
    RETURN '支流數量' AS 項目, count(r) AS 數量
}
RETURN 項目, 數量
ORDER BY 數量 DESC


// ----------------------------------------
// 10. 找出淡水河水系中高程最高的10個測站
// ----------------------------------------
MATCH (ws:WaterSystem {name: '淡水河'})
MATCH (r:River)-[:BELONGS_TO]->(ws)
MATCH (s:Station)-[:MONITORS]->(r)
WHERE s.elevation IS NOT NULL
RETURN s.name AS 測站名稱,
       r.name AS 所在河川,
       s.elevation AS 高程,
       s.type AS 測站類型,
       s.city AS 縣市
ORDER BY s.elevation DESC
LIMIT 10
