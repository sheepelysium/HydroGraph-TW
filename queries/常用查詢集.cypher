// ============================================
// 台灣水文知識圖譜 - 常用查詢集
// 使用方式: 複製單個查詢到 Neo4j Browser 執行
// ============================================

// ----------------------------------------
// 1. 整體統計概覽
// ----------------------------------------
CALL {
    MATCH (r:River)
    RETURN '河川總數' AS 項目, count(r) AS 數量

    UNION

    MATCH (s:Station)
    RETURN '測站總數' AS 項目, count(s) AS 數量

    UNION

    MATCH (ws:WaterSystem)
    RETURN '水系數量' AS 項目, count(ws) AS 數量

    UNION

    MATCH (w:Watershed)
    RETURN '集水區數量' AS 項目, count(w) AS 數量

    UNION

    MATCH ()-[r:MONITORS]->()
    RETURN 'MONITORS關係' AS 項目, count(r) AS 數量
}
RETURN 項目, 數量
ORDER BY 數量 DESC


// ----------------------------------------
// 2. 所有水系的河川和測站統計
// ----------------------------------------
MATCH (ws:WaterSystem)
OPTIONAL MATCH (r:River)-[:BELONGS_TO]->(ws)
OPTIONAL MATCH (s:Station)-[:MONITORS]->(r)
WITH ws, count(DISTINCT r) AS 河川數, count(DISTINCT s) AS 測站數
ORDER BY 測站數 DESC
RETURN ws.name AS 水系名稱, 河川數, 測站數


// ----------------------------------------
// 3. 測站數量最多的前10條河川
// ----------------------------------------
MATCH (r:River)
MATCH (s:Station)-[:MONITORS]->(r)
WITH r, count(s) AS 測站數
ORDER BY 測站數 DESC
LIMIT 10
RETURN r.name AS 河川名稱,
       r.code AS 河川代碼,
       測站數


// ----------------------------------------
// 4. 各縣市的測站分布統計
// ----------------------------------------
MATCH (s:Station)
WHERE s.city IS NOT NULL
WITH s.city AS 縣市,
     count(s) AS 總測站數,
     count(CASE WHEN s:Rainfall THEN 1 END) AS 雨量測站,
     count(CASE WHEN s:WaterLevel THEN 1 END) AS 水位測站
ORDER BY 總測站數 DESC
RETURN 縣市, 總測站數, 雨量測站, 水位測站


// ----------------------------------------
// 5. 高程最高的20個測站
// ----------------------------------------
MATCH (s:Station)
WHERE s.elevation IS NOT NULL
OPTIONAL MATCH (s)-[:MONITORS]->(r:River)
RETURN s.name AS 測站名稱,
       s.elevation AS 高程,
       s.type AS 類型,
       s.city AS 縣市,
       r.name AS 監測河川
ORDER BY s.elevation DESC
LIMIT 20


// ----------------------------------------
// 6. 查詢特定河川的完整資訊
// ----------------------------------------
// 使用時請將 '濁水溪' 改為您要查詢的河川名稱
MATCH (r:River {name: '濁水溪'})
OPTIONAL MATCH (r)-[:BELONGS_TO]->(ws:WaterSystem)
OPTIONAL MATCH (tributary:River)-[:IS_TRIBUTARY_OF]->(r)
OPTIONAL MATCH (s:Station)-[:MONITORS]->(r)
RETURN r.name AS 河川名稱,
       r.code AS 河川代碼,
       r.level AS 階層,
       ws.name AS 所屬水系,
       count(DISTINCT tributary) AS 支流數,
       count(DISTINCT s) AS 測站數


// ----------------------------------------
// 7. 查詢特定測站的詳細資訊
// ----------------------------------------
// 使用時請將 '清泉' 改為您要查詢的測站名稱
MATCH (s:Station)
WHERE s.name CONTAINS '清泉'
OPTIONAL MATCH (s)-[:MONITORS]->(r:River)
OPTIONAL MATCH (r)-[:BELONGS_TO]->(ws:WaterSystem)
RETURN s.name AS 測站名稱,
       s.code AS 測站代號,
       s.type AS 測站類型,
       s.elevation AS 高程,
       s.city AS 縣市,
       s.management_unit AS 管理單位,
       r.name AS 監測河川,
       ws.name AS 所屬水系


// ----------------------------------------
// 8. 河川階層分布統計
// ----------------------------------------
MATCH (r:River)
WITH r.level AS 階層, count(r) AS 河川數
ORDER BY 階層
RETURN 階層, 河川數


// ----------------------------------------
// 9. 各管理單位管理的測站統計
// ----------------------------------------
MATCH (s:Station)
WHERE s.management_unit IS NOT NULL
WITH s.management_unit AS 管理單位,
     count(s) AS 測站數,
     count(CASE WHEN s:Rainfall THEN 1 END) AS 雨量測站,
     count(CASE WHEN s:WaterLevel THEN 1 END) AS 水位測站
ORDER BY 測站數 DESC
RETURN 管理單位, 測站數, 雨量測站, 水位測站


// ----------------------------------------
// 10. 沒有測站監測的河川
// ----------------------------------------
MATCH (r:River)
WHERE NOT EXISTS { MATCH (r)<-[:MONITORS]-() }
OPTIONAL MATCH (r)-[:BELONGS_TO]->(ws:WaterSystem)
RETURN r.name AS 河川名稱,
       r.code AS 河川代碼,
       r.level AS 階層,
       ws.name AS 所屬水系
ORDER BY r.level
LIMIT 50


// ----------------------------------------
// 11. 同時監測多條河川的測站 (如果存在)
// ----------------------------------------
MATCH (s:Station)-[:MONITORS]->(r:River)
WITH s, collect(r.name) AS 監測河川, count(r) AS 河川數
WHERE 河川數 > 1
RETURN s.name AS 測站名稱,
       s.type AS 測站類型,
       河川數,
       監測河川
ORDER BY 河川數 DESC


// ----------------------------------------
// 12. 特定水系的河川階層樹狀結構
// ----------------------------------------
// 使用時請將 '淡水河' 改為您要查詢的水系
MATCH (ws:WaterSystem {name: '淡水河'})
MATCH (r:River)-[:BELONGS_TO]->(ws)
WHERE r.level = 1
OPTIONAL MATCH path = (r)<-[:IS_TRIBUTARY_OF*1..3]-(tributary:River)
RETURN r.name AS 主流,
       [node in nodes(path) | node.name] AS 支流路徑
LIMIT 20


// ----------------------------------------
// 13. 雨量測站和水位測站的分布比較
// ----------------------------------------
MATCH (s:Station)
WITH labels(s) AS 標籤類型,
     count(s) AS 數量,
     avg(s.elevation) AS 平均高程
RETURN 標籤類型, 數量, round(平均高程, 2) AS 平均高程
ORDER BY 數量 DESC


// ----------------------------------------
// 14. 查詢特定集水區的資訊
// ----------------------------------------
MATCH (w:Watershed)
OPTIONAL MATCH (w)-[:PART_OF]->(b:Basin)
OPTIONAL MATCH (s:Station)-[:LOCATED_IN]->(w)
WITH w, b, count(DISTINCT s) AS 測站數
WHERE w.name IS NOT NULL
RETURN w.name AS 集水區名稱,
       b.name AS 所屬流域,
       w.area_km2 AS 面積,
       測站數
ORDER BY w.area_km2 DESC
LIMIT 20


// ----------------------------------------
// 15. 視覺化查詢 - 淡水河水系網路圖
// ----------------------------------------
// 在 Neo4j Browser 中會顯示圖形
MATCH path = (ws:WaterSystem {name: '淡水河'})<-[:BELONGS_TO]-(r:River)
WHERE r.level <= 2
OPTIONAL MATCH (s:Station)-[:MONITORS]->(r)
RETURN path, s
LIMIT 100
