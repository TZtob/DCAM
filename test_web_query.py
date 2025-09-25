#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import asset_analyze

# 模拟系统查询
def test_system_query():
    # 模拟从systems.json读取的系统3(lfs)的信息
    lfs_system = {
        "name": "lfs",
        "customer_id": "2",
        "customer_name": "IDEA",
        "yaml_file": "lfs_clusters.yaml",
        "cluster_name": "lfs"
    }
    
    yaml_file = lfs_system['yaml_file']
    if not os.path.exists(yaml_file):
        print(f"错误：YAML文件 {yaml_file} 不存在")
        return
    
    print(f"=== 测试系统 {lfs_system['name']} 的查询 ===")
    print(f"YAML文件: {yaml_file}")
    print(f"客户: {lfs_system['customer_name']}")
    
    # 测试查询类型 6 (设备序列号)
    print("\n--- 测试设备序列号查询 (类型6) ---")
    try:
        result = asset_analyze.query_assets(yaml_file, 6)
        print(f"查询成功，结果类型: {type(result)}")
        print(f"结果键: {list(result.keys())}")
        if 'devices' in result:
            print(f"设备数量: {len(result['devices'])}")
            for i, device in enumerate(result['devices'][:3]):
                print(f"设备 {i+1}: {device}")
        else:
            print(f"完整结果: {result}")
    except Exception as e:
        print(f"设备序列号查询失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试查询类型 7 (IP地址)
    print("\n--- 测试IP地址查询 (类型7) ---")
    try:
        result = asset_analyze.query_assets(yaml_file, 7)
        print(f"查询成功，结果类型: {type(result)}")
        print(f"结果键: {list(result.keys())}")
        if 'devices' in result:
            print(f"设备数量: {len(result['devices'])}")
            for i, device in enumerate(result['devices'][:3]):
                print(f"设备 {i+1}: {device}")
        else:
            print(f"完整结果: {result}")
    except Exception as e:
        print(f"IP地址查询失败: {e}")
        import traceback
        traceback.print_exc()

# 模拟加载Asset_owner筛选
def test_asset_owner_filter():
    print("\n=== 测试Asset_owner筛选 ===")
    yaml_file = "lfs_clusters.yaml"
    
    # 测试没有筛选
    print("--- 没有筛选条件 ---")
    try:
        result = asset_analyze.query_assets(yaml_file, 6, None)
        print(f"无筛选结果设备数量: {len(result.get('devices', []))}")
    except Exception as e:
        print(f"无筛选查询失败: {e}")
    
    # 测试筛选IDEA
    print("--- 筛选Asset_owner=IDEA ---")
    try:
        result = asset_analyze.query_assets(yaml_file, 6, "IDEA")
        print(f"筛选IDEA结果设备数量: {len(result.get('devices', []))}")
        if result.get('devices'):
            print(f"第一个设备的Asset_owner: {result['devices'][0].get('Asset_owner')}")
    except Exception as e:
        print(f"筛选IDEA查询失败: {e}")
    
    # 测试筛选不存在的owner
    print("--- 筛选Asset_owner=NotExist ---")
    try:
        result = asset_analyze.query_assets(yaml_file, 6, "NotExist")
        print(f"筛选NotExist结果设备数量: {len(result.get('devices', []))}")
    except Exception as e:
        print(f"筛选NotExist查询失败: {e}")

if __name__ == "__main__":
    test_system_query()
    test_asset_owner_filter()