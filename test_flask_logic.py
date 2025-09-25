#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import asset_analyze

def get_systems():
    """获取系统列表"""
    try:
        with open('systems.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def test_system_query_logic():
    """测试系统查询逻辑，模拟Flask API的处理"""
    
    systems = get_systems()
    print(f"系统列表: {json.dumps(systems, indent=2, ensure_ascii=False)}")
    
    # 测试系统ID 3
    system_id = "3"
    if system_id not in systems:
        print(f"错误：系统ID {system_id} 不存在")
        return
    
    system = systems[system_id]
    print(f"\n系统信息: {json.dumps(system, indent=2, ensure_ascii=False)}")
    
    yaml_file = system.get('yaml_file')
    if not yaml_file:
        print(f"错误：系统 {system_id} 没有yaml_file字段")
        return
        
    if not os.path.exists(yaml_file):
        print(f"错误：YAML文件 {yaml_file} 不存在")
        return
    
    print(f"\nYAML文件存在: {yaml_file}")
    
    # 测试查询类型6 (设备序列号)
    print(f"\n=== 执行查询类型6 (设备序列号) ===")
    try:
        result = asset_analyze.query_assets(yaml_file, 6, None)
        print(f"查询成功，结果类型: {type(result)}")
        print(f"结果键: {list(result.keys())}")
        if 'devices' in result:
            print(f"设备数量: {len(result['devices'])}")
            for i, device in enumerate(result['devices']):
                print(f"设备 {i+1}: {device}")
        else:
            print(f"完整结果: {result}")
    except Exception as e:
        print(f"查询失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试查询类型7 (IP地址)
    print(f"\n=== 执行查询类型7 (IP地址) ===")
    try:
        result = asset_analyze.query_assets(yaml_file, 7, None)
        print(f"查询成功，结果类型: {type(result)}")
        print(f"结果键: {list(result.keys())}")
        if 'devices' in result:
            print(f"设备数量: {len(result['devices'])}")
            for i, device in enumerate(result['devices']):
                print(f"设备 {i+1}: {device}")
        else:
            print(f"完整结果: {result}")
    except Exception as e:
        print(f"查询失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_system_query_logic()