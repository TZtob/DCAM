#!/usr/bin/env python3
"""
更新现有YAML文件中的Asset_owner字段
将"待选择Customer"替换为正确的客户名称
"""

import json
import yaml
import os

def load_json_db(filename):
    """加载JSON数据库文件"""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def update_yaml_asset_owner(yaml_path, customer_name):
    """更新YAML文件中的Asset_owner字段"""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        updated = False
        if 'clusters' in data:
            for cluster in data['clusters']:
                if cluster.get('Asset_owner') == '待选择Customer':
                    cluster['Asset_owner'] = customer_name
                    updated = True
                    print(f"  更新集群 {cluster.get('Cluster_name', 'Unknown')} 的Asset_owner为: {customer_name}")
        
        if updated:
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            print(f"✓ 已更新文件: {yaml_path}")
            return True
        else:
            print(f"- 文件无需更新: {yaml_path}")
            return False
    except Exception as e:
        print(f"✗ 更新文件失败 {yaml_path}: {e}")
        return False

def main():
    """主函数"""
    print("开始更新现有YAML文件中的Asset_owner字段...\n")
    
    # 加载系统数据库
    systems = load_json_db('systems.json')
    customers = load_json_db('customers.json')
    
    if not systems:
        print("未找到系统数据库文件")
        return
    
    if not customers:
        print("未找到客户数据库文件")
        return
    
    updated_count = 0
    
    for system_id, system in systems.items():
        if system.get('status') == 'imported' and system.get('yaml_file'):
            yaml_path = system['yaml_file']
            customer_id = system.get('customer_id')
            
            print(f"处理系统: {system.get('name', 'Unknown')} (ID: {system_id})")
            
            if not os.path.exists(yaml_path):
                print(f"  ✗ YAML文件不存在: {yaml_path}")
                continue
            
            if not customer_id or customer_id not in customers:
                print(f"  ✗ 客户ID无效: {customer_id}")
                continue
            
            customer_name = customers[customer_id]['name']
            print(f"  客户名称: {customer_name}")
            
            if update_yaml_asset_owner(yaml_path, customer_name):
                updated_count += 1
            
            print()  # 空行分隔
    
    print(f"更新完成! 共更新了 {updated_count} 个YAML文件。")

if __name__ == "__main__":
    main()