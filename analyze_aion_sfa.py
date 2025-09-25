#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
分析AION系统导入的SFA文件
检查OST容量提取是否正常
"""

import tarfile
import json
import os
import re

def analyze_aion_sfa_files():
    """分析AION系统的SFA文件"""
    
    print("🔍 分析AION系统SFA文件")
    print("=" * 60)
    
    uploads_dir = "data/customers/AION/lfs/uploads"
    
    if not os.path.exists(uploads_dir):
        print(f"❌ uploads目录不存在: {uploads_dir}")
        return
    
    # 查找SFA文件
    files = os.listdir(uploads_dir)
    sfa_files = [f for f in files if f.endswith('.tar.gz') and 'sfainfo' in f]
    
    print(f"📁 找到 {len(sfa_files)} 个SFA文件:")
    for f in sfa_files:
        print(f"   - {f}")
    
    total_capacity = 0
    all_osts = []
    
    for sfa_file in sfa_files:
        filepath = os.path.join(uploads_dir, sfa_file)
        
        print(f"\n{'='*60}")
        print(f"📄 分析文件: {sfa_file}")
        
        try:
            with tarfile.open(filepath, 'r:gz') as tar:
                # 1. 检查系统信息
                try:
                    system_info_file = tar.extractfile('sfa-logs/SFAStorageSystem.json')
                    if system_info_file:
                        system_data = json.loads(system_info_file.read().decode('utf-8'))
                        if system_data and len(system_data) > 0:
                            system_name = system_data[0].get('Name', 'Unknown')
                            print(f"💾 系统名: {system_name}")
                except:
                    print(f"💾 系统名: 无法获取")
                
                # 2. 检查设备信息
                try:
                    bundle_info_file = tar.extractfile('sfa-logs/BundleInfo.json')
                    if bundle_info_file:
                        bundle_data = json.loads(bundle_info_file.read().decode('utf-8'))
                        if bundle_data and len(bundle_data) > 0:
                            bundle = bundle_data[0]
                            device_type = bundle.get('Platform')
                            c0_serial = bundle.get('Controller0Serial')
                            c1_serial = bundle.get('Controller1Serial')
                            print(f"🖥️  设备类型: {device_type}")
                            print(f"🖥️  控制器: C0={c0_serial}, C1={c1_serial}")
                except Exception as e:
                    print(f"🖥️  设备信息: 无法获取 - {e}")
                
                # 3. 详细分析虚拟磁盘
                try:
                    virtual_disk_file = tar.extractfile('sfa-logs/SFAVirtualDisk.json')
                    if virtual_disk_file:
                        virtual_disks = json.loads(virtual_disk_file.read().decode('utf-8'))
                        
                        print(f"💿 虚拟磁盘总数: {len(virtual_disks)}")
                        
                        device_osts = []
                        device_capacity = 0
                        
                        for disk in virtual_disks:
                            disk_name = disk.get('Name', '').strip()
                            instance = disk.get('instance', '').strip()
                            
                            print(f"   💽 {disk_name}: {instance[:80]}{'...' if len(instance) > 80 else ''}")
                            
                            # 检查是否是OST
                            if 'ost' in disk_name.lower():
                                # 解析容量
                                capacity = 0
                                if 'Cap=' in instance:
                                    cap_part = instance.split('Cap=')[1].split(',')[0].strip()
                                    parts = cap_part.split()
                                    if len(parts) >= 2:
                                        try:
                                            value = float(parts[0])
                                            unit = parts[1].upper()
                                            if unit == 'TIB':
                                                capacity = value
                                            elif unit == 'GIB':
                                                capacity = value / 1024
                                            print(f"      ✅ OST容量: {capacity:.2f} TiB")
                                        except:
                                            print(f"      ❌ 容量解析失败: {cap_part}")
                                    else:
                                        print(f"      ❌ 容量格式错误: {cap_part}")
                                else:
                                    print(f"      ❌ 未找到容量信息")
                                
                                device_osts.append({
                                    'name': disk_name,
                                    'capacity': capacity,
                                    'file': sfa_file
                                })
                                device_capacity += capacity
                                all_osts.append({
                                    'name': disk_name,
                                    'capacity': capacity,
                                    'file': sfa_file
                                })
                        
                        print(f"📊 设备OST数量: {len(device_osts)}")
                        print(f"📦 设备总容量: {device_capacity:.2f} TiB")
                        total_capacity += device_capacity
                        
                except Exception as e:
                    print(f"❌ 虚拟磁盘分析失败: {e}")
        
        except Exception as e:
            print(f"❌ 文件处理失败: {e}")
    
    print(f"\n{'='*60}")
    print(f"🎯 汇总结果:")
    print(f"   📁 SFA文件数: {len(sfa_files)}")
    print(f"   💽 OST总数: {len(all_osts)}")
    print(f"   📦 总容量: {total_capacity:.2f} TiB")
    
    if len(all_osts) == 0:
        print(f"\n❌ 未找到任何OST！")
        print("可能的原因:")
        print("1. SFA文件中没有包含虚拟磁盘信息")
        print("2. OST命名不包含'ost'关键字")
        print("3. 文件格式损坏")
    elif total_capacity == 0:
        print(f"\n⚠️  找到了OST但容量为0！")
        print("可能的原因:")
        print("1. 容量信息格式不标准")
        print("2. 容量解析逻辑需要调整")
        
        print(f"\n📋 OST详情:")
        for ost in all_osts:
            print(f"   {ost['name']}: {ost['capacity']:.2f} TiB (来自 {ost['file']})")
    else:
        print(f"\n✅ 容量提取成功!")
        return total_capacity
    
    return 0

if __name__ == "__main__":
    analyze_aion_sfa_files()