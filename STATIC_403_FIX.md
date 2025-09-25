# 修复静态文件 403 Forbidden 问题

## 问题描述

访问静态资源时出现 403 Forbidden 错误：
```
GET https://ddnsupport.com.cn/dcam/static/DDN-main-logo.svg 403 (Forbidden)
```

这表明 Nginx 可以找到文件路径，但没有足够的权限访问该文件。

## 解决方案

### 1. 检查文件权限

首先，需要检查静态文件的权限：

```bash
# 确认静态文件的存在
ls -la /opt/dcam/static/DDN-main-logo.svg

# 检查静态文件夹的权限
ls -la /opt/dcam/static/
```

### 2. 修复文件权限

设置适当的权限，确保 Nginx 可以读取静态文件：

```bash
# 确保静态文件夹和文件可被 Nginx 用户(通常是 www-data 或 nginx)读取
sudo chmod -R 755 /opt/dcam/static/
sudo chown -R dcam:www-data /opt/dcam/static/

# 或者直接确保所有用户可读
sudo chmod -R 755 /opt/dcam/static/
```

### 3. 确认 Nginx 配置正确

确认 Nginx 配置中的静态文件位置配置正确：

```nginx
# 应该是这样的
location /dcam/static/ {
    alias /opt/dcam/static/;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

确认该配置指向了正确的路径，并且使用了 `alias` 而不是 `root`。

### 4. SELinux 相关问题 (仅适用于 CentOS/RHEL)

如果您的系统使用 SELinux，可能需要设置正确的上下文：

```bash
# 检查 SELinux 状态
sestatus

# 设置适当的 SELinux 上下文
sudo semanage fcontext -a -t httpd_sys_content_t "/opt/dcam/static(/.*)?"
sudo restorecon -Rv /opt/dcam/static/
```

### 5. 检查日志文件

查看 Nginx 错误日志以获取更多详细信息：

```bash
sudo tail -f /var/log/nginx/error.log
```

### 6. 临时测试解决方案

如果以上步骤无法解决问题，可以暂时测试关闭 Nginx 的访问控制：

```bash
# 编辑 Nginx 配置
sudo nano /etc/nginx/sites-available/dcam

# 修改静态文件块
location /dcam/static/ {
    alias /opt/dcam/static/;
    expires 1y;
    add_header Cache-Control "public, immutable";
    # 临时添加，仅用于测试
    allow all;
}

# 重新加载 Nginx
sudo nginx -t && sudo systemctl reload nginx
```

## 验证修复

修复后重新访问 https://ddnsupport.com.cn/dcam/login 页面，确认 DDN logo 能够正常显示。