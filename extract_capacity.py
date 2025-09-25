import tarfile
import json
import os
import glob

def extract_ost_capacity_from_sfainfo(tar_path):
    """
    从 sfainfo.tar.gz 中提取 OST 卷的总容量
    """
    total_capacity = 0
    device_name = os.path.basename(tar_path).replace('-sfainfo.tar.gz', '')
    
    print(f"处理设备: {device_name}")
    
    try:
        with tarfile.open(tar_path, 'r:gz') as tar:
            # 查找 SFAVirtualDisk.json 文件
            for member in tar.getmembers():
                if member.name.endswith('SFAVirtualDisk.json'):
                    print(f"  找到文件: {member.name}")
                    
                    # 提取并读取 JSON 文件
                    file_obj = tar.extractfile(member)
                    if file_obj:
                        try:
                            data = json.load(file_obj)
                            
                            # 遍历所有虚拟磁盘
                            ost_count = 0
                            for disk in data:
                                disk_name = disk.get('Name', '')
                                if 'ost' in disk_name.lower():
                                    capacity = disk.get('Capacity', 0)
                                    total_capacity += capacity
                                    ost_count += 1
                                    print(f"    OST卷: {disk_name}, 容量: {capacity}")
                            
                            print(f"  设备 {device_name} 总计 {ost_count} 个OST卷")
                            
                        except json.JSONDecodeError as e:
                            print(f"  JSON解析错误: {e}")
                    break
            else:
                print(f"  警告: 未找到 SFAVirtualDisk.json 文件")
                
    except Exception as e:
        print(f"  错误: {e}")
    
    print(f"  设备 {device_name} OST总容量: {total_capacity}")
    return total_capacity

def get_total_cluster_capacity(sfainfo_tar_list):
    """
    计算集群总容量（所有设备OST卷容量之和）
    """
    total_capacity = 0
    
    print("开始计算集群总容量...")
    print("=" * 50)
    
    for tar_path in sfainfo_tar_list:
        if os.path.exists(tar_path):
            device_capacity = extract_ost_capacity_from_sfainfo(tar_path)
            total_capacity += device_capacity
        else:
            print(f"警告: 文件不存在 {tar_path}")
        print("-" * 30)
    
    print(f"集群总容量: {total_capacity}")
    print("=" * 50)
    
    return total_capacity

# 测试函数
if __name__ == "__main__":
    # 获取当前目录下的所有 sfainfo.tar.gz 文件
    sfainfo_files = glob.glob("*sfainfo.tar.gz")
    
    if sfainfo_files:
        print(f"找到 {len(sfainfo_files)} 个 sfainfo 文件:")
        for f in sfainfo_files:
            print(f"  - {f}")
        print()
        
        total_capacity = get_total_cluster_capacity(sfainfo_files)
        print(f"\n最终结果: 集群总容量 = {total_capacity}")
    else:
        print("未找到任何 sfainfo.tar.gz 文件")