#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试系统名称冲突问题
模拟两个不同客户创建同名系统的情况
"""

import json
import os
from datetime import datetime

def test_system_name_conflicts():
    """测试系统名称冲突问题"""
    print("=== 系统名称冲突测试 ===")
    
    # 模拟当前系统数据
    systems = {
        "1": {
            "name": "AI400",
            "customer_id": "1",
            "customer_name": "SHLab",
            "yaml_file": "AI400_clusters.yaml"
        },
        "2": {
            "name": "ES7990", 
            "customer_id": "1",
            "customer_name": "SHLab",
            "yaml_file": "ES7990_clusters.yaml"
        },
        "3": {
            "name": "lfs",
            "customer_id": "2", 
            "customer_name": "IDEA",
            "yaml_file": "lfs_clusters.yaml"
        }
    }
    
    print("当前系统列表：")
    for sid, system in systems.items():
        print(f"  {sid}: {system['name']} ({system['customer_name']}) -> {system['yaml_file']}")
    
    # 模拟冲突场景1：不同客户创建同名系统
    print("\n=== 冲突场景1：客户IDEA再创建一个名为'AI400'的系统 ===")
    
    new_system_name = "AI400"  # 与客户SHLab的系统同名
    new_customer_id = "2"      # IDEA客户
    
    # 检查名称冲突（当前系统没有这个检查）
    conflicts = []
    for sid, system in systems.items():
        if system['name'] == new_system_name:
            conflicts.append({
                'system_id': sid,
                'system': system
            })
    
    if conflicts:
        print(f"❌ 发现系统名称冲突！")
        for conflict in conflicts:
            print(f"   现有系统: {conflict['system']['name']} (客户: {conflict['system']['customer_name']}, 文件: {conflict['system']['yaml_file']})")
        
        # 模拟当前系统会怎么处理
        yaml_filename = f"{new_system_name}_clusters.yaml"
        print(f"   新系统将使用文件: {yaml_filename}")
        
        # 检查是否会覆盖现有文件
        existing_files = [s['yaml_file'] for s in systems.values() if s.get('yaml_file')]
        if yaml_filename in existing_files:
            print(f"   ⚠️  YAML文件冲突！{yaml_filename} 已存在，会被覆盖！")
        
    else:
        print(f"✅ 没有发现名称冲突")
    
    # 模拟冲突场景2：相同客户内部的重名
    print(f"\n=== 冲突场景2：客户SHLab再创建一个名为'AI400'的系统 ===")
    
    same_customer_conflicts = []
    for sid, system in systems.items():
        if system['name'] == new_system_name and system['customer_id'] == "1":
            same_customer_conflicts.append(system)
    
    if same_customer_conflicts:
        print(f"❌ 同客户内系统名称冲突！")
        for system in same_customer_conflicts:
            print(f"   现有系统: {system['name']} (客户: {system['customer_name']})")
    
    # 推荐解决方案
    print(f"\n=== 推荐解决方案 ===")
    print("1. 全局唯一性检查：禁止任何客户创建重名系统")
    print("2. 客户范围唯一性：同一客户内禁止重名，不同客户可以重名")
    print("3. 文件名前缀：YAML文件使用 'customer_system_clusters.yaml' 格式")
    print("4. 系统标识符：使用 customer_name-system_name 作为唯一标识")
    
    # 演示改进后的命名方案
    print(f"\n=== 改进后的文件命名示例 ===")
    for sid, system in systems.items():
        current_file = system.get('yaml_file', 'N/A')
        improved_file = f"{system['customer_name']}_{system['name']}_clusters.yaml"
        print(f"  系统: {system['name']} ({system['customer_name']})")
        print(f"    当前文件: {current_file}")
        print(f"    改进文件: {improved_file}")
        print()

if __name__ == "__main__":
    test_system_name_conflicts()