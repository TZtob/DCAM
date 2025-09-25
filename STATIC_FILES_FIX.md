# DCAM 静态资源问题修复指南

我们已经解决了URL重定向问题，现在还需要解决静态资源（如DDN logo）的路径问题。已经为login.html页面修复了此问题，但其他模板也可能需要类似的更新。

## 已实施的修改

1. 更新了Flask应用初始化，添加了`static_url_path`：
   ```python
   app = Flask(__name__, static_url_path='/dcam/static')
   ```

2. 添加了自定义的`static_url`模板函数：
   ```python
   @app.context_processor
   def inject_url_data():
       return {
           'url_prefix': '/dcam',
           'static_url': lambda filename: f'/dcam/static/{filename}'
       }
   ```

3. 修改了login.html模板，使用新的`static_url`函数：
   ```html
   <!-- 原来的 -->
   <img src="{{ url_for('static', filename='DDN-main-logo.svg') }}" alt="DDN Logo" class="ddn-logo">
   
   <!-- 修改后的 -->
   <img src="{{ static_url('DDN-main-logo.svg') }}" alt="DDN Logo" class="ddn-logo">
   ```

## 需要更新的其他文件

您需要检查所有模板文件，将`url_for('static', filename='...')`替换为`static_url('...')`：

1. 使用grep搜索所有模板文件中的`url_for('static'`或`url_for("static"`
2. 对每个找到的文件进行相应的修改

以下是一些可能需要修改的常见静态资源引用：

```html
<!-- CSS文件 -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
<!-- 修改为 -->
<link rel="stylesheet" href="{{ static_url('css/style.css') }}">

<!-- JavaScript文件 -->
<script src="{{ url_for('static', filename='js/script.js') }}"></script>
<!-- 修改为 -->
<script src="{{ static_url('js/script.js') }}"></script>

<!-- 图片 -->
<img src="{{ url_for('static', filename='images/logo.png') }}">
<!-- 修改为 -->
<img src="{{ static_url('images/logo.png') }}">
```

## Nginx配置确认

请确保Nginx配置中的静态文件location块配置正确：

```nginx
# Static files for DCAM
location /dcam/static/ {
    alias /opt/dcam/static/;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

确保这个路径与Flask应用配置的`static_url_path`一致，并且指向正确的静态文件目录。