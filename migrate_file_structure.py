#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件结构迁移脚本 - 将YAML文件按Customer-System层级重新组织
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path

def create_hierarchical_structure():
    """创建基于Customer-System层级的目录结构"""
    print("=== 创建层级化文件结构 ===")
    
    # 读取客户和系统信息
    with open('customers.json', 'r', encoding='utf-8') as f:
        customers = json.load(f)
    
    with open('systems.json', 'r', encoding='utf-8') as f:
        systems = json.load(f)
    
    # 创建主目录结构
    base_dirs = ['data', 'data/customers', 'data/uploads', 'data/backups']
    for dir_path in base_dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ 创建目录: {dir_path}")
    
    # 为每个客户创建目录
    for customer_id, customer_info in customers.items():
        customer_name = customer_info['name']
        customer_dir = f"data/customers/{customer_name}"
        os.makedirs(customer_dir, exist_ok=True)
        print(f"✅ 创建客户目录: {customer_dir}")
        
        # 为该客户的每个系统创建目录
        customer_systems = [s for s in systems.values() if s['customer_id'] == customer_id]
        for system in customer_systems:
            system_name = system['name']
            system_dir = f"{customer_dir}/{system_name}"
            reports_dir = f"{system_dir}/reports"
            os.makedirs(system_dir, exist_ok=True)
            os.makedirs(reports_dir, exist_ok=True)
            print(f"  ✅ 创建系统目录: {system_dir}")
            print(f"  ✅ 创建报告目录: {reports_dir}")

def backup_current_files():
    """备份当前的YAML文件"""
    print("\n=== 备份当前文件 ===")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"data/backups/migration_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # 查找所有YAML文件
    yaml_files = []
    for file in os.listdir('.'):
        if file.endswith('_clusters.yaml'):
            yaml_files.append(file)
    
    # 备份YAML文件
    for yaml_file in yaml_files:
        if os.path.exists(yaml_file):
            backup_path = f"{backup_dir}/{yaml_file}"
            shutil.copy2(yaml_file, backup_path)
            print(f"  ✅ 备份: {yaml_file} -> {backup_path}")
    
    return backup_dir, yaml_files

def migrate_yaml_files():
    """迁移YAML文件到新的目录结构"""
    print("\n=== 迁移YAML文件 ===")
    
    # 读取系统信息
    with open('systems.json', 'r', encoding='utf-8') as f:
        systems = json.load(f)
    
    migrated_files = []
    
    for system_id, system_info in systems.items():
        customer_name = system_info['customer_name']
        system_name = system_info['name']
        old_yaml_file = system_info['yaml_file']
        
        # 新的文件路径
        new_yaml_file = f"data/customers/{customer_name}/{system_name}/{system_name}_clusters.yaml"
        
        # 移动文件
        if os.path.exists(old_yaml_file):
            # 确保目标目录存在
            os.makedirs(os.path.dirname(new_yaml_file), exist_ok=True)
            
            # 移动文件
            shutil.move(old_yaml_file, new_yaml_file)
            print(f"  ✅ 迁移: {old_yaml_file} -> {new_yaml_file}")
            
            migrated_files.append({
                'system_id': system_id,
                'old_path': old_yaml_file,
                'new_path': new_yaml_file,
                'customer': customer_name,
                'system': system_name
            })
        else:
            print(f"  ⚠️  文件不存在: {old_yaml_file}")
    
    return migrated_files

def update_system_records(migrated_files):
    """更新systems.json中的文件路径"""
    print("\n=== 更新系统记录 ===")
    
    # 读取当前systems.json
    with open('systems.json', 'r', encoding='utf-8') as f:
        systems = json.load(f)
    
    # 更新文件路径
    for migration in migrated_files:
        system_id = migration['system_id']
        new_path = migration['new_path']
        
        if system_id in systems:
            systems[system_id]['yaml_file'] = new_path
            print(f"  ✅ 更新系统 {system_id}: {migration['system']} -> {new_path}")
    
    # 保存更新后的systems.json
    with open('systems.json', 'w', encoding='utf-8') as f:
        json.dump(systems, f, ensure_ascii=False, indent=2)
    
    print("✅ 系统记录已更新")

def migrate_upload_files():
    """迁移上传文件到新的uploads目录"""
    print("\n=== 迁移上传文件 ===")
    
    # 查找tar.gz文件（上传的原始文件）
    upload_files = []
    for file in os.listdir('.'):
        if file.endswith('.tar.gz') and 'sfainfo' in file:
            upload_files.append(file)
    
    # 移动到新的uploads目录
    for upload_file in upload_files:
        new_path = f"data/uploads/{upload_file}"
        if os.path.exists(upload_file):
            shutil.move(upload_file, new_path)
            print(f"  ✅ 迁移上传文件: {upload_file} -> {new_path}")

def create_directory_readme():
    """为每个目录创建README说明文件"""
    print("\n=== 创建目录说明文件 ===")
    
    # 主目录README
    main_readme = """# DCAM 数据目录结构

## 目录说明

- `customers/` - 按客户组织的系统数据
- `uploads/` - 原始上传的sfainfo文件
- `backups/` - 备份文件

## 客户目录结构

每个客户目录包含该客户的所有系统：
```
customers/
├── {客户名称}/
│   ├── {系统名称}/
│   │   ├── {系统名称}_clusters.yaml  # 系统配置文件
│   │   └── reports/                    # 系统报告文件
│   └── ...
```

## 文件命名规则

- 系统配置文件：`{系统名称}_clusters.yaml`
- 报告文件：存放在对应系统的 `reports/` 目录中
"""
    
    with open('data/README.md', 'w', encoding='utf-8') as f:
        f.write(main_readme)
    print("✅ 创建主目录说明文件: data/README.md")
    
    # 为每个客户目录创建README
    with open('customers.json', 'r', encoding='utf-8') as f:
        customers = json.load(f)
    
    for customer_info in customers.values():
        customer_name = customer_info['name']
        customer_readme = f"""# {customer_name} 系统数据

## 客户信息
- 客户名称：{customer_info['name']}
- 联系人：{customer_info.get('contact', 'N/A')}
- 邮箱：{customer_info.get('email', 'N/A')}
- 描述：{customer_info.get('description', 'N/A')}

## 系统列表

每个系统目录包含：
- `{{}}_clusters.yaml` - 系统配置和设备信息
- `reports/` - 系统分析报告和历史记录
"""
        
        readme_path = f"data/customers/{customer_name}/README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(customer_readme)
        print(f"✅ 创建客户说明文件: {readme_path}")

def print_migration_summary(backup_dir, migrated_files):
    """打印迁移总结"""
    print("\n" + "="*60)
    print("📁 文件结构迁移完成！")
    print("="*60)
    
    print(f"\n📋 迁移统计：")
    print(f"  • 备份目录：{backup_dir}")
    print(f"  • 迁移的YAML文件：{len(migrated_files)} 个")
    
    print(f"\n📂 新的目录结构：")
    print("data/")
    print("├── customers/          # 客户数据")
    
    # 显示实际的客户-系统结构
    with open('customers.json', 'r', encoding='utf-8') as f:
        customers = json.load(f)
    
    with open('systems.json', 'r', encoding='utf-8') as f:
        systems = json.load(f)
    
    for customer_info in customers.values():
        customer_name = customer_info['name']
        print(f"│   ├── {customer_name}/")
        
        customer_systems = [s for s in systems.values() if s['customer_name'] == customer_name]
        for i, system in enumerate(customer_systems):
            is_last = i == len(customer_systems) - 1
            prefix = "│   │   └──" if is_last else "│   │   ├──"
            system_name = system['name']
            print(f"{prefix} {system_name}/")
            if not is_last:
                print(f"│   │   │   ├── {system_name}_clusters.yaml")
                print(f"│   │   │   └── reports/")
            else:
                print(f"│   │       ├── {system_name}_clusters.yaml")
                print(f"│   │       └── reports/")
    
    print("├── uploads/            # 原始上传文件")
    print("└── backups/            # 备份文件")
    
    print(f"\n✅ 优势：")
    print("  • 📁 按客户-系统层级组织，便于管理")
    print("  • 🔍 快速定位特定客户的系统数据")
    print("  • 📊 每个系统有独立的报告目录")
    print("  • 🔒 备份和上传文件分离存储")
    print("  • 📝 每个目录都有详细说明文档")

def main():
    """主函数"""
    print("🔄 开始文件结构迁移...")
    
    try:
        # 1. 创建目录结构
        create_hierarchical_structure()
        
        # 2. 备份当前文件
        backup_dir, yaml_files = backup_current_files()
        
        # 3. 迁移YAML文件
        migrated_files = migrate_yaml_files()
        
        # 4. 更新系统记录
        update_system_records(migrated_files)
        
        # 5. 迁移上传文件
        migrate_upload_files()
        
        # 6. 创建说明文档
        create_directory_readme()
        
        # 7. 显示迁移总结
        print_migration_summary(backup_dir, migrated_files)
        
    except Exception as e:
        print(f"\n❌ 迁移过程中出现错误: {e}")
        print("请检查错误信息并重试")
        return False
    
    return True

if __name__ == "__main__":
    main()