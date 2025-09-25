# DCAM静态资源403问题更新日志

## 2025-09-24 更新
解决了DCAM静态资源403 Forbidden错误的问题。

## 问题表现
在访问DCAM应用时，登录页面无法加载DDN logo图片，浏览器返回以下错误：
```
"GET /dcam/static/DDN-main-logo.svg HTTP/2.0" 403 555
```

## 解决方案

### 1. 内联SVG方案
将SVG直接嵌入HTML中，彻底避开静态文件访问权限问题：
- 创建了 `login_inline_svg.html` 模板
- 更新了登录函数使用新的模板
```python
return render_template('login_inline_svg.html')
```

### 2. 直接通过Flask提供静态文件
添加了特定的Flask路由来处理静态文件：
```python
@app.route('/dcam/static/<path:filename>')
def serve_static(filename):
    """直接提供静态文件，绕过Nginx的403问题"""
    app.logger.info(f"Serving static file: {filename} from folder: {app.static_folder}")
    return send_from_directory(app.static_folder, filename)

@app.route('/dcam/logo')
def serve_logo():
    """直接提供DDN logo文件"""
    app.logger.info(f"Serving DDN logo from folder: {app.static_folder}")
    return send_from_directory(app.static_folder, 'DDN-main-logo.svg')
```

### 3. Nginx配置简化
修改了Nginx配置，移除了单独的静态文件处理部分，直接将所有请求转发给Flask应用。

## 测试方法
创建了测试脚本 `test_logo_access.py` 来验证静态资源访问。

## 重要提醒
如果部署在生产环境，记得：
1. 将新的配置文件部署到正确的位置
2. 重启DCAM服务
3. 重新加载Nginx配置

## 下一步建议
未来可考虑使用更专业的前端资源处理方案，例如：
- 使用CDN托管静态资源
- 使用前端构建工具如Webpack优化静态资源