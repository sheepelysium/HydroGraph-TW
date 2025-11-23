"""
環境檢查腳本 - HydroGraph-TW
快速檢查所有必要套件是否正確安裝
"""

def check_packages():
    """檢查所有必要套件"""
    packages = {
        # Core dependencies
        'pandas': 'Data processing',
        'numpy': 'Numerical computing',
        'openpyxl': 'Excel file handling',

        # Graph database
        'neo4j': 'Neo4j driver',

        # LangGraph and LangChain
        'langgraph': 'LangGraph workflow',
        'langgraph.graph': 'LangGraph graph module',
        'langchain_core': 'LangChain core',

        # LLM
        'google.generativeai': 'Google Gemini AI',

        # Network
        'requests': 'HTTP requests',
        'httpx': 'Async HTTP client',
        'certifi': 'SSL certificates',
        'charset_normalizer': 'Character encoding',
    }

    print("=" * 70)
    print("  HydroGraph-TW Environment Check")
    print("=" * 70)
    print()

    success_count = 0
    failed_packages = []

    for package, description in packages.items():
        try:
            __import__(package)
            print(f"[OK] {package:30s} - {description}")
            success_count += 1
        except ImportError as e:
            print(f"[FAIL] {package:30s} - {description}")
            failed_packages.append(package)

    print()
    print("=" * 70)
    print(f"Results: {success_count}/{len(packages)} packages installed")
    print("=" * 70)

    if failed_packages:
        print()
        print("[ERROR] Missing packages:")
        for pkg in failed_packages:
            print(f"  - {pkg}")
        print()
        print("Run this command to install missing packages:")
        print("  python -m pip install -r requirements.txt")
        return False
    else:
        print()
        print("[SUCCESS] All packages are installed correctly!")
        print()
        print("Next steps:")
        print("  1. Start Neo4j database (port 7687)")
        print("  2. Run: python scripts/langgraph_gemini_poc.py")
        return True


def check_neo4j():
    """檢查 Neo4j 連線"""
    try:
        from neo4j import GraphDatabase

        print()
        print("=" * 70)
        print("  Neo4j Connection Check")
        print("=" * 70)
        print()

        # 嘗試連線
        driver = GraphDatabase.driver(
            "bolt://127.0.0.1:7687",
            auth=("neo4j", "geoinfor")
        )

        driver.verify_connectivity()
        print("[OK] Neo4j connection successful!")
        print("     URI: bolt://127.0.0.1:7687")
        print("     User: neo4j")

        # 查詢節點數量
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()['count']
            print(f"     Total nodes: {count}")

        driver.close()
        return True

    except Exception as e:
        print(f"[FAIL] Neo4j connection failed")
        print(f"       Error: {str(e)}")
        print()
        print("Please check:")
        print("  1. Neo4j is running on port 7687")
        print("  2. Password is correct (default: geoinfor)")
        return False


if __name__ == "__main__":
    # 檢查套件
    packages_ok = check_packages()

    # 如果套件都OK,檢查 Neo4j
    if packages_ok:
        check_neo4j()

    print()
    input("Press Enter to exit...")
