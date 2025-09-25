# DCAM Production Deployment Checklist

## Pre-Deployment Checklist ✅

### Server Environment
- [ ] Server has Redmine running successfully
- [ ] Domain name is configured and accessible
- [ ] SSL certificates are valid and working
- [ ] Nginx is installed and configured
- [ ] Python 3.8+ is available
- [ ] User has sudo privileges
- [ ] Sufficient disk space (min 1GB)

### Files Preparation
- [ ] DCAM project files are ready
- [ ] deployment scripts are executable
- [ ] requirements.txt is updated
- [ ] backup.sh script is prepared

## Deployment Steps Checklist 📋

### Step 1: File Transfer
- [ ] Compress DCAM project files
- [ ] Upload to server `/tmp` directory
- [ ] Verify file integrity after upload

### Step 2: Server Deployment
- [ ] Extract files to `/opt/dcam`
- [ ] Set proper ownership (`www-data:www-data`)
- [ ] Run deployment script (`./deploy.sh`)
- [ ] Verify DCAM service is running

### Step 3: Nginx Configuration
- [ ] Locate existing Nginx configuration
- [ ] Add DCAM location blocks
- [ ] Test Nginx configuration (`nginx -t`)
- [ ] Reload Nginx configuration

### Step 4: Verification
- [ ] Check DCAM service status
- [ ] Test local connectivity (port 5001)
- [ ] Test web access via domain
- [ ] Verify Redmine still works

### Step 5: Security Setup
- [ ] Configure firewall rules
- [ ] Set file permissions
- [ ] Change default admin password
- [ ] Create additional user accounts

### Step 6: Backup Configuration
- [ ] Test backup script execution
- [ ] Set up cron job for automated backups
- [ ] Verify backup directory exists

## Post-Deployment Verification ✅

### Functional Testing
- [ ] DCAM login page accessible
- [ ] User authentication works
- [ ] Customer management functions
- [ ] System management functions
- [ ] File upload functionality
- [ ] Asset query features

### Performance Testing
- [ ] Response time is acceptable
- [ ] Large file uploads work
- [ ] Multiple concurrent users
- [ ] Memory usage is reasonable

### Monitoring Setup
- [ ] Log monitoring is active
- [ ] Error alerting configured
- [ ] Performance metrics tracked
- [ ] Backup verification scheduled

## Maintenance Schedule 📅

### Daily Tasks
- [ ] Check service status
- [ ] Review error logs
- [ ] Monitor disk space

### Weekly Tasks
- [ ] Verify backup completion
- [ ] Check SSL certificate validity
- [ ] Review access logs

### Monthly Tasks
- [ ] Update system packages
- [ ] Test backup restoration
- [ ] Performance optimization review

## Emergency Contacts 📞

| Role | Contact | Phone | Email |
|------|---------|--------|-------|
| System Admin | [Name] | [Phone] | [Email] |
| Technical Support | [Name] | [Phone] | [Email] |
| Business Owner | [Name] | [Phone] | [Email] |

## Important URLs and Commands 🔗

### Service Commands
```bash
# Start/Stop DCAM
sudo systemctl start dcam
sudo systemctl stop dcam
sudo systemctl restart dcam

# Check status
sudo systemctl status dcam
sudo journalctl -u dcam -f

# Nginx commands
sudo nginx -t
sudo systemctl reload nginx
```

### Access URLs
- **DCAM Production**: https://your-domain.com/dcam/
- **Redmine Production**: https://your-domain.com/
- **Server SSH**: ssh user@your-server

### File Locations
- **DCAM Application**: `/opt/dcam/`
- **Nginx Config**: `/etc/nginx/sites-available/`
- **Service Config**: `/etc/systemd/system/dcam.service`
- **Backups**: `/opt/backups/dcam/`
- **Logs**: `journalctl -u dcam`

## Rollback Plan 🔄

In case of deployment failure:

1. **Stop DCAM service**:
   ```bash
   sudo systemctl stop dcam
   sudo systemctl disable dcam
   ```

2. **Remove Nginx configuration**:
   ```bash
   sudo nano /etc/nginx/sites-available/your-site
   # Remove DCAM location blocks
   sudo nginx -t && sudo systemctl reload nginx
   ```

3. **Restore from backup** (if needed):
   ```bash
   cd /opt/backups/dcam/
   tar -xzf dcam_config_YYYYMMDD_HHMMSS.tar.gz
   ```

4. **Verify Redmine is working**:
   - Check https://your-domain.com/
   - Verify all Redmine functions

## Success Criteria ✅

Deployment is considered successful when:

- [ ] DCAM is accessible via https://your-domain.com/dcam/
- [ ] Redmine continues to work normally
- [ ] User authentication functions properly
- [ ] File upload/download works
- [ ] All major features are operational
- [ ] No security vulnerabilities introduced
- [ ] Backup system is functional
- [ ] Monitoring is active

---

**Deployment Date**: _______________
**Deployed By**: _______________
**Verified By**: _______________
**Sign-off**: _______________