#!/bin/bash

# DCAM Backup Script
# Run this script regularly to backup DCAM data

BACKUP_DIR="/opt/backups/dcam"
DCAM_DIR="/opt/dcam"
DATE=$(date +%Y%m%d_%H%M%S)

echo "🔄 Starting DCAM backup - $DATE"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup data files
echo "📁 Backing up data files..."
tar -czf $BACKUP_DIR/dcam_data_$DATE.tar.gz \
    $DCAM_DIR/*.json \
    $DCAM_DIR/data/ \
    --exclude="$DCAM_DIR/data/uploads" 2>/dev/null || true

# Backup configuration files
echo "⚙️ Backing up configuration..."
tar -czf $BACKUP_DIR/dcam_config_$DATE.tar.gz \
    $DCAM_DIR/app.py \
    $DCAM_DIR/config.py \
    $DCAM_DIR/requirements.txt \
    /etc/systemd/system/dcam.service \
    /etc/nginx/sites-available/dcam 2>/dev/null || true

# Clean old backups (keep 30 days)
echo "🧹 Cleaning old backups..."
find $BACKUP_DIR -name "dcam_*_*.tar.gz" -mtime +30 -delete

echo "✅ Backup completed: $BACKUP_DIR/dcam_*_$DATE.tar.gz"
echo "📊 Backup directory size: $(du -sh $BACKUP_DIR | cut -f1)"