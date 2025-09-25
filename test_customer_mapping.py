#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试DCAM系统中修复后的get_customer_yaml_mapping函数
"""

import os
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_get_customer_yaml_mapping():
    """测试get_customer_yaml_mapping函数"""
    try:
        # 动态导入app模块
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from app import get_customer_yaml_mapping
        
        # 调用函数并获取结果
        customer_mapping = get_customer_yaml_mapping()
        
        # 输出结果
        logging.info("客户与YAML文件映射：")
        for customer, yaml_file in customer_mapping.items():
            logging.info(f"  - {customer}: {yaml_file}")
            
            # 验证文件是否存在
            if not os.path.exists(yaml_file):
                logging.warning(f"YAML文件不存在: {yaml_file}")
            
        # 返回映射结果
        return customer_mapping
    except ImportError:
        logging.error("无法导入app模块，请确认app.py文件存在")
        return None
    except Exception as e:
        logging.error(f"测试get_customer_yaml_mapping时出错: {str(e)}")
        return None

def test_customer_yaml_file(yaml_file):
    """测试YAML文件格式"""
    try:
        import yaml
        
        # 读取YAML文件
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        # 检查文件结构
        if not data:
            logging.error(f"YAML文件为空或格式无效: {yaml_file}")
            return False
            
        if 'customer' not in data:
            logging.error(f"YAML文件缺少customer字段: {yaml_file}")
            return False
            
        if 'clusters' not in data:
            logging.warning(f"YAML文件缺少clusters字段: {yaml_file}")
            
        logging.info(f"YAML文件格式正确: {yaml_file}")
        logging.info(f"  - 客户: {data['customer']}")
        if 'clusters' in data:
            logging.info(f"  - 集群数量: {len(data['clusters'])}")
            
        return True
    except Exception as e:
        logging.error(f"测试YAML文件时出错: {str(e)}")
        return False

def test_dashboard_route():
    """测试dashboard路由所需的数据"""
    try:
        # 动态导入app模块
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from app import get_customer_yaml_mapping
        
        # 获取客户映射
        customers = get_customer_yaml_mapping()
        
        # 检查映射是否为空
        if not customers:
            logging.error("客户映射为空，dashboard路由将无法正常工作")
            return False
            
        # 输出映射结果
        logging.info(f"找到 {len(customers)} 个客户，dashboard路由应该可以正常工作")
        return True
    except Exception as e:
        logging.error(f"测试dashboard路由时出错: {str(e)}")
        return False

if __name__ == "__main__":
    logging.info("开始测试get_customer_yaml_mapping函数...")
    
    # 测试get_customer_yaml_mapping函数
    customer_mapping = test_get_customer_yaml_mapping()
    
    if customer_mapping:
        # 测试第一个YAML文件
        if customer_mapping:
            first_yaml = next(iter(customer_mapping.values()))
            test_customer_yaml_file(first_yaml)
            
        # 测试dashboard路由
        test_dashboard_route()
        
    logging.info("测试完成")