#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json

def test_systems_by_owner():
    base_url = "http://127.0.0.1:5000"
    
    print("=== 测试按资产所有者筛选系统 ===")
    
    # 测试1：获取所有系统
    print("\n--- 测试1：所有系统 ---")
    try:
        url = f"{base_url}/api/all_systems"
        response = requests.get(url)
        if response.status_code == 200:
            all_systems = response.json()
            print(f"所有系统数量: {len(all_systems)}")
            for system in all_systems:
                print(f"  - ID: {system['id']}, 名称: {system['name']}, 客户: {system.get('customer_name', 'N/A')}")
        else:
            print(f"请求失败: {response.status_code}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试2：按资产所有者"IDEA"筛选
    print("\n--- 测试2：筛选资产所有者IDEA ---")
    try:
        url = f"{base_url}/api/systems_by_owner?asset_owner=IDEA"
        response = requests.get(url)
        if response.status_code == 200:
            idea_systems = response.json()
            print(f"IDEA的系统数量: {len(idea_systems)}")
            for system in idea_systems:
                print(f"  - ID: {system['id']}, 名称: {system['name']}, 客户ID: {system.get('customer_id', 'N/A')}")
        else:
            print(f"请求失败: {response.status_code}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试3：按资产所有者"SHLab"筛选
    print("\n--- 测试3：筛选资产所有者SHLab ---")
    try:
        url = f"{base_url}/api/systems_by_owner?asset_owner=SHLab"
        response = requests.get(url)
        if response.status_code == 200:
            shlab_systems = response.json()
            print(f"SHLab的系统数量: {len(shlab_systems)}")
            for system in shlab_systems:
                print(f"  - ID: {system['id']}, 名称: {system['name']}, 客户ID: {system.get('customer_id', 'N/A')}")
        else:
            print(f"请求失败: {response.status_code}")
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_systems_by_owner()