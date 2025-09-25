#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试DCAM应用程序的基本功能
"""

import sys
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_app_import():
    """测试app.py导入"""
    try:
        import app
        logging.info("✅ app.py导入成功")
        return True
    except Exception as e:
        logging.error(f"❌ app.py导入失败: {str(e)}")
        return False

def test_key_functions():
    """测试关键函数"""
    try:
        from app import get_customer_yaml_mapping, get_customers, get_systems
        
        # 测试get_customer_yaml_mapping函数
        customers = get_customer_yaml_mapping()
        logging.info(f"✅ get_customer_yaml_mapping函数工作正常，找到 {len(customers)} 个客户")
        
        # 测试get_customers函数
        customer_data = get_customers()
        logging.info(f"✅ get_customers函数工作正常，找到 {len(customer_data)} 个客户记录")
        
        # 测试get_systems函数
        systems_data = get_systems()
        logging.info(f"✅ get_systems函数工作正常，找到 {len(systems_data)} 个系统记录")
        
        return True
    except Exception as e:
        logging.error(f"❌ 关键函数测试失败: {str(e)}")
        return False

def test_generate_cluster_yaml_import():
    """测试generate_cluster_yaml函数导入"""
    try:
        from generate_cluster_yaml import generate_cluster_yaml
        logging.info("✅ generate_cluster_yaml函数导入成功")
        return True
    except Exception as e:
        logging.error(f"❌ generate_cluster_yaml函数导入失败: {str(e)}")
        return False

def test_customer_name_in_yaml():
    """测试YAML文件是否包含客户名"""
    try:
        import yaml
        from app import get_systems
        
        systems = get_systems()
        yaml_files_checked = 0
        yaml_files_with_customer = 0
        
        for system_id, system in systems.items():
            yaml_file = system.get('yaml_file')
            if yaml_file and os.path.exists(yaml_file):
                yaml_files_checked += 1
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        yaml_data = yaml.safe_load(f)
                        if yaml_data and 'customer' in yaml_data:
                            yaml_files_with_customer += 1
                            logging.info(f"✅ YAML文件 {yaml_file} 包含客户名: {yaml_data['customer']}")
                        else:
                            logging.warning(f"⚠️ YAML文件 {yaml_file} 缺少客户名")
                except Exception as e:
                    logging.error(f"❌ 读取YAML文件 {yaml_file} 失败: {str(e)}")
        
        logging.info(f"检查了 {yaml_files_checked} 个YAML文件，其中 {yaml_files_with_customer} 个包含客户名")
        return yaml_files_checked > 0
    except Exception as e:
        logging.error(f"❌ 测试YAML文件客户名失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    logging.info("开始DCAM应用程序功能测试...")
    
    # 测试项目列表
    tests = [
        ("应用程序导入", test_app_import),
        ("关键函数", test_key_functions),
        ("generate_cluster_yaml导入", test_generate_cluster_yaml_import),
        ("YAML文件客户名", test_customer_name_in_yaml)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logging.info(f"正在测试: {test_name}")
        if test_func():
            passed += 1
        else:
            logging.error(f"测试失败: {test_name}")
    
    # 输出测试结果
    logging.info(f"测试完成: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！应用程序应该可以正常工作。")
        return True
    else:
        print(f"\n⚠️ {total - passed} 项测试失败，请检查相关问题。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)