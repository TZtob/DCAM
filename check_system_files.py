#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查系统导入文件的工具
用于排查容量计算问题
"""

import os
import json
import yaml

def check_system_files(customer_name, system_name):
    """检查指定系统的导入文件情况"""
    
    print(f"🔍 检查系统文件情况")
    print(f"👤 客户: {customer_name}")
    print(f"💾 系统: {system_name}")
    print("=" * 60)
    
    # 1. 检查系统配置
    systems_db_path = "systems.json"
    if os.path.exists(systems_db_path):
        with open(systems_db_path, 'r', encoding='utf-8') as f:
            systems = json.load(f)
        
        # 查找系统
        target_system = None
        target_system_id = None
        for system_id, system in systems.items():
            if (system.get('customer_name') == customer_name and 
                system.get('name') == system_name):
                target_system = system
                target_system_id = system_id
                break
        
        if target_system:
            print(f"✅ 找到系统配置 (ID: {target_system_id})")
            print(f"   状态: {target_system.get('status', 'unknown')}")
            print(f"   创建时间: {target_system.get('created_at', 'unknown')}")
            if target_system.get('imported_at'):
                print(f"   导入时间: {target_system.get('imported_at')}")
            
            # 检查文件记录
            if 'import_files_count' in target_system:
                files_count = target_system['import_files_count']
                print(f"   📄 TOML文件: {files_count.get('toml', 0)}个")
                print(f"   📦 SFA文件: {files_count.get('sfa', 0)}个")
            else:
                print("   ⚠️  无导入文件记录")
        else:
            print(f"❌ 未找到系统配置")
            return False
    else:
        print(f"❌ 系统数据库不存在: {systems_db_path}")
        return False
    
    print("\n" + "-" * 40)
    
    # 2. 检查系统目录结构
    system_dir = f"data/customers/{customer_name}/{system_name}"
    print(f"📁 检查系统目录: {system_dir}")
    
    if os.path.exists(system_dir):
        print(f"✅ 系统目录存在")
        
        # 检查uploads目录
        uploads_dir = os.path.join(system_dir, "uploads")
        if os.path.exists(uploads_dir):
            print(f"✅ uploads目录存在: {uploads_dir}")
            
            files = os.listdir(uploads_dir)
            toml_files = [f for f in files if f.endswith('.toml')]
            sfa_files = [f for f in files if f.endswith('.tar.gz')]
            
            print(f"   📄 TOML文件: {len(toml_files)}个")
            for f in toml_files:
                print(f"      - {f}")
            
            print(f"   📦 SFA文件: {len(sfa_files)}个")
            for f in sfa_files:
                print(f"      - {f}")
                
        else:
            print(f"❌ uploads目录不存在")
        
        # 检查YAML配置文件
        yaml_filename = f"{system_name}_clusters.yaml"
        yaml_path = os.path.join(system_dir, yaml_filename)
        if os.path.exists(yaml_path):
            print(f"✅ YAML配置存在: {yaml_path}")
            
            # 读取容量信息
            try:
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    yaml_data = yaml.safe_load(f)
                
                if yaml_data and 'clusters' in yaml_data:
                    cluster = yaml_data['clusters'][0]
                    capacity = cluster.get('Capacity', 'null')
                    print(f"   📊 集群容量: {capacity}")
                    
                    devices = cluster.get('devices', [])
                    print(f"   🖥️  设备数量: {len(devices)}")
                    
                    for i, device in enumerate(devices):
                        device_name = device.get('Device_name', f'Device-{i+1}')
                        device_capacity = device.get('Capacity', 'null')
                        print(f"      {device_name}: {device_capacity}")
                        
            except Exception as e:
                print(f"   ❌ 读取YAML失败: {e}")
        else:
            print(f"❌ YAML配置不存在: {yaml_path}")
    else:
        print(f"❌ 系统目录不存在")
        return False
    
    print("\n" + "-" * 40)
    
    # 3. 给出建议
    print("💡 问题排查建议:")
    
    if not target_system.get('imported_at'):
        print("   1. 系统尚未导入配置，请先导入TOML和SFA文件")
    elif not os.path.exists(uploads_dir):
        print("   1. uploads目录不存在，可能是旧版本导入的系统")
        print("   2. 建议重新导入配置文件以获得完整的文件归档")
    elif len(sfa_files) == 0:
        print("   1. 没有SFA文件，无法计算容量")
        print("   2. 请确保导入了正确的SFA info文件")
    elif capacity == 'null':
        print("   1. 容量计算失败，可能是SFA文件格式问题")
        print("   2. 建议检查SFA文件中是否包含OST信息")
        print("   3. 可以使用容量修复工具重新计算")
    else:
        print("   1. 系统配置看起来正常")
        print("   2. 如果仍有问题，请检查具体的错误日志")
    
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("使用方法: python check_system_files.py <客户名> <系统名>")
        print("示例: python check_system_files.py AION lfs")
    else:
        customer_name = sys.argv[1]
        system_name = sys.argv[2]
        check_system_files(customer_name, system_name)