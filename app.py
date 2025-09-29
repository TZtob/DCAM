# 注册get_user为Jinja2模板全局函数
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from functools import wraps
import asset_analyze
import os
import json
import yaml
import logging
import copy
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import tempfile
import shutil
from generate_cluster_yaml import generate_cluster_yaml

# 定义应用路径常量
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_DIR = os.path.join(DATA_DIR, 'db')
CUSTOMERS_DB = os.path.join(DB_DIR, 'customers.json')
SYSTEMS_DB = os.path.join(DB_DIR, 'systems.json')
ACCESS_LOG_DB = os.path.join(DB_DIR, 'access_log.json')
USERS_DB = os.path.join(DB_DIR, 'users.json')

# 配置日志记录
logging.basicConfig(
    filename='dcam.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
app.secret_key = 'dcam-secret-key-2025'  # 用于flash消息
app.debug = True  # 开启调试模式，方便查看错误

# 配置应用URL设置，防止与其他应用混淆
app.config['SERVER_NAME'] = None  # 不限制服务器名，允许通过IP访问
app.config['APPLICATION_ROOT'] = '/'  # 应用根路径
app.config['PREFERRED_URL_SCHEME'] = 'http'  # 默认URL方案

# 应用初始化函数
def init_application_environment():
    """初始化应用环境，确保工作目录和文件权限正确"""
    # 记录当前工作目录
    current_dir = os.getcwd()
    print(f"[系统初始化] 当前工作目录: {current_dir}")
    
    # 获取应用所在的绝对路径
    app_dir = os.path.abspath(os.path.dirname(__file__))
    print(f"[系统初始化] 应用目录: {app_dir}")
    
    # 在非Docker环境下，可能需要切换工作目录
    # 在Docker中，通常已经在正确的目录(/app)下
    is_docker = os.path.exists('/.dockerenv')
    print(f"[系统初始化] 是否在Docker环境中运行: {is_docker}")
    
    if not is_docker and current_dir != app_dir:
        try:
            os.chdir(app_dir)
            print(f"[系统初始化] 已切换工作目录: {os.getcwd()}")
        except Exception as e:
            print(f"[系统初始化] 切换工作目录失败: {str(e)}")
    
    # 确保目录结构存在
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(DB_DIR, exist_ok=True)
    
    # 处理旧数据库文件迁移 (如果数据库文件在旧位置，移动到新位置)
    old_db_files = {
        os.path.join(BASE_DIR, 'customers.json'): CUSTOMERS_DB,
        os.path.join(BASE_DIR, 'systems.json'): SYSTEMS_DB,
        os.path.join(BASE_DIR, 'access_log.json'): ACCESS_LOG_DB,
        os.path.join(BASE_DIR, 'users.json'): USERS_DB
    }
    
    for old_path, new_path in old_db_files.items():
        if os.path.exists(old_path) and not os.path.exists(new_path):
            try:
                print(f"[系统初始化] 迁移旧数据库文件: {old_path} -> {new_path}")
                # 先复制，成功后再删除，确保数据安全
                import shutil
                shutil.copy2(old_path, new_path)
                os.remove(old_path)
            except Exception as e:
                print(f"[系统初始化] 迁移数据库文件失败: {str(e)}")
    
    # 检查数据库文件的存在和权限
    for db_file in [CUSTOMERS_DB, SYSTEMS_DB, ACCESS_LOG_DB, USERS_DB]:
        # 如果文件不存在，创建一个空的JSON文件
        if not os.path.exists(db_file):
            try:
                with open(db_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
                print(f"[系统初始化] 创建空数据库文件: {db_file}")
            except Exception as e:
                print(f"[系统初始化] 创建数据库文件失败: {db_file} - {str(e)}")
        
        # 检查文件是否可读写
        try:
            with open(db_file, 'a+') as test_file:
                test_file.seek(0)
                test_file.read(1)  # 测试读取
            print(f"[系统初始化] 数据库文件可读写: {db_file}")
        except Exception as e:
            print(f"[系统初始化] 数据库文件访问异常: {db_file} - {str(e)}")
            # 尝试修复权限
            try:
                import stat
                os.chmod(db_file, stat.S_IWRITE | stat.S_IREAD)
                print(f"[系统初始化] 已尝试修复文件权限: {db_file}")
            except Exception as perm_e:
                print(f"[系统初始化] 修复权限失败: {str(perm_e)}")
    
    # Docker环境下的特殊处理
    if is_docker:
        print("[系统初始化] 正在进行Docker环境特殊配置")
        # 确保数据目录有正确的权限
        try:
            for dir_path in [DATA_DIR, DB_DIR]:
                # Docker中可能以非root用户运行，确保有足够权限
                os.chmod(dir_path, 0o777)  # 所有用户可读写执行
                print(f"[系统初始化] 已设置目录权限: {dir_path}")
        except Exception as e:
            print(f"[系统初始化] 设置目录权限失败: {str(e)}")
            
        # 打印卷挂载信息，帮助排查
        print("\n[系统初始化] Docker卷挂载信息:")
        try:
            with open('/proc/mounts', 'r') as f:
                mounts = [line for line in f if '/app' in line]
                for mount in mounts:
                    print(f"  {mount.strip()}")
        except Exception as e:
            print(f"  无法读取挂载信息: {str(e)}")

# 在应用启动时初始化环境
init_application_environment()

# 确保使用统一的文件上传目录结构
def get_system_uploads_dir(customer_name, system_name):
    """获取系统上传文件目录路径"""
    return f"data/customers/{customer_name}/{system_name}/uploads"

# 添加错误处理器
@app.errorhandler(500)
def internal_server_error(e):
    logging.error(f"500错误: {str(e)}")
    print(f"严重错误: {str(e)}")
    return "服务器内部错误，请查看日志了解详情", 500

# 配置日志记录钩子
@app.before_request
def log_request_info():
    # 记录每个请求的路径和参数，帮助排查问题
    logging.info(f"请求路径: {request.path}, 参数: {request.args}")
    
    # 在控制台中也输出请求信息
    print(f"DEBUG - 请求路径: {request.path}, 方法: {request.method}, 参数: {request.args}")

# 配置响应安全头
@app.after_request
def add_security_headers(response):
    """添加安全响应头，防止被其他应用影响"""
    # 防止点击劫持
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # 防止XSS攻击
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # 防止MIME类型嗅探
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # 引用者策略
    response.headers['Referrer-Policy'] = 'same-origin'
    
    # 内容安全策略（基本版）
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    
    return response

# 配置允许的文件扩展名
ALLOWED_EXTENSIONS = {'toml', 'conf', 'gz', 'tar.gz'}

# 数据存储文件 - 使用Docker友好的路径，确保数据持久化
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_DIR = os.path.join(DATA_DIR, 'db')  # 数据库文件专用目录
os.makedirs(DATA_DIR, exist_ok=True)  # 确保数据目录存在
os.makedirs(DB_DIR, exist_ok=True)  # 确保数据库目录存在

# 数据库文件路径 - 存储在挂载的data/db目录下以确保Docker持久化
CUSTOMERS_DB = os.path.join(DB_DIR, 'customers.json')
SYSTEMS_DB = os.path.join(DB_DIR, 'systems.json')
ACCESS_LOG_DB = os.path.join(DB_DIR, 'access_log.json')
USERS_DB = os.path.join(DB_DIR, 'users.json')

# 打印数据库文件路径，便于调试
print(f"数据库文件位置:")
print(f"CUSTOMERS_DB: {CUSTOMERS_DB}")
print(f"SYSTEMS_DB: {SYSTEMS_DB}")
print(f"当前工作目录: {os.getcwd()}")

# 注册自定义过滤器
@app.template_filter('datetime')
def format_datetime(value):
    """格式化日期时间"""
    if not value:
        return ''
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime('%Y-%m-%d %H:%M')
    except (ValueError, TypeError):
        return value

@app.template_filter('date')
def format_date(value):
    """格式化日期"""
    if not value:
        return ''
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        return value

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_json_db(filename):
    """加载JSON数据库文件"""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json_db(filename, data):
    """保存JSON数据库文件，返回操作是否成功"""
    print(f"\n[DB操作] 开始保存数据库文件: {filename}")
    print(f"[DB操作] 文件绝对路径: {os.path.abspath(filename)}")
    print(f"[DB操作] 当前工作目录: {os.getcwd()}")
    
    # 检查是否在Docker环境中运行
    is_docker = os.path.exists('/.dockerenv')
    if is_docker:
        print(f"[DB操作] 在Docker环境中运行，数据应持久化到挂载卷")
        
        # 检查文件是否在挂载的卷内
        if '/app/data' in os.path.abspath(filename):
            print(f"[DB操作] 文件位于挂载卷中，持久化应正常")
        else:
            print(f"[DB操作] 警告: 文件不在挂载卷中，可能会导致数据丢失")
    
    try:
        # 确保目标目录存在
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            print(f"[DB操作] 创建目录: {directory}")
            os.makedirs(directory, exist_ok=True)
            
            # 在Docker环境中设置正确的目录权限
            if is_docker:
                try:
                    os.chmod(directory, 0o777)  # 确保所有用户都有读写权限
                    print(f"[DB操作] 在Docker中设置目录权限: {directory}")
                except Exception as perm_e:
                    print(f"[DB操作] 设置目录权限失败: {str(perm_e)}")
        
        # 检查文件权限
        if os.path.exists(filename):
            try:
                # 测试文件是否可写
                with open(filename, 'a') as test:
                    pass
                print(f"[DB操作] 文件存在且可写: {filename}")
            except PermissionError:
                print(f"[DB操作] 警告: 文件权限错误，尝试修改权限: {filename}")
                try:
                    import stat
                    os.chmod(filename, stat.S_IWRITE | stat.S_IREAD)
                except Exception as perm_e:
                    print(f"[DB操作] 修改权限失败: {str(perm_e)}")
            except Exception as access_e:
                print(f"[DB操作] 文件访问异常: {str(access_e)}")
        
        # 先写入临时文件，成功后再重命名，避免写入过程中的中断导致文件损坏
        temp_filename = f"{filename}.tmp"
        print(f"[DB操作] 写入临时文件: {temp_filename}")
        with open(temp_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()  # 确保数据写入磁盘
            os.fsync(f.fileno())  # 在Linux上强制同步文件系统
        
        # 备份现有文件（如果存在）
        if os.path.exists(filename):
            backup_filename = f"{filename}.bak"
            if os.path.exists(backup_filename):
                print(f"[DB操作] 删除旧备份: {backup_filename}")
                os.remove(backup_filename)
            print(f"[DB操作] 创建新备份: {filename} -> {backup_filename}")
            os.rename(filename, backup_filename)
        
        # 将临时文件重命名为正式文件
        print(f"[DB操作] 重命名临时文件为正式文件: {temp_filename} -> {filename}")
        os.rename(temp_filename, filename)
        
        # 验证文件是否写入成功
        if os.path.exists(filename):
            print(f"[DB操作] 验证成功: 文件已写入 {filename}, 大小: {os.path.getsize(filename)} 字节")
            return True
        else:
            print(f"[DB操作] 验证失败: 文件不存在 {filename}")
            return False
    except Exception as e:
        print(f"[DB操作] 错误: 保存数据库文件 {filename} 失败: {str(e)}")
        # 如果临时文件存在，清理它
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except Exception as clean_e:
                print(f"[DB操作] 清理临时文件失败: {str(clean_e)}")
        
        # 尝试使用备用方法写入文件
        try:
            print(f"[DB操作] 尝试备用方法写入文件: {filename}")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            if os.path.exists(filename):
                print(f"[DB操作] 备用方法成功: 文件已写入 {filename}")
                return True
            else:
                print(f"[DB操作] 备用方法失败: 文件不存在 {filename}")
        except Exception as backup_e:
            print(f"[DB操作] 备用方法失败: {str(backup_e)}")
        
        return False

def get_customers():
    """获取所有客户"""
    try:
        customers_data = load_json_db(CUSTOMERS_DB)
        # 检查是否成功加载
        if customers_data is None:
            print(f"[警告] 无法加载客户数据，返回空字典")
            return {}
        return customers_data
    except Exception as e:
        print(f"[错误] 获取客户数据失败: {str(e)}")
        # 尝试使用备份文件
        try:
            backup_file = f"{CUSTOMERS_DB}.bak"
            if os.path.exists(backup_file):
                print(f"[恢复] 尝试从备份恢复客户数据: {backup_file}")
                with open(backup_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        # 如果都失败了，返回空字典
        return {}

def get_systems(customer_id=None):
    """获取系统列表，可选择按客户过滤"""
    systems_data = {}
    
    # 尝试加载系统数据
    try:
        systems_data = load_json_db(SYSTEMS_DB)
        if systems_data is None:
            print(f"[警告] 无法加载系统数据，返回空字典")
            return {}
    except Exception as e:
        print(f"[错误] 加载系统数据失败: {str(e)}")
        
        # 尝试从备份恢复
        try:
            backup_file = f"{SYSTEMS_DB}.bak"
            if os.path.exists(backup_file):
                print(f"[恢复] 尝试从备份恢复系统数据: {backup_file}")
                with open(backup_file, 'r', encoding='utf-8') as f:
                    systems_data = json.load(f)
        except Exception as backup_e:
            print(f"[错误] 从备份恢复失败: {str(backup_e)}")
            return {}
    
    # 处理系统数据
    for system_id, sys in systems_data.items():
        # 兼容旧数据，补充archived字段
        if 'archived' not in sys:
            sys['archived'] = False
        
        # 计算SFA设备数量
        sfa_device_count = 0
        yaml_file = sys.get('yaml_file')
        if yaml_file and os.path.exists(yaml_file):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    yaml_data = yaml.safe_load(f)
                    # 如果YAML文件中有clusters数据，计算SFA设备总数
                    if yaml_data and 'clusters' in yaml_data:
                        for cluster in yaml_data['clusters']:
                            if 'devices' in cluster:
                                devices = cluster['devices']
                                if isinstance(devices, list):
                                    sfa_device_count += len(devices)
                                elif isinstance(devices, dict):  # 处理可能的字典形式
                                    sfa_device_count += 1
            except Exception as e:
                print(f"计算系统 {system_id} 的SFA设备数量出错: {str(e)}")
        
        # 添加SFA设备数量
        sys['sfa_device_count'] = sfa_device_count
    
    # 如果指定了客户ID，按客户过滤
    if customer_id:
        filtered_systems = {}
        for system_id, system in systems_data.items():
            if system.get('customer_id') == customer_id:
                filtered_systems[system_id] = system
        return filtered_systems
    
    return systems_data

def log_access(entity_type, entity_id):
    """记录访问日志"""
    access_logs = load_json_db(ACCESS_LOG_DB)
    
    # 初始化日志结构（如果不存在）
    if 'customers' not in access_logs:
        access_logs['customers'] = {}
    if 'systems' not in access_logs:
        access_logs['systems'] = {}
    
    current_time = datetime.now().isoformat()
    
    # 记录访问时间
    if entity_type == 'customer':
        access_logs['customers'][entity_id] = current_time
    elif entity_type == 'system':
        access_logs['systems'][entity_id] = current_time
    
    save_json_db(ACCESS_LOG_DB, access_logs)


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

def convert_conf_to_toml(conf_file_path, toml_file_path):
    """将 exascaler.conf 格式转换为 exascaler.toml 格式"""
    try:
        import configparser
        import toml
        
        # 创建configparser实例，允许重复的选项名
        config = configparser.ConfigParser(allow_no_value=True)
        config.optionxform = str  # 保持键的大小写
        config.read(conf_file_path, encoding='utf-8')
        
        # 转换为字典结构
        toml_data = {}
        
        for section_name in config.sections():
            section = config[section_name]
            section_dict = {}
            
            for key, value in section.items():
                if value is None:
                    section_dict[key] = True  # 无值的配置项作为布尔值处理
                    continue
                    
                # 处理不同类型的值
                # 尝试转换为数字
                try:
                    if '.' in value:
                        section_dict[key] = float(value)
                    else:
                        section_dict[key] = int(value)
                except ValueError:
                    # 处理布尔值
                    if value.lower() in ('true', 'yes', '1', 'on'):
                        section_dict[key] = True
                    elif value.lower() in ('false', 'no', '0', 'off'):
                        section_dict[key] = False
                    else:
                        # 处理字符串值，移除引号
                        section_dict[key] = value.strip('"\'')
            
            # 处理特殊的节名格式（如 sfa SFA_NAME）
            if section_name.startswith('sfa '):
                # EXAScaler 格式: [sfa SFA_NAME] -> ["sfa SFA_NAME"]
                toml_data[section_name] = section_dict
            else:
                # 普通节名
                toml_data[section_name] = section_dict
        
        # 后处理：确保生成的TOML符合EXAScaler期望的格式
        # 如果有SFA相关的节，确保它们的格式正确
        processed_data = {}
        for key, value in toml_data.items():
            if key.startswith('sfa '):
                # 确保SFA节有正确的controllers格式
                if 'controllers' in value and isinstance(value['controllers'], str):
                    # 如果controllers是空格分隔的字符串，转换为正确格式
                    controllers = value['controllers'].split()
                    if len(controllers) >= 2:
                        value['controllers'] = controllers[:2]  # 只取前两个控制器IP
                processed_data[key] = value
            else:
                processed_data[key] = value
        
        # 写入TOML文件
        with open(toml_file_path, 'w', encoding='utf-8') as f:
            toml.dump(processed_data, f)
        
        app.logger.info(f"成功将 {conf_file_path} 转换为 {toml_file_path}")
        return True
        
    except Exception as e:
        app.logger.error(f"配置文件转换失败: {str(e)}")
        return False

def get_recent_items(entity_type, limit=5):
    """获取最近访问的实体"""
    access_logs = load_json_db(ACCESS_LOG_DB)
    
    if entity_type not in access_logs or not access_logs[entity_type]:
        return []
    
    # 按访问时间排序
    sorted_items = sorted(
        access_logs[entity_type].items(),
        key=lambda x: x[1],
        reverse=True
    )[:limit]
    
    # 获取实体ID
    entity_ids = [item[0] for item in sorted_items]
    
    # 获取实体详细信息
    if entity_type == 'customers':
        entities = get_customers()
        return [
            {
                'id': entity_id,
                'name': entities.get(entity_id, {}).get('name', '未知客户'),
                'last_accessed_at': access_logs[entity_type][entity_id]
            }
            for entity_id in entity_ids if entity_id in entities
        ]
    elif entity_type == 'systems':
        entities = get_systems()
        return [
            {
                'id': entity_id,
                'name': entities.get(entity_id, {}).get('name', '未知系统'),
                'customer_name': entities.get(entity_id, {}).get('customer_name', ''),
                'last_accessed_at': access_logs[entity_type][entity_id]
            }
            for entity_id in entity_ids if entity_id in entities
        ]
    
    return []

# ========== 用户认证相关函数 ==========

def load_users():
    """加载用户数据"""
    return load_json_db(USERS_DB)

def save_users(users):
    """保存用户数据"""
    save_json_db(USERS_DB, users)

def create_user(username, password, role='user'):
    """创建新用户"""
    users = load_users()
    if username in users:
        return False
    
    users[username] = {
        'password_hash': generate_password_hash(password),
        'role': role,
        'created_at': datetime.now().isoformat()
    }
    save_users(users)
    return True

def verify_user(username, password):
    """验证用户凭证"""
    users = load_users()
    if username not in users:
        return False
    
    return check_password_hash(users[username]['password_hash'], password)

def get_user(username):
    """获取用户信息"""

    users = load_users()
    return users.get(username)

def is_safe_url(target):
    """检查重定向URL是否安全（仅允许DCAM应用内部的相对URL）"""
    if not target:
        return False
    
    # 检查是否包含外部域名或协议
    if any(target.startswith(scheme) for scheme in ['http://', 'https://', 'ftp://', '//']):
        return False
    
    # 检查是否包含可能的恶意字符
    if any(char in target for char in ['@', '\\', '\n', '\r', '\t']):
        return False
    
    # 只允许以/开头的相对路径，且必须是DCAM应用的路径
    if target.startswith('/') and not target.startswith('//'):
        # 额外检查：确保路径看起来像DCAM应用的路径
        # 允许的路径模式：/, /login, /customers, /systems, /search等
        allowed_patterns = [
            '/', '/login', '/logout', '/change_password',
            '/customers', '/systems', '/search',
            '/api/', '/customer/', '/systems/'
        ]
        
        # 检查是否匹配允许的路径模式
        for pattern in allowed_patterns:
            if target.startswith(pattern):
                return True
        
        # 如果不匹配任何已知模式，返回False
        return False
    
    return False

# 注册get_user为Jinja2模板全局函数
app.jinja_env.globals['get_user'] = get_user

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def init_default_user():
    """初始化默认管理员用户"""
    users = load_users()
    if not users:  # 如果没有用户，创建默认管理员
        create_user('admin', 'admin123', 'admin')
        print("Created default admin user: admin/admin123")

# 客户与 YAML 文件映射（扩展为动态映射）
def get_customer_yaml_mapping():
    """获取客户和YAML文件的映射关系"""
    yaml_files = {}
    try:
        # 寻找所有客户的YAML文件
        data_dir = 'data'
        if os.path.exists(data_dir):
            for filename in os.listdir(data_dir):
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    filepath = os.path.join(data_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)
                            if data and 'customer' in data:
                                yaml_files[data['customer']] = filepath
                    except Exception as e:
                        logging.error(f"读取YAML文件 {filepath} 时出错: {str(e)}")
        
        # 另外读取项目根目录下的yaml文件
        for filename in os.listdir('.'):
            if filename.endswith('.yaml') or filename.endswith('.yml'):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                        if data and 'customer' in data:
                            yaml_files[data['customer']] = filename
                except Exception as e:
                    logging.error(f"读取YAML文件 {filename} 时出错: {str(e)}")
    except Exception as e:
        logging.error(f"获取客户YAML文件映射时出错: {str(e)}")
    
    # 如果没有找到任何客户，添加默认客户用于测试
    if not yaml_files:
        yaml_files["测试客户"] = "byd_ddn_clusters.yaml"
        
    return yaml_files

def is_expired(system):
    try:
        created = datetime.fromisoformat(system.get('created_at', ''))
        return (datetime.now() - created).days > 365
    except Exception:
        return False

# 注册为Jinja2模板全局函数
app.jinja_env.globals['is_expired'] = is_expired

# 归档系统
@app.route('/systems/<system_id>/archive', methods=['POST'])
@login_required
def archive_system(system_id):
    systems = get_systems()
    if system_id not in systems:
        flash('系统不存在', 'error')
        return redirect(url_for('systems_list'))
    system = systems[system_id]
    # 仅管理员可归档
    user = get_user(session['username'])
    if not user or user.get('role') != 'admin':
        flash('仅管理员可归档', 'error')
        return redirect(url_for('system_detail', system_id=system_id))
    system['archived'] = True
    save_json_db(SYSTEMS_DB, systems)
    flash('系统已归档', 'success')
    return redirect(url_for('system_detail', system_id=system_id))

# 解除归档
@app.route('/systems/<system_id>/unarchive', methods=['POST'])
@login_required
def unarchive_system(system_id):
    systems = get_systems()
    if system_id not in systems:
        flash('系统不存在', 'error')
        return redirect(url_for('systems_list'))
    system = systems[system_id]
    # 仅管理员可解除归档
    user = get_user(session['username'])
    if not user or user.get('role') != 'admin':
        flash('仅管理员可解除归档', 'error')
        return redirect(url_for('system_detail', system_id=system_id))
    system['archived'] = False
    save_json_db(SYSTEMS_DB, systems)
    flash('已解除归档', 'success')
    return redirect(url_for('system_detail', system_id=system_id))

# 删除系统
@app.route('/systems/<system_id>/delete', methods=['POST'])
@login_required
def delete_system(system_id):
    """删除系统"""
    systems = get_systems()
    if system_id not in systems:
        flash('系统不存在', 'error')
        return redirect(url_for('systems_list'))
    
    # 仅管理员可删除
    user = get_user(session['username'])
    if not user or user.get('role') != 'admin':
        flash('仅管理员可删除系统', 'error')
        return redirect(url_for('system_detail', system_id=system_id))
    
    system = systems[system_id]
    system_name = system.get('name', 'Unknown System')
    customer_name = system.get('customer_name', '')
    
    try:
        # 1. 保存删除前的数据（用于回滚）
        old_systems = copy.deepcopy(systems)
        old_access_logs = None
        
        # 2. 从系统数据库中删除
        systems.pop(system_id)
        success = save_json_db(SYSTEMS_DB, systems)
        if not success:
            flash('系统数据库更新失败，操作已取消', 'error')
            return redirect(url_for('system_detail', system_id=system_id))
        
        # 3. 从访问日志中删除系统相关记录
        access_logs = load_json_db(ACCESS_LOG_DB)
        old_access_logs = copy.deepcopy(access_logs)
        if 'systems' in access_logs and system_id in access_logs['systems']:
            access_logs['systems'].pop(system_id)
            success = save_json_db(ACCESS_LOG_DB, access_logs)
            if not success:
                # 如果访问日志更新失败，回滚系统数据库
                save_json_db(SYSTEMS_DB, old_systems)
                flash('访问日志更新失败，操作已取消', 'error')
                return redirect(url_for('system_detail', system_id=system_id))
        
        # 4. 在数据库更新成功后，尝试删除文件（即使失败也不影响数据库操作）
        # 删除系统的YAML文件
        if system.get('yaml_file') and os.path.exists(system['yaml_file']):
            try:
                os.remove(system['yaml_file'])
            except Exception as e:
                flash(f'删除系统 {system_name} 的资产文件失败：{str(e)}', 'warning')
                print(f"删除YAML文件失败: {str(e)}")
        
        # 删除系统的上传文件目录（配置文件和日志文件）
        if customer_name and system_name:
            system_uploads_dir = get_system_uploads_dir(customer_name, system_name)
            if os.path.exists(system_uploads_dir):
                try:
                    # 先尝试删除只读文件属性
                    import stat
                    for root, dirs, files in os.walk(system_uploads_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                os.chmod(file_path, stat.S_IWRITE)
                            except Exception:
                                pass  # 忽略权限错误，继续处理
                    
                    # 等待一小段时间，允许可能的文件锁释放
                    import time
                    time.sleep(0.5)
                    
                    # 现在尝试删除目录
                    import shutil
                    shutil.rmtree(system_uploads_dir, ignore_errors=True)
                    print(f"已删除系统上传文件目录: {system_uploads_dir}")
                    
                    # 如果目录仍然存在，则提示用户
                    if os.path.exists(system_uploads_dir):
                        print(f"警告：系统上传目录仍然存在: {system_uploads_dir}，可能需要手动删除")
                        flash(f'系统 {system_name} 的上传目录可能需要手动删除', 'warning')
                except Exception as e:
                    flash(f'删除系统 {system_name} 的上传文件目录失败：{str(e)}', 'warning')
                    print(f"删除系统上传文件目录失败: {str(e)}")
                    # 目录删除失败但数据库已更新，所以系统数据仍然被成功删除了
        
        flash(f'系统 {system_name} 已成功删除！', 'success')
    except Exception as e:
        # 捕获所有未处理的异常，并尝试回滚
        print(f"删除系统时发生未处理的异常: {str(e)}")
        if 'old_systems' in locals():
            save_json_db(SYSTEMS_DB, old_systems)
        if 'old_access_logs' in locals() and old_access_logs is not None:
            save_json_db(ACCESS_LOG_DB, old_access_logs)
        flash(f'删除系统 {system_name} 时发生错误：{str(e)}', 'error')
    
    # 确保重定向，即使发生异常
    return redirect(url_for('systems_list'))

def get_customer_yaml_mapping():
    """动态获取客户YAML映射"""
    customers = get_customers()
    mapping = {}
    for customer_id, customer_info in customers.items():
        yaml_file = customer_info.get('yaml_file')
        if yaml_file and os.path.exists(yaml_file):
            mapping[customer_info['name']] = yaml_file
    
    # 保留原有的静态映射作为备用
    mapping.update({
        'BYD': 'byd_ddn_clusters.yaml',
    })
    return mapping

# 查询类型映射
QUERY_TYPES = {
    0: "所有查询",
    1: "设备数量统计",
    2: "SFA版本详情",
    3: "EXA版本详情", 
    4: "BBU过期日期计算",
    5: "集群容量查询",
    6: "设备序列号查询",
    7: "集群IP地址查询"
}

# ========== 用户认证路由 ==========

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    # 日志记录，用于调试
    logging.info(f"Login route accessed: Path={request.path}, Args={request.args}, Remote={request.remote_addr}")
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if verify_user(username, password):
            session['username'] = username
            session['user_role'] = get_user(username)['role']
            flash('登录成功', 'success')
            
            # 重定向到登录前访问的页面，但只允许内部URL
            next_page = request.args.get('next')
            
            # 检查next_page是否是安全的内部URL
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            else:
                # 没有next参数或不安全，重定向到主页
                return redirect(url_for('index'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """用户注销"""
    session.clear()
    flash('已成功退出登录', 'info')
    
    # 重定向到登录页面
    return redirect(url_for('login'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证当前密码
        if not verify_user(session['username'], current_password):
            flash('当前密码错误', 'error')
            return render_template('change_password.html')
        
        # 验证新密码
        if len(new_password) < 6:
            flash('新密码长度至少6位', 'error')
            return render_template('change_password.html')
            
        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'error')
            return render_template('change_password.html')
        
        # 更新密码
        users = load_users()
        users[session['username']]['password_hash'] = generate_password_hash(new_password)
        save_users(users)
        
        flash('密码修改成功！', 'success')
        return redirect(url_for('index'))
    
    return render_template('change_password.html')

@app.route('/customer/<customer_name>')
def customer_page(customer_name):
    """客户页面：显示查询选项"""
    logging.info(f"访问客户页面: {customer_name}")
    print(f"DEBUG: 访问客户页面 {customer_name}")
    customer_yaml_mapping = get_customer_yaml_mapping()
    if customer_name not in customer_yaml_mapping:
        flash(f"客户 {customer_name} 不存在", "error")
        return redirect(url_for('index'))
    
    yaml_file = customer_yaml_mapping[customer_name]
    # 获取可用的资产所有者列表
    asset_owners = asset_analyze.get_asset_owners(yaml_file)
    
    return render_template('customer.html', 
                         customer_name=customer_name, 
                         query_types=QUERY_TYPES,
                         asset_owners=asset_owners)

@app.route('/api/cluster_names/<customer_name>')
def get_cluster_names_api(customer_name):
    """API：根据客户和资产所有者获取集群名称列表"""
    customer_yaml_mapping = get_customer_yaml_mapping()
    if customer_name not in customer_yaml_mapping:
        return jsonify([])
    
    yaml_file = customer_yaml_mapping[customer_name]
    asset_owner = request.args.get('asset_owner')
    cluster_names = asset_analyze.get_cluster_names(yaml_file, asset_owner)
    
    return jsonify(cluster_names)

@app.route('/customer/<customer_name>/query', methods=['POST'])
def execute_query(customer_name):
    """执行查询"""
    customer_yaml_mapping = get_customer_yaml_mapping()
    if customer_name not in customer_yaml_mapping:
        return f"客户 {customer_name} 不存在", 404
    
    query_type = int(request.form.get('query_type'))
    asset_owner = request.form.get('asset_owner', '').strip() or None
    cluster_name = request.form.get('cluster_name', '').strip() or None
    
    yaml_file = customer_yaml_mapping[customer_name]
    yaml_path = os.path.join(os.path.dirname(__file__), yaml_file)
    
    result = asset_analyze.query_customer_info(
        yaml_path=yaml_path,
        query_type=query_type,
        asset_owner=asset_owner,
        cluster_name=cluster_name
    )
    
    return render_template('result.html',
                         customer_name=customer_name,
                         query_type=QUERY_TYPES.get(query_type),
                         result=result)

# ==================== 新增功能路由 ====================

@app.route('/')
@login_required
def index():
    """主页：显示最近访问的客户和系统"""
    # 获取最近访问数据
    recent_customers = get_recent_items('customers')
    recent_systems = get_recent_items('systems')
    
    return render_template('main_index.html', 
                          recent_customers=recent_customers, 
                          recent_systems=recent_systems)

@app.route('/search')
@login_required
def search():
    """全局搜索功能"""
    query = request.args.get('q', '').strip().lower()
    
    if not query:
        flash('请输入搜索关键词', 'warning')
        return redirect(url_for('index'))
    
    customers = get_customers()
    systems = get_systems()
    
    # 搜索结果
    customer_results = []
    system_results = []
    
    # 搜索客户
    for customer_id, customer in customers.items():
        if query in customer.get('name', '').lower():
            customer_results.append({
                'id': customer_id,
                'name': customer.get('name'),
                'contact': customer.get('contact', ''),
                'email': customer.get('email', ''),
                'created_at': customer.get('created_at', '')
            })
    
    # 搜索系统
    for system_id, system in systems.items():
        if query in system.get('name', '').lower() or query in system.get('customer_name', '').lower():
            system_results.append({
                'id': system_id,
                'name': system.get('name'),
                'customer_name': system.get('customer_name', ''),
                'customer_id': system.get('customer_id', ''),
                'status': system.get('status', ''),
                'created_at': system.get('created_at', '')
            })
    
    return render_template('search_results.html', 
                          query=query,
                          customer_results=customer_results,
                          system_results=system_results)

@app.route('/customers')
@login_required
def customers_list():
    """客户管理页面"""
    customers = get_customers()
    systems = get_systems()
    
    # 计算每个客户下的系统数量
    systems_count = {}
    for system_id, system in systems.items():
        customer_id = system.get('customer_id')
        if customer_id:
            systems_count[customer_id] = systems_count.get(customer_id, 0) + 1
    
    return render_template('customers.html', customers=customers, systems_count=systems_count)

@app.route('/customers/<customer_id>')
@login_required
def customer_detail(customer_id):
    """客户详情页面"""
    customers = get_customers()
    if customer_id not in customers:
        flash('客户不存在', 'error')
        return redirect(url_for('customers_list'))
    
    # 记录客户访问
    log_access('customer', customer_id)
    
    customer = customers[customer_id]
    systems = get_systems(customer_id)
    
    return render_template('customer_detail.html', 
                         customer=customer,
                         customer_id=customer_id,
                         systems=systems)

@app.route('/customers/new', methods=['GET', 'POST'])
@login_required
def new_customer():
    """新建客户"""
    if request.method == 'POST':
        name = request.form.get('name')
        contact = request.form.get('contact', '')
        email = request.form.get('email', '')
        description = request.form.get('description', '')
        
        if not name:
            flash('客户名称不能为空', 'error')
            return render_template('new_customer.html')
        
        customers = get_customers()
        customer_id = str(len(customers) + 1)
        
        customers[customer_id] = {
            'name': name,
            'contact': contact,
            'email': email,
            'description': description,
            'created_at': datetime.now().isoformat()
        }
        
        save_json_db(CUSTOMERS_DB, customers)
        flash(f'客户 {name} 创建成功！', 'success')
        return redirect(url_for('customers_list'))
    
    return render_template('new_customer.html')

@app.route('/customers/<customer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    """编辑客户"""
    customers = get_customers()
    if customer_id not in customers:
        flash('客户不存在', 'error')
        return redirect(url_for('customers_list'))
    
    customer = customers[customer_id]
    
    if request.method == 'POST':
        name = request.form.get('name')
        contact = request.form.get('contact', '')
        email = request.form.get('email', '')
        description = request.form.get('description', '')
        
        if not name:
            flash('客户名称不能为空', 'error')
            return render_template('edit_customer.html', customer=customer, customer_id=customer_id)
        
        # 更新系统中的客户名称引用
        if name != customer['name']:
            systems = get_systems()
            for system_id, system in systems.items():
                if system.get('customer_id') == customer_id:
                    system['customer_name'] = name
            save_json_db(SYSTEMS_DB, systems)
        
        # 更新客户信息
        customers[customer_id].update({
            'name': name,
            'contact': contact,
            'email': email,
            'description': description,
            'updated_at': datetime.now().isoformat()
        })
        
        save_json_db(CUSTOMERS_DB, customers)
        flash(f'客户 {name} 更新成功！', 'success')
        return redirect(url_for('customer_detail', customer_id=customer_id))
    
    return render_template('edit_customer.html', customer=customer, customer_id=customer_id)

@app.route('/customers/<customer_id>/delete', methods=['GET', 'POST'])
def delete_customer(customer_id):
    """删除客户"""
    customers = get_customers()
    if customer_id not in customers:
        flash('客户不存在', 'error')
        return redirect(url_for('customers_list'))
    
    # 如果是GET请求，重定向到客户列表（防止直接访问删除链接）
    if request.method == 'GET':
        return redirect(url_for('customers_list'))
    
    customer_name = customers[customer_id]['name']
    
    try:
        # 1. 保存删除前的数据（用于回滚）
        old_customers = copy.deepcopy(customers)
        old_systems = copy.deepcopy(get_systems())
        old_access_logs = copy.deepcopy(load_json_db(ACCESS_LOG_DB))
        
        # 2. 收集需要删除的系统信息
        systems = old_systems  # 使用复制的系统数据
        systems_to_delete = []
        affected_systems_info = []  # 存储需要处理文件的系统信息
        
        for system_id, system in systems.items():
            if system.get('customer_id') == customer_id:
                systems_to_delete.append(system_id)
                system_name = system.get('name', '')
                yaml_file = system.get('yaml_file')
                
                affected_systems_info.append({
                    'id': system_id,
                    'name': system_name,
                    'yaml_file': yaml_file
                })
        
        # 3. 更新系统数据库
        for system_id in systems_to_delete:
            systems.pop(system_id)
        
        if not save_json_db(SYSTEMS_DB, systems):
            flash('系统数据库更新失败，操作已取消', 'error')
            return redirect(url_for('customer_detail', customer_id=customer_id))
        
        # 4. 更新访问日志
        access_logs = load_json_db(ACCESS_LOG_DB)
        if 'customers' in access_logs and customer_id in access_logs['customers']:
            access_logs['customers'].pop(customer_id)
        
        # 同时删除相关系统的访问记录
        if 'systems' in access_logs:
            for system_id in systems_to_delete:
                if system_id in access_logs['systems']:
                    access_logs['systems'].pop(system_id)
        
        if not save_json_db(ACCESS_LOG_DB, access_logs):
            # 回滚系统数据库
            save_json_db(SYSTEMS_DB, old_systems)
            flash('访问日志更新失败，操作已取消', 'error')
            return redirect(url_for('customer_detail', customer_id=customer_id))
        
        # 5. 更新客户数据库
        customers.pop(customer_id)
        if not save_json_db(CUSTOMERS_DB, customers):
            # 回滚之前的更改
            save_json_db(SYSTEMS_DB, old_systems)
            save_json_db(ACCESS_LOG_DB, old_access_logs)
            flash('客户数据库更新失败，操作已取消', 'error')
            return redirect(url_for('customer_detail', customer_id=customer_id))
        
        # 6. 数据库更新成功后，处理文件删除操作（这些操作失败不会影响数据库更新）
        # 删除系统文件
        for system_info in affected_systems_info:
            system_name = system_info['name']
            yaml_file = system_info['yaml_file']
            
            # 删除系统的YAML文件
            if yaml_file and os.path.exists(yaml_file):
                try:
                    os.remove(yaml_file)
                    print(f"已删除系统YAML文件: {yaml_file}")
                except Exception as e:
                    flash(f'删除系统 {system_name} 的资产文件失败：{str(e)}', 'warning')
                    print(f"删除系统YAML文件失败: {str(e)}")
            
            # 删除系统的上传文件目录
            if customer_name and system_name:
                system_uploads_dir = get_system_uploads_dir(customer_name, system_name)
                if os.path.exists(system_uploads_dir):
                    try:
                        # 先尝试删除只读文件属性
                        import stat
                        for root, dirs, files in os.walk(system_uploads_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                try:
                                    os.chmod(file_path, stat.S_IWRITE)
                                except Exception:
                                    pass  # 忽略权限错误，继续处理
                        
                        # 等待一小段时间，允许可能的文件锁释放
                        import time
                        time.sleep(0.5)
                        
                        # 现在尝试删除目录
                        shutil.rmtree(system_uploads_dir, ignore_errors=True)
                        print(f"已删除系统上传文件目录: {system_uploads_dir}")
                        
                        # 如果目录仍然存在，则提示用户
                        if os.path.exists(system_uploads_dir):
                            print(f"警告：系统上传目录仍然存在: {system_uploads_dir}，可能需要手动删除")
                            flash(f'系统 {system_name} 的上传目录可能需要手动删除', 'warning')
                    except Exception as e:
                        flash(f'删除系统 {system_name} 的上传文件目录失败：{str(e)}', 'warning')
                        print(f"删除系统上传文件目录失败: {str(e)}")
        
        # 删除客户目录
        customer_dir = f"data/customers/{customer_name}"
        if os.path.exists(customer_dir):
            try:
                # 先尝试删除只读文件属性
                import stat
                for root, dirs, files in os.walk(customer_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            os.chmod(file_path, stat.S_IWRITE)
                        except Exception:
                            pass  # 忽略权限错误，继续处理
                
                # 等待一小段时间，允许可能的文件锁释放
                import time
                time.sleep(0.5)
                
                # 现在尝试删除整个目录树
                shutil.rmtree(customer_dir, ignore_errors=True)
                print(f"已删除客户目录: {customer_dir}")
                
                # 双重检查，如果目录仍然存在则通知用户
                if os.path.exists(customer_dir):
                    print(f"警告：客户目录仍然存在: {customer_dir}，可能需要手动删除")
                    flash(f'客户 {customer_name} 的某些文件可能需要手动删除', 'warning')
            except Exception as e:
                flash(f'删除客户 {customer_name} 的目录失败：{str(e)}', 'warning')
                print(f"删除客户目录失败: {str(e)}")
                # 目录删除失败但数据库已更新，所以客户数据仍然被成功删除了
        
        flash(f'客户 {customer_name} 及其所有系统已成功删除！', 'success')
    
    except Exception as e:
        # 捕获所有未处理的异常，并尝试回滚
        print(f"删除客户时发生未处理的异常: {str(e)}")
        # 尝试回滚所有数据库操作
        if 'old_customers' in locals():
            save_json_db(CUSTOMERS_DB, old_customers)
        if 'old_systems' in locals():
            save_json_db(SYSTEMS_DB, old_systems)
        if 'old_access_logs' in locals():
            save_json_db(ACCESS_LOG_DB, old_access_logs)
        flash(f'删除客户 {customer_name} 时发生错误：{str(e)}', 'error')
    
    # 确保重定向，即使发生异常
    return redirect(url_for('customers_list'))

@app.route('/systems')
@login_required
def systems_list():
    """系统管理页面"""
    # 获取可能的客户ID过滤参数
    customer_id = request.args.get('customer_id')
    
    # 如果指定了客户ID，记录访问
    if customer_id:
        log_access('customer', customer_id)
    
    # 获取系统和客户数据
    systems = get_systems(customer_id)
    customers = get_customers()
    
    return render_template('systems.html', systems=systems, customers=customers, filter_customer_id=customer_id)

@app.route('/systems/new', methods=['GET', 'POST'])
@login_required
def new_system():
    """新建系统"""
    customers = get_customers()
    
    # 从URL参数中获取预选的客户ID
    selected_customer_id = request.args.get('customer_id', '')
    
    if request.method == 'POST':
        name = request.form.get('name')
        customer_id = request.form.get('customer_id')
        description = request.form.get('description', '')
        
        if not name or not customer_id:
            flash('系统名称和客户不能为空', 'error')
            return render_template('new_system.html', customers=customers, selected_customer_id=selected_customer_id)
        
        if customer_id not in customers:
            flash('选择的客户不存在', 'error')
            return render_template('new_system.html', customers=customers, selected_customer_id=selected_customer_id)
        
        systems = get_systems()
        
        # 🔧 系统名称冲突检测：同一客户内系统名必须唯一
        for existing_id, existing_system in systems.items():
            if (existing_system.get('name') == name and 
                existing_system.get('customer_id') == customer_id):
                flash(f'客户 {customers[customer_id]["name"]} 下已存在名为 "{name}" 的系统，请使用其他名称', 'error')
                return render_template('new_system.html', customers=customers)
        
        system_id = str(len(systems) + 1)
        customer_name = customers[customer_id]['name']
        
        # 🔧 新的层级化文件路径：data/customers/客户名/系统名/系统名_clusters.yaml
        yaml_filename = f"data/customers/{customer_name}/{name}/{name}_clusters.yaml"
        
        # 创建系统目录结构
        system_dir = f"data/customers/{customer_name}/{name}"
        reports_dir = f"{system_dir}/reports"
        os.makedirs(system_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)
        
        systems[system_id] = {
            'name': name,
            'customer_id': customer_id,
            'customer_name': customer_name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'status': 'created',  # created, configured, imported, deployed
            'yaml_file': yaml_filename  # 层级化文件路径
        }
        
        save_json_db(SYSTEMS_DB, systems)
        flash(f'系统 {name} 创建成功！YAML文件将使用: {yaml_filename}', 'success')
        return redirect(url_for('customer_detail', customer_id=customer_id))
    
    return render_template('new_system.html', customers=customers, selected_customer_id=selected_customer_id)

@app.route('/systems/<system_id>/import', methods=['GET', 'POST'])
@login_required
def import_config(system_id):
    """导入配置文件"""
    systems = get_systems()
    if system_id not in systems:
        flash('系统不存在', 'error')
        return redirect(url_for('systems_list'))
    
    system = systems[system_id]
    
    if request.method == 'POST':
        # 处理exascaler配置文件上传（支持.toml和.conf格式）
        config_file = request.files.get('toml_file')
        if not config_file or config_file.filename == '':
            flash('请选择exascaler配置文件（支持.toml或.conf格式）', 'error')
            return render_template('import_config.html', system=system)
        
        # 处理sfa log文件上传
        sfa_files = request.files.getlist('sfa_files')
        if not sfa_files or all(f.filename == '' for f in sfa_files):
            flash('请选择至少一个SFA log文件', 'error')
            return render_template('import_config.html', system=system)
        
        # 保存上传的文件
        import tempfile
        import os
        
        try:
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            
            # 保存配置文件
            config_filename = secure_filename(config_file.filename)
            config_path = os.path.join(temp_dir, config_filename)
            config_file.save(config_path)
            
            # 处理配置文件格式转换
            if config_filename.lower().endswith('.conf'):
                # 如果是.conf文件，转换为.toml格式
                toml_filename = config_filename.rsplit('.', 1)[0] + '.toml'
                toml_path = os.path.join(temp_dir, toml_filename)
                
                if convert_conf_to_toml(config_path, toml_path):
                    flash('检测到exascaler.conf文件，已自动转换为TOML格式', 'success')
                    # 使用转换后的TOML文件
                    config_path = toml_path
                    config_filename = toml_filename
                else:
                    flash('exascaler.conf文件转换失败，请检查文件格式', 'error')
                    return render_template('import_config.html', system=system)
            elif not config_filename.lower().endswith('.toml'):
                flash('不支持的配置文件格式，请上传.toml或.conf文件', 'error')
                return render_template('import_config.html', system=system)
            
            # 现在config_path指向有效的TOML文件
            toml_path = config_path
            toml_filename = config_filename
            
            # 保存SFA文件
            sfa_paths = []
            for sfa_file in sfa_files:
                if sfa_file.filename != '':
                    sfa_filename = secure_filename(sfa_file.filename)
                    sfa_path = os.path.join(temp_dir, sfa_filename)
                    sfa_file.save(sfa_path)
                    sfa_paths.append(sfa_path)
            
            # 调用generate_cluster_yaml处理
            cluster_name = request.form.get('cluster_name', system['name'])
            
            # 🔧 使用层级化文件结构
            customer_name = system.get('customer_name')
            if system.get('yaml_file'):
                # 使用预设的文件路径（新系统创建时已设置）
                output_filename = system['yaml_file']
            else:
                # 兼容旧系统，使用新的层级化路径
                output_filename = f"data/customers/{customer_name}/{system['name']}/{system['name']}_clusters.yaml"
            
            # 确保目录存在
            output_dir = os.path.dirname(output_filename)
            os.makedirs(output_dir, exist_ok=True)
            
            # 创建系统专用的uploads目录
            system_uploads_dir = get_system_uploads_dir(customer_name, system['name'])
            os.makedirs(system_uploads_dir, exist_ok=True)
            
            output_path = os.path.join(os.path.dirname(__file__), output_filename)
            
            # 执行生成
            generate_cluster_yaml(toml_path, cluster_name, sfa_paths, output_path, customer_name)
            
            # 更新系统状态
            systems[system_id]['status'] = 'imported'
            systems[system_id]['yaml_file'] = output_filename
            systems[system_id]['cluster_name'] = cluster_name
            systems[system_id]['imported_at'] = datetime.now().isoformat()
            save_json_db(SYSTEMS_DB, systems)
            
            # 归档上传的文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 归档 TOML 文件
            permanent_toml_filename = f"{timestamp}_{toml_filename}"
            permanent_toml_path = os.path.join(system_uploads_dir, permanent_toml_filename)
            shutil.copy2(toml_path, permanent_toml_path)
            app.logger.info(f"TOML文件已归档至 {permanent_toml_path}")
            
            # 归档 SFA 文件
            for i, sfa_path in enumerate(sfa_paths):
                sfa_filename = os.path.basename(sfa_path)
                permanent_sfa_filename = f"{timestamp}_{i+1}_{sfa_filename}"
                permanent_sfa_path = os.path.join(system_uploads_dir, permanent_sfa_filename)
                shutil.copy2(sfa_path, permanent_sfa_path)
                app.logger.info(f"SFA文件已归档至 {permanent_sfa_path}")
            
            # 清理临时文件
            shutil.rmtree(temp_dir)
            
            flash(f'配置导入成功！生成的YAML文件：{output_filename}', 'success')
            return redirect(url_for('system_detail', system_id=system_id))
            
        except Exception as e:
            # 清理临时文件
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)
            
            flash(f'配置导入失败：{str(e)}', 'error')
            return render_template('import_config.html', system=system)
    
    return render_template('import_config.html', system=system)

@app.route('/systems/<system_id>')
@login_required
def system_detail(system_id):
    """系统详情页面"""
    systems = get_systems()
    if system_id not in systems:
        flash('系统不存在', 'error')
        return redirect(url_for('systems_list'))
    
    # 记录系统访问
    log_access('system', system_id)
    # 同步客户名到YAML
    sync_customer_name_to_yaml(system_id)

    
    system = systems[system_id]
    customers = get_customers()
    
    # 如果有YAML文件，尝试加载资产信息
    assets_info = None
    if system.get('yaml_file') and os.path.exists(system['yaml_file']):
        try:
            with open(system['yaml_file'], 'r', encoding='utf-8') as f:
                assets_info = yaml.safe_load(f)
        except Exception as e:
            flash(f'读取资产文件失败：{str(e)}', 'warning')
    
    return render_template('system_detail.html', 
                         system=system,
                         system_id=system_id,
                         customers=customers,
                         assets_info=assets_info)

@app.route('/systems/<system_id>/update_yaml', methods=['POST'])
def update_yaml(system_id):
    """更新系统YAML数据文件"""
    systems = get_systems()
    if system_id not in systems:
        flash('系统不存在', 'error')
        return redirect(url_for('systems_list'))
    
    system = systems[system_id]
    
    # 检查系统是否有关联的YAML文件
    if not system.get('yaml_file') or not os.path.exists(system['yaml_file']):
        flash('此系统没有关联的YAML文件', 'error')
        return redirect(url_for('system_detail', system_id=system_id))
    
    try:
        # 从表单获取编辑后的YAML数据
        yaml_data = request.form.get('yaml_data')
        if not yaml_data:
            flash('没有收到有效的YAML数据', 'error')
            return redirect(url_for('system_detail', system_id=system_id))
        
        # 解析JSON数据
        edited_data = json.loads(yaml_data)
        
        # 备份原始文件
        yaml_file_path = system['yaml_file']
        backup_path = f"{yaml_file_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        shutil.copy2(yaml_file_path, backup_path)
        
        # 将编辑后的数据写入YAML文件
        with open(yaml_file_path, 'w', encoding='utf-8') as f:
            yaml.dump(edited_data, f, default_flow_style=False, allow_unicode=True)
        
        # 更新系统记录
        system['updated_at'] = datetime.now().isoformat()
        save_json_db(SYSTEMS_DB, systems)
        
        flash('YAML数据已更新', 'success')
    except json.JSONDecodeError as e:
        flash(f'JSON解析错误：{str(e)}', 'error')
    except yaml.YAMLError as e:
        flash(f'YAML写入错误：{str(e)}', 'error')
    except Exception as e:
        flash(f'更新YAML数据时发生错误：{str(e)}', 'error')
    
    return redirect(url_for('system_detail', system_id=system_id))
            
@app.route('/systems/<system_id>/update_config', methods=['GET', 'POST'])
@login_required
def update_system_config(system_id):
    """更新系统配置信息"""
    systems = get_systems()
    if system_id not in systems:
        flash('系统不存在', 'error')
        return redirect(url_for('systems_list'))
    
    system = systems[system_id]
    
    # 检查系统是否已归档
    if system.get('archived', False):
        flash('已归档的系统无法更新', 'error')
        return redirect(url_for('system_detail', system_id=system_id))
    
    # 检查系统是否已导入过配置
    if system.get('status') != 'imported' or not system.get('yaml_file'):
        flash('只有已导入配置的系统才能使用更新功能', 'error')
        return redirect(url_for('system_detail', system_id=system_id))
    
    if request.method == 'POST':
        # 处理exascaler配置文件上传（支持.toml和.conf格式）
        config_file = request.files.get('toml_file')
        if not config_file or config_file.filename == '':
            flash('请选择exascaler配置文件（支持.toml或.conf格式）', 'error')
            return render_template('update_config.html', system=system, system_id=system_id)
        
        # 处理sfa log文件上传
        sfa_files = request.files.getlist('sfa_files')
        if not sfa_files or all(f.filename == '' for f in sfa_files):
            flash('请选择至少一个SFA log文件', 'error')
            return render_template('update_config.html', system=system, system_id=system_id)
        
        # 保存上传的文件
        import tempfile
        
        try:
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            
            # 保存配置文件
            config_filename = secure_filename(config_file.filename)
            config_path = os.path.join(temp_dir, config_filename)
            config_file.save(config_path)
            
            # 处理配置文件格式转换
            if config_filename.lower().endswith('.conf'):
                # 如果是.conf文件，转换为.toml格式
                toml_filename = config_filename.rsplit('.', 1)[0] + '.toml'
                toml_path = os.path.join(temp_dir, toml_filename)
                
                if convert_conf_to_toml(config_path, toml_path):
                    flash('检测到exascaler.conf文件，已自动转换为TOML格式', 'success')
                    # 使用转换后的TOML文件
                    config_path = toml_path
                    config_filename = toml_filename
                else:
                    flash('exascaler.conf文件转换失败，请检查文件格式', 'error')
                    return render_template('update_config.html', system=system, system_id=system_id)
            elif not config_filename.lower().endswith('.toml'):
                flash('不支持的配置文件格式，请上传.toml或.conf文件', 'error')
                return render_template('update_config.html', system=system, system_id=system_id)
            
            # 现在config_path指向有效的TOML文件
            toml_path = config_path
            toml_filename = config_filename
            
            # 保存SFA文件
            sfa_paths = []
            for sfa_file in sfa_files:
                if sfa_file.filename != '':
                    sfa_filename = secure_filename(sfa_file.filename)
                    sfa_path = os.path.join(temp_dir, sfa_filename)
                    sfa_file.save(sfa_path)
                    sfa_paths.append(sfa_path)
            
            # 调用generate_cluster_yaml处理
            cluster_name = request.form.get('cluster_name', system['name'])
            
            # 使用预设的文件路径
            output_filename = system['yaml_file']
            
            # 备份原始文件
            backup_path = f"{output_filename}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            try:
                if os.path.exists(output_filename):
                    shutil.copy2(output_filename, backup_path)
                    print(f"已备份原始YAML文件到: {backup_path}")
            except Exception as e:
                print(f"备份文件失败: {str(e)}")
                flash(f"备份原始文件失败: {str(e)}", 'error')
                return render_template('update_config.html', system=system, system_id=system_id)
            
            # 获取客户名
            customer_name = None
            try:
                # 首先从系统记录中获取客户名
                if 'customer_name' in system:
                    customer_name = system['customer_name']
                    logging.info(f"从系统记录中获取到客户名: {customer_name}")
                
                # 如果系统记录没有客户名，尝试从YAML文件中获取
                if not customer_name and os.path.exists(output_filename):
                    with open(output_filename, 'r', encoding='utf-8') as f:
                        old_yaml = yaml.safe_load(f)
                        if old_yaml and 'customer' in old_yaml:
                            customer_name = old_yaml['customer']
                            logging.info(f"从原始YAML文件中获取到客户名: {customer_name}")
                
                # 如果从系统和YAML都没获取到，尝试从客户表中获取
                if not customer_name and 'customer_id' in system:
                    customers = get_customers()
                    if system['customer_id'] in customers:
                        customer_name = customers[system['customer_id']]['name']
                        logging.info(f"从客户表中获取到客户名: {customer_name}")
            except Exception as e:
                logging.warning(f"获取客户名时出错: {str(e)}")
            
            # 获取客户名
            customer_name = None
            
            # 1. 尝试从系统记录获取
            if 'customer_name' in system:
                customer_name = system['customer_name']
                logging.info(f"从系统记录获取到客户名: {customer_name}")
            
            # 2. 从客户记录获取
            elif 'customer_id' in system:
                customers = get_customers()
                if system['customer_id'] in customers:
                    customer_name = customers[system['customer_id']].get('name')
                    logging.info(f"从客户表获取到客户名: {customer_name}")
            
            # 3. 从原YAML文件获取
            if not customer_name and os.path.exists(output_filename):
                try:
                    with open(output_filename, 'r', encoding='utf-8') as f:
                        yaml_data = yaml.safe_load(f)
                        if yaml_data and 'customer' in yaml_data:
                            customer_name = yaml_data['customer']
                            logging.info(f"从原始YAML文件获取到客户名: {customer_name}")
                except Exception as e:
                    logging.warning(f"读取原始YAML文件获取客户名失败: {str(e)}")
            
            # 调用生成函数，直接传递客户名参数
            try:
                generate_cluster_yaml(toml_path, cluster_name, sfa_paths, output_filename, customer_name)
                
                # 记录结果
                if customer_name:
                    logging.info(f"已完成系统配置更新，保留了客户名: {customer_name}")
                else:
                    logging.warning("已完成系统配置更新，但未能保留客户名")
                
                flash('系统配置已成功更新', 'success')
                
                # 更新系统记录
                system['updated_at'] = datetime.now().isoformat()
                if 'update_count' not in system:
                    system['update_count'] = 1
                else:
                    system['update_count'] += 1
                
                # 保存系统记录
                save_json_db(SYSTEMS_DB, systems)
                
                # 清理临时文件
                shutil.rmtree(temp_dir)
                
                # 记录访问
                log_access('system', system_id)
                
                return redirect(url_for('system_detail', system_id=system_id))
            except Exception as e:
                flash(f'配置更新失败：{str(e)}', 'error')
                return render_template('update_config.html', system=system, system_id=system_id)
            
        except Exception as e:
            flash(f'处理文件失败：{str(e)}', 'error')
            return render_template('update_config.html', system=system, system_id=system_id)
    
    return render_template('update_config.html', system=system, system_id=system_id)

# ==================== 集成旧版DCAM查询功能 ====================

@app.route('/api/asset_owners/<system_id>')
def get_asset_owners_api(system_id):
    """获取系统资产所有者列表API"""
    systems = get_systems()
    if system_id not in systems:
        return jsonify([])
    
    system = systems[system_id]
    if not system.get('yaml_file') or not os.path.exists(system['yaml_file']):
        return jsonify([])
    
    try:
        asset_owners = asset_analyze.get_asset_owners(system['yaml_file'])
        return jsonify(asset_owners)
    except Exception as e:
        app.logger.error(f"获取资产所有者失败: {str(e)}")
        return jsonify([])

@app.route('/api/cluster_names/<system_id>')
def get_system_cluster_names_api(system_id):
    """获取系统集群名称列表API"""
    systems = get_systems()
    if system_id not in systems:
        return jsonify([])
    
    system = systems[system_id]
    if not system.get('yaml_file') or not os.path.exists(system['yaml_file']):
        return jsonify([])
    
    asset_owner = request.args.get('asset_owner')
    
    try:
        cluster_names = asset_analyze.get_cluster_names(system['yaml_file'], asset_owner)
        return jsonify(cluster_names)
    except Exception as e:
        app.logger.error(f"获取集群名称失败: {str(e)}")
        return jsonify([])

@app.route('/api/system_asset_query/<system_id>')
def system_asset_query_api(system_id):
    """执行系统资产查询API"""
    systems = get_systems()
    if system_id not in systems:
        return jsonify({"error": "系统不存在"})
    
    system = systems[system_id]
    if not system.get('yaml_file') or not os.path.exists(system['yaml_file']):
        return jsonify({"error": "系统没有关联的YAML文件"})
    
    try:
        # 获取查询参数
        query_type = int(request.args.get('query_type', 0))
        asset_owner = request.args.get('asset_owner', '').strip() or None
        cluster_name = request.args.get('cluster_name', '').strip() or None
        
        # 执行查询
        result = asset_analyze.query_customer_info(
            yaml_path=system['yaml_file'],
            query_type=query_type,
            asset_owner=asset_owner,
            cluster_name=cluster_name
        )
        
        # 添加查询类型信息
        result['query_type'] = query_type
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"执行资产查询失败: {str(e)}")
        return jsonify({"error": f"查询失败: {str(e)}"})

# 查询类型定义
QUERY_TYPES = {
    0: "所有查询",
    1: "设备数量统计",
    2: "SFA版本详情",
    3: "EXA版本详情", 
    4: "BBU过期日期计算",
    5: "集群容量查询",
    6: "设备序列号查询",
    7: "集群IP地址查询"
}

# 获取所有资产所有者列表的API
@app.route('/api/global_query')
@login_required
def global_query_api():
    """执行全局资产查询API"""
    try:
        # 获取查询参数
        query_type = int(request.args.get('query_type', 0))
        asset_owner = request.args.get('asset_owner', '').strip() or None
        customer_id = request.args.get('customer_id', '').strip() or None
        system_id = request.args.get('system_id', '').strip() or None
        
        if query_type not in QUERY_TYPES:
            return jsonify({"error": f"不支持的查询类型: {query_type}"})
        
        # 对于"所有查询"类型，需要执行所有查询类型并合并结果
        is_all_query = (query_type == 0)
        
        # 如果指定了系统ID，调用系统查询API
        if system_id:
            systems = get_systems()
            if system_id not in systems:
                return jsonify({"error": "系统不存在"})
            
            system = systems[system_id]
            if not system.get('yaml_file') or not os.path.exists(system['yaml_file']):
                return jsonify({"error": "系统没有关联的YAML文件"})
            
            # 处理"所有查询"选项
            if is_all_query:
                all_results = {"query_type": 0, "all_query_results": {}}
                # 执行每种查询类型
                for qt in range(1, 8):  # 1到7的所有查询类型
                    try:
                        result = asset_analyze.query_assets(system['yaml_file'], qt, asset_owner)
                        result['query_type'] = qt
                        all_results["all_query_results"][qt] = result
                    except Exception as e:
                        app.logger.error(f"执行查询类型 {qt} 失败: {str(e)}")
                return jsonify(all_results)
            else:
                # 调用单个查询类型的逻辑
                app.logger.info(f"执行单个查询: 类型={query_type}, 系统ID={system_id}, YAML文件={system['yaml_file']}")
                result = asset_analyze.query_assets(system['yaml_file'], query_type, asset_owner)
                app.logger.info(f"查询结果: {result}")
                result['query_type'] = query_type
                return jsonify(result)
        
        # 全局查询逻辑
        systems = get_systems()
        combined_results = {}
        
        # 根据客户ID或资产所有者过滤系统
        filtered_systems = []
        for sys_id, system in systems.items():
            if system.get('yaml_file') and os.path.exists(system['yaml_file']):
                # 优先使用客户ID过滤
                if customer_id:
                    if system.get('customer_id') == customer_id:
                        filtered_systems.append((sys_id, system))
                # 如果没有客户ID，但有资产所有者，用资产所有者过滤
                elif asset_owner:
                    owners = asset_analyze.get_asset_owners(system['yaml_file'])
                    if asset_owner in owners:
                        filtered_systems.append((sys_id, system))
                else:
                    filtered_systems.append((sys_id, system))
        
        # 处理"所有查询"选项
        if is_all_query:
            all_results = {"query_type": 0, "all_query_results": {}}
            # 执行每种查询类型
            for qt in range(1, 8):  # 1到7的所有查询类型
                qt_results = {}
                for sys_id, system in filtered_systems:
                    try:
                        result = asset_analyze.query_assets(system['yaml_file'], qt, asset_owner)
                        # 将结果整合到该查询类型的结果中
                        for key, value in result.items():
                            # 跳过可能导致问题的特殊键
                            if key in ['query_type', 'error']:
                                continue
                                
                            if key not in qt_results:
                                qt_results[key] = value
                            elif isinstance(value, list) and isinstance(qt_results[key], list):
                                # 安全地合并列表，确保数据类型兼容
                                try:
                                    qt_results[key].extend(value)
                                except Exception as e:
                                    app.logger.warning(f"列表合并失败，键: {key}, 错误: {str(e)}")
                                    qt_results[key] = value
                            elif isinstance(value, dict) and isinstance(qt_results[key], dict):
                                # 安全地合并字典
                                try:
                                    qt_results[key].update(value)
                                except Exception as e:
                                    app.logger.warning(f"字典合并失败，键: {key}, 错误: {str(e)}")
                                    qt_results[key] = value
                            elif isinstance(value, (int, float)) and isinstance(qt_results[key], (int, float)):
                                # 安全地合并数字
                                try:
                                    qt_results[key] = qt_results.get(key, 0) + value
                                except Exception as e:
                                    app.logger.warning(f"数字合并失败，键: {key}, 错误: {str(e)}")
                                    qt_results[key] = value
                            else:
                                # 类型不匹配时，使用新值覆盖
                                qt_results[key] = value
                    except Exception as e:
                        app.logger.error(f"处理系统 {sys_id} 查询类型 {qt} 失败: {str(e)}")
                
                qt_results['query_type'] = qt
                all_results["all_query_results"][qt] = qt_results
            
            combined_results = all_results
        else:
            # 合并所有系统的查询结果
            for sys_id, system in filtered_systems:
                try:
                    result = asset_analyze.query_assets(system['yaml_file'], query_type, asset_owner)
                    # 将结果整合到总结果中
                    for key, value in result.items():
                        if key not in combined_results:
                            combined_results[key] = value
                        elif isinstance(value, list):
                            if key not in combined_results:
                                combined_results[key] = []
                            # 确保类型匹配再扩展
                            if isinstance(combined_results[key], list):
                                combined_results[key].extend(value)
                            else:
                                combined_results[key] = value
                        elif isinstance(value, dict):
                            if key not in combined_results:
                                combined_results[key] = {}
                            if isinstance(combined_results[key], dict):
                                combined_results[key].update(value)
                            else:
                                combined_results[key] = value
                        elif isinstance(value, (int, float)):
                            if key in combined_results and isinstance(combined_results[key], (int, float)):
                                combined_results[key] = combined_results.get(key, 0) + value
                            else:
                                combined_results[key] = value
                except Exception as e:
                    app.logger.error(f"处理系统 {sys_id} 查询失败: {str(e)}")
            
            combined_results['query_type'] = query_type
        return jsonify(combined_results)
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        app.logger.error(f"执行全局资产查询失败: {str(e)}")
        app.logger.error(f"详细错误信息: {tb_str}")
        return jsonify({"error": f"查询失败: {str(e)}"})

@app.route('/api/asset_owners_list')
def get_asset_owners_list_api():
    """API：获取所有系统中的资产所有者列表"""
    all_asset_owners = set()
    systems = get_systems()
    
    app.logger.info(f"获取资产所有者列表，系统数量: {len(systems)}")
    
    for system_id, system in systems.items():
        app.logger.info(f"处理系统: {system_id}, 系统名称: {system.get('name')}")
        if system.get('yaml_file') and os.path.exists(system['yaml_file']):
            try:
                app.logger.info(f"获取系统 {system_id} 的资产所有者，YAML文件: {system['yaml_file']}")
                owners = asset_analyze.get_asset_owners(system['yaml_file'])
                app.logger.info(f"系统 {system_id} 的资产所有者: {owners}")
                all_asset_owners.update(owners)
            except Exception as e:
                app.logger.error(f"读取系统 {system_id} 的资产所有者失败: {str(e)}")
    
    result = list(all_asset_owners)
    app.logger.info(f"返回所有资产所有者: {result}")
    return jsonify(result)

# 获取所有系统列表的API
@app.route('/api/all_systems')
def get_all_systems_api():
    """API：获取所有系统列表"""
    systems = get_systems()
    result = []
    
    for system_id, system in systems.items():
        app.logger.info(f"系统 {system_id}: {system}")
        result.append({
            'id': system_id,
            'name': system.get('name', 'Unknown System'),
            'customer_id': system.get('customer_id', ''),
            'customer_name': system.get('customer_name', '')
        })
    
    app.logger.info(f"返回的系统列表: {result}")
    return jsonify(result)

# 根据资产所有者获取系统列表的API
@app.route('/api/systems_by_owner')
def get_systems_by_owner_api():
    """API：根据资产所有者获取系统列表"""
    asset_owner = request.args.get('asset_owner')
    if not asset_owner:
        return get_all_systems_api()
    
    systems = get_systems()
    result = []
    
    for system_id, system in systems.items():
        if system.get('yaml_file') and os.path.exists(system['yaml_file']):
            try:
                owners = asset_analyze.get_asset_owners(system['yaml_file'])
                if asset_owner in owners:
                    result.append({
                        'id': system_id,
                        'name': system.get('name', 'Unknown System'),
                        'customer_id': system.get('customer_id', '')
                    })
            except Exception as e:
                app.logger.error(f"读取系统 {system_id} 的资产所有者失败: {str(e)}")
    
    return jsonify(result)

# 根据客户ID获取系统列表的API
@app.route('/api/systems_by_customer')
def get_systems_by_customer_api():
    """API：根据客户ID获取系统列表"""
    customer_id = request.args.get('customer_id')
    app.logger.info(f"系统按客户过滤请求, customer_id: {customer_id}")
    
    if not customer_id:
        return get_all_systems_api()
    
    systems = get_systems()
    result = []
    
    for system_id, system in systems.items():
        # 确保数据类型匹配 - 都转换为字符串比较
        system_customer_id = str(system.get('customer_id', ''))
        request_customer_id = str(customer_id)
        
        app.logger.info(f"比较客户ID: 系统的customer_id='{system_customer_id}' vs 请求的customer_id='{request_customer_id}'")
        
        if system_customer_id == request_customer_id:
            app.logger.info(f"匹配的系统 {system_id}: {system}")
            system_data = {
                'id': system_id,
                'name': system.get('name', 'Unknown System'),
                'customer_id': system.get('customer_id', ''),
                'customer_name': system.get('customer_name', '')
            }
            app.logger.info(f"返回的系统数据: {system_data}")
            result.append(system_data)
    
    app.logger.info(f"按客户过滤后的系统列表: {result}")
    return jsonify(result)

# 获取客户列表的API（用于下拉菜单）
@app.route('/api/customers_list')
def get_customers_list_api():
    """API：获取所有客户列表"""
    customers = get_customers()
    result = []
    
    for customer_id, customer in customers.items():
        result.append({
            'id': customer_id,
            'name': customer.get('name', 'Unknown Customer'),
            'description': customer.get('description', '')
        })
    
    return jsonify(result)

@app.route('/test_systems_query')
def test_systems_query():
    """测试系统管理页面快速查询功能"""
    with open('test_systems_query.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/simple_systems_test')
def simple_systems_test():
    """简单的系统管理快速查询测试页面"""
    with open('simple_systems_test.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/test_system_detail_query')
def test_system_detail_query():
    """测试系统详情页面快速查询功能"""
    with open('test_system_detail_query.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/systems/<system_id>/edit_yaml', methods=['GET', 'POST'])
@login_required
def edit_yaml(system_id):
    """编辑系统YAML文件"""
    systems = get_systems()
    if system_id not in systems:
        flash('系统不存在', 'error')
        return redirect(url_for('systems_list'))
    
    system = systems[system_id]
    
    # 检查YAML文件是否存在
    if not system.get('yaml_file') or not os.path.exists(system['yaml_file']):
        flash('系统没有YAML文件或文件不存在', 'error')
        return redirect(url_for('system_detail', system_id=system_id))
    
    # 读取YAML文件内容
    try:
        with open(system['yaml_file'], 'r', encoding='utf-8') as f:
            yaml_content = f.read()
    except Exception as e:
        flash(f'读取YAML文件失败: {str(e)}', 'error')
        return redirect(url_for('system_detail', system_id=system_id))
    
    # 处理表单提交
    if request.method == 'POST':
        new_yaml_content = request.form.get('yaml_content')
        if not new_yaml_content:
            flash('YAML内容不能为空', 'error')
        else:
            try:
                # 验证YAML格式
                yaml_data = yaml.safe_load(new_yaml_content)
                
                # 保存到文件
                with open(system['yaml_file'], 'w', encoding='utf-8') as f:
                    f.write(new_yaml_content)
                
                flash('YAML文件已成功更新', 'success')
                return redirect(url_for('system_detail', system_id=system_id))
            except Exception as e:
                flash(f'保存YAML失败: {str(e)}', 'error')
    
    return render_template('edit_yaml.html', 
                         system=system,
                         system_id=system_id,
                         yaml_content=yaml_content)

def cleanup_old_upload_structure():
    """清理旧的上传目录结构，迁移到新的层级化结构"""
    old_upload_dir = 'data/uploads'
    if os.path.exists(old_upload_dir):
        try:
            # 检查是否有文件
            has_files = False
            for _, _, files in os.walk(old_upload_dir):
                if files:
                    has_files = True
                    break
            
            if has_files:
                # 如果有文件，为安全起见，重命名目录而不是删除
                backup_dir = f"{old_upload_dir}_archived_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                print(f"发现旧上传目录中有文件，将目录重命名为 {backup_dir} 以备份")
                os.rename(old_upload_dir, backup_dir)
            else:
                # 如果没有文件，直接删除目录
                import shutil
                shutil.rmtree(old_upload_dir)
                print(f"已删除空的旧上传目录: {old_upload_dir}")
        except Exception as e:
            print(f"清理旧上传目录时出错: {str(e)}")

if __name__ == '__main__':
    # 设置应用根目录为工作目录，确保文件操作一致性
    script_dir = os.path.abspath(os.path.dirname(__file__))
    print(f"脚本目录: {script_dir}")
    print(f"切换工作目录前: {os.getcwd()}")
    os.chdir(script_dir)
    print(f"切换工作目录后: {os.getcwd()}")
    
    # 初始化默认用户
    init_default_user()
    
    # 清理旧的上传目录结构
    cleanup_old_upload_structure()
    
    # 输出所有注册的路由，便于调试
    print("\n所有注册的路由:")
    for rule in app.url_map.iter_rules():
        print(f"{rule} -> {rule.endpoint}")
    
    # 检查并记录数据库文件状态
    print("\n数据库文件状态:")
    for db_file in [CUSTOMERS_DB, SYSTEMS_DB, ACCESS_LOG_DB, USERS_DB]:
        if os.path.exists(db_file):
            print(f"- {os.path.basename(db_file)}: 存在, 大小: {os.path.getsize(db_file)} 字节")
        else:
            print(f"- {os.path.basename(db_file)}: 不存在")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
