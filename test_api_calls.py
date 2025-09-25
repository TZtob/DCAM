#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json

def test_api_calls():
    base_url = "http://127.0.0.1:5000"
    
    # 测试系统3(lfs)的设备序列号查询
    print("=== 测试系统3(lfs)的设备序列号查询 ===")
    try:
        url = f"{base_url}/api/global_query?query_type=6&system_id=3"
        print(f"请求URL: {url}")
        response = requests.get(url)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据类型: {type(data)}")
            print(f"响应数据键: {list(data.keys())}")
            if 'devices' in data:
                print(f"设备数量: {len(data['devices'])}")
                for i, device in enumerate(data['devices'][:3]):
                    print(f"设备 {i+1}: {device}")
            else:
                print(f"完整响应: {data}")
        else:
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试系统3(lfs)的IP地址查询
    print("\n=== 测试系统3(lfs)的IP地址查询 ===")
    try:
        url = f"{base_url}/api/global_query?query_type=7&system_id=3"
        print(f"请求URL: {url}")
        response = requests.get(url)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据类型: {type(data)}")
            print(f"响应数据键: {list(data.keys())}")
            if 'devices' in data:
                print(f"设备数量: {len(data['devices'])}")
                for i, device in enumerate(data['devices'][:3]):
                    print(f"设备 {i+1}: {device}")
            else:
                print(f"完整响应: {data}")
        else:
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试全局查询（不指定系统ID）
    print("\n=== 测试全局设备序列号查询 ===")
    try:
        url = f"{base_url}/api/global_query?query_type=6"
        print(f"请求URL: {url}")
        response = requests.get(url)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据类型: {type(data)}")
            print(f"响应数据键: {list(data.keys())}")
            if 'devices' in data:
                print(f"设备数量: {len(data['devices'])}")
                # 查找lfs相关的设备
                lfs_devices = [d for d in data['devices'] if d.get('Cluster_name') == 'lfs']
                print(f"lfs集群设备数量: {len(lfs_devices)}")
                for i, device in enumerate(lfs_devices[:3]):
                    print(f"lfs设备 {i+1}: {device}")
            else:
                print(f"完整响应: {data}")
        else:
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_api_calls()