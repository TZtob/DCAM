#!/bin/bash

# 此脚本用于修复本地部署后的500错误问题

# 设置颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}开始进行500错误修复...${NC}"

# 检查Flask应用是否在运行
echo -e "${BLUE}1. 检查应用状态...${NC}"
if pgrep -f "python.*app.py" > /dev/null; then
  echo -e "${RED}Flask应用正在运行，请先停止应用再继续修复${NC}"
  read -p "是否要继续修复？(y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "修复已取消"
    exit 1
  fi
fi

# 备份当前文件
echo -e "${BLUE}2. 创建文件备份...${NC}"
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
cp app.py $BACKUP_DIR/
cp templates/customer.html $BACKUP_DIR/
cp templates/dcam_index.html $BACKUP_DIR/
cp templates/login.html $BACKUP_DIR/
echo -e "${GREEN}备份完成：$BACKUP_DIR/${NC}"

# 修复JavaScript API请求中的URL前缀
echo -e "${BLUE}3. 修复模板中的JavaScript API URL...${NC}"
sed -i 's|/dcam/api/cluster_names/|/api/cluster_names/|g' templates/customer.html
echo -e "${GREEN}已更新customer.html中的API路径${NC}"

# 修复模板中的URL引用
echo -e "${BLUE}4. 修复模板中的URL引用...${NC}"
sed -i 's|url_for("dcam_index")|url_for("dashboard")|g' templates/customer.html
echo -e "${GREEN}已更新customer.html中的URL引用${NC}"

# 增强错误处理和日志记录
echo -e "${BLUE}5. 增强Flask应用错误处理...${NC}"

# 添加错误处理器和详细日志记录
cat > error_handler_patch.py << 'EOF'
# 添加错误处理器
@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error(f"500错误: {str(e)}")
    return "服务器内部错误，请查看日志了解详情", 500

# 在请求处理前添加更详细的日志
@app.before_request
def log_request_info():
    app.logger.info(f"请求路径: {request.path}, 方法: {request.method}, 参数: {request.args}")
EOF

# 将错误处理器添加到app.py
echo -e "${GREEN}错误处理代码已生成，请手动添加到app.py${NC}"

# 测试修复
echo -e "${BLUE}6. 修复完成！${NC}"
echo -e "${BLUE}请启动Flask应用测试修复是否成功:${NC}"
echo -e "${GREEN}python app.py${NC}"
echo
echo -e "${BLUE}如果仍有问题，请查看日志文件:${NC}"
echo -e "${GREEN}tail -f dcam.log${NC}"