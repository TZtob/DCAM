#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
概念统一和数据一致性维护脚本

目的：统一 Customer 和 Asset Owner 概念，确保数据一致性

概念说明：
1. Customer（客户）：
   - 存储在 customers.json 中
   - 是系统级别的概念
   - 每个系统属于一个客户
   - 用于权限管理、数据隔离

2. Asset Owner（资产所有者）：
   - 存储在 YAML 文件中
   - 是设备级别的标签
   - 可能与客户名称相同，但不强制要求
   - 用于设备管理、资产追踪

建议：
- 保持两个概念的独立性
- 添加数据一致性检查
- 提供同步工具
"""

import json
import os
from datetime import datetime
import asset_analyze

def load_customers():
    """加载客户数据"""
    try:
        with open('customers.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_systems():
    """加载系统数据"""
    try:
        with open('systems.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def analyze_customer_asset_owner_consistency():
    """分析客户和资产所有者的一致性"""
    print("=== 客户-资产所有者一致性分析 ===\n")
    
    customers = load_customers()
    systems = load_systems()
    
    print("📊 数据概览：")
    print(f"   客户总数: {len(customers)}")
    print(f"   系统总数: {len(systems)}")
    
    # 分析每个系统
    inconsistencies = []
    
    for system_id, system in systems.items():
        system_name = system.get('name', 'Unknown')
        customer_id = system.get('customer_id')
        customer_name = system.get('customer_name', 'Unknown')
        yaml_file = system.get('yaml_file')
        
        print(f"\n🔍 分析系统: {system_name} (ID: {system_id})")
        print(f"   客户ID: {customer_id}")
        print(f"   客户名称: {customer_name}")
        print(f"   YAML文件: {yaml_file}")
        
        if yaml_file and os.path.exists(yaml_file):
            try:
                # 获取YAML文件中的资产所有者
                asset_owners = asset_analyze.get_asset_owners(yaml_file)
                print(f"   资产所有者: {asset_owners}")
                
                # 检查一致性
                if customer_name not in asset_owners:
                    inconsistencies.append({
                        'system_id': system_id,
                        'system_name': system_name,
                        'customer_name': customer_name,
                        'asset_owners': asset_owners,
                        'issue': 'customer_name不在asset_owners中'
                    })
                    print(f"   ⚠️  不一致: 客户 '{customer_name}' 不在资产所有者 {asset_owners} 中")
                else:
                    print(f"   ✅ 一致: 客户名称匹配资产所有者")
                    
            except Exception as e:
                print(f"   ❌ 无法读取YAML文件: {e}")
                inconsistencies.append({
                    'system_id': system_id,
                    'system_name': system_name,
                    'yaml_file': yaml_file,
                    'issue': f'YAML文件读取失败: {e}'
                })
        else:
            print(f"   ❌ YAML文件不存在")
            inconsistencies.append({
                'system_id': system_id,
                'system_name': system_name,
                'yaml_file': yaml_file,
                'issue': 'YAML文件不存在'
            })
    
    # 总结报告
    print(f"\n📋 一致性检查报告：")
    print(f"   总系统数: {len(systems)}")
    print(f"   不一致项: {len(inconsistencies)}")
    
    if inconsistencies:
        print(f"\n⚠️  发现的不一致性：")
        for i, issue in enumerate(inconsistencies, 1):
            print(f"   {i}. 系统: {issue['system_name']} (ID: {issue['system_id']})")
            print(f"      问题: {issue['issue']}")
            if 'customer_name' in issue:
                print(f"      客户: {issue['customer_name']}")
            if 'asset_owners' in issue:
                print(f"      资产所有者: {issue['asset_owners']}")
    else:
        print(f"   ✅ 所有系统都保持一致性")
    
    return inconsistencies

def suggest_unification_strategy():
    """建议统一策略"""
    print(f"\n💡 概念统一建议：")
    
    print(f"""
1. 🏢 Customer（客户）概念：
   - 用途：系统级归属、权限管理、数据隔离
   - 存储：customers.json
   - 作用域：系统级别
   - 唯一性：每个系统只属于一个客户

2. 🏷️  Asset Owner（资产所有者）概念：
   - 用途：设备标识、资产管理、运维标签
   - 存储：YAML文件中的设备记录
   - 作用域：设备级别
   - 灵活性：可与客户名称不同

3. 🔄 数据一致性策略：
   - 保持概念独立性
   - 提供同步工具（可选）
   - 在UI中明确区分两个概念
   - 添加数据验证检查

4. 📝 代码重构建议：
   - 在API中明确返回customer_name和asset_owner
   - 在前端区分显示这两个概念
   - 添加数据一致性验证
   - 提供数据同步选项
""")

def create_consistency_report():
    """创建一致性报告文件"""
    inconsistencies = analyze_customer_asset_owner_consistency()
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_systems': len(load_systems()),
            'total_customers': len(load_customers()),
            'inconsistencies_count': len(inconsistencies)
        },
        'inconsistencies': inconsistencies
    }
    
    report_file = f"consistency_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 一致性报告已保存到: {report_file}")
    return report_file

def main():
    """主函数"""
    print("🔍 开始客户-资产所有者概念分析...\n")
    
    try:
        # 分析一致性
        inconsistencies = analyze_customer_asset_owner_consistency()
        
        # 提供建议
        suggest_unification_strategy()
        
        # 创建报告
        create_consistency_report()
        
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {e}")

if __name__ == "__main__":
    main()