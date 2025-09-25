#!/usr/bin/env python3
import requests
import json

def test_customer_filter():
    url = "http://127.0.0.1:5000/api/systems_by_customer?customer_id=1"
    try:
        print(f"测试URL: {url}")
        response = requests.get(url)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"返回数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_customer_filter()