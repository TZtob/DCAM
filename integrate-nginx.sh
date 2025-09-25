#!/bin/bash

# DCAM Nginx Integration Script
# This script will safely integrate DCAM into your existing Redmine Nginx configuration

set -e

echo "🔧 Integrating DCAM with existing Redmine Nginx configuration..."

NGINX_CONF="/etc/nginx/conf.d/redmine.conf"
BACKUP_CONF="/etc/nginx/conf.d/redmine.conf.backup.$(date +%Y%m%d_%H%M%S)"

# Backup existing configuration
echo "💾 Creating backup of existing Nginx configuration..."
sudo cp $NGINX_CONF $BACKUP_CONF
echo "✅ Backup created: $BACKUP_CONF"

# Check if DCAM configuration already exists
if grep -q "location /dcam/" $NGINX_CONF; then
    echo "⚠️  DCAM configuration already exists in Nginx config"
    echo "📝 Current DCAM location blocks:"
    grep -A 10 "location /dcam/" $NGINX_CONF
    read -p "Do you want to update the configuration? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Configuration update cancelled"
        exit 0
    fi
fi

# Add DCAM upstream if not exists
if ! grep -q "upstream dcam" $NGINX_CONF; then
    echo "📡 Adding DCAM upstream configuration..."
    sudo sed -i '/upstream redmine/a\\n# Definition of upstream for DCAM\nupstream dcam {\n  server                        127.0.0.1:5001;\n}' $NGINX_CONF
fi

# Add DCAM location blocks
echo "📍 Adding DCAM location blocks..."

# Create temporary file with DCAM configuration
cat > /tmp/dcam_locations.conf << 'EOF'

# DCAM application configuration
  location /dcam/ {
    proxy_pass                  http://dcam/;
    proxy_set_header            Host $http_host;
    proxy_set_header            X-Real-IP $remote_addr;
    proxy_set_header            X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header            X-Forwarded-Proto $scheme;
    proxy_redirect              off;
    
    # Handle large file uploads for DCAM
    proxy_connect_timeout       300;
    proxy_send_timeout          300;
    proxy_read_timeout          300;
  }

# DCAM static files
  location /dcam/static/ {
    alias                       /opt/dcam/static/;
    expires                     1y;
    add_header                  Cache-Control "public, immutable";
  }
EOF

# Insert DCAM configuration after server_name line
sudo sed -i '/server_name.*_;/r /tmp/dcam_locations.conf' $NGINX_CONF

# Clean up
rm /tmp/dcam_locations.conf

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration test passed"
    
    # Reload Nginx
    echo "🔄 Reloading Nginx..."
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded successfully"
    
    echo ""
    echo "🎉 DCAM integration completed successfully!"
    echo ""
    echo "📊 Configuration summary:"
    echo "- Redmine: https://your-domain.com/ (unchanged)"
    echo "- DCAM: https://your-domain.com/dcam/"
    echo ""
    echo "📝 Backup location: $BACKUP_CONF"
    echo ""
    echo "🔍 Test your configuration:"
    echo "curl -I https://your-domain.com/dcam/"
    
else
    echo "❌ Nginx configuration test failed!"
    echo "🔄 Restoring backup configuration..."
    sudo cp $BACKUP_CONF $NGINX_CONF
    echo "✅ Configuration restored from backup"
    echo ""
    echo "📝 Please check the configuration manually:"
    echo "sudo nano $NGINX_CONF"
    exit 1
fi

echo ""
echo "📋 Next steps:"
echo "1. Ensure DCAM service is running: sudo systemctl status dcam"
echo "2. Test DCAM access: https://your-domain.com/dcam/"
echo "3. Check logs if needed: sudo journalctl -u dcam -f"