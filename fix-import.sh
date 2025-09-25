#!/bin/bash

# DCAM Import Error Fix Script
# This script fixes the gunicorn import error

set -e

echo "🔧 Fixing DCAM import error..."

DCAM_DIR="/opt/dcam"
cd $DCAM_DIR

echo "📋 Current directory structure:"
ls -la $DCAM_DIR

echo ""
echo "🔍 Checking app.py structure..."
if [ -f "app.py" ]; then
    echo "✅ app.py exists"
    echo "   File size: $(stat -c '%s' app.py) bytes"
    
    # Check if the file has Flask app definition
    if grep -q "app = Flask" app.py; then
        echo "✅ Flask app found in app.py"
    else
        echo "❌ No Flask app definition found"
        echo "   Looking for Flask app variable..."
        grep -n "Flask\|app\s*=" app.py | head -5
    fi
else
    echo "❌ app.py not found!"
    echo "   Available Python files:"
    find . -name "*.py" -type f
    exit 1
fi

echo ""
echo "🐍 Testing Python import..."
cd $DCAM_DIR
sudo -u dcam $DCAM_DIR/venv/bin/python -c "
import sys
sys.path.insert(0, '/opt/dcam')
try:
    import app
    print('✅ Successfully imported app module')
    if hasattr(app, 'app'):
        print('✅ Flask app object found')
    else:
        print('❌ No Flask app object named \"app\" found')
        print('Available attributes:', [attr for attr in dir(app) if not attr.startswith('_')])
except Exception as e:
    print('❌ Import error:', str(e))
    import traceback
    traceback.print_exc()
"

echo ""
echo "🔧 Checking if we need to create WSGI entry point..."

# Check if there's a main execution block
if grep -q "if __name__ == '__main__':" app.py; then
    echo "✅ Main execution block found"
else
    echo "⚠️  No main execution block found"
fi

# Create a simple WSGI entry point if needed
echo ""
echo "📝 Creating wsgi.py entry point..."
cat > wsgi.py << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Add the application directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask application
try:
    from app import app
    application = app
except ImportError as e:
    print(f"Error importing app: {e}")
    raise

if __name__ == "__main__":
    application.run()
EOF

sudo chown dcam:dcam wsgi.py
sudo chmod +x wsgi.py

echo "✅ Created wsgi.py entry point"

echo ""
echo "🧪 Testing wsgi.py import..."
sudo -u dcam $DCAM_DIR/venv/bin/python -c "
try:
    import wsgi
    print('✅ Successfully imported wsgi module')
    if hasattr(wsgi, 'application'):
        print('✅ WSGI application object found')
    else:
        print('❌ No WSGI application object found')
except Exception as e:
    print('❌ WSGI import error:', str(e))
    import traceback
    traceback.print_exc()
"

echo ""
echo "🔄 Updating systemd service to use wsgi.py..."

# Update systemd service
sudo tee /etc/systemd/system/dcam.service > /dev/null <<EOF
[Unit]
Description=DCAM Flask Application
After=network.target

[Service]
Type=exec
User=dcam
Group=dcam
WorkingDirectory=$DCAM_DIR
Environment=PATH=$DCAM_DIR/venv/bin
Environment=FLASK_ENV=production
Environment=PYTHONPATH=$DCAM_DIR
ExecStart=$DCAM_DIR/venv/bin/gunicorn --bind 127.0.0.1:5001 --workers 3 --timeout 120 wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Updated systemd service configuration"

echo ""
echo "🚀 Testing gunicorn with wsgi.py..."
sudo systemctl daemon-reload

# Test gunicorn manually first
echo "   Testing manual gunicorn start..."
cd $DCAM_DIR
timeout 5s sudo -u dcam $DCAM_DIR/venv/bin/gunicorn --bind 127.0.0.1:5002 --workers 1 wsgi:application &
TEST_PID=$!
sleep 2

if ps -p $TEST_PID > /dev/null 2>&1; then
    echo "✅ Manual gunicorn test successful"
    kill $TEST_PID 2>/dev/null || true
    
    echo ""
    echo "🔄 Starting DCAM service..."
    sudo systemctl start dcam
    sleep 3
    
    if sudo systemctl is-active --quiet dcam; then
        echo "✅ DCAM service started successfully!"
        sudo systemctl status dcam --no-pager -l
    else
        echo "❌ Service still not starting. Checking logs..."
        sudo journalctl -u dcam --no-pager -l -n 10
    fi
else
    echo "❌ Manual gunicorn test failed"
    echo "   Checking for detailed error..."
fi

echo ""
echo "📋 If service is working, test with:"
echo "curl -I http://127.0.0.1:5001/"
echo ""
echo "📝 Monitor logs with:"
echo "sudo journalctl -u dcam -f"