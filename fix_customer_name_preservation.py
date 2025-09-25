#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复客户名在YAML更新中丢失的问题
"""

import os
import yaml
import sys
import logging
from datetime import datetime
import shutil

def update_generate_cluster_yaml():
    """更新generate_cluster_yaml函数确保正确处理客户名"""
    # 读取原始文件
    with open('generate_cluster_yaml.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原始文件
    backup_file = f"generate_cluster_yaml.py.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
    shutil.copy2('generate_cluster_yaml.py', backup_file)
    print(f"已备份原始文件到: {backup_file}")
    
    # 确保函数签名包含customer_name参数
    if "def generate_cluster_yaml(toml_path, cluster_name, sfainfo_paths=None, output_path=" not in content:
        print("错误: 未找到正确的函数签名，请手动更新")
        return False
    
    # 确保函数签名中有客户名参数
    if "customer_name=None" not in content:
        content = content.replace(
            "def generate_cluster_yaml(toml_path, cluster_name, sfainfo_paths=None, output_path=\"generated_clusters.yaml\")",
            "def generate_cluster_yaml(toml_path, cluster_name, sfainfo_paths=None, output_path=\"generated_clusters.yaml\", customer_name=None)"
        )
        print("已添加customer_name参数到函数签名")
    
    # 修改客户名处理逻辑
    yaml_gen_section = """
    # 生成YAML文件，确保正确缩进
    with open(output_path, 'w', encoding='utf-8') as f:
        # 创建自定义Dumper以确保正确的缩进
        class IndentedDumper(yaml.Dumper):
            def increase_indent(self, flow=False, indentless=False):
                return super(IndentedDumper, self).increase_indent(flow, False)
        
        # 构建顶层数据结构
        output_data = {"clusters": [cluster]}
        
        # 处理客户名信息
        if customer_name:
            # 优先使用传入的客户名
            output_data["customer"] = customer_name
            print(f"使用传入的客户名: {customer_name}")
        else:
            # 如果没有传入客户名，尝试从原始文件读取
            try:
                # 读取之前我们需要检查文件是否存在，这样才能处理第一次生成的情况
                if os.path.exists(output_path):
                    with open(output_path, 'r', encoding='utf-8') as orig_file:
                        orig_data = yaml.safe_load(orig_file)
                        if orig_data and 'customer' in orig_data:
                            output_data["customer"] = orig_data["customer"]
                            print(f"从原始YAML文件中保留客户名: {orig_data['customer']}")
            except Exception as e:
                print(f"读取原始客户名失败: {str(e)}")
        
        # 检查最终是否有客户名
        if "customer" not in output_data:
            print("警告: 未能获取客户名，生成的YAML将不包含客户信息")
        
        # dump时使用自定义Dumper并设置缩进
        yaml.dump(
            output_data,
            f,
            Dumper=IndentedDumper,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
            indent=2,
            width=1000  # 增加宽度限制避免不必要的换行
        )
"""
    
    # 寻找并替换YAML生成部分
    start_marker = "    # 生成YAML文件，确保正确缩进"
    end_marker = "        )"
    
    start_pos = content.find(start_marker)
    if start_pos == -1:
        print("错误: 未找到YAML生成代码的开始部分")
        return False
    
    # 找到结束位置
    end_pos = content.find(end_marker, start_pos)
    if end_pos == -1:
        print("错误: 未找到YAML生成代码的结束部分")
        return False
    
    end_pos = content.find("\n", end_pos) + 1  # 包含整行
    
    # 替换代码
    new_content = content[:start_pos] + yaml_gen_section + content[end_pos:]
    
    # 写回文件
    with open('generate_cluster_yaml.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("已更新generate_cluster_yaml.py，添加了客户名处理逻辑")
    return True

def update_app_update_config():
    """更新app.py中的update_system_config函数处理客户名"""
    # 读取app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原始文件
    backup_file = f"app.py.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
    shutil.copy2('app.py', backup_file)
    print(f"已备份原始文件到: {backup_file}")
    
    # 查找update_system_config函数中调用generate_cluster_yaml的部分
    update_section = """            # 获取客户名
            customer_name = None
            
            # 1. 尝试从系统记录获取
            if 'customer_name' in system:
                customer_name = system['customer_name']
                logging.info(f"从系统记录获取到客户名: {customer_name}")
            
            # 2. 从客户记录获取
            elif 'customer_id' in system:
                customers = get_customers()
                if system['customer_id'] in customers:
                    customer_name = customers[system['customer_id']].get('name')
                    logging.info(f"从客户表获取到客户名: {customer_name}")
            
            # 3. 从原YAML文件获取
            if not customer_name and os.path.exists(output_filename):
                try:
                    with open(output_filename, 'r', encoding='utf-8') as f:
                        yaml_data = yaml.safe_load(f)
                        if yaml_data and 'customer' in yaml_data:
                            customer_name = yaml_data['customer']
                            logging.info(f"从原始YAML文件获取到客户名: {customer_name}")
                except Exception as e:
                    logging.warning(f"读取原始YAML文件获取客户名失败: {str(e)}")
            
            # 调用生成函数，直接传递客户名参数
            try:
                generate_cluster_yaml(toml_path, cluster_name, sfa_paths, output_filename, customer_name)
                
                # 记录结果
                if customer_name:
                    logging.info(f"已完成系统配置更新，保留了客户名: {customer_name}")
                else:
                    logging.warning("已完成系统配置更新，但未能保留客户名")"""
    
    # 查找需替换的部分
    markers = [
        "            # 读取原始YAML，获取客户名",
        "            # 调用生成函数",
        "            try:",
        "                generate_cluster_yaml("
    ]
    
    replace_start = None
    for marker in markers:
        pos = content.find(marker)
        if pos != -1:
            replace_start = pos
            break
    
    if replace_start is None:
        print("错误: 未找到需要替换的代码位置")
        return False
    
    # 找到替换结束点
    replace_end_markers = [
        "                if customer_name:",
        "                # 如果有客户名，确保更新后",
        "                flash('系统配置已成功更新'"
    ]
    
    replace_end = None
    for marker in replace_end_markers:
        pos = content.find(marker, replace_start)
        if pos != -1:
            replace_end = pos
            break
    
    if replace_end is None:
        print("错误: 未找到需要替换的代码结束位置")
        return False
    
    # 替换代码
    new_content = content[:replace_start] + update_section + content[replace_end:]
    
    # 写回文件
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("已更新app.py中的客户名处理逻辑")
    return True

def create_direct_fix():
    """创建一个即时修复脚本来更新现有YAML文件添加客户名"""
    # 读取系统数据
    try:
        import json
        with open('systems.json', 'r', encoding='utf-8') as f:
            systems = json.load(f)
            
        with open('customers.json', 'r', encoding='utf-8') as f:
            customers = json.load(f)
            
        print(f"找到 {len(systems)} 个系统记录和 {len(customers)} 个客户记录")
        
        # 获取系统和客户对应关系
        fixed = 0
        for system_id, system in systems.items():
            if not system.get('yaml_file') or not os.path.exists(system.get('yaml_file')):
                continue
                
            yaml_path = system.get('yaml_file')
            
            try:
                # 读取YAML
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    yaml_data = yaml.safe_load(f)
                
                # 检查是否已有客户名
                if yaml_data and 'customer' in yaml_data:
                    continue  # 已有客户名，跳过
                    
                # 获取客户名
                customer_name = None
                
                # 从系统记录获取
                if 'customer_name' in system:
                    customer_name = system['customer_name']
                
                # 从客户表获取
                elif 'customer_id' in system and system['customer_id'] in customers:
                    customer_name = customers[system['customer_id']].get('name')
                
                # 如果找到了客户名，更新YAML
                if customer_name:
                    yaml_data['customer'] = customer_name
                    
                    # 写回文件
                    with open(yaml_path, 'w', encoding='utf-8') as f:
                        yaml.dump(yaml_data, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
                        
                    print(f"已更新 {yaml_path} 添加客户名: {customer_name}")
                    fixed += 1
                    
            except Exception as e:
                print(f"处理 {yaml_path} 时出错: {str(e)}")
                
        print(f"已修复 {fixed} 个YAML文件，添加了客户名")
        
    except Exception as e:
        print(f"创建直接修复脚本失败: {str(e)}")
        return False
        
    return True

if __name__ == "__main__":
    print("正在修复系统配置更新丢失客户名的问题...")
    
    # 更新generate_cluster_yaml.py
    if update_generate_cluster_yaml():
        print("✅ 已成功更新generate_cluster_yaml.py")
    else:
        print("❌ 更新generate_cluster_yaml.py失败")
    
    # 更新app.py
    if update_app_update_config():
        print("✅ 已成功更新app.py")
    else:
        print("❌ 更新app.py失败")
    
    # 创建直接修复脚本
    print("\n正在检查和修复现有YAML文件...")
    if create_direct_fix():
        print("✅ 现有YAML文件检查和修复完成")
    else:
        print("❌ 现有YAML文件检查和修复失败")
    
    print("\n修复完成，请重启应用程序让修改生效")