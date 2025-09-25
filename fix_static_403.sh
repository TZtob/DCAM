#!/bin/bash

# 此脚本修复静态文件403 Forbidden错误
# 使用方法: 在服务器上以root权限运行 sudo bash fix_static_403.sh

# 1. 修复文件权限
echo "修复静态文件权限..."
chmod -R 755 /opt/dcam/static/

# 检查www-data用户是否存在 (Debian/Ubuntu)
if id "www-data" &>/dev/null; then
  chown -R dcam:www-data /opt/dcam/static/
  echo "已设置权限: dcam:www-data"
# 检查nginx用户是否存在 (CentOS/RHEL)
elif id "nginx" &>/dev/null; then
  chown -R dcam:nginx /opt/dcam/static/
  echo "已设置权限: dcam:nginx"
else
  echo "未找到标准web服务器用户，使用全局可读权限"
  chmod -R a+r /opt/dcam/static/
fi

# 2. SELinux设置 (仅适用于CentOS/RHEL)
if command -v sestatus &>/dev/null; then
  if sestatus | grep -q "enabled"; then
    echo "SELinux已启用，设置适当的安全上下文..."
    semanage fcontext -a -t httpd_sys_content_t "/opt/dcam/static(/.*)?"
    restorecon -Rv /opt/dcam/static/
    echo "SELinux上下文已设置"
  fi
fi

# 3. 更新Nginx配置
echo "正在检查和更新Nginx配置..."
NGINX_CONF_PATH="/etc/nginx/sites-available/dcam"

if [ -f "$NGINX_CONF_PATH" ]; then
  # 备份原始配置
  cp "$NGINX_CONF_PATH" "${NGINX_CONF_PATH}.bak.$(date +%Y%m%d%H%M%S)"
  
  # 修改静态文件配置
  sed -i '/location \/dcam\/static\/ {/,/}/c\
    location /dcam/static/ {\
        alias /opt/dcam/static/;\
        allow all;\
        autoindex on;\
        expires 1y;\
        add_header Cache-Control "public, immutable";\
    }' "$NGINX_CONF_PATH"
  
  echo "Nginx配置已更新"
  
  # 测试并重新加载Nginx
  if nginx -t; then
    systemctl reload nginx
    echo "Nginx已重新加载"
  else
    echo "错误: Nginx配置测试失败，请手动检查配置"
    exit 1
  fi
else
  echo "警告: 未找到Nginx配置文件 $NGINX_CONF_PATH"
  echo "请手动更新您的Nginx配置"
fi

echo "完成！请检查DDN logo是否可以正常显示"