#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import yaml
import glob
import asset_analyze

# 加载所有YAML文件
yaml_files = glob.glob('*_clusters.yaml')
print(f'找到的YAML文件: {yaml_files}')

all_clusters = []
for yaml_file in yaml_files:
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            clusters = data.get('clusters', [])
            print(f'{yaml_file}: 加载了 {len(clusters)} 个集群')
            for cluster in clusters:
                print(f'  - 集群名: {cluster.get("Cluster_name")}, Asset_owner: {cluster.get("Asset_owner")}')
            all_clusters.extend(clusters)
    except Exception as e:
        print(f'加载 {yaml_file} 时出错: {e}')

print(f'\n总共加载了 {len(all_clusters)} 个集群')

# 测试序列号查询
print('\n=== 测试设备序列号查询 ===')
result = asset_analyze.option6_serial_numbers(all_clusters)
print(f'查询结果类型: {type(result)}')
print(f'查询结果设备数量: {len(result.get("devices", []))}')
for i, device in enumerate(result.get("devices", [])[:3]):  # 只显示前3个设备
    print(f'设备 {i+1}: {device}')

# 测试IP地址查询
print('\n=== 测试IP地址查询 ===')
ip_result = asset_analyze.option7_cluster_ips(all_clusters)
print(f'IP查询结果类型: {type(ip_result)}')
print(f'IP查询结果设备数量: {len(ip_result.get("devices", []))}')
for i, device in enumerate(ip_result.get("devices", [])[:3]):  # 只显示前3个设备
    print(f'设备 {i+1}: {device}')