# -*- coding: utf-8 -*-
"""
Neo4j 自定義程序初始化腳本
使用 APOC installProcedure API（持久化版本，重啟後自動保留）
"""
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# 載入環境變數
load_dotenv()

# 連接設定
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

print("=" * 80)
print("初始化 Neo4j 自定義程序與全文索引")
print("=" * 80)
print(f"連接到：{NEO4J_URI}\n")

# 建立連接
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Fulltext 索引定義
FULLTEXT_INDEXES = [
    {
        'name': 'stationSearch',
        'labels': ['Station'],
        'properties': ['name', 'code', 'cwa_code'],
        'description': '測站全文搜尋索引（名稱、代碼、氣象局代碼）'
    },
    {
        'name': 'riverSearch',
        'labels': ['River'],
        'properties': ['name', 'code'],
        'description': '河川全文搜尋索引（名稱、代碼）'
    }
]

# 定義所有自定義程序（明確命名版：6 個程序）
# 設計原則：工具名稱自解釋，減少 LLM 參數判斷錯誤
CUSTOM_PROCEDURES = [
    # ========== 測站類（3 個）==========

    # 1. searchStation - 搜尋測站
    {
        'name': 'searchStation',
        'description': '搜尋測站（用關鍵字搜尋站名、站號、地名）',
        'query': '''
            CALL db.index.fulltext.queryNodes("stationSearch", $keyword)
            YIELD node AS s, score
            WITH s, score, CASE WHEN s:Rainfall THEN "雨量" ELSE "水位" END AS stationType
            WHERE ($filterType = "全部" OR stationType = $filterType)
              AND (s.name CONTAINS $keyword OR $keyword CONTAINS s.name
                   OR s.code CONTAINS $keyword OR $keyword CONTAINS s.code
                   OR COALESCE(s.cwa_code, "") CONTAINS $keyword OR $keyword CONTAINS COALESCE(s.cwa_code, "")
                   OR COALESCE(s.address, "") CONTAINS $keyword OR $keyword CONTAINS COALESCE(s.address, "")
                   OR COALESCE(s.city, "") CONTAINS $keyword OR $keyword CONTAINS COALESCE(s.city, ""))
            OPTIONAL MATCH (s)-[:LOCATED_ON]->(r:River)
            OPTIONAL MATCH (s)-[:LOCATED_IN]->(w:Watershed)
            RETURN s.code AS code,
                   s.name AS name,
                   stationType AS type,
                   s.cwa_code AS cwaCode,
                   s.status AS status,
                   s.category AS category,
                   s.management_unit AS managementUnit,
                   s.water_system AS waterSystem,
                   s.river AS riverName,
                   r.name AS matchedRiver,
                   r.code AS riverCode,
                   w.name AS watershed,
                   s.elevation AS elevation,
                   s.city AS city,
                   s.address AS address,
                   s.x_twd97 AS xTwd97,
                   s.y_twd97 AS yTwd97,
                   s.backup_station_code AS backupStationCode,
                   s.rainfall_minute_years AS rainfallMinuteYears,
                   s.rainfall_hour_years AS rainfallHourYears,
                   s.rainfall_daily_years AS rainfallDailyYears,
                   s.rainfall_monthly_years AS rainfallMonthlyYears,
                   s.water_level_hour_years AS waterLevelHourYears,
                   s.water_level_daily_years AS waterLevelDailyYears,
                   s.water_level_monthly_years AS waterLevelMonthlyYears,
                   s.flow_hour_years AS flowHourYears,
                   s.flow_daily_years AS flowDailyYears,
                   s.flow_monthly_years AS flowMonthlyYears,
                   s.sediment_years AS sedimentYears,
                   CASE
                     WHEN s:Rainfall THEN "https://gweb.wra.gov.tw/HydroInfo/StDataInfo/StDataInfo?RA&" + COALESCE(s.cwa_code, s.code)
                     ELSE "https://gweb.wra.gov.tw/HydroInfo/StDataInfo/StDataInfo?LE&" + s.code
                   END AS apiUrl,
                   score,
                   CASE
                     WHEN $keyword CONTAINS replace(replace(s.city, '臺', '台'), '市', '')
                          OR $keyword CONTAINS replace(replace(s.city, '臺', '台'), '縣', '')
                          OR replace(replace(s.city, '臺', '台'), '市', '') CONTAINS $keyword
                          OR replace(replace(s.city, '臺', '台'), '縣', '') CONTAINS $keyword
                     THEN 0
                     ELSE 1
                   END AS cityPriority
            ORDER BY cityPriority ASC, score DESC
            LIMIT 5
        ''',
        'mode': 'read',
        'outputs': [
            ['code', 'STRING'],
            ['name', 'STRING'],
            ['type', 'STRING'],
            ['cwaCode', 'STRING'],
            ['status', 'STRING'],
            ['category', 'STRING'],
            ['managementUnit', 'STRING'],
            ['waterSystem', 'STRING'],
            ['riverName', 'STRING'],
            ['matchedRiver', 'STRING'],
            ['riverCode', 'STRING'],
            ['watershed', 'STRING'],
            ['elevation', 'FLOAT'],
            ['city', 'STRING'],
            ['address', 'STRING'],
            ['xTwd97', 'FLOAT'],
            ['yTwd97', 'FLOAT'],
            ['backupStationCode', 'STRING'],
            ['rainfallMinuteYears', 'STRING'],
            ['rainfallHourYears', 'STRING'],
            ['rainfallDailyYears', 'STRING'],
            ['rainfallMonthlyYears', 'STRING'],
            ['waterLevelHourYears', 'STRING'],
            ['waterLevelDailyYears', 'STRING'],
            ['waterLevelMonthlyYears', 'STRING'],
            ['flowHourYears', 'STRING'],
            ['flowDailyYears', 'STRING'],
            ['flowMonthlyYears', 'STRING'],
            ['sedimentYears', 'STRING'],
            ['apiUrl', 'STRING'],
            ['score', 'FLOAT'],
            ['cityPriority', 'INT']
        ],
        'inputs': [
            ['keyword', 'STRING'],
            ['filterType', 'STRING']
        ]
    },

    # 2. getStationsByRiver - 河川上的測站
    {
        'name': 'getStationsByRiver',
        'description': '查詢河川上的所有測站',
        'query': '''
            MATCH (s:Station)-[:LOCATED_ON]->(r:River {name: $riverName})
            RETURN s.code AS code,
                   s.name AS name,
                   CASE WHEN s:Rainfall THEN "雨量" ELSE "水位" END AS type,
                   s.city AS city,
                   r.name AS river,
                   s.status AS status
            ORDER BY s.name
        ''',
        'mode': 'read',
        'outputs': [
            ['code', 'STRING'],
            ['name', 'STRING'],
            ['type', 'STRING'],
            ['city', 'STRING'],
            ['river', 'STRING'],
            ['status', 'STRING']
        ],
        'inputs': [
            ['riverName', 'STRING']
        ]
    },

    # 3. getStationsByWaterSystem - 水系內的測站
    {
        'name': 'getStationsByWaterSystem',
        'description': '查詢水系內所有河川的測站',
        'query': '''
            MATCH (s:Station)-[:LOCATED_ON]->(r:River)-[:BELONGS_TO]->(ws:WaterSystem {name: $waterSystemName})
            RETURN s.code AS code,
                   s.name AS name,
                   CASE WHEN s:Rainfall THEN "雨量" ELSE "水位" END AS type,
                   s.city AS city,
                   r.name AS river,
                   s.status AS status
            ORDER BY r.name, s.name
        ''',
        'mode': 'read',
        'outputs': [
            ['code', 'STRING'],
            ['name', 'STRING'],
            ['type', 'STRING'],
            ['city', 'STRING'],
            ['river', 'STRING'],
            ['status', 'STRING']
        ],
        'inputs': [
            ['waterSystemName', 'STRING']
        ]
    },

    # ========== 河川類（3 個）==========

    # 4. getRiverTributaries - 河川的所有支流（遞迴）
    {
        'name': 'getRiverTributaries',
        'description': '查詢河川的所有支流（遞迴查詢所有層級）',
        'query': '''
            MATCH (tributary:River)-[:FLOWS_INTO*]->(main:River {name: $riverName})
            RETURN DISTINCT tributary.name AS name,
                   tributary.level AS level,
                   tributary.code AS code
            ORDER BY tributary.level, tributary.name
        ''',
        'mode': 'read',
        'outputs': [
            ['name', 'STRING'],
            ['level', 'INT'],
            ['code', 'STRING']
        ],
        'inputs': [
            ['riverName', 'STRING']
        ]
    },

    # 5. getRiversInWaterSystem - 水系內的所有河川
    {
        'name': 'getRiversInWaterSystem',
        'description': '查詢水系內的所有河川',
        'query': '''
            MATCH (r:River)-[:BELONGS_TO]->(ws:WaterSystem {name: $waterSystemName})
            RETURN r.name AS name,
                   r.level AS level,
                   r.code AS code
            ORDER BY r.level, r.name
        ''',
        'mode': 'read',
        'outputs': [
            ['name', 'STRING'],
            ['level', 'INT'],
            ['code', 'STRING']
        ],
        'inputs': [
            ['waterSystemName', 'STRING']
        ]
    },

    # 6. getRiverFlowPath - 河川流向路徑
    {
        'name': 'getRiverFlowPath',
        'description': '查詢河川從支流到主流的完整流向路徑',
        'query': '''
            MATCH path = (start:River {name: $riverName})-[:FLOWS_INTO*0..]->(end:River)
            WHERE NOT (end)-[:FLOWS_INTO]->()
            WITH [node IN nodes(path) | node.name] AS riverPath
            RETURN riverPath
            LIMIT 1
        ''',
        'mode': 'read',
        'outputs': [
            ['riverPath', 'LIST OF STRING']
        ],
        'inputs': [
            ['riverName', 'STRING']
        ]
    }
]

try:
    with driver.session() as session:
        # 檢查 APOC 是否可用
        print("[檢查] 驗證 APOC 是否已安裝...")
        try:
            result = session.run("RETURN apoc.version() AS version")
            version = result.single()['version']
            print(f"    [OK] APOC 版本: {version}\n")
        except Exception as e:
            print(f"    [ERROR] APOC 未安裝或不可用")
            print(f"    錯誤訊息: {e}")
            print("\n請先安裝 APOC 插件！")
            exit(1)

        # 建立 Fulltext 索引
        print("[索引] 建立 Fulltext 全文索引...\n")
        for idx in FULLTEXT_INDEXES:
            try:
                # 檢查索引是否存在
                check_result = session.run(
                    "SHOW INDEXES WHERE name = $name",
                    name=idx['name']
                )
                existing = check_result.single()

                if existing:
                    print(f"  {idx['name']}: 索引已存在，跳過")
                else:
                    # 建立新索引
                    labels = ':'.join(idx['labels'])
                    properties = ', '.join([f"n.{p}" for p in idx['properties']])
                    create_query = f"""
                        CREATE FULLTEXT INDEX {idx['name']} IF NOT EXISTS
                        FOR (n:{labels})
                        ON EACH [{properties}]
                    """
                    session.run(create_query)
                    print(f"  {idx['name']}: [OK] 已建立")
                    print(f"    說明: {idx['description']}")
                    print(f"    標籤: {idx['labels']}")
                    print(f"    欄位: {idx['properties']}")

            except Exception as e:
                print(f"  {idx['name']}: [ERROR] {e}")

        print()

    # 移除舊的自定義程序
    # 步驟 1: 在 neo4j database 列出現有程序
    # 步驟 2: 在 system database 執行 dropProcedure
    print("[清理] 移除舊的自定義程序...")

    # 先在 neo4j 列出程序
    with driver.session(database="neo4j") as neo4j_session:
        try:
            result = neo4j_session.run("CALL apoc.custom.list() YIELD name RETURN name")
            procedures = [r['name'] for r in result]
        except Exception as e:
            print(f"    [INFO] 列出程序時發生問題: {e}")
            procedures = []

    # 再在 system 執行刪除
    if procedures:
        with driver.session(database="system") as system_session:
            for proc_name in procedures:
                try:
                    # dropProcedure(name, databaseName) - 必須指定目標資料庫
                    system_session.run(
                        "CALL apoc.custom.dropProcedure($name, $databaseName)",
                        parameters={'name': proc_name, 'databaseName': 'neo4j'}
                    )
                    print(f"    [OK] 已移除 {proc_name}")
                except Exception as e:
                    print(f"    [WARN] 移除 {proc_name} 失敗: {e}")
            print(f"    [OK] 已清理 {len(procedures)} 個舊程序\n")
    else:
        print("    [INFO] 沒有舊程序需要清理\n")

    # 使用 system database 來安裝程序（installProcedure 必須在 system db 執行）
    with driver.session(database="system") as system_session:
        # 建立所有自定義程序
        print("[建立] 開始建立自定義程序（使用 system database）...\n")
        created_count = 0

        for proc in CUSTOM_PROCEDURES:
            try:
                print(f"  建立程序: custom.{proc['name']}")
                print(f"    說明: {proc['description']}")

                # 使用 installProcedure (APOC 5.x 新版持久化 API)
                # 格式: CALL apoc.custom.installProcedure(signature, statement, mode, description)
                # signature 格式: "name(param1::TYPE, param2::TYPE) :: (out1::TYPE, out2::TYPE)"
                # 注意：必須在 system database 執行，程序會持久化到磁碟，重啟後自動保留

                # 建立 signature
                input_parts = []
                for inp in proc['inputs']:
                    if len(inp) >= 2:
                        input_parts.append(f"{inp[0]} :: {inp[1]}")

                output_parts = []
                for out in proc['outputs']:
                    if len(out) >= 2:
                        output_parts.append(f"{out[0]} :: {out[1]}")

                signature = f"{proc['name']}({', '.join(input_parts)}) :: ({', '.join(output_parts)})"

                # 參數順序: signature, statement, databaseName, mode, description
                system_session.run(
                    "CALL apoc.custom.installProcedure($signature, $statement, $databaseName, $mode, $description)",
                    parameters={
                        'signature': signature,
                        'statement': proc['query'].strip(),
                        'databaseName': 'neo4j',  # 程序要安裝到的目標資料庫
                        'mode': proc['mode'],
                        'description': proc['description']
                    }
                )

                print(f"    [OK] 建立成功\n")
                created_count += 1

            except Exception as e:
                print(f"    [ERROR] 建立失敗: {e}\n")

    print("=" * 80)
    print(f"完成！成功建立 {created_count}/{len(CUSTOM_PROCEDURES)} 個自定義程序")
    print("=" * 80)

    # 在 neo4j database 驗證已建立的程序
    with driver.session(database="neo4j") as neo4j_session:
        print("\n[驗證] 已建立的自定義程序：\n")
        result = neo4j_session.run("CALL apoc.custom.list() YIELD name, description RETURN name, description")
        for record in result:
            print(f"  • custom.{record['name']}")
            print(f"    {record['description']}\n")

        # 使用範例
        print("=" * 80)
        print("使用範例（明確命名版 6 個程序）")
        print("=" * 80)
        print("""
// ========== 測站類（3 個）==========

// 1. searchStation - 搜尋測站
CALL custom.searchStation("三峽", "全部")
YIELD code, name, type, city, matchedRiver
RETURN code, name, type, city, matchedRiver

// 2. getStationsByRiver - 河川上的測站
CALL custom.getStationsByRiver("大甲溪")
YIELD code, name, type, city, status
RETURN code, name, type, city, status

// 3. getStationsByWaterSystem - 水系內的測站
CALL custom.getStationsByWaterSystem("大甲溪水系")
YIELD code, name, type, city, river, status
RETURN code, name, type, river, city

// ========== 河川類（3 個）==========

// 4. getRiverTributaries - 河川的所有支流（遞迴）
CALL custom.getRiverTributaries("大甲溪")
YIELD name, level, code
RETURN name, level, code

// 5. getRiversInWaterSystem - 水系內的所有河川
CALL custom.getRiversInWaterSystem("大甲溪水系")
YIELD name, level, code
RETURN name, level, code

// 6. getRiverFlowPath - 河川流向路徑
CALL custom.getRiverFlowPath("南湖溪")
YIELD riverPath
RETURN riverPath
        """)

except Exception as e:
    print(f"\n[ERROR] 發生錯誤: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.close()
    print("\n已關閉 Neo4j 連線")
