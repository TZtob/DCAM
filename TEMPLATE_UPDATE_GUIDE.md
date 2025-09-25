# DCAM 模板更新指南

为了解决 URL 重定向问题，我们修改了应用代码以支持 URL 前缀。为了确保所有模板都能正确处理 URL 前缀，请按照以下指南更新模板文件：

## 模板中的链接应该更新为以下格式之一

### 选项1: 使用新的 full_url_for 函数 (推荐)

```html
<!-- 旧版本 -->
<a href="{{ url_for('index') }}">首页</a>
<a href="{{ url_for('customer_page', customer_name=customer) }}">客户页面</a>
<form action="{{ url_for('login') }}" method="post">

<!-- 新版本 - 使用 full_url_for 函数 -->
<a href="{{ full_url_for('index') }}">首页</a>
<a href="{{ full_url_for('customer_page', customer_name=customer) }}">客户页面</a>
<form action="{{ full_url_for('login') }}" method="post">
```

### 选项2: 使用 url_prefix 函数

```html
<!-- 旧版本 -->
<a href="{{ url_for('index') }}">首页</a>

<!-- 新版本 - 使用 url_prefix -->
<a href="{{ url_prefix() }}{{ url_for('index') }}">首页</a>
```

## 对于表单提交

确保所有表单的 action 属性都使用了 full_url_for:

```html
<!-- 旧版本 -->
<form action="{{ url_for('login') }}" method="post">

<!-- 新版本 -->
<form action="{{ full_url_for('login') }}" method="post">
```

## 对于静态资源 (CSS, JS, 图片等)

```html
<!-- 旧版本 -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">

<!-- 新版本 -->
<link rel="stylesheet" href="{{ full_url_for('static', filename='css/style.css') }}">
```

## 对于重定向的 JavaScript 代码

如果在 JavaScript 中有硬编码的路径或使用了 url_for，也需要更新：

```javascript
// 旧版本
window.location.href = "/customers";
// 或
window.location.href = "{{ url_for('customers') }}";

// 新版本
window.location.href = "{{ url_prefix() }}/customers";
// 或
window.location.href = "{{ full_url_for('customers') }}";
```

## 主要需要检查的模板文件

1. 登录相关模板 (login.html, logout.html)
2. 主导航模板 (layout.html, base.html, navbar.html)
3. 索引/首页模板 (index.html, main_index.html, dcam_index.html)
4. 包含表单提交的页面
5. 包含 JavaScript 重定向的页面

通过这些更改，应用将能够在反向代理后正确处理 URL 前缀，解决重定向问题。