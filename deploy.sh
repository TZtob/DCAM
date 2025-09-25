#!/bin/bash

# DCAM Production Deployment Script
# Run this script on your server to deploy DCAM

set -e

echo "🚀 Starting DCAM deployment..."

# Configuration
DCAM_DIR="/opt/dcam"
SERVICE_NAME="dcam"
NGINX_SITE="dcam"
USER="dcam"

# Create dedicated user for DCAM
echo "👤 Creating DCAM user..."
sudo useradd --system --shell /bin/false --home-dir $DCAM_DIR --create-home $USER 2>/dev/null || echo "User $USER already exists"

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p $DCAM_DIR
sudo chown $USER:$USER $DCAM_DIR

# Set up Python virtual environment
echo "🐍 Setting up Python environment..."
cd $DCAM_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt not found, installing basic dependencies..."
    pip install Flask==2.3.3 PyYAML==6.0.1 Werkzeug==2.3.7 gunicorn==21.2.0
fi

# Set proper permissions
echo "🔐 Setting file permissions..."
sudo chown -R $USER:$USER $DCAM_DIR
sudo chmod -R 755 $DCAM_DIR

# Create systemd service
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=DCAM Flask Application
After=network.target

[Service]
Type=exec
User=$USER
Group=$USER
WorkingDirectory=$DCAM_DIR
Environment=PATH=$DCAM_DIR/venv/bin
Environment=FLASK_ENV=production
ExecStart=$DCAM_DIR/venv/bin/gunicorn --bind 127.0.0.1:5001 --workers 3 --timeout 120 app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Start and enable service
echo "🔄 Starting DCAM service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# Check service status
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ DCAM service is running"
else
    echo "❌ DCAM service failed to start"
    sudo systemctl status $SERVICE_NAME
    exit 1
fi

# Create nginx configuration template
echo "🌐 Creating nginx configuration template..."
sudo tee /etc/nginx/sites-available/$NGINX_SITE > /dev/null <<EOF
# DCAM Application Configuration
# Please customize this configuration based on your setup

server {
    listen 80;
    server_name your-domain.com;  # CHANGE THIS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;  # CHANGE THIS

    # SSL configuration - UPDATE THESE PATHS
    ssl_certificate /path/to/your/ssl/cert.pem;
    ssl_certificate_key /path/to/your/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;

    # DCAM application (path-based deployment)
    location /dcam/ {
        proxy_pass http://127.0.0.1:5001/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # Handle large file uploads
        client_max_body_size 100M;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    # Static files for DCAM
    location /dcam/static/ {
        alias $DCAM_DIR/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Your existing Redmine configuration should remain here
    # location / {
    #     proxy_pass http://127.0.0.1:3000;
    #     # ... other Redmine settings
    # }
}
EOF

echo "⚠️  Please complete the following manual steps:"
echo ""
echo "1. Edit nginx configuration:"
echo "   sudo nano /etc/nginx/sites-available/$NGINX_SITE"
echo "   - Update server_name to your actual domain"
echo "   - Update SSL certificate paths"
echo "   - Add your existing Redmine configuration"
echo ""
echo "2. Enable nginx site:"
echo "   sudo ln -s /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/"
echo "   sudo nginx -t"
echo "   sudo systemctl reload nginx"
echo ""
echo "3. Create backup directory:"
echo "   sudo mkdir -p /opt/backups/dcam"
echo ""
echo "4. Set up log rotation (optional):"
echo "   sudo nano /etc/logrotate.d/dcam"
echo ""
echo "🎉 DCAM deployment completed!"
echo "📊 Service status: $(sudo systemctl is-active $SERVICE_NAME)"
echo "📝 Check logs: sudo journalctl -u $SERVICE_NAME -f"
EOF