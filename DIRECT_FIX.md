# 修复 DCAM 的反向代理重定向问题 - 替代方案

以下是一个更直接的修复方法，使用 Flask 的 `APPLICATION_ROOT` 配置而不是 WSGI 中间件：

## 1. 修改 app.py (简化方案)

```python
# 在 Flask 应用初始化后立即添加
app = Flask(__name__)
app.secret_key = 'dcam-secret-key-2025'
app.config['APPLICATION_ROOT'] = '/dcam'  # 设置应用根路径为 /dcam

# 添加模板上下文处理器
@app.context_processor
def inject_url_prefix():
    return {'url_prefix': '/dcam'}
```

## 2. 修改 Nginx 配置

```nginx
location /dcam/ {
    # 关键修改：不要在 proxy_pass 末尾添加斜杠！
    proxy_pass http://127.0.0.1:5001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_redirect off;
    
    client_max_body_size 100M;
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
}
```

## 3. 额外的调试方案

如果上面的解决方案不起作用，可以尝试这个最简单的方法，在 app.py 中直接修改 `/login` 路由：

```python
@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    # 调试代码
    with open('/tmp/dcam_login_debug.log', 'a') as f:
        f.write(f"Request: {request.url}, Args: {request.args}\n")
        f.write(f"Headers: {request.headers}\n")
        f.write(f"Path: {request.path}, Script Root: {request.script_root}\n")
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if verify_user(username, password):
            session['username'] = username
            session['user_role'] = get_user(username)['role']
            flash('登录成功', 'success')
            
            next_page = request.args.get('next')
            
            # 调试 next 参数的处理
            with open('/tmp/dcam_login_debug.log', 'a') as f:
                f.write(f"Next page: {next_page}\n")
            
            # 强制重定向到 /dcam/
            return redirect('/dcam/')
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')
```

## 4. 修改 dcam_index 路由

```python
@app.route('/dcam')
def dcam_index():
    # 确保请求路径结尾有斜杠
    if not request.path.endswith('/'):
        return redirect('/dcam/')
        
    """主页：选择客户"""
    customer_yaml_mapping = get_customer_yaml_mapping()
    return render_template('dcam_index.html', customers=customer_yaml_mapping)
```

## 5. 一个临时解决方案 - 在 app.py 主程序中添加自定义重定向处理

```python
@app.before_request
def fix_dcam_redirects():
    # 如果是要重定向到登录页面的请求
    if request.path == '/dcam/' and 'username' not in session:
        # 直接返回登录页面，但强制指定 next 参数为 /dcam/
        return redirect('/dcam/login?next=/dcam/')
```