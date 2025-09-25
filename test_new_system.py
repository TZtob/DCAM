#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试新建系统功能的改进
验证从客户页面跳转时自动选择客户
"""

import requests
import time

def test_new_system_functionality():
    """测试新建系统功能"""
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 测试新建系统功能改进")
    print("=" * 50)
    
    # 1. 测试从客户页面跳转的创建系统
    print("\n1️⃣ 测试从客户页面跳转创建系统...")
    
    try:
        # 模拟从客户页面跳转 (customer_id=1 对应某个客户)
        url_with_customer = f"{base_url}/systems/new?customer_id=1"
        response = requests.get(url_with_customer, allow_redirects=False)
        
        print(f"  访问URL: {url_with_customer}")
        print(f"  HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 检查响应内容是否包含预期的元素
            content = response.text
            
            if 'customer-display' in content:
                print("  ✅ 找到客户显示组件")
            else:
                print("  ❌ 未找到客户显示组件")
                
            if 'type="hidden"' in content and 'customer_id' in content:
                print("  ✅ 找到隐藏的客户ID字段")
            else:
                print("  ❌ 未找到隐藏的客户ID字段")
                
        elif response.status_code == 302:
            print("  ⚠️  被重定向，可能需要登录")
        else:
            print(f"  ❌ 意外的状态码: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
    
    # 2. 测试常规创建系统（不带customer_id参数）
    print("\n2️⃣ 测试常规创建系统...")
    
    try:
        url_normal = f"{base_url}/systems/new"
        response = requests.get(url_normal, allow_redirects=False)
        
        print(f"  访问URL: {url_normal}")
        print(f"  HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            if '<select id="customer_id"' in content:
                print("  ✅ 找到客户选择下拉框")
            else:
                print("  ❌ 未找到客户选择下拉框")
                
            if 'customer-display' not in content:
                print("  ✅ 未显示客户预选组件（符合预期）")
            else:
                print("  ❌ 意外显示了客户预选组件")
                
        elif response.status_code == 302:
            print("  ⚠️  被重定向，可能需要登录")
        else:
            print(f"  ❌ 意外的状态码: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 测试完成")
    print("\n💡 建议:")
    print("   1. 在浏览器中访问客户详情页面")
    print("   2. 点击'添加系统'按钮")
    print("   3. 验证客户名称是否自动填入且不可编辑")

if __name__ == "__main__":
    # 等待应用完全启动
    time.sleep(2)
    test_new_system_functionality()