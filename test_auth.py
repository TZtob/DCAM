#!/usr/bin/env python3
"""
用户认证系统测试脚本
"""

import sys
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash

# 添加app.py路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_auth_system():
    """测试认证系统"""
    print("🔐 测试DCAM用户认证系统")
    print("=" * 50)
    
    # 测试用户数据文件
    users_file = 'users.json'
    
    # 创建测试用户
    test_users = {
        'admin': {
            'password_hash': generate_password_hash('admin123'),
            'role': 'admin',
            'created_at': '2025-01-01T00:00:00'
        },
        'user1': {
            'password_hash': generate_password_hash('password123'),
            'role': 'user', 
            'created_at': '2025-01-01T00:00:00'
        }
    }
    
    # 保存测试用户文件
    with open(users_file, 'w', encoding='utf-8') as f:
        json.dump(test_users, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 创建用户数据文件: {users_file}")
    print("\n🔑 默认用户凭证:")
    print("管理员: admin / admin123")
    print("普通用户: user1 / password123")
    
    # 测试密码验证
    print("\n🧪 测试密码验证:")
    
    # 正确密码
    admin_hash = test_users['admin']['password_hash']
    if check_password_hash(admin_hash, 'admin123'):
        print("✅ admin密码验证 - 通过")
    else:
        print("❌ admin密码验证 - 失败")
    
    # 错误密码
    if not check_password_hash(admin_hash, 'wrongpassword'):
        print("✅ 错误密码验证 - 正确拒绝")
    else:
        print("❌ 错误密码验证 - 错误接受")
    
    print("\n🚀 用户认证系统配置完成!")
    print("\n📋 启动说明:")
    print("1. 运行: python app.py")
    print("2. 访问: http://localhost:5000")
    print("3. 使用上述凭证登录")
    print("4. 首次登录后建议修改密码")

if __name__ == '__main__':
    test_auth_system()