#!/usr/bin/env python3
import time
import requests
import json

def wait_and_test():
    time.sleep(2)  # 等待Flask启动
    
    print("测试 systems_by_customer API")
    
    # 测试客户ID=1
    try:
        response = requests.get('http://127.0.0.1:5000/api/systems_by_customer?customer_id=1')
        if response.status_code == 200:
            data = response.json()
            print(f"客户ID=1的系统: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"请求失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"请求异常: {e}")
    
    # 测试客户ID=2  
    try:
        response = requests.get('http://127.0.0.1:5000/api/systems_by_customer?customer_id=2')
        if response.status_code == 200:
            data = response.json()
            print(f"客户ID=2的系统: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"请求失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"请求异常: {e}")

if __name__ == "__main__":
    wait_and_test()