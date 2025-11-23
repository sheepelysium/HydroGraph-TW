# test_permissions.py
from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
user = "neo4j"
password = "geoinfor"  # 改成你的密碼

driver = GraphDatabase.driver(uri, auth=(user, password))

try:
    print("測試 1: 連線...")
    with driver.session(database="neo4j") as session:
        session.run("RETURN 1")
    print("✅ 連線成功")
    
    print("\n測試 2: 建立節點...")
    with driver.session(database="neo4j") as session:
        session.run("CREATE (test:Test {name: 'test'})")
    print("✅ 建立成功")
    
    print("\n測試 3: 查詢節點...")
    with driver.session(database="neo4j") as session:
        result = session.run("MATCH (n:Test) RETURN count(n) as count")
        count = result.single()["count"]
        print(f"✅ 找到 {count} 個測試節點")
    
    print("\n測試 4: 刪除節點...")
    with driver.session(database="neo4j") as session:
        session.run("MATCH (n:Test) DELETE n")
    print("✅ 刪除成功")
    
    print("\n測試 5: 清空全部資料...")
    with driver.session(database="neo4j") as session:
        session.run("MATCH (n) DETACH DELETE n")
    print("✅ 清空成功")
    
    print("\n🎉 所有測試通過!")
    print("\n現在可以執行完整的匯入腳本了!")
    
except Exception as e:
    print(f"\n❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    driver.close()