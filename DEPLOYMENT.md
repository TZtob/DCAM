# DCAM Application Deployment Guide

## Prerequisites
- Ubuntu/CentOS server with Redmine already running
- Nginx as web server
- Python 3.8+ available

## 1. Deploy DCAM Application

### 1.1 Create deployment directory
```bash
sudo mkdir -p /opt/dcam
sudo chown $USER:$USER /opt/dcam
```

### 1.2 Upload DCAM files
```bash
# Transfer files to server
rsync -avz --exclude '__pycache__' --exclude '*.pyc' /path/to/DCAM/ user@your-server:/opt/dcam/
```

### 1.3 Set up Python environment
```bash
cd /opt/dcam
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 1.4 Create requirements.txt
```bash
Flask==2.3.3
PyYAML==6.0.1
Werkzeug==2.3.7
gunicorn==21.2.0
toml==0.10.2
```

### 1.5 Create systemd service
```bash
sudo nano /etc/systemd/system/dcam.service
```

Content:
```ini
[Unit]
Description=DCAM Flask Application
After=network.target

[Service]
Type=exec
User=dcam
Group=dcam
WorkingDirectory=/opt/dcam
Environment=PATH=/opt/dcam/venv/bin
Environment=FLASK_ENV=production
ExecStart=/opt/dcam/venv/bin/gunicorn --bind 127.0.0.1:5001 --workers 3 --timeout 120 app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 1.6 Start DCAM service
```bash
sudo systemctl daemon-reload
sudo systemctl enable dcam
sudo systemctl start dcam
sudo systemctl status dcam
```

## 2. Configure Nginx Reverse Proxy

### 2.1 Create DCAM nginx configuration
```bash
sudo nano /etc/nginx/sites-available/dcam
```

Content:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL configuration (reuse existing certificates)
    ssl_certificate /path/to/your/ssl/cert.pem;
    ssl_certificate_key /path/to/your/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;

    # DCAM application
    location /dcam/ {
        proxy_pass http://127.0.0.1:5001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Script-Name /dcam;  # 重要: 传递URL前缀给Flask应用
        proxy_redirect off;
        
        # Handle large file uploads
        client_max_body_size 100M;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    # Static files for DCAM
    location /dcam/static/ {
        alias /opt/dcam/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Existing Redmine configuration
    location / {
        # Your existing Redmine proxy configuration
        proxy_pass http://127.0.0.1:3000;
        # ... other Redmine settings
    }
}
```

### 2.2 Enable the configuration
```bash
sudo ln -s /etc/nginx/sites-available/dcam /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 3. Alternative: Subdomain Deployment

If you prefer a subdomain approach:

### 3.1 DNS Configuration
Add a CNAME record: `dcam.your-domain.com` → `your-domain.com`

### 3.2 Nginx Configuration for Subdomain
```nginx
server {
    listen 80;
    server_name dcam.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dcam.your-domain.com;

    # SSL configuration (same certificates)
    ssl_certificate /path/to/your/ssl/cert.pem;
    ssl_certificate_key /path/to/your/ssl/private.key;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 100M;
    }

    location /static/ {
        alias /opt/dcam/static/;
        expires 1y;
    }
}
```

## 4. Security Considerations

### 4.1 Firewall
```bash
sudo ufw allow 5001/tcp  # Only if needed for debugging
```

### 4.2 File permissions
```bash
sudo chown -R www-data:www-data /opt/dcam
sudo chmod -R 755 /opt/dcam
```

### 4.3 Environment variables
```bash
sudo nano /opt/dcam/.env
```

Content:
```bash
SECRET_KEY=your-super-secret-production-key
FLASK_ENV=production
```

## 5. Backup Strategy

### 5.1 Data backup script
```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/dcam"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/dcam_data_$DATE.tar.gz /opt/dcam/*.json /opt/dcam/data/
find $BACKUP_DIR -name "dcam_data_*.tar.gz" -mtime +30 -delete
```

## 6. Monitoring

### 6.1 Log monitoring
```bash
sudo journalctl -u dcam -f
sudo tail -f /var/log/nginx/access.log | grep dcam
```

## 7. Update Process

### 7.1 Update script
```bash
#!/bin/bash
cd /opt/dcam
git pull origin main  # if using git
sudo systemctl restart dcam
sudo systemctl reload nginx
```

## Access URLs

- **Path-based**: https://your-domain.com/dcam/
- **Subdomain-based**: https://dcam.your-domain.com/

Choose the approach that best fits your existing infrastructure!