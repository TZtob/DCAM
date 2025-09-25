#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统名称冲突解决方案 - 数据迁移脚本
将现有系统更新为新的命名方案，解决跨客户系统名冲突问题
"""

import json
import os
import shutil
from datetime import datetime

def migrate_system_naming():
    """迁移系统命名方案"""
    print("=== 系统命名方案迁移 ===")
    
    # 读取现有系统数据
    try:
        with open('systems.json', 'r', encoding='utf-8') as f:
            systems = json.load(f)
    except FileNotFoundError:
        print("❌ systems.json 文件不存在")
        return
    
    print(f"找到 {len(systems)} 个系统")
    
    # 备份原始文件
    backup_filename = f"systems_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    shutil.copy2('systems.json', backup_filename)
    print(f"✅ 已备份原始文件为: {backup_filename}")
    
    # 迁移每个系统
    updated_systems = {}
    file_mappings = {}  # 记录文件重命名映射
    
    for system_id, system in systems.items():
        customer_name = system.get('customer_name', 'Unknown')
        system_name = system.get('name', 'Unknown')
        old_yaml_file = system.get('yaml_file')
        
        print(f"\n处理系统 {system_id}: {system_name} ({customer_name})")
        
        # 生成新的文件名
        new_yaml_file = f"{customer_name}_{system_name}_clusters.yaml"
        
        # 更新系统信息
        updated_system = system.copy()
        updated_system['yaml_file'] = new_yaml_file
        
        # 如果旧文件存在，计划重命名
        if old_yaml_file and old_yaml_file != new_yaml_file:
            print(f"  文件重命名: {old_yaml_file} -> {new_yaml_file}")
            file_mappings[old_yaml_file] = new_yaml_file
        
        updated_systems[system_id] = updated_system
        print(f"  ✅ 系统信息已更新")
    
    # 保存更新后的系统信息
    with open('systems.json', 'w', encoding='utf-8') as f:
        json.dump(updated_systems, f, indent=2, ensure_ascii=False)
    print(f"\n✅ 已保存更新后的系统配置")
    
    # 重命名YAML文件
    print(f"\n=== 重命名YAML文件 ===")
    for old_file, new_file in file_mappings.items():
        if os.path.exists(old_file):
            if os.path.exists(new_file):
                backup_old = f"{new_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.move(new_file, backup_old)
                print(f"  ⚠️  目标文件已存在，备份为: {backup_old}")
            
            shutil.move(old_file, new_file)
            print(f"  ✅ {old_file} -> {new_file}")
        else:
            print(f"  ⚠️  源文件不存在: {old_file}")
    
    print(f"\n=== 迁移完成 ===")
    print("新的命名方案优势：")
    print("1. ✅ 解决跨客户系统名冲突")
    print("2. ✅ YAML文件名包含客户信息")
    print("3. ✅ 支持同一客户内的系统名唯一性检查")
    print("4. ✅ 向后兼容现有数据")

def test_conflict_prevention():
    """测试新的冲突预防机制"""
    print(f"\n=== 测试冲突预防机制 ===")
    
    # 读取更新后的系统数据
    with open('systems.json', 'r', encoding='utf-8') as f:
        systems = json.load(f)
    
    # 模拟创建新系统的冲突检测
    test_cases = [
        {'name': 'AI400', 'customer_id': '1', 'customer_name': 'SHLab'},  # 同客户重名
        {'name': 'AI400', 'customer_id': '2', 'customer_name': 'IDEA'},   # 跨客户重名（允许）
        {'name': 'NewSystem', 'customer_id': '1', 'customer_name': 'SHLab'}, # 新名称（允许）
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: 客户 {test_case['customer_name']} 创建系统 '{test_case['name']}'")
        
        # 检查同客户内是否有重名
        conflict_found = False
        for system_id, system in systems.items():
            if (system.get('name') == test_case['name'] and 
                system.get('customer_id') == test_case['customer_id']):
                conflict_found = True
                print(f"  ❌ 冲突！已存在系统: ID={system_id}")
                break
        
        if not conflict_found:
            print(f"  ✅ 允许创建")
            yaml_file = f"{test_case['customer_name']}_{test_case['name']}_clusters.yaml"
            print(f"  📁 YAML文件: {yaml_file}")

if __name__ == "__main__":
    migrate_system_naming()
    test_conflict_prevention()