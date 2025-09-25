#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试系统配置更新是否正确保留客户名
"""

import os
import yaml
import sys
import logging
import tempfile
import shutil
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_test_yaml():
    """创建测试用的YAML文件，包含客户名"""
    try:
        # 创建临时目录和临时文件
        temp_dir = tempfile.mkdtemp()
        yaml_path = os.path.join(temp_dir, "test_cluster.yaml")
        
        # 创建测试YAML内容
        test_data = {
            "customer": "测试客户",
            "clusters": [
                {
                    "Cluster_name": "Test_Cluster",
                    "EXA version": "6.0.0",
                    "devices": []
                }
            ]
        }
        
        # 写入YAML文件
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_data, f, allow_unicode=True, default_flow_style=False)
            
        logging.info(f"创建测试YAML文件: {yaml_path}")
        
        return yaml_path, temp_dir
    except Exception as e:
        logging.error(f"创建测试YAML文件失败: {str(e)}")
        return None, None

def simulate_generate_cluster_yaml(yaml_path):
    """模拟调用generate_cluster_yaml函数生成新的YAML文件"""
    try:
        # 从generate_cluster_yaml模块导入函数
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from generate_cluster_yaml import generate_cluster_yaml
        
        # 创建临时的toml文件和sfainfo文件
        temp_toml = os.path.join(os.path.dirname(yaml_path), "test.toml")
        with open(temp_toml, 'w') as f:
            f.write('[exascaler]\nversion = "6.1.0"\n\n[sfa]\n[sfa.SFA01]\ncontrollers = ["10.0.0.1", "10.0.0.2"]')
        
        # 调用函数生成新的YAML文件
        cluster_name = "Updated_Cluster"
        # 不传客户名参数，测试从原始文件读取
        generate_cluster_yaml(temp_toml, cluster_name, [], yaml_path)
        
        logging.info(f"模拟更新YAML文件完成: {yaml_path}")
        
        return True
    except Exception as e:
        logging.error(f"模拟更新YAML文件失败: {str(e)}")
        return False

def check_yaml_customer(yaml_path):
    """检查YAML文件是否保留了客户名"""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # 检查客户名是否存在
        if 'customer' in data:
            customer_name = data['customer']
            logging.info(f"找到客户名: {customer_name}")
            return True, customer_name
        else:
            logging.warning("未找到客户名!")
            return False, None
    except Exception as e:
        logging.error(f"检查YAML文件失败: {str(e)}")
        return False, None

def main():
    logging.info("开始测试系统配置更新是否保留客户名")
    
    # 创建测试YAML文件
    yaml_path, temp_dir = create_test_yaml()
    if not yaml_path:
        return False
    
    try:
        # 读取原始YAML文件
        before_result, before_customer = check_yaml_customer(yaml_path)
        if not before_result:
            logging.error("测试失败: 原始YAML文件没有客户名")
            return False
        
        logging.info(f"原始客户名: {before_customer}")
        
        # 模拟更新YAML文件
        if not simulate_generate_cluster_yaml(yaml_path):
            return False
        
        # 检查更新后的YAML文件
        after_result, after_customer = check_yaml_customer(yaml_path)
        if not after_result:
            logging.error("测试失败: 更新后的YAML文件丢失了客户名")
            return False
        
        logging.info(f"更新后的客户名: {after_customer}")
        
        # 比较客户名是否一致
        if before_customer != after_customer:
            logging.error(f"测试失败: 客户名发生变化 ({before_customer} -> {after_customer})")
            return False
        
        logging.info("测试通过: 客户名成功保留")
        return True
    
    finally:
        # 清理临时目录
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logging.info(f"已清理临时目录: {temp_dir}")
            except Exception as e:
                logging.warning(f"清理临时目录失败: {str(e)}")

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 测试通过: 系统配置更新会正确保留客户名")
    else:
        print("\n❌ 测试失败: 系统配置更新可能会丢失客户名")