# DCAM URL 重定向问题 - 最终解决方案

## 问题分析

Nginx 日志显示持续存在的 URL 重定向问题:
```
"GET /dcam/ HTTP/2.0" 302 263
"GET /login?next=https://ddnsupport.com.cn/ HTTP/2.0" 302 92
"GET / HTTP/2.0" 200 17944
```

我们已经尝试了几种解决方案，但问题依然存在。这次我们采用直接、强制性的方法解决问题。

## 最终解决方案

### 1. 简化应用配置

我们放弃了复杂的 WSGI 中间件方法，转而使用直接、明确的配置：

```python
# 设置应用根路径
app.config['APPLICATION_ROOT'] = '/dcam'
app.config['PREFERRED_URL_SCHEME'] = 'https'

# 添加模板上下文处理器
@app.context_processor
def inject_url_data():
    return {
        'url_prefix': '/dcam'  # 直接使用硬编码的前缀
    }
```

### 2. 路由级别的强制重定向处理

添加了一个全局请求处理器，直接拦截并修复问题请求：

```python
@app.before_request
def fix_dcam_redirects():
    # 直接处理 /dcam/ 路径，强制正确的认证流程
    if request.path == '/dcam/' and 'username' not in session:
        return redirect('/dcam/login?next=/dcam/')
```

### 3. 修改关键路由

1. 登录路由直接处理外部URL重定向：
```python
if next_page:
    # 检查 next 参数是否有正确的前缀
    if next_page.startswith('https://') and '/dcam/' not in next_page:
        # 修复外部URL，强制重定向到DCAM应用
        return redirect('/dcam/')
    else:
        return redirect(next_page)
else:
    # 如果没有next参数，强制重定向到DCAM应用
    return redirect('/dcam/')
```

2. 登出路由使用硬编码路径：
```python
return redirect('/dcam/login')
```

3. 登录验证装饰器使用明确的路径：
```python
if 'username' not in session:
    if request.path.startswith('/dcam'):
        return redirect(f'/dcam/login?next={request.path}')
    else:
        return redirect('/dcam/login?next=/dcam/')
```

4. 索引路由直接重定向到DCAM应用：
```python
if request.path == '/':
    return redirect('/dcam/')
```

5. 添加了带斜杠版本的DCAM路由：
```python
@app.route('/dcam/')
def dcam_index_with_slash():
    # ...
```

### 4. Nginx配置修改

关键改动是去掉 proxy_pass 末尾的斜杠：

```nginx
location /dcam {
    # 没有在结尾添加斜杠！
    proxy_pass http://127.0.0.1:5001;
    # ... 其他设置
}
```

## 部署步骤

1. 更新 app.py 文件，应用所有上述修改
2. 更新 Nginx 配置文件，使用新提供的 nginx_direct_fix.conf
3. 重启 DCAM 服务: `sudo systemctl restart dcam`
4. 测试 Nginx 配置: `sudo nginx -t`
5. 重新加载 Nginx: `sudo systemctl reload nginx`

## 故障排查

如果问题仍然存在，可以添加额外的日志记录来调试：

```python
import logging

# 配置日志
logging.basicConfig(filename='/tmp/dcam_debug.log', level=logging.DEBUG)

# 在需要调试的地方添加日志
@app.route('/login', methods=['GET', 'POST'])
def login():
    logging.debug(f"Login request: URL={request.url}, Args={request.args}")
    # ...
```