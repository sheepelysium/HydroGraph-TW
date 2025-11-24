"""
清空 Neo4j 資料庫
"""
from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "geoinfor"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

print("="*80)
print("清空 Neo4j 資料庫")
print("="*80)

# 警告
print("\n[WARNING] 此操作將刪除所有節點和關係!")
print("[WARNING] 此操作無法復原!")

# 先顯示目前的資料量
with driver.session() as session:
    # 統計節點
    result = session.run("MATCH (n) RETURN count(n) as count")
    node_count = result.single()['count']

    # 統計關係
    result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
    rel_count = result.single()['count']

    print(f"\n目前資料庫狀態:")
    print(f"  節點數量: {node_count}")
    print(f"  關係數量: {rel_count}")

# 確認
response = input("\n確定要清空所有資料嗎? (輸入 'DELETE ALL' 確認): ")

if response == 'DELETE ALL':
    print("\n開始清空資料庫...")

    with driver.session() as session:
        # 刪除所有節點和關係
        session.run("MATCH (n) DETACH DELETE n")

    print("[OK] 資料庫已清空!")

    # 驗證
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN count(n) as count")
        node_count = result.single()['count']
        result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
        rel_count = result.single()['count']

        print(f"\n清空後狀態:")
        print(f"  節點數量: {node_count}")
        print(f"  關係數量: {rel_count}")
else:
    print("\n[CANCEL] 取消操作")

driver.close()
print("\n" + "="*80)
