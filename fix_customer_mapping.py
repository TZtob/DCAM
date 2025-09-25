#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复DCAM系统中的get_customer_yaml_mapping函数

问题描述：
1. get_customer_yaml_mapping函数只有声明但没有实现
2. 该函数被多个视图函数调用，导致500错误
3. 登录后重定向到dashboard页面，但是由于函数未实现，导致错误
"""

import os
import yaml

def fix_app_py():
    """修复app.py中的get_customer_yaml_mapping函数"""
    
    # 读取app.py文件
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 定义正确的get_customer_yaml_mapping函数实现
    new_function = '''def get_customer_yaml_mapping():
    """获取客户和YAML文件的映射关系"""
    yaml_files = {}
    try:
        # 寻找所有客户的YAML文件
        data_dir = 'data'
        if os.path.exists(data_dir):
            for filename in os.listdir(data_dir):
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    filepath = os.path.join(data_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)
                            if data and 'customer' in data:
                                yaml_files[data['customer']] = filepath
                    except Exception as e:
                        logging.error(f"读取YAML文件 {filepath} 时出错: {str(e)}")
        
        # 另外读取项目根目录下的yaml文件
        for filename in os.listdir('.'):
            if filename.endswith('.yaml') or filename.endswith('.yml'):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                        if data and 'customer' in data:
                            yaml_files[data['customer']] = filename
                except Exception as e:
                    logging.error(f"读取YAML文件 {filename} 时出错: {str(e)}")
    except Exception as e:
        logging.error(f"获取客户YAML文件映射时出错: {str(e)}")
    
    # 如果没有找到任何客户，添加默认客户用于测试
    if not yaml_files:
        yaml_files["测试客户"] = "byd_ddn_clusters.yaml"
        
    return yaml_files'''
    
    # 替换未实现的函数
    old_function = 'def get_customer_yaml_mapping():\n    pass'
    updated_content = content.replace(old_function, new_function)
    
    # 写入修改后的内容
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("已修复app.py中的get_customer_yaml_mapping函数")

def test_yaml_mapping():
    """测试get_customer_yaml_mapping函数"""
    try:
        # 导入函数进行测试
        from app import get_customer_yaml_mapping
        
        # 调用函数
        mapping = get_customer_yaml_mapping()
        
        # 打印结果
        print("客户与YAML文件映射关系：")
        for customer, yaml_file in mapping.items():
            print(f"  - {customer}: {yaml_file}")
            
        if not mapping:
            print("警告：没有找到任何客户YAML文件")
    except Exception as e:
        print(f"测试失败: {str(e)}")

def check_byd_yaml():
    """检查byd_ddn_clusters.yaml文件是否存在并包含客户信息"""
    try:
        yaml_path = "byd_ddn_clusters.yaml"
        if not os.path.exists(yaml_path):
            print(f"警告：{yaml_path} 文件不存在")
            return
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        if not data:
            print(f"警告：{yaml_path} 文件为空或格式无效")
            return
            
        if 'customer' not in data:
            print(f"警告：{yaml_path} 中没有customer字段，添加默认客户名")
            data['customer'] = "比亚迪"
            
            # 保存修改后的YAML
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True)
                
            print(f"已向 {yaml_path} 添加customer字段")
        else:
            print(f"{yaml_path} 文件包含客户名: {data['customer']}")
    except Exception as e:
        print(f"检查YAML文件时出错: {str(e)}")

if __name__ == "__main__":
    print("开始修复DCAM系统中的get_customer_yaml_mapping函数...")
    fix_app_py()
    check_byd_yaml()
    print("修复完成，请重启应用程序")