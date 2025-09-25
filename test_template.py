#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
验证模板语法正确性
"""

from flask import Flask, render_template

app = Flask(__name__)

# 模拟数据
mock_customers = {
    "1": {"name": "AION客户"},
    "2": {"name": "IDEA客户"}, 
    "3": {"name": "SHLab客户"}
}

def test_template_rendering():
    """测试模板渲染"""
    print("🧪 测试模板渲染")
    print("=" * 40)
    
    with app.test_request_context():
        # 1. 测试有预选客户的情况
        try:
            html = render_template('new_system.html', 
                                 customers=mock_customers, 
                                 preselected_customer_id="1")
            print("✅ 预选客户模式渲染成功")
            
            # 检查关键内容
            if 'customer-display' in html:
                print("  ✅ 包含客户显示组件")
            if 'type="hidden"' in html:
                print("  ✅ 包含隐藏字段")
            if 'AION客户' in html:
                print("  ✅ 显示客户名称")
                
        except Exception as e:
            print(f"❌ 预选客户模式渲染失败: {e}")
        
        # 2. 测试无预选客户的情况
        try:
            html = render_template('new_system.html', 
                                 customers=mock_customers, 
                                 preselected_customer_id=None)
            print("✅ 常规模式渲染成功")
            
            # 检查关键内容
            if '<select id="customer_id"' in html:
                print("  ✅ 包含选择下拉框")
            if 'customer-display' not in html:
                print("  ✅ 未包含客户显示组件")
                
        except Exception as e:
            print(f"❌ 常规模式渲染失败: {e}")

if __name__ == "__main__":
    test_template_rendering()