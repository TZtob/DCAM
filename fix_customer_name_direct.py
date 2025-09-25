import os
import yaml
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def add_customer_name_to_app():
    """修改app.py中的update_system_config函数确保传递客户名"""
    try:
        # 读取app.py
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.readlines()
        
        # 查找generate_cluster_yaml调用
        line_number = -1
        for i, line in enumerate(content):
            if "generate_cluster_yaml(toml_path, cluster_name, sfa_paths, output_filename" in line:
                line_number = i
                break
        
        if line_number >= 0:
            # 检查是否已经包含客户名参数
            if "customer_name" not in content[line_number]:
                # 添加客户名参数
                content[line_number] = content[line_number].replace(
                    "generate_cluster_yaml(toml_path, cluster_name, sfa_paths, output_filename)",
                    "generate_cluster_yaml(toml_path, cluster_name, sfa_paths, output_filename, customer_name)"
                )
                logging.info(f"已在line {line_number+1}添加customer_name参数")
            
                # 写回文件
                with open('app.py', 'w', encoding='utf-8') as f:
                    f.writelines(content)
                
                logging.info("已成功更新app.py")
                return True
            else:
                logging.info("app.py已经包含customer_name参数，无需更新")
                return True
        else:
            logging.warning("未找到generate_cluster_yaml调用，无法更新app.py")
            return False
            
    except Exception as e:
        logging.error(f"更新app.py时出错: {str(e)}")
        return False

def update_yaml_files():
    """更新所有YAML文件，确保包含客户名"""
    try:
        # 读取系统和客户数据
        with open('systems.json', 'r', encoding='utf-8') as f:
            systems = json.load(f)
        
        with open('customers.json', 'r', encoding='utf-8') as f:
            customers = json.load(f)
            
        updated_count = 0
        
        # 遍历所有系统
        for system_id, system in systems.items():
            yaml_file = system.get('yaml_file')
            if not yaml_file or not os.path.exists(yaml_file):
                continue
                
            try:
                # 读取YAML
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    yaml_data = yaml.safe_load(f)
                
                # 检查是否已有客户名
                if yaml_data and 'customer' in yaml_data:
                    logging.info(f"YAML文件 {yaml_file} 已有客户名: {yaml_data['customer']}")
                    continue
                
                # 查找客户名
                customer_name = None
                
                # 1. 从系统记录中获取
                if 'customer_name' in system:
                    customer_name = system['customer_name']
                
                # 2. 从客户表中获取
                elif 'customer_id' in system and system['customer_id'] in customers:
                    customer_name = customers[system['customer_id']].get('name')
                
                if customer_name:
                    # 添加客户名
                    yaml_data['customer'] = customer_name
                    
                    # 保存YAML
                    with open(yaml_file, 'w', encoding='utf-8') as f:
                        yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False)
                        
                    logging.info(f"已更新YAML文件 {yaml_file} 添加客户名: {customer_name}")
                    updated_count += 1
                else:
                    logging.warning(f"找不到YAML文件 {yaml_file} 对应的客户名")
            
            except Exception as e:
                logging.error(f"处理YAML文件 {yaml_file} 时出错: {str(e)}")
        
        logging.info(f"共更新了 {updated_count} 个YAML文件")
        return True
    
    except Exception as e:
        logging.error(f"更新YAML文件时出错: {str(e)}")
        return False

def create_customer_yaml_sync_function():
    """创建一个用于同步客户名的函数"""
    try:
        # 创建函数代码
        function_code = '''
def sync_customer_name_to_yaml(system_id):
    """同步系统的客户名到YAML文件"""
    systems = get_systems()
    if system_id not in systems:
        return False
    
    system = systems[system_id]
    yaml_file = system.get('yaml_file')
    
    if not yaml_file or not os.path.exists(yaml_file):
        return False
    
    try:
        # 读取YAML
        with open(yaml_file, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)
        
        if not yaml_data:
            return False
        
        # 获取客户名
        customer_name = None
        
        # 1. 从系统记录中获取
        if 'customer_name' in system:
            customer_name = system['customer_name']
        
        # 2. 从客户表中获取
        elif 'customer_id' in system:
            customers = get_customers()
            if system['customer_id'] in customers:
                customer_name = customers[system['customer_id']].get('name')
        
        if customer_name:
            # 更新YAML
            yaml_data['customer'] = customer_name
            
            # 保存YAML
            with open(yaml_file, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False)
                
            return True
        
        return False
    except Exception as e:
        logging.error(f"同步客户名时出错: {str(e)}")
        return False
'''
        
        # 读取app.py
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找合适的位置插入函数
        insert_pos = content.find("def get_recent_items(entity_type, limit=5):")
        if insert_pos > 0:
            insert_pos = content.rfind("\n\n", 0, insert_pos) + 2
            new_content = content[:insert_pos] + function_code + content[insert_pos:]
            
            # 写回文件
            with open('app.py', 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            logging.info("已添加sync_customer_name_to_yaml函数")
            return True
        else:
            logging.warning("找不到合适的位置添加函数")
            return False
            
    except Exception as e:
        logging.error(f"创建同步函数时出错: {str(e)}")
        return False

def update_system_detail_function():
    """更新system_detail函数，添加客户名同步功能"""
    try:
        # 读取app.py
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.readlines()
        
        # 查找system_detail函数中记录访问的行
        line_number = -1
        for i, line in enumerate(content):
            if "# 记录系统访问" in line and "log_access" in content[i+1]:
                line_number = i + 1
                break
        
        if line_number >= 0:
            # 添加客户名同步代码
            sync_code = "    # 同步客户名到YAML\n    sync_customer_name_to_yaml(system_id)\n\n"
            content.insert(line_number + 1, sync_code)
            
            # 写回文件
            with open('app.py', 'w', encoding='utf-8') as f:
                f.writelines(content)
                
            logging.info("已更新system_detail函数添加客户名同步功能")
            return True
        else:
            logging.warning("找不到合适的位置添加客户名同步代码")
            return False
            
    except Exception as e:
        logging.error(f"更新system_detail函数时出错: {str(e)}")
        return False

if __name__ == "__main__":
    print("正在修复系统更新配置丢失客户名的问题...")
    
    # 1. 修改app.py中的update_system_config函数
    if add_customer_name_to_app():
        print("✅ 已成功更新app.py中的update_system_config函数")
    else:
        print("❌ 更新app.py中的update_system_config函数失败")
    
    # 2. 更新现有YAML文件
    if update_yaml_files():
        print("✅ 已成功更新现有YAML文件添加客户名")
    else:
        print("❌ 更新现有YAML文件失败")
    
    # 3. 创建客户名同步函数
    if create_customer_yaml_sync_function():
        print("✅ 已创建客户名同步函数")
    else:
        print("❌ 创建客户名同步函数失败")
    
    # 4. 更新system_detail函数
    if update_system_detail_function():
        print("✅ 已更新system_detail函数添加客户名同步功能")
    else:
        print("❌ 更新system_detail函数添加客户名同步功能失败")
    
    print("\n修复完成，请重启应用程序让修改生效")