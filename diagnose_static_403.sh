#!/bin/bash

# 此脚本详细诊断并修复静态文件403 Forbidden错误
# 使用方法: 在服务器上以root权限运行 sudo bash diagnose_static_403.sh

# 输出诊断信息
echo "============== 静态文件403问题诊断脚本 =============="
echo "当前时间: $(date)"
echo "当前用户: $(whoami)"
echo "系统信息: $(uname -a)"
echo

# 1. 检查文件是否存在
echo "============== 检查文件存在性 =============="
STATIC_DIR="/opt/dcam/static"
LOGO_FILE="$STATIC_DIR/DDN-main-logo.svg"

if [ -d "$STATIC_DIR" ]; then
    echo "✓ 静态目录存在: $STATIC_DIR"
    ls -la "$STATIC_DIR"
else
    echo "✗ 错误: 静态目录不存在: $STATIC_DIR"
    echo "正在创建目录..."
    mkdir -p "$STATIC_DIR"
    echo "目录已创建"
fi

if [ -f "$LOGO_FILE" ]; then
    echo "✓ Logo文件存在: $LOGO_FILE"
    ls -la "$LOGO_FILE"
else
    echo "✗ 错误: Logo文件不存在: $LOGO_FILE"
    echo "请确保将DDN-main-logo.svg文件放置在正确的位置"
fi
echo

# 2. 检查Nginx配置
echo "============== 检查Nginx配置 =============="
echo "Nginx版本: $(nginx -v 2>&1)"
echo "Nginx配置测试结果:"
nginx -t 2>&1

# 检查Nginx配置文件中的静态路径配置
echo "检查静态文件配置..."
NGINX_CONF_FILES=$(find /etc/nginx -name "*.conf" -type f)

echo "在以下文件中搜索静态文件配置:"
for conf in $NGINX_CONF_FILES; do
    if grep -q "/dcam/static" "$conf"; then
        echo "找到静态文件配置: $conf"
        grep -A 10 -B 2 "/dcam/static" "$conf" | cat -n
    fi
done
echo

# 3. 检查运行Nginx的用户
echo "============== 检查Nginx用户 =============="
NGINX_USER=$(ps aux | grep nginx | grep master | awk '{print $1}' | head -1)
echo "Nginx正在以用户'$NGINX_USER'运行"

# 检查worker进程用户
NGINX_WORKERS=$(ps aux | grep nginx | grep worker)
echo "Nginx worker进程:"
echo "$NGINX_WORKERS"
echo

# 4. 全面检查文件权限
echo "============== 检查完整权限链 =============="
# 检查从根目录到静态文件的完整路径
PATHS_TO_CHECK=(
    "/"
    "/opt"
    "/opt/dcam"
    "$STATIC_DIR"
    "$LOGO_FILE"
)

for path in "${PATHS_TO_CHECK[@]}"; do
    if [ -e "$path" ]; then
        echo "路径: $path"
        ls -ld "$path"
        
        # 检查访问权限
        if [ -r "$path" ]; then
            echo "  ✓ 可读"
        else
            echo "  ✗ 不可读"
        fi
        
        if [ -d "$path" ] && [ -x "$path" ]; then
            echo "  ✓ 目录可执行(可搜索)"
        elif [ -d "$path" ]; then
            echo "  ✗ 目录不可执行(不可搜索)"
        fi
        echo
    else
        echo "路径不存在: $path"
        echo
    fi
done

# 5. SELinux检查
echo "============== 检查SELinux =============="
if command -v sestatus &>/dev/null; then
    echo "SELinux状态:"
    sestatus
    
    if sestatus | grep -q "enabled"; then
        echo "检查静态目录的SELinux上下文:"
        ls -Z "$STATIC_DIR"
        
        echo "Nginx应该的上下文:"
        if [ -d "/var/www" ]; then
            ls -Z /var/www -d
        fi
    fi
else
    echo "系统未安装SELinux或sestatus命令"
fi
echo

# 6. 检查Nginx错误日志
echo "============== Nginx错误日志 =============="
ERROR_LOGS=$(find /var/log/nginx -name "error*" -type f)

for log in $ERROR_LOGS; do
    echo "检查日志: $log"
    if [ -r "$log" ]; then
        # 尝试查找与静态文件相关的最近错误
        echo "最近的相关错误:"
        grep -i "static\|forbidden\|permission\|denied" "$log" | tail -n 10
    else
        echo "无法读取日志文件 (权限问题)"
    fi
    echo
done

# 7. 尝试修复问题
echo "============== 修复措施 =============="
echo "正在应用全面的权限修复..."

# 创建一个测试SVG文件，如果Logo文件不存在
if [ ! -f "$LOGO_FILE" ]; then
    echo "创建测试SVG文件..."
    cat > "$LOGO_FILE" << EOF
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="50">
  <rect width="200" height="50" style="fill:rgb(0,0,255);" />
  <text x="25" y="35" font-family="Arial" font-size="20" fill="white">DDN Logo</text>
</svg>
EOF
    echo "测试SVG文件已创建"
fi

# 应用广泛的权限修复
echo "应用权限修复:"
chmod -R 755 /opt/dcam
find /opt/dcam -type f -exec chmod 644 {} \;

# 确定Web服务器用户
WEB_SERVER_USER=""
if id "www-data" &>/dev/null; then
    WEB_SERVER_USER="www-data"  # Debian/Ubuntu
elif id "nginx" &>/dev/null; then
    WEB_SERVER_USER="nginx"  # CentOS/RHEL
elif id "apache" &>/dev/null; then
    WEB_SERVER_USER="apache"  # 某些系统
fi

if [ -n "$WEB_SERVER_USER" ]; then
    echo "设置所有权给: $NGINX_USER:$WEB_SERVER_USER"
    chown -R "$NGINX_USER:$WEB_SERVER_USER" /opt/dcam
else
    echo "无法确定Web服务器用户，设置全局可读权限"
    chmod -R o+r /opt/dcam
fi

# 处理SELinux（如果启用）
if command -v sestatus &>/dev/null && sestatus | grep -q "enabled"; then
    echo "设置SELinux上下文..."
    if command -v semanage &>/dev/null; then
        semanage fcontext -a -t httpd_sys_content_t "/opt/dcam(/.*)?"
        restorecon -Rv /opt/dcam
    else
        echo "警告: 未找到semanage命令，无法设置SELinux上下文"
        echo "考虑临时禁用SELinux来测试: sudo setenforce 0"
    fi
fi

# 创建临时Nginx测试配置
echo "创建测试Nginx配置..."
TEST_CONF="/tmp/nginx_test_static.conf"

cat > "$TEST_CONF" << EOF
server {
    listen 8080;
    server_name localhost;

    location /test-static/ {
        alias /opt/dcam/static/;
        autoindex on;
    }
}
EOF

echo "请考虑添加以下配置到Nginx并重新加载:"
cat "$TEST_CONF"

echo
echo "============== 诊断完成 =============="
echo "如果以上修复不起作用，请考虑以下操作:"
echo "1. 检查Nginx配置中的路径是否正确"
echo "2. 确保静态文件夹在正确的位置"
echo "3. 可能需要临时禁用SELinux: sudo setenforce 0"
echo "4. 检查系统级别的AppArmor或其他安全限制"
echo "5. 尝试简化配置，先确保基本访问可行再添加复杂配置"
echo "6. 检查磁盘空间和inode使用情况"