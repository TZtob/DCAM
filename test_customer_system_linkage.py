#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试客户-系统联动功能
"""

import requests
import time

def test_customer_system_api():
    """测试客户-系统联动API"""
    base_url = "http://127.0.0.1:5000"
    
    print("=== 测试客户-系统联动功能 ===\n")
    
    # 等待Flask服务器启动
    print("等待服务器响应...")
    for i in range(10):
        try:
            response = requests.get(f"{base_url}/", timeout=2)
            if response.status_code == 200:
                print("✅ 服务器已就绪")
                break
        except:
            time.sleep(1)
    else:
        print("❌ 无法连接到服务器")
        return False
    
    try:
        # 1. 测试客户列表API
        print("\n1. 测试客户列表API")
        response = requests.get(f"{base_url}/api/customers_list")
        if response.status_code == 200:
            customers = response.json()
            print(f"✅ 客户列表API工作正常，返回{len(customers)}个客户:")
            for customer in customers:
                print(f"   - ID: {customer['id']}, 名称: {customer['name']}")
        else:
            print(f"❌ 客户列表API返回错误状态码: {response.status_code}")
            return False
        
        # 2. 测试系统列表API（所有系统）
        print("\n2. 测试所有系统API")
        response = requests.get(f"{base_url}/api/all_systems")
        if response.status_code == 200:
            all_systems = response.json()
            print(f"✅ 所有系统API工作正常，返回{len(all_systems)}个系统:")
            for system in all_systems:
                print(f"   - ID: {system['id']}, 名称: {system['name']}, 客户: {system.get('customer_id', 'N/A')}")
        else:
            print(f"❌ 所有系统API返回错误状态码: {response.status_code}")
            return False
        
        # 3. 测试按客户过滤系统API
        for customer in customers:
            customer_id = customer['id']
            customer_name = customer['name']
            
            print(f"\n3. 测试客户 {customer_name} (ID: {customer_id}) 的系统")
            response = requests.get(f"{base_url}/api/systems_by_customer?customer_id={customer_id}")
            if response.status_code == 200:
                customer_systems = response.json()
                print(f"✅ 客户系统API工作正常，客户 {customer_name} 有{len(customer_systems)}个系统:")
                for system in customer_systems:
                    print(f"   - ID: {system['id']}, 名称: {system['name']}, 客户: {system.get('customer_name', 'N/A')}")
            else:
                print(f"❌ 客户系统API返回错误状态码: {response.status_code}")
                return False
        
        # 4. 测试查询功能
        print(f"\n4. 测试查询功能")
        
        # 测试全局查询（所有客户）
        response = requests.get(f"{base_url}/api/global_query?query_type=1")
        if response.status_code == 200:
            print("✅ 全局查询（所有客户）工作正常")
        else:
            print(f"❌ 全局查询返回错误状态码: {response.status_code}")
            return False
        
        # 测试客户过滤查询
        for customer in customers:
            customer_id = customer['id']
            customer_name = customer['name']
            
            response = requests.get(f"{base_url}/api/global_query?query_type=1&customer_id={customer_id}")
            if response.status_code == 200:
                print(f"✅ 客户 {customer_name} 的过滤查询工作正常")
            else:
                print(f"❌ 客户 {customer_name} 的过滤查询返回错误状态码: {response.status_code}")
                return False
        
        print(f"\n🎉 所有测试通过！客户-系统联动功能工作正常！")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        return False

if __name__ == "__main__":
    test_customer_system_api()