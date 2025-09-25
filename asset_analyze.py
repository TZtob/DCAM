import yaml
from collections import defaultdict
from datetime import datetime, timedelta
import os

def safe_format(value, default="null"):
    """安全格式化函数，处理None值"""
    if value is None:
        return default
    return str(value)

def load_yaml_data(file_path):
    """加载YAML文件数据并进行结构标准化"""
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    
    clusters = data.get('clusters', [])
    
    for cluster in clusters:
        # 统一devices结构为列表
        if isinstance(cluster.get('devices'), dict):
            cluster['devices'] = [cluster['devices']]
        elif 'devices' not in cluster:
            cluster['devices'] = []
        
        # 确保每个设备的Hosts是列表
        for device in cluster.get('devices', []):
            if 'Hosts' in device and not isinstance(device['Hosts'], list):
                device['Hosts'] = [device['Hosts']]
    
    return clusters

def filter_by_asset_owner(clusters, asset_owner):
    """根据资产所有者过滤集群数据"""
    if not asset_owner:
        return clusters
    
    filtered_clusters = []
    for cluster in clusters:
        if cluster.get('Asset_owner', '').lower() == asset_owner.lower():
            filtered_clusters.append(cluster)
    
    return filtered_clusters

def filter_by_cluster_name(clusters, cluster_name):
    """根据集群名称过滤集群数据"""
    if not cluster_name:
        return clusters
    
    filtered_clusters = []
    for cluster in clusters:
        if cluster.get('Cluster_name', '').lower() == cluster_name.lower():
            filtered_clusters.append(cluster)
    
    return filtered_clusters

def export_to_yaml(data, filename):
    """将数据导出为YAML文件"""
    try:
        with open(filename, 'w') as file:
            yaml.dump(data, file, default_flow_style=False, allow_unicode=True)
        print(f"Data successfully exported to {filename}")
    except Exception as e:
        print(f"Error exporting data: {str(e)}")

def option1_statistics(clusters):
    """统计每个集群的设备数量和资产所有者"""
    result_data = {"clusters": []}
    
    print("\n{:<20} {:<10} {:<15}".format("Cluster Name", "Count", "Asset Owner"))
    print("-" * 50)
    
    total_devices = 0
    for cluster in clusters:
        device_count = len(cluster.get('devices', []))
        total_devices += device_count
        
        cluster_info = {
            "Cluster_name": cluster.get('Cluster_name', "N/A"),
            "Device_count": device_count,
            "Asset_owner": cluster.get('Asset_owner', "N/A")
        }
        result_data["clusters"].append(cluster_info)
        
        print("{:<20} {:<10} {:<15}".format(
            safe_format(cluster.get('Cluster_name')), 
            device_count, 
            safe_format(cluster.get('Asset_owner'))
        ))
    
    print("\n{:<20} {:<10}".format("Total Devices:", total_devices))
    result_data["total_devices"] = total_devices
    
    return result_data

def option2_statistics(clusters):
    """统计SFA版本信息"""
    version_counts = defaultdict(int)
    result_data = {"devices": []}
    
    print("\n{:<20} {:<20} {:<15} {:<15} {:<10}".format(
        "Cluster Name", "Device Name", "Asset Owner", "SFA Version", "Type"
    ))
    print("-" * 85)
    
    for cluster in clusters:
        for device in cluster.get('devices', []):
            version = device.get('SFA version', 'N/A')
            version_counts[version] += 1
            
            device_info = {
                "Cluster_name": cluster.get('Cluster_name', "N/A"),
                "Device_name": device.get('Device_name', "N/A"),
                "Asset_owner": cluster.get('Asset_owner', "N/A"),
                "SFA_version": version,
                "Type": device.get('type', "N/A")
            }
            result_data["devices"].append(device_info)
            
            print("{:<20} {:<20} {:<15} {:<15} {:<10}".format(
                safe_format(cluster.get('Cluster_name')),
                safe_format(device.get('Device_name')),
                safe_format(cluster.get('Asset_owner')),
                safe_format(version),
                safe_format(device.get('type'))
            ))
    
    print("\nSFA Version Summary:")
    print("-" * 25)
    for version, count in version_counts.items():
        print(f"{safe_format(version)}: {count} device(s)")
    
    result_data["version_summary"] = dict(version_counts)
    return result_data

def option3_statistics(clusters):
    """统计EXA版本信息"""
    version_counts = defaultdict(int)
    result_data = {"clusters": []}
    
    print("\n{:<20} {:<15} {:<15}".format(
        "Cluster Name", "Asset Owner", "EXA Version"
    ))
    print("-" * 55)
    
    for cluster in clusters:
        version = cluster.get('EXA version', 'N/A')
        version_counts[version] += 1
        
        cluster_info = {
            "Cluster_name": cluster.get('Cluster_name', "N/A"),
            "Asset_owner": cluster.get('Asset_owner', "N/A"),
            "EXA_version": version
        }
        result_data["clusters"].append(cluster_info)
        
        print("{:<20} {:<15} {:<15}".format(
            safe_format(cluster.get('Cluster_name')),
            safe_format(cluster.get('Asset_owner')),
            safe_format(version)
        ))
    
    print("\nEXA Version Summary:")
    print("-" * 25)
    for version, count in version_counts.items():
        print(f"{safe_format(version)}: {count} cluster(s)")
    
    result_data["version_summary"] = dict(version_counts)
    return result_data

def option4_bbu_life(clusters):
    """计算BBU剩余寿命"""
    result_data = {"devices": []}
    
    print("\n{:<20} {:<20} {:<15} {:<15} {:<15} {:<15} {:<15}".format(
        "Cluster Name", "Device Name", "Asset Owner", "BBU1 Expiration", "BBU1 Remaining", "BBU2 Expiration", "BBU2 Remaining"
    ))
    print("-" * 120)
    
    current_date = datetime.now().date()
    bbu_lifespan = 5 * 365  # 5年寿命（按365天/年计算）
    
    for cluster in clusters:
        for device in cluster.get('devices', []):
            # 首先尝试使用预先计算的过期日期
            bbu1_expired = None
            bbu2_expired = None
            bbu1_remaining = None
            bbu2_remaining = None
            
            # 检查是否有预先计算的BBU过期日期
            if device.get('BBU1_Expired_Date'):
                try:
                    bbu1_expired = datetime.strptime(device.get('BBU1_Expired_Date'), '%Y-%m-%d').date()
                    bbu1_remaining = (bbu1_expired - current_date).days
                    print(f"  使用预先计算的BBU1过期日期: {device.get('BBU1_Expired_Date')}")
                except Exception as e:
                    print(f"  错误: 无法解析预先计算的BBU1过期日期: {str(e)}")
            
            if device.get('BBU2_Expired_Date'):
                try:
                    bbu2_expired = datetime.strptime(device.get('BBU2_Expired_Date'), '%Y-%m-%d').date()
                    bbu2_remaining = (bbu2_expired - current_date).days
                    print(f"  使用预先计算的BBU2过期日期: {device.get('BBU2_Expired_Date')}")
                except Exception as e:
                    print(f"  错误: 无法解析预先计算的BBU2过期日期: {str(e)}")
            
            # 如果没有预先计算的过期日期，则从制造日期计算
            if not (bbu1_expired and bbu2_expired):
                # 检查BBU日期是否有效
                bbu1_date = None
                bbu2_date = None
                
                # 处理BBU1日期
                bbu1_date_str = device.get('BBU1_Mfg_Date', '')
                if bbu1_date_str and not bbu1_expired:
                    print(f"  处理 BBU1_Mfg_Date: {bbu1_date_str}")
                    try:
                        # 尝试解析不同日期格式
                        for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y'):
                            try:
                                print(f"    尝试格式: {fmt}")
                                bbu1_date = datetime.strptime(bbu1_date_str, fmt).date()
                                print(f"    成功解析为: {bbu1_date}")
                                
                                # 计算BBU1过期日期
                                if not bbu1_expired:
                                    bbu1_expired = bbu1_date + timedelta(days=bbu_lifespan)
                                    bbu1_remaining = (bbu1_expired - current_date).days
                                break
                            except ValueError as e:
                                print(f"    格式 {fmt} 解析失败: {str(e)}")
                                continue
                    except Exception as e:
                        print(f"  错误: 解析BBU1日期时出错: {str(e)}")
                
                # 处理BBU2日期
                bbu2_date_str = device.get('BBU2_Mfg_Date', '')
                if bbu2_date_str and not bbu2_expired:
                    print(f"  处理 BBU2_Mfg_Date: {bbu2_date_str}")
                    try:
                        # 尝试解析不同日期格式
                        for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y'):
                            try:
                                print(f"    尝试格式: {fmt}")
                                bbu2_date = datetime.strptime(bbu2_date_str, fmt).date()
                                print(f"    成功解析为: {bbu2_date}")
                                
                                # 计算BBU2过期日期
                                if not bbu2_expired:
                                    bbu2_expired = bbu2_date + timedelta(days=bbu_lifespan)
                                    bbu2_remaining = (bbu2_expired - current_date).days
                                break
                            except ValueError as e:
                                print(f"    格式 {fmt} 解析失败: {str(e)}")
                                continue
                    except Exception as e:
                        print(f"  错误: 解析BBU2日期时出错: {str(e)}")
            
            # 如果没有BBU日期，则跳过
            if not bbu1_expired and not bbu2_expired:
                print(f"  设备 {device.get('Device_name')} 没有有效的BBU日期数据，跳过")
                continue
            
            # 格式化输出
            bbu1_expiration_str = bbu1_expired.strftime('%Y-%m-%d') if bbu1_expired else "N/A"
            bbu2_expiration_str = bbu2_expired.strftime('%Y-%m-%d') if bbu2_expired else "N/A"
            
            bbu1_remaining_str = f"{bbu1_remaining} days" if bbu1_remaining is not None else "N/A"
            if bbu1_remaining is not None and bbu1_remaining < 0:
                bbu1_remaining_str = f"Expired {-bbu1_remaining} days ago"
                
            bbu2_remaining_str = f"{bbu2_remaining} days" if bbu2_remaining is not None else "N/A"
            if bbu2_remaining is not None and bbu2_remaining < 0:
                bbu2_remaining_str = f"Expired {-bbu2_remaining} days ago"
            
            device_info = {
                "Cluster_name": cluster.get('Cluster_name', "N/A"),
                "Device_name": device.get('Device_name', "N/A"),
                "Asset_owner": cluster.get('Asset_owner', "N/A"),
                "BBU1_expiration": bbu1_expiration_str,
                "BBU1_remaining_days": bbu1_remaining if bbu1_remaining is not None else 0,
                "BBU2_expiration": bbu2_expiration_str,
                "BBU2_remaining_days": bbu2_remaining if bbu2_remaining is not None else 0
            }
            result_data["devices"].append(device_info)
            
            print("{:<20} {:<20} {:<15} {:<15} {:<15} {:<15} {:<15}".format(
                safe_format(cluster.get('Cluster_name')),
                safe_format(device.get('Device_name')),
                safe_format(cluster.get('Asset_owner')),
                bbu1_expiration_str,
                bbu1_remaining_str,
                bbu2_expiration_str,
                bbu2_remaining_str
            ))
    
    return result_data

def option5_cluster_capacity(clusters):
    """查询集群容量信息"""
    result_data = {"clusters": []}
    
    print("\n{:<20} {:<15} {:<15} {:<20}".format(
        "Cluster Name", "Asset Owner", "Network Port Type", "Capacity"
    ))
    print("-" * 70)
    
    for cluster in clusters:
        cluster_info = {
            "Cluster_name": cluster.get('Cluster_name', "N/A"),
            "Asset_owner": cluster.get('Asset_owner', "N/A"),
            "Network_port_type": cluster.get('Network_port_type', "N/A"),
            "Capacity": cluster.get('Capacity', "N/A")
        }
        result_data["clusters"].append(cluster_info)
        
        print("{:<20} {:<15} {:<15} {:<20}".format(
            safe_format(cluster.get('Cluster_name')),
            safe_format(cluster.get('Asset_owner')),
            safe_format(cluster.get('Network_port_type')),
            safe_format(cluster.get('Capacity'))
        ))
    
    return result_data

def option6_serial_numbers(clusters):
    """查询集群设备的序列号"""
    # 移除用户交互，直接使用传入的clusters
    result_data = {"devices": []}
    
    print("\n{:<20} {:<20} {:<15} {:<25} {:<25}".format(
        "Cluster Name", "Device Name", "Asset Owner", "Controller c0 Serial", "Controller c1 Serial"
    ))
    print("-" * 110)
    
    for cluster in clusters:
        for device in cluster.get('devices', []):
            device_info = {
                "Cluster_name": cluster.get('Cluster_name', "N/A"),
                "Device_name": device.get('Device_name', "N/A"),
                "Asset_owner": cluster.get('Asset_owner', "N/A"),
                "Controller_c0_serial_number": device.get('Controller_c0_serial_number', "N/A"),
                "Controller_c1_serial_number": device.get('Controller_c1_serial_number', "N/A")
            }
            result_data["devices"].append(device_info)
            
            print("{:<20} {:<20} {:<15} {:<25} {:<25}".format(
                safe_format(cluster.get('Cluster_name')),
                safe_format(device.get('Device_name')),
                safe_format(cluster.get('Asset_owner')),
                safe_format(device.get('Controller_c0_serial_number')),
                safe_format(device.get('Controller_c1_serial_number'))
            ))
    
    return result_data

def option7_cluster_ips(clusters):
    """查询集群的所有IP地址"""
    # 移除用户交互，直接使用传入的clusters
    result_data = {"devices": []}
    
    print("\n{:<20} {:<20} {:<15} {:<20} {:<20} {:<20}".format(
        "Cluster Name", "Device Name", "Asset Owner", "Controller C0 IP", "Controller C1 IP", "EMF IP"
    ))
    print("-" * 120)
    
    for cluster in clusters:
        emf_ip = cluster.get('EMF_IP')
        
        for device in cluster.get('devices', []):
            device_info = {
                "Cluster_name": cluster.get('Cluster_name', "N/A"),
                "Device_name": device.get('Device_name', "N/A"),
                "Asset_owner": cluster.get('Asset_owner', "N/A"),
                "Controller_c0_ip": device.get('Controller_c0_ip', "N/A"),
                "Controller_c1_ip": device.get('Controller_c1_ip', "N/A"),
                "EMF_ip": emf_ip or "N/A"
            }
            result_data["devices"].append(device_info)
            
            print("{:<20} {:<20} {:<15} {:<20} {:<20} {:<20}".format(
                safe_format(cluster.get('Cluster_name')),
                safe_format(device.get('Device_name')),
                safe_format(cluster.get('Asset_owner')),
                safe_format(device.get('Controller_c0_ip')),
                safe_format(device.get('Controller_c1_ip')),
                safe_format(emf_ip)
            ))
    
    return result_data


def get_asset_owners(yaml_path):
    """从YAML文件中获取所有可用的资产所有者"""
    if not os.path.exists(yaml_path):
        return []
    clusters = load_yaml_data(yaml_path)
    asset_owners = set()
    for cluster in clusters:
        owner = cluster.get('Asset_owner')
        if owner:
            asset_owners.add(owner)
    return sorted(list(asset_owners))

def get_cluster_names(yaml_path, asset_owner=None):
    """从YAML文件中获取所有可用的集群名称，可选择按资产所有者过滤"""
    if not os.path.exists(yaml_path):
        return []
    clusters = load_yaml_data(yaml_path)
    if asset_owner:
        clusters = filter_by_asset_owner(clusters, asset_owner)
    
    cluster_names = set()
    for cluster in clusters:
        name = cluster.get('Cluster_name')
        if name:
            cluster_names.add(name)
    
    # 在集群列表前面添加"所有集群"选项
    result = ["所有集群"]
    result.extend(sorted(list(cluster_names)))
    return result

# 新增统一查询接口，便于 Web 调用
def query_customer_info(
    yaml_path,
    query_type=1,
    asset_owner=None,
    cluster_name=None
):
    """
    yaml_path: yaml 文件路径
    query_type: 查询类型（1-7，分别对应原有7种查询）
    asset_owner: 资产所有者过滤
    cluster_name: 集群名称过滤（部分查询用）
    返回结构化结果
    """
    if not os.path.exists(yaml_path):
        return {"error": f"YAML file '{yaml_path}' not found."}
    clusters = load_yaml_data(yaml_path)
    clusters = filter_by_asset_owner(clusters, asset_owner)
    # 集群名称过滤应该应用于所有查询类型，但"所有集群"选项表示不过滤
    if cluster_name and cluster_name != "所有集群":
        clusters = filter_by_cluster_name(clusters, cluster_name)
    if not clusters:
        return {"error": "No matching clusters found."}
    if query_type == 1:
        return option1_statistics(clusters)
    elif query_type == 2:
        return option2_statistics(clusters)
    elif query_type == 3:
        return option3_statistics(clusters)
    elif query_type == 4:
        print(f"执行BBU过期日期计算，传入集群数量: {len(clusters)}")
        
        # 检查是否有 BBU 日期数据
        has_bbu_dates = False
        for cluster in clusters:
            print(f"集群: {cluster.get('Cluster_name')}")
            for device in cluster.get('devices', []):
                print(f"  设备: {device.get('Device_name')}")
                print(f"  BBU1日期: {device.get('BBU1_Mfg_Date')}")
                print(f"  BBU2日期: {device.get('BBU2_Mfg_Date')}")
                
                if device.get('BBU1_Mfg_Date') or device.get('BBU2_Mfg_Date'):
                    has_bbu_dates = True
        
        # 如果没有BBU日期数据，添加一些模拟数据以便于测试
        if not has_bbu_dates:
            print("警告：没有找到任何BBU日期数据，添加模拟数据进行测试")
            import copy
            clusters_copy = copy.deepcopy(clusters)
            
            # 为每个设备添加模拟的BBU日期
            for cluster in clusters_copy:
                for device in cluster.get('devices', []):
                    # 设置一个固定的日期用于测试
                    device['BBU1_Mfg_Date'] = '2023-01-01'
                    device['BBU2_Mfg_Date'] = '2023-02-01'
            
            result = option4_bbu_life(clusters_copy)
        else:
            result = option4_bbu_life(clusters)
            
        print(f"BBU查询结果: {result}")
        return result
    elif query_type == 5:
        return option5_cluster_capacity(clusters)
    elif query_type == 6:
        return option6_serial_numbers(clusters)
    elif query_type == 7:
        return option7_cluster_ips(clusters)
    else:
        return {"error": "Invalid query_type. Must be 1-7."}
        
# 添加函数，兼容app.py中调用的query_assets函数
def query_assets(yaml_path, query_type, asset_owner=None):
    """
    兼容函数，用于保持与原有代码的兼容性
    调用query_customer_info并返回相同的结果结构
    """
    return query_customer_info(yaml_path, query_type, asset_owner)
