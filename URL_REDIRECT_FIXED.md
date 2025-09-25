# DCAM URL 重定向问题 - 最终修复方案

## 最新进展

我们现在看到了一个不同的错误：

```
"GET /dcam/ HTTP/2.0" 302 233 
"GET /dcam/login?next=/dcam/ HTTP/2.0" 404 207
```

这表明我们已经成功地让应用保持在 `/dcam/` 前缀下，但 `/dcam/login` 路由返回了 404 错误。

## 完整修复方案

我们实施了一个综合性方法来解决所有相关问题：

### 1. 添加双路由支持

为关键路由添加了双路由支持，同时处理带前缀和不带前缀的访问：

```python
@app.route('/login', methods=['GET', 'POST'])
@app.route('/dcam/login', methods=['GET', 'POST'])
def login():
    # ...

@app.route('/logout')
@app.route('/dcam/logout')
def logout():
    # ...

@app.route('/change_password', methods=['GET', 'POST'])
@app.route('/dcam/change_password', methods=['GET', 'POST'])
def change_password():
    # ...
```

### 2. 增强了请求拦截器功能

扩展了 `fix_dcam_redirects` 函数来处理更多的情况：

```python
@app.before_request
def fix_dcam_redirects():
    # 记录请求信息，帮助调试
    if 'login' in request.path or request.path == '/dcam/' or request.path == '/':
        logging.info(f"Debug - Path: {request.path}, Args: {request.args}")

    # 修复所有重要的路由 
    if request.path == '/':
        # 根路径重定向到 DCAM
        return redirect('/dcam/')
    elif request.path == '/dcam/' and 'username' not in session:
        # DCAM 根路径未登录时重定向到 DCAM 登录页
        return redirect('/dcam/login?next=/dcam/')
    elif request.path == '/login' and 'next' in request.args:
        # 如果访问了旧的登录路径，重定向到带前缀的登录路径
        next_url = request.args.get('next')
        return redirect(f'/dcam/login?next={next_url}')
```

### 3. 添加日志记录

为应用添加了详细的日志记录，以便于排查问题：

```python
import logging

# 配置日志记录
logging.basicConfig(
    filename='dcam.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 在关键路由中添加日志记录
@app.route('/dcam/login', methods=['GET', 'POST'])
def login():
    logging.info(f"Login route accessed: Path={request.path}, Args={request.args}")
    # ...
```

## 部署步骤

1. 更新 `app.py`，包含所有上述修改
2. 确认 Nginx 配置中的 `proxy_pass` 不包含末尾的斜杠
3. 重启 DCAM 应用：`sudo systemctl restart dcam`
4. 重新加载 Nginx：`sudo systemctl reload nginx`

## 验证和调试

部署完成后：

1. 检查应用日志：`sudo tail -f /opt/dcam/dcam.log`
2. 监控 Nginx 访问日志：`sudo tail -f /var/log/nginx/access.log | grep dcam`
3. 访问 https://ddnsupport.com.cn/dcam/ 验证正确的重定向行为

如果问题仍然存在，日志文件将提供详细信息，帮助进一步排查问题。