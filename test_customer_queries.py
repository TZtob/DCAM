#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json
import time

def test_customer_page_queries():
    base_url = "http://127.0.0.1:5000"
    
    # 模拟客户页面的查询（客户IDEA，asset_owner=IDEA，系统lfs）
    print("=== 模拟客户页面查询 ===")
    
    # 测试1：设备序列号查询 - 指定系统ID
    print("\n--- 测试1：客户页面 - 设备序列号查询（指定系统lfs）---")
    try:
        url = f"{base_url}/api/global_query?query_type=6&asset_owner=IDEA&system_id=3"
        print(f"请求URL: {url}")
        response = requests.get(url)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据类型: {type(data)}")
            print(f"响应数据键: {list(data.keys())}")
            if 'devices' in data:
                print(f"设备数量: {len(data['devices'])}")
                for i, device in enumerate(data['devices']):
                    print(f"设备 {i+1}: {device}")
            else:
                print(f"完整响应: {data}")
        else:
            print(f"响应内容: {response.text}")
        
        time.sleep(1)  # 等待1秒避免请求过快
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试2：IP地址查询 - 指定系统ID
    print("\n--- 测试2：客户页面 - IP地址查询（指定系统lfs）---")
    try:
        url = f"{base_url}/api/global_query?query_type=7&asset_owner=IDEA&system_id=3"
        print(f"请求URL: {url}")
        response = requests.get(url)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据类型: {type(data)}")
            print(f"响应数据键: {list(data.keys())}")
            if 'devices' in data:
                print(f"设备数量: {len(data['devices'])}")
                for i, device in enumerate(data['devices']):
                    print(f"设备 {i+1}: {device}")
            else:
                print(f"完整响应: {data}")
        else:
            print(f"响应内容: {response.text}")
        
        time.sleep(1)
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试3：设备序列号查询 - 不指定系统ID，只用asset_owner筛选
    print("\n--- 测试3：全局查询 - 设备序列号（仅筛选IDEA）---")
    try:
        url = f"{base_url}/api/global_query?query_type=6&asset_owner=IDEA"
        print(f"请求URL: {url}")
        response = requests.get(url)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据类型: {type(data)}")
            print(f"响应数据键: {list(data.keys())}")
            if 'devices' in data:
                print(f"设备数量: {len(data['devices'])}")
                for i, device in enumerate(data['devices']):
                    print(f"设备 {i+1}: {device}")
            else:
                print(f"完整响应: {data}")
        else:
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    # 等待2秒确保Flask服务器完全启动
    print("等待Flask服务器启动...")
    time.sleep(2)
    test_customer_page_queries()