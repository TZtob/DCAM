#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试脚本 - 检查API返回的数据
"""

import json
import os

# 设置数据库文件路径
SYSTEMS_DB = 'systems.json'
CUSTOMERS_DB = 'customers.json'

def load_json_db(db_file):
    """加载JSON数据库"""
    if os.path.exists(db_file):
        try:
            with open(db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载 {db_file} 失败: {e}")
            return {}
    return {}

def get_systems():
    """获取系统列表"""
    return load_json_db(SYSTEMS_DB)

def get_customers():
    """获取客户列表"""
    return load_json_db(CUSTOMERS_DB)

def debug_systems_api():
    """模拟 /api/all_systems 的数据返回"""
    print("=== 调试 /api/all_systems ===")
    
    systems = get_systems()
    result = []
    
    for system_id, system in systems.items():
        print(f"系统 {system_id}: {system}")
        
        system_data = {
            'id': system_id,
            'name': system.get('name', 'Unknown System'),
            'customer_id': system.get('customer_id', ''),
            'customer_name': system.get('customer_name', '')
        }
        
        print(f"返回数据: {system_data}")
        result.append(system_data)
    
    print(f"最终返回: {json.dumps(result, indent=2, ensure_ascii=False)}")
    return result

def debug_systems_by_customer_api(customer_id):
    """模拟 /api/systems_by_customer 的数据返回"""
    print(f"=== 调试 /api/systems_by_customer?customer_id={customer_id} ===")
    
    systems = get_systems()
    result = []
    
    for system_id, system in systems.items():
        if system.get('customer_id') == customer_id:
            print(f"匹配的系统 {system_id}: {system}")
            
            system_data = {
                'id': system_id,
                'name': system.get('name', 'Unknown System'),
                'customer_id': system.get('customer_id', ''),
                'customer_name': system.get('customer_name', '')
            }
            
            print(f"返回数据: {system_data}")
            result.append(system_data)
    
    print(f"最终返回: {json.dumps(result, indent=2, ensure_ascii=False)}")
    return result

if __name__ == "__main__":
    print("检查当前工作目录:", os.getcwd())
    print("系统文件存在:", os.path.exists(SYSTEMS_DB))
    print("客户文件存在:", os.path.exists(CUSTOMERS_DB))
    print()
    
    # 调试所有系统
    debug_systems_api()
    print("\n" + "="*50 + "\n")
    
    # 调试特定客户的系统
    debug_systems_by_customer_api('1')  # SHLab
    print("\n" + "="*50 + "\n")
    debug_systems_by_customer_api('2')  # IDEA