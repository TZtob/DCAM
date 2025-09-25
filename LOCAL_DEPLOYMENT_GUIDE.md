# DCAM应用本地部署恢复指南

## 概述

本文档记录了将DCAM应用从云主机部署配置恢复为本地部署的过程。恢复主要涉及移除为云主机部署添加的URL前缀和路由重定向逻辑。

## 已恢复的更改

### 1. 移除Flask应用初始化自定义

```python
# 从
app = Flask(__name__, static_url_path='/dcam/static')
app.secret_key = 'dcam-secret-key-2025'
app.config['APPLICATION_ROOT'] = '/dcam'
app.config['PREFERRED_URL_SCHEME'] = 'https'

# 改为
app = Flask(__name__)
app.secret_key = 'dcam-secret-key-2025'
```

### 2. 移除静态文件服务自定义路由

移除了以下路由和相关函数：
- `/dcam/static/<path:filename>` (serve_static)
- `/dcam/logo` (serve_logo)
- 上下文处理器 `inject_url_data`

### 3. 移除URL重定向预处理逻辑

移除了 `fix_dcam_redirects` 函数，替换为简单的请求日志记录器。

### 4. 恢复标准路由路径

- 移除了所有路由中的 `/dcam` 前缀
- 更新了URL生成以使用 `url_for` 而非硬编码路径
- 移除了重复的路由注册（如 `/login` 和 `/dcam/login`）

### 5. 更新模板静态资源引用

将模板中的 `static_url` 函数调用替换为标准的 `url_for('static', filename='...')` 函数。

## 测试指南

恢复更改后，请按照以下步骤验证应用是否正常工作：

1. 启动Flask应用：
   ```bash
   python app.py
   ```

2. 访问以下URL：
   - http://localhost:5000/ - 应重定向到登录页面
   - http://localhost:5000/login - 应显示登录表单
   - http://localhost:5000/dashboard - 登录后应显示主页

3. 验证静态资源：
   - 检查DDN logo是否正确显示
   - 检查其他静态资源（CSS、JS等）是否加载

## 部署注意事项

如果需要将应用重新部署到云主机上（使用URL前缀），请参考以下文件了解所需的修改：
- STATIC_RESOURCE_FIX_GUIDE.md
- RESTORE_ORIGINAL_LOGO.md
- URL_REDIRECT_FIXED.md

## 常见问题

### 静态文件无法显示
如果静态文件无法显示，请确保：
- 静态文件位于应用根目录下的 `static` 文件夹中
- DDN-main-logo.svg 文件存在且有正确的权限

### 路由问题
如果路由有问题，请检查：
- 是否所有硬编码的 `/dcam` 前缀都已移除
- 是否正确使用 `url_for` 生成URL

### 重定向循环
如果遇到重定向循环，可能是因为某些重定向逻辑仍然存在，请检查：
- `before_request` 钩子中是否有遗留的重定向逻辑
- 路由函数中是否有硬编码的重定向