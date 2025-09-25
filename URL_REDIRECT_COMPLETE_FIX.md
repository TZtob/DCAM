# DCAM URL 重定向问题 - 完整修复方案

## 问题分析

从 Nginx 日志看到的问题：
```
"GET /dcam/ HTTP/2.0" 302 263
"GET /login?next=https://ddnsupport.com.cn/ HTTP/2.0" 302 92
"GET / HTTP/2.0" 200 17944
```

这表明当访问 `/dcam/` 路径时，应用会将请求重定向到 `/login`，然后重定向到根路径 `/`，丢失了 `/dcam/` 前缀。

## 解决方案

我们实施了一个全面的解决方案，包含以下几个关键部分：

### 1. Flask WSGI 中间件

添加了一个 `ReverseProxied` 中间件来正确处理反向代理提供的 URL 前缀：

```python
class ReverseProxied(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ.get('PATH_INFO', '')
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_FORWARDED_PROTO', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)

# 应用中间件
app.wsgi_app = ReverseProxied(app.wsgi_app)
```

### 2. 修复登录重定向

更新了登录验证装饰器，确保它在重定向时保留 URL 前缀：

```python
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            script_name = request.environ.get('SCRIPT_NAME', '')
            if script_name:
                return redirect(f"{script_name}{url_for('login', next=request.url)}")
            else:
                return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
```

### 3. 修复登录和注销路由

确保登录和注销功能在重定向时考虑 URL 前缀：

```python
@app.route('/login', methods=['GET', 'POST'])
def login():
    # ...
    next_page = request.args.get('next')
    if next_page:
        return redirect(next_page)  # 保持完整URL包括前缀
    else:
        script_name = request.environ.get('SCRIPT_NAME', '')
        if script_name:
            return redirect(f"{script_name}{url_for('index')}")
        else:
            return redirect(url_for('index'))
    # ...

@app.route('/logout')
def logout():
    session.clear()
    flash('已成功退出登录', 'info')
    script_name = request.environ.get('SCRIPT_NAME', '')
    if script_name:
        return redirect(f"{script_name}{url_for('login')}")
    else:
        return redirect(url_for('login'))
```

### 4. 首页路由处理

修复了主页路由，确保它在存在 URL 前缀时正确处理重定向：

```python
@app.route('/')
@login_required
def index():
    script_name = request.environ.get('SCRIPT_NAME', '')
    if script_name and request.path == '/':
        return redirect(f"{script_name}/")
    # ...
```

### 5. 添加模板辅助函数

添加了模板上下文处理器，提供辅助函数使所有模板能够正确生成链接：

```python
@app.context_processor
def inject_url_data():
    def get_script_name():
        return request.environ.get('SCRIPT_NAME', '')
    
    return {
        'url_prefix': get_script_name,
        'full_url_for': lambda endpoint, **kwargs: get_script_name() + url_for(endpoint, **kwargs)
    }
```

### 6. Nginx 配置修改

确保 Nginx 配置正确传递 `X-Script-Name` 头信息：

```nginx
location /dcam/ {
    proxy_pass http://127.0.0.1:5001/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Script-Name /dcam;  # 关键：传递URL前缀信息
    proxy_redirect off;
}
```

## 部署步骤

1. 更新 Flask 应用代码（app.py）
2. 按照 TEMPLATE_UPDATE_GUIDE.md 更新模板文件中的链接
3. 更新 Nginx 配置
4. 重新加载 Nginx: `sudo systemctl reload nginx`
5. 重启 DCAM 服务: `sudo systemctl restart dcam`

## 验证

部署完成后，访问以下链接并确认它们正确工作：

1. https://ddnsupport.com.cn/dcam/ - 应保持在 DCAM 应用内
2. 登录后，所有链接都应该保持 /dcam/ 前缀
3. 登出后，应该重定向到 /dcam/login