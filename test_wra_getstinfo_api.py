# -*- coding: utf-8 -*-
"""
測試水利署 GetSTInfo API
找出正確的參數格式
"""
import requests
import json

# 測試不同的請求方式
base_url = "https://gweb.wra.gov.tw/HydroInfo/Comm/GetSTInfo"

print("="*80)
print("測試水利署 GetSTInfo API")
print("="*80)

# 停用 SSL 警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 測試 1: GET 請求 (無參數)
print("\n[測試 1] GET 請求 (無參數)")
try:
    response = requests.get(base_url, timeout=10, verify=False)
    print(f"  狀態碼: {response.status_code}")
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"  回應類型: JSON")
            print(f"  資料摘要: {str(data)[:200]}...")
        except:
            print(f"  回應類型: 純文字")
            print(f"  回應內容: {response.text[:200]}...")
except Exception as e:
    print(f"  錯誤: {e}")

# 測試 2: GET 請求 (帶測站代碼參數)
print("\n[測試 2] GET 請求 (帶測站代碼)")
params_list = [
    {"stno": "1140H043"},
    {"StNo": "1140H043"},
    {"station_code": "1140H043"},
    {"code": "1140H043"},
]

for params in params_list:
    try:
        response = requests.get(base_url, params=params, timeout=10, verify=False)
        if response.status_code == 200:
            print(f"  [OK] 參數 {params} 成功!")
            try:
                data = response.json()
                print(f"    回應: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
                break
            except:
                print(f"    回應: {response.text[:200]}...")
    except Exception as e:
        print(f"  [X] 參數 {params} 失敗: {e}")

# 測試 3: POST 請求
print("\n[測試 3] POST 請求")
post_data_list = [
    {"stno": "1140H043"},
    {"StNo": "1140H043"},
]

for post_data in post_data_list:
    try:
        response = requests.post(base_url, json=post_data, timeout=10, verify=False)
        if response.status_code == 200:
            print(f"  [OK] POST 參數 {post_data} 成功!")
            try:
                data = response.json()
                print(f"    回應: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}...")
                break
            except:
                print(f"    回應: {response.text[:200]}...")
    except Exception as e:
        print(f"  [X] POST 參數 {post_data} 失敗: {e}")

# 測試 4: 模擬瀏覽器行為 (帶 Referer)
print("\n[測試 4] 模擬瀏覽器請求 (帶 Referer)")
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://gweb.wra.gov.tw/HydroInfo/StDataInfo/StDataInfo?LE&1140H043&2024,2024"
}

try:
    response = requests.get(base_url, headers=headers, timeout=10, verify=False)
    print(f"  狀態碼: {response.status_code}")
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"  [OK] 成功取得資料!")
            print(f"  回應: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}...")
        except:
            print(f"  回應: {response.text[:300]}...")
except Exception as e:
    print(f"  錯誤: {e}")

# 測試 5: 檢查是否需要先訪問頁面建立 Session
print("\n[測試 5] 使用 Session (先訪問網頁)")
session = requests.Session()

try:
    # 先訪問測站頁面
    page_url = "https://gweb.wra.gov.tw/HydroInfo/StDataInfo/StDataInfo?LE&1140H043&2024,2024"
    print(f"  步驟 1: 訪問頁面 {page_url}")
    session.get(page_url, timeout=10, verify=False)

    # 再呼叫 API
    print(f"  步驟 2: 呼叫 GetSTInfo API")
    response = session.get(base_url, timeout=10, verify=False)
    print(f"  狀態碼: {response.status_code}")

    if response.status_code == 200:
        try:
            data = response.json()
            print(f"  [OK] 成功! 這個 API 需要先訪問頁面建立 Session!")
            print(f"  回應資料:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except:
            print(f"  回應: {response.text[:300]}...")
except Exception as e:
    print(f"  錯誤: {e}")

print("\n" + "="*80)
print("測試完成")
print("="*80)
