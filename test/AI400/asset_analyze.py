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
    with open(file_path, 'r') as file:
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
            "Cluster_name": cluster.get('Cluster_name'),
            "Device_count": device_count,
            "Asset_owner": cluster.get('Asset_owner')
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
                "Cluster_name": cluster.get('Cluster_name'),
                "Device_name": device.get('Device_name'),
                "Asset_owner": cluster.get('Asset_owner'),
                "SFA_version": version,
                "Type": device.get('type')
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
            "Cluster_name": cluster.get('Cluster_name'),
            "Asset_owner": cluster.get('Asset_owner'),
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
    
    print("\n{:<20} {:<20} {:<15} {:<15} {:<15}".format(
        "Cluster Name", "Device Name", "Asset Owner", "BBU Expiration", "Remaining Days"
    ))
    print("-" * 90)
    
    current_date = datetime.now().date()
    bbu_lifespan = 5 * 365  # 5年寿命（按365天/年计算）
    
    for cluster in clusters:
        for device in cluster.get('devices', []):
            # 检查BBU日期是否有效
            bbu_dates = []
            for bbu_key in ['BBU1_Mfg_Date', 'BBU2_Mfg_Date']:
                bbu_date_str = device.get(bbu_key, '')
                if bbu_date_str:
                    try:
                        # 尝试解析不同日期格式
                        for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y'):
                            try:
                                bbu_date = datetime.strptime(bbu_date_str, fmt).date()
                                bbu_dates.append(bbu_date)
                                break
                            except ValueError:
                                continue
                    except Exception:
                        pass
            
            if not bbu_dates:
                continue  # 没有有效BBU日期则跳过
            
            # 使用最早的BBU日期计算过期时间
            oldest_bbu = min(bbu_dates)
            expiration_date = oldest_bbu + timedelta(days=bbu_lifespan)
            remaining_days = (expiration_date - current_date).days
            
            # 格式化输出
            expiration_str = expiration_date.strftime('%Y-%m-%d')
            remaining_str = f"{remaining_days} days"
            if remaining_days < 0:
                remaining_str = f"Expired {-remaining_days} days ago"
            
            device_info = {
                "Cluster_name": cluster.get('Cluster_name'),
                "Device_name": device.get('Device_name'),
                "Asset_owner": cluster.get('Asset_owner'),
                "BBU_expiration": expiration_str,
                "Remaining_days": remaining_days
            }
            result_data["devices"].append(device_info)
            
            print("{:<20} {:<20} {:<15} {:<15} {:<15}".format(
                safe_format(cluster.get('Cluster_name')),
                safe_format(device.get('Device_name')),
                safe_format(cluster.get('Asset_owner')),
                expiration_str,
                remaining_str
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
            "Cluster_name": cluster.get('Cluster_name'),
            "Asset_owner": cluster.get('Asset_owner'),
            "Network_port_type": cluster.get('Network_port_type'),
            "Capacity": cluster.get('Capacity')
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
    cluster_name = input("\nEnter Cluster name to query (leave empty for all): ").strip()
    
    # 根据集群名称进一步过滤
    filtered_clusters = filter_by_cluster_name(clusters, cluster_name)
    
    if not filtered_clusters:
        if cluster_name:
            print(f"No clusters found with name '{cluster_name}'")
        else:
            print("No clusters found")
        return None
    
    result_data = {"clusters": []}
    
    print("\n{:<20} {:<20} {:<15} {:<25} {:<25}".format(
        "Cluster Name", "Device Name", "Asset Owner", "Controller c0 Serial", "Controller c1 Serial"
    ))
    print("-" * 110)
    
    for cluster in filtered_clusters:
        cluster_info = {
            "Cluster_name": cluster.get('Cluster_name'),
            "Asset_owner": cluster.get('Asset_owner'),
            "devices": []
        }
        
        for device in cluster.get('devices', []):
            device_info = {
                "Device_name": device.get('Device_name'),
                "Controller_c0_serial_number": device.get('Controller_c0_serial_number'),
                "Controller_c1_serial_number": device.get('Controller_c1_serial_number')
            }
            cluster_info["devices"].append(device_info)
            
            print("{:<20} {:<20} {:<15} {:<25} {:<25}".format(
                safe_format(cluster.get('Cluster_name')),
                safe_format(device.get('Device_name')),
                safe_format(cluster.get('Asset_owner')),
                safe_format(device.get('Controller_c0_serial_number')),
                safe_format(device.get('Controller_c1_serial_number'))
            ))
        
        result_data["clusters"].append(cluster_info)
    
    return result_data

def option7_cluster_ips(clusters):
    """查询集群的所有IP地址"""
    cluster_name = input("\nEnter Cluster name to query (leave empty for all): ").strip()
    
    # 根据集群名称进一步过滤
    filtered_clusters = filter_by_cluster_name(clusters, cluster_name)
    
    if not filtered_clusters:
        if cluster_name:
            print(f"No clusters found with name '{cluster_name}'")
        else:
            print("No clusters found")
        return None
    
    result_data = {"clusters": []}
    
    for cluster in filtered_clusters:
        cluster_info = {
            "Cluster_name": cluster.get('Cluster_name'),
            "EMF_IP": cluster.get('EMF_IP'),
            "devices": []
        }
        
        print(f"\nCluster Name: {safe_format(cluster.get('Cluster_name'))}")
        print(f"EMF_IP: {safe_format(cluster.get('EMF_IP'))}")
        print("-" * 50)
        
        for device in cluster.get('devices', []):
            device_info = {
                "Device_name": device.get('Device_name'),
                "Controller_c0_ip": device.get('Controller_c0_ip'),
                "Controller_c1_ip": device.get('Controller_c1_ip'),
                "hosts": []
            }
            
            print(f"Device Name: {safe_format(device.get('Device_name'))}")
            print(f"  Controller_c0_ip: {safe_format(device.get('Controller_c0_ip'))}")
            print(f"  Controller_c1_ip: {safe_format(device.get('Controller_c1_ip'))}")
            print("  Hosts:")
            
            for host in device.get('Hosts', []):
                host_info = {
                    "hostname": host.get('hostname'),
                    "ip": host.get('ip', {})
                }
                device_info["hosts"].append(host_info)
                
                print(f"    Hostname: {safe_format(host.get('hostname'))}")
                ip_info = host.get('ip', {})
                for key, value in ip_info.items():
                    print(f"      {key}: {safe_format(value)}")
            
            cluster_info["devices"].append(device_info)
        
        result_data["clusters"].append(cluster_info)
    
    return result_data

def main():
    file_path = None
    clusters = []
    
    while True:
        print("\n===== Cluster Management System =====")
        print("0. Load YAML file")
        if file_path:
            print(f"   Current file: {file_path}")
        print("1. List device count per cluster")
        print("2. List SFA version details")
        print("3. List EXA version details")
        print("4. Calculate BBU expiration dates")
        print("5. Query cluster capacity")
        print("6. Query device serial numbers")
        print("7. Query cluster IP addresses")
        print("8. Exit")
        
        choice = input("Enter your choice (0-8): ")
        
        if choice == '0':
            # 加载YAML文件
            new_path = input("Enter YAML file path: ").strip()
            if not new_path:
                print("No file path provided.")
                continue
            
            if not os.path.exists(new_path):
                print(f"Error: File '{new_path}' not found.")
                continue
            
            try:
                clusters = load_yaml_data(new_path)
                file_path = new_path
                print(f"Successfully loaded {len(clusters)} clusters from {new_path}")
            except Exception as e:
                print(f"Error loading file: {str(e)}")
        
        elif choice in ['1', '2', '3', '4', '5', '6', '7']:
            if not clusters:
                print("Please load a YAML file first (option 0).")
                continue
            
            # 询问Asset_owner名称
            asset_owner = input("Enter Asset_owner name to query (leave empty for all): ").strip()
            filtered_clusters = filter_by_asset_owner(clusters, asset_owner)
            
            if not filtered_clusters:
                print(f"No clusters found for Asset_owner '{asset_owner}'")
                continue
            
            result_data = None
            if choice == '1':
                result_data = option1_statistics(filtered_clusters)
            elif choice == '2':
                result_data = option2_statistics(filtered_clusters)
            elif choice == '3':
                result_data = option3_statistics(filtered_clusters)
            elif choice == '4':
                result_data = option4_bbu_life(filtered_clusters)
            elif choice == '5':
                result_data = option5_cluster_capacity(filtered_clusters)
            elif choice == '6':
                result_data = option6_serial_numbers(filtered_clusters)
            elif choice == '7':
                result_data = option7_cluster_ips(filtered_clusters)
            
            # 询问是否导出结果
            if result_data is not None:
                export_choice = input("\nDo you want to export the results to a YAML file? (yes/no): ").strip().lower()
                if export_choice in ['yes', 'y']:
                    filename = input("Enter filename for export: ").strip()
                    if filename:
                        if not filename.endswith('.yaml') and not filename.endswith('.yml'):
                            filename += '.yaml'
                        export_to_yaml(result_data, filename)
        
        elif choice == '8':
            print("Exiting program.")
            break
        
        else:
            print("Invalid choice. Please enter a number between 0-8.")

if __name__ == "__main__":
    main()
