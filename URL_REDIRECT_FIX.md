# 修复 DCAM URL 重定向问题

## 问题描述
当访问 `/dcam/` 路径时，应用将请求重定向到 `/login` 而不是 `/dcam/login`，导致URL前缀丢失，认证后重定向到根路径而非DCAM应用。

从Nginx日志看到:
```
"GET /dcam/ HTTP/2.0" 302 263
"GET /login?next=https://ddnsupport.com.cn/ HTTP/2.0" 302 92
"GET / HTTP/2.0" 200 17944
```

## 解决方案

### 1. 修改 Flask 应用代码

在 app.py 中添加了处理反向代理URL前缀的中间件:

```python
# 处理反向代理URL前缀
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

### 2. 修改 Nginx 配置

在 Nginx 配置中添加了 `X-Script-Name` 请求头:

```nginx
location /dcam/ {
    proxy_pass http://127.0.0.1:5001/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Script-Name /dcam;  # 重要: 传递URL前缀给Flask应用
    proxy_redirect off;
    
    # Handle large file uploads
    client_max_body_size 100M;
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
}
```

### 3. 依赖修改

确保添加 `toml` 包到 requirements.txt:
```
toml==0.10.2
```

## 部署步骤

1. 更新 Flask 应用代码
2. 重启 DCAM 服务: `sudo systemctl restart dcam`
3. 更新 Nginx 配置: `sudo nano /etc/nginx/sites-available/dcam`
4. 测试 Nginx 配置: `sudo nginx -t`
5. 重新加载 Nginx: `sudo systemctl reload nginx`

## 验证

访问 `https://ddnsupport.com.cn/dcam/` 应该可以正确保持在 DCAM 应用内，不会重定向到根目录。