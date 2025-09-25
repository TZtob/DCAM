import requests
import os
import sys
from pathlib import Path

def test_logo_routes():
    """测试不同的logo访问路由"""
    base_url = "https://ddnsupport.com.cn"  # 替换为您的实际域名
    routes = [
        "/dcam/static/DDN-main-logo.svg",
        "/dcam/logo"
    ]
    
    print("测试DDN Logo访问...")
    
    for route in routes:
        full_url = f"{base_url}{route}"
        print(f"\n尝试访问: {full_url}")
        
        try:
            response = requests.get(full_url)
            print(f"状态码: {response.status_code}")
            print(f"内容类型: {response.headers.get('Content-Type')}")
            
            if response.status_code == 200:
                print("✓ 成功访问!")
                if "image/svg+xml" in response.headers.get('Content-Type', ''):
                    print("✓ 返回了正确的SVG内容")
                    
                    # 保存内容以便验证
                    filename = Path(f"logo_test_{route.replace('/', '_')}.svg")
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    print(f"✓ 已保存内容到: {filename}")
                else:
                    print("✗ 内容类型不是SVG")
            else:
                print(f"✗ 访问失败: HTTP {response.status_code}")
                print(f"响应内容: {response.text[:200]}...")
        except Exception as e:
            print(f"✗ 错误: {str(e)}")

    print("\n测试登录页面...")
    try:
        login_url = f"{base_url}/dcam/login"
        print(f"尝试访问: {login_url}")
        response = requests.get(login_url)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ 成功访问登录页面!")
            
            # 检查页面内容中是否包含内联SVG
            if "<svg" in response.text and "</svg>" in response.text:
                print("✓ 页面包含内联SVG")
            else:
                print("✗ 页面中未找到内联SVG")
        else:
            print(f"✗ 访问登录页面失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ 错误: {str(e)}")

if __name__ == "__main__":
    test_logo_routes()