#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本 - 模拟浏览器调用API
"""

import requests
import json

def test_api_call(url):
    """测试API调用"""
    try:
        print(f"调用API: {url}")
        response = requests.get(url)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"返回数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return data
        else:
            print(f"错误响应: {response.text}")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None

if __name__ == "__main__":
    base_url = "http://127.0.0.1:5000"
    
    # 测试所有系统
    print("=== 测试 /api/all_systems ===")
    test_api_call(f"{base_url}/api/all_systems")
    print()
    
    # 测试按客户过滤的系统
    print("=== 测试 /api/systems_by_customer?customer_id=1 ===")
    test_api_call(f"{base_url}/api/systems_by_customer?customer_id=1")
    print()
    
    print("=== 测试 /api/systems_by_customer?customer_id=2 ===")
    test_api_call(f"{base_url}/api/systems_by_customer?customer_id=2")
    print()
    
    # 测试没有customer_id的情况
    print("=== 测试 /api/systems_by_customer (无参数) ===")
    test_api_call(f"{base_url}/api/systems_by_customer")