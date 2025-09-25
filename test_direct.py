#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单直接地测试客户名保留功能
"""

import os
import yaml
import tempfile
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 步骤1: 创建测试YAML文件
temp_dir = tempfile.mkdtemp()
yaml_path = os.path.join(temp_dir, "test.yaml")

# 创建包含客户名的YAML数据
yaml_data = {
    "customer": "测试客户",
    "clusters": [
        {
            "Cluster_name": "Test_Cluster",
            "devices": []
        }
    ]
}

# 写入YAML文件
with open(yaml_path, 'w', encoding='utf-8') as f:
    yaml.dump(yaml_data, f, allow_unicode=True)
    
logging.info(f"已创建测试YAML文件: {yaml_path}")

# 步骤2: 导入generate_cluster_yaml函数
from generate_cluster_yaml import generate_cluster_yaml

# 步骤3: 创建简单的TOML文件
toml_path = os.path.join(temp_dir, "test.toml")
with open(toml_path, 'w', encoding='utf-8') as f:
    f.write('[exascaler]\nversion = "6.1.0"\n\n[sfa]\n[sfa.SFA01]\ncontrollers = ["10.0.0.1", "10.0.0.2"]')

# 步骤4: 调用函数处理YAML
logging.info("调用generate_cluster_yaml函数...")
generate_cluster_yaml(toml_path, "新集群名称", [], yaml_path)

# 步骤5: 验证结果
logging.info("验证处理后的YAML文件...")
with open(yaml_path, 'r', encoding='utf-8') as f:
    new_yaml = yaml.safe_load(f)

if 'customer' in new_yaml:
    logging.info(f"成功! 客户名被保留: {new_yaml['customer']}")
    print("\n✅ 测试成功: 客户名被正确保留")
else:
    logging.error("失败! 客户名丢失!")
    print("\n❌ 测试失败: 客户名丢失")

# 清理临时目录
import shutil
shutil.rmtree(temp_dir)
logging.info(f"已清理临时目录: {temp_dir}")