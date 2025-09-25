#!/bin/bash

# DCAM Service Fix Script
# Run this to fix the systemd service configuration issues

set -e

echo "🔧 Fixing DCAM service configuration..."

# Configuration
DCAM_DIR="/opt/dcam"
SERVICE_NAME="dcam"
USER="dcam"

# Stop existing service if running
echo "⏹️ Stopping existing service..."
sudo systemctl stop $SERVICE_NAME 2>/dev/null || echo "Service not running"
sudo systemctl disable $SERVICE_NAME 2>/dev/null || echo "Service not enabled"

# Create dedicated user for DCAM
echo "👤 Creating DCAM user..."
sudo useradd --system --shell /bin/false --home-dir $DCAM_DIR $USER 2>/dev/null || echo "User $USER already exists"

# Fix ownership and permissions
echo "🔐 Fixing ownership and permissions..."
sudo chown -R $USER:$USER $DCAM_DIR
sudo chmod -R 755 $DCAM_DIR

# Recreate systemd service with correct configuration
echo "⚙️ Recreating systemd service..."
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

# Reload systemd and start service
echo "🔄 Reloading systemd and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# Wait a moment and check status
sleep 3

if sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ DCAM service is now running successfully!"
    echo "📊 Service status:"
    sudo systemctl status $SERVICE_NAME --no-pager -l
else
    echo "❌ Service still not running. Checking logs..."
    echo "📝 Recent logs:"
    sudo journalctl -u $SERVICE_NAME --no-pager -l -n 20
    exit 1
fi

echo ""
echo "🎉 Fix completed!"
echo "🌐 You can now access DCAM at: https://your-domain.com/dcam/"
echo "📝 Monitor logs with: sudo journalctl -u $SERVICE_NAME -f"