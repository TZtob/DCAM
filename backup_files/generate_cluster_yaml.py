import argparse
import toml
import yaml
import tarfile
import json
import os
import glob
import re
from datetime import datetime, timedelta

def calculate_bbu_expired_date(mfg_date_str):
    """
    计算BBU过期日期
    BBU过期日期 = 制造日期 + 1825天 (约5年)
    """
    if not mfg_date_str:
        return None
    
    try:
        # 解析制造日期字符串，例如: '2021-08-12T08:59:33+08:00'
        mfg_date = datetime.fromisoformat(mfg_date_str.replace('Z', '+00:00'))
        
        # 添加1825天
        expired_date = mfg_date + timedelta(days=1825)
        
        # 返回格式化的日期字符串（只保留日期部分，便于阅读）
        return expired_date.strftime('%Y-%m-%d')
        
    except Exception as e:
        print(f"    计算BBU过期日期失败: {mfg_date_str}, 错误: {e}")
        return None

def extract_network_info_from_sfainfo_files(sfainfo_files):
    """
    从所有设备的SFAClientIOC.json文件中提取Mellanox网络信息
    只处理Description中包含Mellanox的数据网络部分
    返回网络描述和端口类型
    """
    all_port_types = set()
    all_network_descriptions = set()
    
    print("提取Mellanox网络信息:")
    
    for sfainfo_file in sfainfo_files:
        print(f"  处理设备: {sfainfo_file}")
        
        try:
            with tarfile.open(sfainfo_file, 'r:gz') as tar:
                client_ioc_file = tar.extractfile('sfa-logs/SFAClientIOC.json')
                if client_ioc_file:
                    content = client_ioc_file.read().decode('utf-8')
                    client_ioc_data = json.loads(content)
                    
                    device_port_types = set()
                    device_descriptions = set()
                    mellanox_count = 0
                    
                    for item in client_ioc_data:
                        if isinstance(item, dict):
                            description = item.get('Description', '')
                            
                            # 只处理Mellanox设备（数据网络）
                            if 'mellanox' in description.lower():
                                mellanox_count += 1
                                
                                # 收集完整的Description
                                device_descriptions.add(description)
                                all_network_descriptions.add(description)
                                
                                # 收集IOCPortTypes
                                ioc_port_types = item.get('IOCPortTypes', [])
                                for port_type in ioc_port_types:
                                    device_port_types.add(port_type)
                                    all_port_types.add(port_type)
                    
                    if mellanox_count > 0:
                        print(f"    发现 {mellanox_count} 个Mellanox网口")
                        print(f"    网络描述: {len(device_descriptions)} 种")
                        print(f"    端口类型: {sorted(device_port_types)}")
                    else:
                        print(f"    未发现Mellanox网口")
                        
        except Exception as e:
            print(f"    读取SFAClientIOC失败: {e}")
    
    # 处理网络描述 - 保持完整的描述信息
    network_description_result = None
    if all_network_descriptions:
        # 如果所有描述都相同，只显示一个；否则用分号分隔
        unique_descriptions = list(all_network_descriptions)
        if len(unique_descriptions) == 1:
            network_description_result = unique_descriptions[0]
        else:
            network_description_result = '; '.join(sorted(unique_descriptions))
    
    # 转换端口类型为用户友好的格式
    friendly_port_types = []
    for port_type in sorted(all_port_types):
        if port_type == 'IOC_PORT_TYPE_INFINIBAND':
            friendly_port_types.append('InfiniBand')
        elif port_type == 'IOC_PORT_TYPE_ETHERNET':
            friendly_port_types.append('Ethernet')
        else:
            # 保留原始格式，去掉前缀
            friendly_name = port_type.replace('IOC_PORT_TYPE_', '').title()
            friendly_port_types.append(friendly_name)
    
    port_type_result = ', '.join(friendly_port_types) if friendly_port_types else None
    
    print(f"  网络描述汇总: {network_description_result}")
    print(f"  网络端口类型汇总: {port_type_result}")
    
    return network_description_result, port_type_result

def extract_device_info_from_sfainfo(sfainfo_file):
    """从sfainfo tar.gz文件中提取设备信息"""
    print(f"处理sfainfo文件: {sfainfo_file}")
    
    device_info = {
        'capacity': 0,
        'type': None,
        'sfa_version': None,
        'system_name': None,
        'controller_c0_serial': None,
        'controller_c1_serial': None,
        'bbu1_expired_date': None,
        'bbu2_expired_date': None
    }
    
    try:
        with tarfile.open(sfainfo_file, 'r:gz') as tar:
            # 1. 从BundleInfo.json提取基本信息
            try:
                bundle_info_file = tar.extractfile('sfa-logs/BundleInfo.json')
                if bundle_info_file:
                    content = bundle_info_file.read().decode('utf-8')
                    bundle_data = json.loads(content)
                    if bundle_data and len(bundle_data) > 0:
                        bundle = bundle_data[0]
                        device_info['type'] = bundle.get('Platform')
                        device_info['controller_c0_serial'] = bundle.get('Controller0Serial')
                        device_info['controller_c1_serial'] = bundle.get('Controller1Serial')
                        print(f"  设备类型: {device_info['type']}")
                        print(f"  控制器序列号: C0={device_info['controller_c0_serial']}, C1={device_info['controller_c1_serial']}")
            except Exception as e:
                print(f"    读取BundleInfo失败: {e}")
            
            # 2. 从SFAStorageSystem.json提取系统名称
            try:
                storage_system_file = tar.extractfile('sfa-logs/SFAStorageSystem.json')
                if storage_system_file:
                    content = storage_system_file.read().decode('utf-8')
                    storage_data = json.loads(content)
                    if storage_data and len(storage_data) > 0:
                        storage = storage_data[0]
                        device_info['system_name'] = storage.get('Name')
                        print(f"  系统名称: {device_info['system_name']}")
            except Exception as e:
                print(f"    读取SFAStorageSystem失败: {e}")
            
            # 3. 从SFAController.json提取SFA版本
            try:
                controller_file = tar.extractfile('sfa-logs/SFAController.json')
                if controller_file:
                    content = controller_file.read().decode('utf-8')
                    controller_data = json.loads(content)
                    if controller_data and len(controller_data) > 0:
                        # 使用第一个控制器的固件版本
                        controller = controller_data[0]
                        device_info['sfa_version'] = controller.get('FWRelease')
                        print(f"  SFA版本: {device_info['sfa_version']}")
            except Exception as e:
                print(f"    读取SFAController失败: {e}")
            
            # 4. 从SFAUPS.json提取BBU制造日期并计算过期日期
            try:
                ups_file = tar.extractfile('sfa-logs/SFAUPS.json')
                if ups_file:
                    content = ups_file.read().decode('utf-8')
                    ups_data = json.loads(content)
                    if ups_data:
                        # 通常有2个BBU
                        for i, ups in enumerate(ups_data):
                            mfg_date = ups.get('BatteryManufactureDate')
                            if mfg_date:
                                expired_date = calculate_bbu_expired_date(mfg_date)
                                if i == 0:
                                    device_info['bbu1_expired_date'] = expired_date
                                elif i == 1:
                                    device_info['bbu2_expired_date'] = expired_date
                        print(f"  BBU过期日期: BBU1={device_info['bbu1_expired_date']}, BBU2={device_info['bbu2_expired_date']}")
            except Exception as e:
                print(f"    读取SFAUPS失败: {e}")
            
            # 5. 计算OST容量
            try:
                virtual_disk_file = tar.extractfile('sfa-logs/SFAVirtualDisk.json')
                if virtual_disk_file:
                    content = virtual_disk_file.read().decode('utf-8')
                    virtual_disks = json.loads(content)
                    
                    total_capacity = 0
                    # 遍历所有虚拟磁盘
                    for disk in virtual_disks:
                        disk_name = disk.get('Name', 'Unknown')
                        
                        # 检查是否是OST卷（通常名称包含'OST'）
                        if 'OST' in disk_name.upper():
                            capacity = 0
                            
                            # 优先从instance字段解析容量，因为这包含真实的OST容量
                            instance_str = disk.get('instance', '')
                            if instance_str:
                                # AION系统的instance中包含类似 "Capacity='713.8 TiB'" 的信息
                                if 'Capacity=' in instance_str:
                                    capacity = parse_capacity_from_instance_with_capacity_field(instance_str)
                                else:
                                    # IDEA系统的instance中包含 "Cap=15.4 TiB" 的信息
                                    capacity = parse_capacity_from_instance(instance_str)
                            
                            # 如果instance解析失败，尝试从Capacity字段解析
                            if capacity == 0 and disk.get('Capacity'):
                                capacity = parse_capacity_from_capacity_field(disk.get('Capacity', ''))
                            
                            if capacity > 0:
                                total_capacity += capacity
                                print(f"    OST卷: {disk_name}, 容量: {capacity} 字节 ({format_capacity(capacity)})")
                            else:
                                print(f"    OST卷: {disk_name}, 无法解析容量 (instance: {disk.get('instance', 'N/A')[:100]}...)")
                    
                    device_info['capacity'] = total_capacity
                    print(f"  设备总容量: {total_capacity} 字节 ({format_capacity(total_capacity)})")
                    
            except Exception as e:
                print(f"    计算容量失败: {e}")
                
    except Exception as e:
        print(f"处理sfainfo文件失败: {e}")
    
    return device_info

def extract_ost_capacity_from_sfainfo(sfainfo_file):
    """从sfainfo tar.gz文件中提取OST容量信息（保留兼容性）"""
    device_info = extract_device_info_from_sfainfo(sfainfo_file)
    return device_info['capacity']

def format_capacity(bytes_value):
    """
    格式化容量显示，超过 1024 TiB 时使用 PiB 单位
    """
    if bytes_value is None:
        return None
    
    # 计算 TiB
    tib_value = bytes_value / (1024**4)
    
    if tib_value >= 1024:
        # 使用 PiB
        pib_value = tib_value / 1024
        return f"{pib_value:.2f} PiB"
    else:
        # 使用 TiB
        return f"{tib_value:.2f} TiB"

def parse_capacity_from_instance(instance_str):
    """
    从 instance 字符串中解析 Cap 值并转换为字节
    例如: "Cap=15.4 TiB" -> 字节数
    """
    if not instance_str or 'Cap=' not in instance_str:
        return 0
    
    try:
        # 提取 Cap= 后面的值
        cap_part = instance_str.split('Cap=')[1].split(',')[0].strip()
        
        # 解析数值和单位
        parts = cap_part.split()
        if len(parts) >= 2:
            value = float(parts[0])
            unit = parts[1].upper()
            
            # 转换为字节
            if unit == 'GIB':
                return int(value * 1024**3)
            elif unit == 'TIB':
                return int(value * 1024**4)
            elif unit == 'MIB':
                return int(value * 1024**2)
            elif unit == 'KIB':
                return int(value * 1024)
            elif unit == 'B':
                return int(value)
            else:
                print(f"    警告: 未知单位 {unit}, 原始值: {cap_part}")
                return 0
        else:
            print(f"    警告: 无法解析容量格式: {cap_part}")
            return 0
            
    except Exception as e:
        print(f"    警告: 解析容量时出错: {e}, 原始字符串: {instance_str}")
        return 0

def parse_capacity_from_capacity_field(capacity_value):
    """
    从 Capacity 字段中解析容量值并转换为字节 (AION系统格式)
    支持两种格式:
    1. 字符串格式: "'713.8 TiB'" -> 字节数
    2. 整数格式: 191595806720 -> 直接是字节数
    """
    if capacity_value is None:
        return 0
    
    try:
        # 如果已经是整数（字节数），直接返回
        if isinstance(capacity_value, (int, float)):
            return int(capacity_value)
        
        # 如果是字符串，解析单位
        if isinstance(capacity_value, str):
            # 去掉引号并分割
            capacity_clean = capacity_value.strip().strip("'\"")
            parts = capacity_clean.split()
            
            if len(parts) >= 2:
                value = float(parts[0])
                unit = parts[1].upper()
                
                # 转换为字节
                if unit == 'GIB':
                    return int(value * 1024**3)
                elif unit == 'TIB':
                    return int(value * 1024**4)
                elif unit == 'MIB':
                    return int(value * 1024**2)
                elif unit == 'KIB':
                    return int(value * 1024)
                elif unit == 'B':
                    return int(value)
                else:
                    print(f"    警告: 未知单位 {unit}, 原始值: {capacity_clean}")
                    return 0
            else:
                print(f"    警告: 无法解析容量格式: {capacity_clean}")
                return 0
        else:
            print(f"    警告: 未知的Capacity数据类型: {type(capacity_value)}")
            return 0
            
    except Exception as e:
        print(f"    警告: 解析Capacity字段时出错: {e}, 原始值: {capacity_value} (类型: {type(capacity_value)})")
        return 0

def parse_capacity_from_instance_with_capacity_field(instance_str):
    """
    从AION系统的instance字段中解析Capacity值并转换为字节
    例如: "SFAVirtualDisk(..., Capacity='713.8 TiB', ...)" -> 字节数
    """
    if not instance_str or 'Capacity=' not in instance_str:
        return 0
    
    try:
        # 提取 Capacity= 后面的值，需要提取到引号内的完整内容
        start_idx = instance_str.find('Capacity=')
        if start_idx == -1:
            return 0
        
        # 从Capacity=之后开始，寻找引号
        after_equal = instance_str[start_idx + len('Capacity='):]
        
        # 查找开始引号
        quote_start = -1
        for i, char in enumerate(after_equal):
            if char in ["'", '"']:
                quote_start = i
                quote_char = char
                break
        
        if quote_start == -1:
            print(f"    警告: 未找到Capacity值的引号，原始字符串: {after_equal[:50]}...")
            return 0
        
        # 查找结束引号
        quote_end = after_equal.find(quote_char, quote_start + 1)
        if quote_end == -1:
            print(f"    警告: 未找到结束引号，原始字符串: {after_equal[:50]}...")
            return 0
        
        # 提取引号内的内容
        capacity_value = after_equal[quote_start + 1:quote_end].strip()
        
        # 解析数值和单位
        parts = capacity_value.split()
        if len(parts) >= 2:
            value = float(parts[0])
            unit = parts[1].upper()
            
            # 转换为字节
            if unit == 'GIB':
                return int(value * 1024**3)
            elif unit == 'TIB':
                return int(value * 1024**4)
            elif unit == 'MIB':
                return int(value * 1024**2)
            elif unit == 'KIB':
                return int(value * 1024)
            elif unit == 'B':
                return int(value)
            else:
                print(f"    警告: 未知单位 {unit}, 从instance解析的值: {capacity_value}")
                return 0
        else:
            print(f"    警告: 无法解析从instance提取的容量格式: '{capacity_value}' (分割后: {parts})")
            return 0
    except Exception as e:
        print(f"    警告: 从instance解析Capacity字段时出错: {e}, 原始instance: {instance_str[:100]}...")
        return 0

def get_total_cluster_capacity(sfainfo_tar_list):
    """
    计算集群总容量（所有设备OST卷容量之和）
    """
    total_capacity = 0
    
    if not sfainfo_tar_list:
        print("警告: 未提供 sfainfo 压缩包，容量将设为 null")
        return None
    
    print("开始计算集群总容量...")
    print("=" * 50)
    
    for tar_path in sfainfo_tar_list:
        if os.path.exists(tar_path):
            device_capacity = extract_ost_capacity_from_sfainfo(tar_path)
            total_capacity += device_capacity
        else:
            print(f"警告: 文件不存在 {tar_path}")
        print("-" * 30)
    
    print(f"集群总容量: {total_capacity} 字节 ({format_capacity(total_capacity)})")
    print("=" * 50)
    
    return total_capacity

def generate_cluster_yaml(toml_path, cluster_name, sfainfo_paths=None, output_path="generated_clusters.yaml", customer_name=None):
    # 读取TOML文件
    with open(toml_path, 'r') as f:
        toml_data = toml.load(f)
    
    # 收集空缺字段信息
    missing_fields = {
        "cluster_level": [],
        "device_level": [],
        "controller_level": []
    }
    
    # 从所有sfainfo文件提取设备信息
    device_info_map = {}
    total_cluster_capacity = 0
    network_description = None
    network_port_types = None
    
    if sfainfo_paths:
        print("\n提取设备信息:")
        for sfainfo_file in sfainfo_paths:
            device_info = extract_device_info_from_sfainfo(sfainfo_file)
            
            # 从文件名提取IP地址作为设备标识
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', os.path.basename(sfainfo_file))
            if ip_match:
                device_ip = ip_match.group(1)
                device_info_map[device_ip] = device_info
                total_cluster_capacity += device_info['capacity']
        
        # 提取网络信息
        print()
        network_description, network_port_types = extract_network_info_from_sfainfo_files(sfainfo_paths)
    
    print(f"\n集群总容量: {total_cluster_capacity} 字节 ({format_capacity(total_cluster_capacity)})")
    
    # 构建集群基础信息
    cluster = {
        "Cluster_name": cluster_name,  # 由参数传入
        "EXA version": toml_data.get("version"),
        "Capacity": format_capacity(total_cluster_capacity) if total_cluster_capacity > 0 else None,  # 从 sfainfo 压缩包计算得出
        "Network_Description": network_description,  # 从sfainfo文件提取的Mellanox网络描述
        "Network_port_type": network_port_types,  # 从sfainfo文件提取
        "EMF_IP": toml_data.get("EMF", {}).get("ip"),
        "Support_status": "待填入",
        "Asset_owner": customer_name if customer_name else "待选择Customer",
        "devices": []
    }
    
    # 记录集群级空缺字段
    for key, value in cluster.items():
        if value is None and key != "devices":
            missing_fields["cluster_level"].append(key)
    
    # 处理每个SFA设备
    for sfa_name, sfa_info in toml_data.get("sfa", {}).items():        
        # 获取设备控制器IP地址
        controller_c0_ip = sfa_info.get("controllers", [None])[0]
        controller_c1_ip = sfa_info.get("controllers", [None, None])[1]
        
        # 查找对应的设备信息（通过IP地址匹配）
        device_info = None
        for ip, info in device_info_map.items():
            if ip == controller_c0_ip or ip == controller_c1_ip:
                device_info = info
                break
        
        # 构建设备信息，优先使用从sfainfo提取的信息
        device = {
            "Device_name": sfa_name,
            "type": device_info['type'] if device_info else None,
            "SFA version": device_info['sfa_version'] if device_info else None,
            "Capacity": format_capacity(device_info['capacity']) if device_info and device_info['capacity'] > 0 else None,
            "Controller_c0_ip": controller_c0_ip,
            "Controller_c1_ip": controller_c1_ip,
            "Controller_c0_serial_number": device_info['controller_c0_serial'] if device_info else None,
            "Controller_c1_serial_number": device_info['controller_c1_serial'] if device_info else None,
            "BBU1_Expired_Date": device_info['bbu1_expired_date'] if device_info else None,
            "BBU2_Expired_Date": device_info['bbu2_expired_date'] if device_info else None,
            "Hosts": []
        }
        
        # 记录设备级空缺字段
        for key, value in device.items():
            if value is None and key not in ["Hosts", "Controller_c0_ip", "Controller_c1_ip"]:
                missing_fields["device_level"].append(f"{sfa_name}:{key}")
        
        # 记录控制器级空缺字段
        if device["Controller_c0_ip"] is not None:
            missing_fields["controller_level"].append(f"{sfa_name}:Controller_c0_serial_number")
        if device["Controller_c1_ip"] is not None:
            missing_fields["controller_level"].append(f"{sfa_name}:Controller_c1_serial_number")
        
        # 收集属于当前设备的主机
        for host_name, host_info in toml_data.get("host", {}).items():
            if host_info.get("sfa") == sfa_name:
                nic_info = host_info.get("nic", {})
                
                # 动态检测所有mlx*接口并生成lnet网络地址
                lnet_networks = []
                
                # 收集所有mlx接口（mlxib*, mlxen*）
                mlx_interfaces = {}
                for nic_name, nic_config in nic_info.items():
                    if nic_name.startswith(('mlxib', 'mlxen')) and nic_config.get('ip'):
                        mlx_interfaces[nic_name] = nic_config['ip']
                
                # 自定义排序：InfiniBand接口优先，然后按编号排序
                def sort_mlx_interfaces(nic_name):
                    if nic_name.startswith('mlxib'):
                        # InfiniBand接口优先级高，编号前加0前缀
                        interface_num = nic_name.replace('mlxib', '')
                        return (0, int(interface_num) if interface_num.isdigit() else 0)
                    elif nic_name.startswith('mlxen'):
                        # 以太网接口优先级低，编号前加1前缀
                        interface_num = nic_name.replace('mlxen', '')
                        return (1, int(interface_num) if interface_num.isdigit() else 0)
                    return (2, 0)  # 其他接口
                
                # 按自定义规则排序
                for nic_name in sorted(mlx_interfaces.keys(), key=sort_mlx_interfaces):
                    ip_addr = mlx_interfaces[nic_name]
                    
                    # 根据接口类型确定协议
                    if nic_name.startswith('mlxib'):
                        # InfiniBand接口: mlxib0 -> @o2ib0, mlxib1 -> @o2ib1
                        interface_num = nic_name.replace('mlxib', '')
                        protocol = f"@o2ib{interface_num}"
                    elif nic_name.startswith('mlxen'):
                        # 以太网接口: mlxen0 -> @tcp0, mlxen1 -> @tcp1
                        interface_num = nic_name.replace('mlxen', '')
                        protocol = f"@tcp{interface_num}"
                    
                    lnet_networks.append(f"{ip_addr}{protocol}")
                
                # 构建IP配置，支持多个lnet网络
                ip_config = {
                    "management": nic_info.get("mgmt0", {}).get("ip"),
                    "lnet1_network": lnet_networks[0] if len(lnet_networks) > 0 else None,
                    "lnet2_network": lnet_networks[1] if len(lnet_networks) > 1 else None
                }
                
                # 如果有更多lnet网络，可以扩展（未来可能需要）
                # for i, lnet_addr in enumerate(lnet_networks[2:], start=3):
                #     ip_config[f"lnet{i}_network"] = lnet_addr
                
                host = {
                    "hostname": host_name,
                    "role": "MDS/OSS",
                    "ip": ip_config
                }
                device["Hosts"].append(host)
        
        cluster["devices"].append(device)
    

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
    
    # 打印空缺值说明
    print(f"\n已生成YAML文件: {output_path}")
    print("\n以下字段未从TOML中获取到，需后续手工补充：")
    if missing_fields["cluster_level"]:
        print(f"1. 集群级字段: {', '.join(missing_fields['cluster_level'])}")
    if missing_fields["device_level"]:
        print(f"2. 设备级字段: {', '.join(missing_fields['device_level'])}")
    if missing_fields["controller_level"]:
        print(f"3. 控制器级字段: {', '.join(missing_fields['controller_level'])}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从exascaler.toml生成集群YAML配置")
    parser.add_argument("toml_file", help="exascaler.toml文件路径")
    parser.add_argument("--cluster-name", required=True, help="集群名称（System name）")
    parser.add_argument("--sfainfo", nargs="*", help="sfainfo.tar.gz文件路径（支持多个）")
    parser.add_argument("-o", "--output", help="输出YAML文件路径", default="generated_clusters.yaml")
    args = parser.parse_args()
    
    generate_cluster_yaml(args.toml_file, args.cluster_name, args.sfainfo, args.output)

