#!/bin/bash

# 这个脚本用于在所有模板中更新静态资源路径
# 将url_for('static', filename='...') 替换为 static_url('...')

# 首先，找到所有包含url_for('static'的模板文件
TEMPLATE_FILES=$(grep -l "url_for('static'" /opt/dcam/templates/*.html)

# 对每个文件执行替换
for file in $TEMPLATE_FILES; do
  echo "处理文件: $file"
  
  # 使用sed替换模式：url_for('static', filename='XXX') -> static_url('XXX')
  sed -i "s/url_for('static', filename='\([^']*\)')/static_url('\1')/g" "$file"
  sed -i 's/url_for("static", filename="\([^"]*\)")/static_url("\1")/g' "$file"
  
  echo "✓ 完成"
done

echo "所有模板文件更新完成"