# DCAM静态资源修复方案（恢复使用原始logo）

## 修复概述
我们已经恢复了使用原始DDN logo文件的方式，同时保留了Flask应用直接提供静态文件的功能，以解决403 Forbidden错误问题。

## 已完成的修改

### 1. 恢复使用原始登录模板
- 不再使用内联SVG版本的登录页面
- 恢复使用原始的`login.html`模板，其中引用外部SVG文件:
  ```html
  <img src="{{ static_url('DDN-main-logo.svg') }}" alt="DDN Logo" class="ddn-logo">
  ```

### 2. 保留直接提供静态文件的Flask路由
保留了两个关键的Flask路由，使Flask应用可以直接提供静态文件，绕过Nginx的权限问题:
```python
# 直接提供静态文件，绕过Nginx的403权限问题
@app.route('/dcam/static/<path:filename>')
def serve_static(filename):
    """直接提供静态文件，绕过Nginx的403问题"""
    app.logger.info(f"Serving static file: {filename} from folder: {app.static_folder}")
    return send_from_directory(app.static_folder, filename)

# 添加一个特殊路由专门处理DDN logo
@app.route('/dcam/logo')
def serve_logo():
    """直接提供DDN logo文件"""
    app.logger.info(f"Serving DDN logo from folder: {app.static_folder}")
    return send_from_directory(app.static_folder, 'DDN-main-logo.svg')
```

### 3. 简化Nginx配置
创建了一个简化的Nginx配置(`nginx_config.conf`)，将所有请求转发给Flask应用处理，包括静态文件。

## 部署步骤

1. **更新Flask应用**
   已恢复使用原始login.html模板，同时保留了Flask应用提供静态文件的路由。

2. **更新Nginx配置**
   需要在服务器上应用简化的Nginx配置:
   ```bash
   sudo cp nginx_config.conf /etc/nginx/conf.d/dcam.conf
   sudo nginx -t && sudo systemctl reload nginx
   ```

3. **重启DCAM服务**
   ```bash
   sudo systemctl restart dcam  # 或您使用的具体服务名称
   ```

## 验证步骤

访问以下URL验证修复:
- https://example.com/dcam/login - 应显示正确的DDN logo
- https://example.com/dcam/static/DDN-main-logo.svg - 应直接显示logo
- https://example.com/dcam/logo - 应通过特殊路由显示logo

## 如果问题仍然存在

如果静态文件访问问题仍然存在，可能需要检查文件权限，建议在服务器上运行以下命令:

```bash
# 确保静态文件目录权限正确
sudo chmod -R 755 /opt/dcam/static

# 确保合适的用户拥有文件
sudo chown -R <wsgi_user>:<nginx_user> /opt/dcam/static

# 如果使用SELinux，设置正确的上下文
sudo chcon -R -t httpd_sys_content_t /opt/dcam/static
```

这些步骤应确保DDN logo可以正确显示，同时保持原始的高品质视觉效果。