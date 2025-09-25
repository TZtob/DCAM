import tarfile
import json

# 提取并查看 JSON 结构
with tarfile.open('2025-09-23-18-05-53-192.168.89.1-SRIDEA_lfs-SFA400NVX2E-sfainfo.tar.gz', 'r:gz') as tar:
    for member in tar.getmembers():
        if member.name.endswith('SFAVirtualDisk.json'):
            print(f"找到文件: {member.name}")
            file_obj = tar.extractfile(member)
            if file_obj:
                data = json.load(file_obj)
                print(f"总共有 {len(data)} 个虚拟磁盘")
                
                # 查看第一个磁盘的结构
                if data:
                    first_disk = data[0]
                    print("\n第一个磁盘的结构:")
                    for key, value in first_disk.items():
                        if key == 'instance' and isinstance(value, dict):
                            print(f"  {key}: (dict)")
                            for sub_key, sub_value in value.items():
                                print(f"    {sub_key}: {sub_value}")
                        else:
                            print(f"  {key}: {value}")
                
                # 查找包含 ost 的磁盘并显示其 instance 结构
                print("\n包含 'ost' 的磁盘:")
                for i, disk in enumerate(data):
                    disk_name = disk.get('Name', '')
                    if 'ost' in disk_name.lower():
                        print(f"\n磁盘 {i}: {disk_name}")
                        instance = disk.get('instance', '')
                        print(f"  instance 字符串: {instance}")
                        
                        # 解析 instance 字符串中的 Cap 值
                        if 'Cap=' in instance:
                            # 提取 Cap= 后面的值
                            cap_part = instance.split('Cap=')[1].split(',')[0].split(')')[0]
                            print(f"  提取的 Cap 值: {cap_part}")
                        
                        if i >= 2:  # 只显示前3个
                            break
            break