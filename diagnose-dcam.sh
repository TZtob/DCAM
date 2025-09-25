#!/bin/bash

# DCAM Service Diagnostic Script
# This script will help diagnose and fix DCAM service startup issues

echo "🔍 DCAM Service Diagnostic Tool"
echo "==============================="

# Check service status
echo "📊 Service Status:"
sudo systemctl status dcam --no-pager -l

echo ""
echo "📝 Recent Service Logs:"
sudo journalctl -u dcam --no-pager -l -n 20

echo ""
echo "🔧 Environment Checks:"

# Check if dcam user exists
echo "👤 Checking dcam user:"
if id dcam &>/dev/null; then
    echo "✅ User 'dcam' exists"
    echo "   Home: $(getent passwd dcam | cut -d: -f6)"
    echo "   Shell: $(getent passwd dcam | cut -d: -f7)"
else
    echo "❌ User 'dcam' does not exist"
    echo "   Creating user..."
    sudo useradd --system --shell /bin/false --home-dir /opt/dcam dcam
    echo "✅ User created"
fi

# Check DCAM directory
echo ""
echo "📁 Checking DCAM directory:"
if [ -d "/opt/dcam" ]; then
    echo "✅ Directory /opt/dcam exists"
    echo "   Owner: $(stat -c '%U:%G' /opt/dcam)"
    echo "   Permissions: $(stat -c '%a' /opt/dcam)"
else
    echo "❌ Directory /opt/dcam does not exist"
    exit 1
fi

# Check Python virtual environment
echo ""
echo "🐍 Checking Python environment:"
if [ -f "/opt/dcam/venv/bin/python" ]; then
    echo "✅ Virtual environment exists"
    echo "   Python version: $(/opt/dcam/venv/bin/python --version 2>&1)"
else
    echo "❌ Virtual environment missing"
    echo "   Creating virtual environment..."
    cd /opt/dcam
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Check gunicorn
echo ""
echo "⚙️ Checking Gunicorn:"
if [ -f "/opt/dcam/venv/bin/gunicorn" ]; then
    echo "✅ Gunicorn exists"
    echo "   Version: $(/opt/dcam/venv/bin/gunicorn --version 2>&1)"
else
    echo "❌ Gunicorn not found"
    echo "   Installing gunicorn..."
    /opt/dcam/venv/bin/pip install gunicorn
    echo "✅ Gunicorn installed"
fi

# Check app.py
echo ""
echo "📄 Checking application files:"
if [ -f "/opt/dcam/app.py" ]; then
    echo "✅ app.py exists"
    echo "   Size: $(stat -c '%s' /opt/dcam/app.py) bytes"
else
    echo "❌ app.py not found"
    echo "   Please ensure all DCAM files are uploaded to /opt/dcam/"
    exit 1
fi

# Check dependencies
echo ""
echo "📦 Checking Python dependencies:"
if [ -f "/opt/dcam/requirements.txt" ]; then
    echo "✅ requirements.txt exists"
    echo "   Installing dependencies..."
    cd /opt/dcam
    ./venv/bin/pip install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "⚠️  requirements.txt not found, installing basic dependencies..."
    cd /opt/dcam
    ./venv/bin/pip install Flask PyYAML Werkzeug gunicorn
fi

# Test application manually
echo ""
echo "🧪 Testing application startup:"
echo "   Attempting to run app directly..."

cd /opt/dcam
timeout 10s sudo -u dcam ./venv/bin/python app.py 2>&1 | head -10 || {
    echo "❌ Application failed to start directly"
    echo "   Checking Python syntax..."
    sudo -u dcam ./venv/bin/python -m py_compile app.py && echo "✅ Python syntax OK" || echo "❌ Python syntax error"
}

# Fix ownership
echo ""
echo "🔐 Fixing file ownership:"
sudo chown -R dcam:dcam /opt/dcam
sudo chmod +x /opt/dcam/venv/bin/*
echo "✅ Ownership fixed"

# Try to start with more verbose logging
echo ""
echo "🚀 Testing gunicorn startup:"
echo "   Running gunicorn with debug output..."
cd /opt/dcam
sudo -u dcam ./venv/bin/gunicorn --bind 127.0.0.1:5001 --workers 1 --timeout 30 --log-level debug app:app &
GUNICORN_PID=$!
sleep 3

if ps -p $GUNICORN_PID > /dev/null; then
    echo "✅ Gunicorn started successfully (PID: $GUNICORN_PID)"
    kill $GUNICORN_PID
    echo "   Stopped test instance"
else
    echo "❌ Gunicorn failed to start"
fi

echo ""
echo "🔧 Suggested fixes:"
echo "1. Check the detailed logs above for specific error messages"
echo "2. Ensure all Python dependencies are installed"
echo "3. Verify app.py has no syntax errors"
echo "4. Check file permissions and ownership"

echo ""
echo "📋 Manual commands to try:"
echo "cd /opt/dcam"
echo "sudo -u dcam ./venv/bin/python app.py"
echo "sudo -u dcam ./venv/bin/gunicorn --bind 127.0.0.1:5001 --workers 1 app:app"

echo ""
echo "🔄 To restart the service after fixes:"
echo "sudo systemctl restart dcam"
echo "sudo systemctl status dcam"