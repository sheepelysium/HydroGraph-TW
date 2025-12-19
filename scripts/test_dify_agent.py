# -*- coding: utf-8 -*-
"""
DIFY Agent 簡易測試腳本

9 個工具各 3 題，共 27 題
專注於易錯和高難度題目
"""
import sys
import io

# 強制使用 UTF-8 編碼輸出
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests
import json
import time
from typing import List, Dict, Optional
from datetime import datetime

# DIFY API 設定
DIFY_API_BASE = "http://localhost:9080/v1"
DIFY_API_KEY = "app-crqGSVTN7WwnQC2p5xIDqI7v"

# 測試間隔時間（秒）
REQUEST_INTERVAL = 5

# 超時警告閾值（秒）
SLOW_THRESHOLD = 20

# 測試案例定義（易錯 + 高難度題目）
TEST_CASES = {
    "searchStation": [
        {
            "query": "中正橋雨量站",
            "expected_tool": "searchStation",
            "expected_contains": ["中正橋", "雨量"],
            "expected_not_contains": ["水位"],
            "note": "易錯：指定雨量站，不應顯示水位站"
        },
        {
            "query": "1450P001 這個站號是哪裡？",
            "expected_tool": "searchStation",
            "expected_contains": ["1450"],
            "note": "站號查詢"
        },
        {
            "query": "牛鬥橋旁邊的那個測站",
            "expected_tool": "searchStation",
            "expected_contains": ["牛鬥"],
            "note": "模糊描述"
        }
    ],

    "getStationsByRiver": [
        {
            "query": "蘭陽溪測站",
            "expected_tool": "getStationsByRiver",
            "expected_contains": ["蘭陽溪"],
            "note": "易錯：蘭陽溪是河川名，不是站名"
        },
        {
            "query": "宜蘭河的水位站詳細資料",
            "expected_tool": "getStationsByRiver",
            "expected_contains": ["宜蘭河"],
            "note": "易錯：宜蘭河是河川名"
        },
        {
            "query": "羅東溪和它的支流上有哪些測站？",
            "expected_tool": "getStationsByRiver",
            "expected_contains": ["羅東溪"],
            "note": "易錯：沒有水系二字，應用 getStationsByRiver"
        }
    ],

    "getStationsByWaterSystem": [
        {
            "query": "蘭陽溪水系有哪些測站？",
            "expected_tool": "getStationsByWaterSystem",
            "expected_min_count": 15,
            "note": "基本水系查詢"
        },
        {
            "query": "蘭陽溪流域範圍內有多少測站？",
            "expected_tool": "getStationsByWaterSystem",
            "expected_contains": ["蘭陽溪"],
            "note": "同義詞：流域範圍 = 水系"
        },
        {
            "query": "從蘭陽溪主流到所有支流，總共設置了哪些測站？",
            "expected_tool": "getStationsByWaterSystem",
            "expected_contains": ["蘭陽溪"],
            "note": "複雜描述"
        }
    ],

    "getStationsByCity": [
        {
            "query": "宜蘭縣有幾個雨量站？",
            "expected_tool": "getStationsByCity",
            "expected_contains": ["宜蘭", "雨量"],
            "note": "縣市+類型篩選"
        },
        {
            "query": "宜蘭有多少個雨量站和水位站？",
            "expected_tool": "getStationsByCity",
            "expected_contains": ["宜蘭"],
            "note": "問兩種類型數量"
        },
        {
            "query": "宜蘭地區從山區到平原的監測站配置",
            "expected_tool": "getStationsByCity",
            "expected_contains": ["宜蘭"],
            "note": "複雜地理描述"
        }
    ],

    "getStationStats": [
        {
            "query": "哪個縣市的測站最多？",
            "expected_tool": "getStationStats",
            "expected_contains": ["縣市"],
            "note": "需要全台統計來排名"
        },
        {
            "query": "宜蘭縣的測站數量在全台排名第幾？",
            "expected_tool": "getStationStats",
            "expected_contains": ["宜蘭"],
            "note": "需要統計後比較"
        },
        {
            "query": "比較各縣市的監測站密度",
            "expected_tool": "getStationStats",
            "expected_contains": ["縣市"],
            "note": "複雜：密度概念"
        }
    ],

    "getRiverTributaries": [
        {
            "query": "蘭陽溪的一級支流和二級支流",
            "expected_tool": "getRiverTributaries",
            "expected_contains": ["蘭陽溪"],
            "note": "問不同層級"
        },
        {
            "query": "匯入蘭陽溪的所有河川",
            "expected_tool": "getRiverTributaries",
            "expected_contains": ["蘭陽溪"],
            "note": "反向描述"
        },
        {
            "query": "羅東溪、宜蘭河、冬山河這些是蘭陽溪的支流嗎？還有其他的嗎？",
            "expected_tool": "getRiverTributaries",
            "expected_contains": ["蘭陽溪"],
            "note": "確認+列舉"
        }
    ],

    "getRiversInWaterSystem": [
        {
            "query": "蘭陽溪水系有哪些河川？",
            "expected_tool": "getRiversInWaterSystem",
            "expected_contains": ["蘭陽溪"],
            "note": "基本水系河川查詢"
        },
        {
            "query": "蘭陽溪水系從主流到支流的完整河川網絡",
            "expected_tool": "getRiversInWaterSystem",
            "expected_contains": ["蘭陽溪"],
            "note": "網絡概念"
        },
        {
            "query": "屬於蘭陽溪水系範圍內的所有大小河川",
            "expected_tool": "getRiversInWaterSystem",
            "expected_contains": ["蘭陽溪"],
            "note": "範圍+大小描述"
        }
    ],

    "getRiverFlowPath": [
        {
            "query": "羅東溪的下游是什麼河？最終流到哪裡？",
            "expected_tool": "getRiverFlowPath",
            "expected_contains": ["羅東溪"],
            "note": "多步驟問法"
        },
        {
            "query": "冬山河從源頭到出海口的流向路徑",
            "expected_tool": "getRiverFlowPath",
            "expected_contains": ["冬山河"],
            "note": "完整路徑"
        },
        {
            "query": "宜蘭河、羅東溪、冬山河這三條河的流向是不是都匯入蘭陽溪？",
            "expected_tool": "getRiverFlowPath",
            "expected_contains": ["宜蘭河"],
            "note": "多河川比較"
        }
    ],

    "searchStationObservation": [
        {
            "query": "中正橋 2023 年雨量資料",
            "expected_tool": "searchStationObservation",
            "expected_contains": ["中正橋", "2023"],
            "note": "測站+年份查詢"
        },
        {
            "query": "牛鬥站去年的水位觀測資料",
            "expected_tool": "searchStationObservation",
            "expected_contains": ["牛鬥"],
            "note": "相對日期：去年"
        },
        {
            "query": "蘭陽大橋 2023 年 8 月的流量資料",
            "expected_tool": "searchStationObservation",
            "expected_contains": ["蘭陽大橋", "2023"],
            "note": "精確到月份"
        }
    ]
}


class DIFYAgentTester:
    """DIFY Agent 測試器"""

    def __init__(self, api_base: str, api_key: str, interval: float = 5.0):
        self.api_base = api_base.rstrip('/')
        self.api_key = api_key
        self.interval = interval
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.results = []
        self.slow_queries = []

    def chat(self, query: str, user: str = "test_user") -> Optional[Dict]:
        """發送對話請求"""
        url = f"{self.api_base}/chat-messages"

        payload = {
            "inputs": {},
            "query": query,
            "response_mode": "blocking",
            "conversation_id": "",
            "user": user
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"   [X] API 請求失敗: {e}")
            return None

    def infer_tool_from_answer(self, answer: str, expected_tool: str) -> bool:
        """從答案內容推斷是否使用了正確的工具"""

        tool_signatures = {
            "searchStation": ["站號", "地址", "狀態", "高程"],
            "getStationsByRiver": ["測站", "站號", "類型", "河川"],
            "getStationsByWaterSystem": ["水系", "測站", "河川"],
            "getStationsByCity": ["縣", "測站", "站號"],
            "getStationStats": ["個", "統計", "數量", "總", "排名"],
            "getRiverTributaries": ["支流", "層級", "level"],
            "getRiversInWaterSystem": ["水系", "河川", "組成"],
            "getRiverFlowPath": ["流向", "流到", "流入", "匯入"],
            "searchStationObservation": ["觀測", "資料", "雨量", "水位", "流量", "期間"],
        }

        if expected_tool not in tool_signatures:
            return True

        keywords = tool_signatures[expected_tool]
        matches = sum(1 for keyword in keywords if keyword in answer)
        return matches >= 1

    def validate_result(self, test_case: Dict, response: Dict) -> Dict:
        """驗證測試結果"""
        result = {
            "status": "PASS",
            "errors": [],
            "warnings": []
        }

        answer = response.get("answer", "")

        # 驗證工具選擇
        expected_tool = test_case.get("expected_tool")
        if expected_tool:
            tool_likely_used = self.infer_tool_from_answer(answer, expected_tool)
            if tool_likely_used:
                result["tool_check"] = f"[OK] 符合 {expected_tool} 特徵"
            else:
                result["status"] = "FAIL"
                result["errors"].append(f"不符合 {expected_tool} 特徵")
                result["tool_check"] = f"[X] 不符合 {expected_tool} 特徵"

        # 驗證必須包含的關鍵字
        if "expected_contains" in test_case:
            missing = [kw for kw in test_case["expected_contains"] if kw not in answer]
            if missing:
                result["warnings"].append(f"缺少關鍵字: {missing}")

        # 驗證不應包含的關鍵字
        if "expected_not_contains" in test_case:
            found = [kw for kw in test_case["expected_not_contains"] if kw in answer]
            if found:
                result["status"] = "FAIL"
                result["errors"].append(f"不應出現: {found}")

        # 驗證最小數量
        if "expected_min_count" in test_case:
            import re
            numbers = re.findall(r'\d+', answer)
            if numbers:
                max_num = max(int(n) for n in numbers)
                min_count = test_case["expected_min_count"]
                if max_num >= min_count:
                    result["count_check"] = f"[OK] {max_num} >= {min_count}"
                else:
                    result["warnings"].append(f"數量不足: {max_num} < {min_count}")

        return result

    def run_test_case(self, tool_name: str, test_case: Dict, case_num: int, total: int) -> Dict:
        """執行單一測試案例"""
        query = test_case["query"]
        note = test_case.get("note", "")
        expected_tool = test_case.get("expected_tool", tool_name)

        print(f"\n{'─'*70}")
        print(f"[{case_num}/{total}] {tool_name}")
        print(f"問題: {query}")
        print(f"說明: {note}")
        print(f"預期工具: {expected_tool}")
        if "expected_contains" in test_case:
            print(f"預期包含: {test_case['expected_contains']}")
        print(f"{'─'*70}")

        # 發送請求並計時
        start_time = time.time()
        response = self.chat(query)
        elapsed = time.time() - start_time

        if not response:
            return {
                "tool": tool_name,
                "query": query,
                "status": "ERROR",
                "error": "API 請求失敗",
                "elapsed": elapsed
            }

        # 取得回答
        answer = response.get("answer", "")

        # 時間標記
        time_icon = "⚠️ 慢" if elapsed > SLOW_THRESHOLD else "✓"
        print(f"\n[時間] {elapsed:.2f}s {time_icon}")

        if elapsed > SLOW_THRESHOLD:
            self.slow_queries.append({
                "query": query,
                "elapsed": elapsed,
                "tool": tool_name
            })

        # 顯示回答（截斷）
        print(f"[回答] {answer[:300]}{'...' if len(answer) > 300 else ''}")

        # 驗證結果
        validation = self.validate_result(test_case, response)

        # 顯示驗證結果
        if "tool_check" in validation:
            print(f"   {validation['tool_check']}")
        if "count_check" in validation:
            print(f"   {validation['count_check']}")
        for warning in validation.get("warnings", []):
            print(f"   [!] {warning}")
        for error in validation.get("errors", []):
            print(f"   [X] {error}")

        # 最終狀態
        status_icon = "[OK]" if validation["status"] == "PASS" else "[X]"
        print(f"\n{status_icon} 狀態: {validation['status']}")

        return {
            "tool": tool_name,
            "query": query,
            "note": note,
            "expected_tool": expected_tool,
            "answer": answer,
            "elapsed": elapsed,
            **validation
        }

    def run_all_tests(self, test_cases: Dict[str, List[Dict]]) -> None:
        """執行所有測試"""
        print("="*70)
        print("DIFY Agent 測試")
        print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"測試數量: {sum(len(cases) for cases in test_cases.values())} 題")
        print(f"間隔時間: {self.interval}s")
        print(f"慢查詢閾值: {SLOW_THRESHOLD}s")
        print("="*70)

        total_cases = sum(len(cases) for cases in test_cases.values())
        current = 0

        for tool_name, cases in test_cases.items():
            print(f"\n\n{'='*70}")
            print(f"工具: {tool_name} ({len(cases)} 題)")
            print(f"{'='*70}")

            for test_case in cases:
                current += 1
                result = self.run_test_case(tool_name, test_case, current, total_cases)
                self.results.append(result)

                # 間隔等待
                if current < total_cases:
                    print(f"\n等待 {self.interval} 秒...")
                    time.sleep(self.interval)

        # 產生報告
        self.generate_report()

    def generate_report(self) -> None:
        """產生測試報告"""
        print("\n\n")
        print("="*70)
        print("測試報告")
        print(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)

        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        errors = sum(1 for r in self.results if r["status"] == "ERROR")

        print(f"\n📊 總覽:")
        print(f"   總測試數: {total}")
        print(f"   ✓ 通過: {passed} ({passed/total*100:.1f}%)")
        print(f"   ✗ 失敗: {failed} ({failed/total*100:.1f}%)")
        print(f"   ⚠ 錯誤: {errors} ({errors/total*100:.1f}%)")

        # 按工具統計
        print(f"\n📈 各工具通過率:")
        tools = {}
        for r in self.results:
            tool = r["tool"]
            if tool not in tools:
                tools[tool] = {"total": 0, "passed": 0}
            tools[tool]["total"] += 1
            if r["status"] == "PASS":
                tools[tool]["passed"] += 1

        for tool, stats in sorted(tools.items()):
            rate = stats["passed"] / stats["total"] * 100
            icon = "✓" if rate == 100 else "△" if rate >= 66 else "✗"
            print(f"   {icon} {tool}: {stats['passed']}/{stats['total']} ({rate:.0f}%)")

        # 效能統計
        times = [r["elapsed"] for r in self.results if "elapsed" in r]
        if times:
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)

            print(f"\n⏱️ 回應時間:")
            print(f"   平均: {avg_time:.2f}s")
            print(f"   最快: {min_time:.2f}s")
            print(f"   最慢: {max_time:.2f}s")

        # 慢查詢
        if self.slow_queries:
            print(f"\n🐢 慢查詢 (>{SLOW_THRESHOLD}s):")
            for sq in self.slow_queries:
                print(f"   [{sq['elapsed']:.2f}s] {sq['tool']}: {sq['query'][:40]}...")

        # 失敗案例
        failed_results = [r for r in self.results if r["status"] == "FAIL"]
        if failed_results:
            print(f"\n❌ 失敗案例:")
            for r in failed_results:
                print(f"\n   問題: {r['query']}")
                print(f"   預期工具: {r.get('expected_tool', r['tool'])}")
                for error in r.get("errors", []):
                    print(f"   原因: {error}")

        # 儲存報告
        self.save_report()

    def save_report(self) -> None:
        """儲存詳細報告到檔案"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"test_report_{timestamp}.json"

        report_data = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "interval": self.interval,
                "slow_threshold": SLOW_THRESHOLD
            },
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r["status"] == "PASS"),
                "failed": sum(1 for r in self.results if r["status"] == "FAIL"),
                "errors": sum(1 for r in self.results if r["status"] == "ERROR")
            },
            "slow_queries": self.slow_queries,
            "results": self.results
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"\n📄 詳細報告已儲存: {report_file}")


def main():
    """主程式"""
    import sys

    AUTO_MODE = '--auto' in sys.argv

    print("DIFY Agent 測試工具")
    print(f"API: {DIFY_API_BASE}")
    print(f"間隔: {REQUEST_INTERVAL}s")
    print(f"慢查詢閾值: {SLOW_THRESHOLD}s")
    print(f"總題數: {sum(len(cases) for cases in TEST_CASES.values())}")

    if AUTO_MODE:
        print("\n[自動模式] 跳過確認...")
    else:
        input("\n按 Enter 開始測試...")

    tester = DIFYAgentTester(DIFY_API_BASE, DIFY_API_KEY, REQUEST_INTERVAL)
    tester.run_all_tests(TEST_CASES)


if __name__ == "__main__":
    main()
