#!/usr/bin/env python3
"""
测试mlx接口动态检测逻辑的各种场景
"""

def test_mlx_interface_detection():
    """模拟不同的mlx接口配置场景"""
    
    test_cases = [
        {
            "name": "标准配置：一个IB + 一个以太网",
            "nic_info": {
                "mgmt0": {"ip": "192.168.89.1"},
                "mlxib0": {"ip": "10.10.64.1"},
                "mlxen0": {"ip": "192.168.90.1"}
            },
            "expected": ["10.10.64.1@o2ib0", "192.168.90.1@tcp0"]
        },
        {
            "name": "多个InfiniBand接口",
            "nic_info": {
                "mgmt0": {"ip": "192.168.89.1"},
                "mlxib0": {"ip": "10.10.64.1"},
                "mlxib1": {"ip": "10.10.65.1"}
            },
            "expected": ["10.10.64.1@o2ib0", "10.10.65.1@o2ib1"]
        },
        {
            "name": "多个以太网接口",
            "nic_info": {
                "mgmt0": {"ip": "192.168.89.1"},
                "mlxen0": {"ip": "192.168.90.1"},
                "mlxen1": {"ip": "192.168.91.1"}
            },
            "expected": ["192.168.90.1@tcp0", "192.168.91.1@tcp1"]
        },
        {
            "name": "混合配置：多个IB + 多个以太网",
            "nic_info": {
                "mgmt0": {"ip": "192.168.89.1"},
                "mlxib0": {"ip": "10.10.64.1"},
                "mlxib1": {"ip": "10.10.65.1"},
                "mlxen0": {"ip": "192.168.90.1"},
                "mlxen1": {"ip": "192.168.91.1"}
            },
            "expected": ["10.10.64.1@o2ib0", "10.10.65.1@o2ib1", "192.168.90.1@tcp0", "192.168.91.1@tcp1"]
        },
        {
            "name": "乱序配置",
            "nic_info": {
                "mgmt0": {"ip": "192.168.89.1"},
                "mlxen1": {"ip": "192.168.91.1"},
                "mlxib1": {"ip": "10.10.65.1"},
                "mlxen0": {"ip": "192.168.90.1"},
                "mlxib0": {"ip": "10.10.64.1"}
            },
            "expected": ["10.10.64.1@o2ib0", "10.10.65.1@o2ib1", "192.168.90.1@tcp0", "192.168.91.1@tcp1"]
        }
    ]
    
    for test_case in test_cases:
        print(f"\n测试场景: {test_case['name']}")
        print("输入配置:")
        for nic_name, nic_config in test_case['nic_info'].items():
            if nic_name.startswith(('mlxib', 'mlxen')):
                print(f"  {nic_name}: {nic_config.get('ip')}")
        
        # 模拟动态检测逻辑
        lnet_networks = []
        mlx_interfaces = {}
        
        for nic_name, nic_config in test_case['nic_info'].items():
            if nic_name.startswith(('mlxib', 'mlxen')) and nic_config.get('ip'):
                mlx_interfaces[nic_name] = nic_config['ip']
        
        # 自定义排序：InfiniBand接口优先，然后按编号排序
        def sort_mlx_interfaces(nic_name):
            if nic_name.startswith('mlxib'):
                interface_num = nic_name.replace('mlxib', '')
                return (0, int(interface_num) if interface_num.isdigit() else 0)
            elif nic_name.startswith('mlxen'):
                interface_num = nic_name.replace('mlxen', '')
                return (1, int(interface_num) if interface_num.isdigit() else 0)
            return (2, 0)
        
        for nic_name in sorted(mlx_interfaces.keys(), key=sort_mlx_interfaces):
            ip_addr = mlx_interfaces[nic_name]
            
            if nic_name.startswith('mlxib'):
                interface_num = nic_name.replace('mlxib', '')
                protocol = f"@o2ib{interface_num}"
            elif nic_name.startswith('mlxen'):
                interface_num = nic_name.replace('mlxen', '')
                protocol = f"@tcp{interface_num}"
            
            lnet_networks.append(f"{ip_addr}{protocol}")
        
        print("生成的lnet地址:")
        for i, addr in enumerate(lnet_networks, 1):
            print(f"  lnet{i}_network: {addr}")
        
        print("期望结果:")
        for i, addr in enumerate(test_case['expected'], 1):
            print(f"  lnet{i}_network: {addr}")
        
        # 验证结果
        if lnet_networks == test_case['expected']:
            print("✅ 测试通过")
        else:
            print("❌ 测试失败")
            print(f"  实际: {lnet_networks}")
            print(f"  期望: {test_case['expected']}")

if __name__ == "__main__":
    test_mlx_interface_detection()