# Hospital Inventory Analytics Dashboard - Deployment Guide

## 🚀 Deployment Options

This guide provides instructions for deploying the Hospital Inventory Analytics Dashboard in different environments.

---

## 1. Local Development (Recommended for Testing)

### Prerequisites
- Python 3.8+
- PostgreSQL (for analytics database)
- Git

### Steps

1. **Clone and navigate:**
   ```bash
   cd dashboard
   ```

2. **Run interactive setup:**
   ```bash
   python setup.py
   ```

3. **Or manual setup:**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Copy and configure .env
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Run dashboard:**
   ```bash
   streamlit run app.py
   ```

Access at: `http://localhost:8501`

---

## 2. Docker (Recommended for Production)

### Prerequisites
- Docker and Docker Compose
- PostgreSQL database (external or see docker-compose option)

### Quick Start

```bash
# Using Docker Compose (includes PostgreSQL)
docker-compose up -d

# Or build and run manually
docker build -t hospital-dashboard -f dashboard/Dockerfile .
docker run -p 8501:8501 --env-file dashboard/.env hospital-dashboard
```

### Access
- Dashboard: `http://localhost:8501`
- Database: `localhost:5432` (if using docker-compose)

### Configuration
Edit `.env` before running:
```bash
POSTGRES_HOST=postgres  # Use service name in docker-compose
POSTGRES_PORT=5432
POSTGRES_DB=analytics
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
```

---

## 3. Linux Server (Production)

### Prerequisites
- Ubuntu/Debian server
- Python 3.8+
- PostgreSQL
- Nginx (optional, for reverse proxy)
- Supervisor or systemd for process management

### Installation

1. **Install system dependencies:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3.11 python3.11-venv python3-pip postgresql-client nginx supervisor
   ```

2. **Clone application:**
   ```bash
   cd /opt
   git clone <repository-url> hospital-dashboard
   cd hospital-dashboard/dashboard
   ```

3. **Create virtual environment:**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your credentials
   ```

5. **Create Supervisor config** (`/etc/supervisor/conf.d/dashboard.conf`):
   ```ini
   [program:hospital-dashboard]
   directory=/opt/hospital-dashboard/dashboard
   command=/opt/hospital-dashboard/dashboard/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
   user=www-data
   autostart=true
   autorestart=true
   stderr_logfile=/var/log/dashboard/error.log
   stdout_logfile=/var/log/dashboard/access.log
   ```

6. **Start supervisor:**
   ```bash
   sudo supervisorctl reread
   sudo supervisorctl update
   sudo supervisorctl start hospital-dashboard
   ```

7. **Configure Nginx** (`/etc/nginx/sites-available/dashboard`):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8501;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

8. **Enable Nginx site:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/dashboard /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### Monitoring

Check status:
```bash
sudo supervisorctl status
tail -f /var/log/dashboard/access.log
```

---

## 4. Windows Server

### Prerequisites
- Windows Server 2019+
- Python 3.8+
- PostgreSQL
- NSSM (Non-Sucking Service Manager) or Task Scheduler

### Installation

1. **Install Python and dependencies:**
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure .env:**
   ```powershell
   Copy-Item .env.example .env
   # Edit .env with notepad
   ```

3. **Create Windows Service with NSSM:**
   ```powershell
   # Download NSSM from nssm.cc
   .\nssm.exe install hospital-dashboard "C:\path\to\venv\Scripts\streamlit.exe" "run app.py --server.port=8501"
   .\nssm.exe start hospital-dashboard
   ```

4. **Or use Task Scheduler:**
   - Create batch file: `run-dashboard.bat`
   - Schedule with Task Scheduler to run at startup

### Access
Visit: `http://localhost:8501`

---

## 5. Kubernetes (Enterprise)

### Prerequisites
- Kubernetes cluster
- Docker registry
- kubectl configured

### Deployment

1. **Build Docker image:**
   ```bash
   docker build -t your-registry/hospital-dashboard:1.0 -f dashboard/Dockerfile .
   docker push your-registry/hospital-dashboard:1.0
   ```

2. **Create ConfigMap for .env:**
   ```yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: dashboard-config
   data:
     POSTGRES_HOST: analytics-db.default.svc.cluster.local
     POSTGRES_PORT: "5432"
     POSTGRES_DB: analytics
     POSTGRES_USER: postgres
     HOSPITAL_NAME: Hospital Inventory Analytics
   ```

3. **Deploy with Kubernetes:**
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: hospital-dashboard
   spec:
     replicas: 2
     selector:
       matchLabels:
         app: hospital-dashboard
     template:
       metadata:
         labels:
           app: hospital-dashboard
       spec:
         containers:
         - name: dashboard
           image: your-registry/hospital-dashboard:1.0
           ports:
           - containerPort: 8501
           envFrom:
           - configMapRef:
               name: dashboard-config
           env:
           - name: POSTGRES_PASSWORD
             valueFrom:
               secretKeyRef:
                 name: db-credentials
                 key: password
   ```

4. **Expose with Service:**
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: hospital-dashboard-svc
   spec:
     type: LoadBalancer
     selector:
       app: hospital-dashboard
     ports:
     - protocol: TCP
       port: 80
       targetPort: 8501
   ```

---

## 6. Cloud Platforms

### AWS

```bash
# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin your-registry
docker tag hospital-dashboard:1.0 your-registry/hospital-dashboard:1.0
docker push your-registry/hospital-dashboard:1.0

# Deploy to ECS
aws ecs create-service --cluster hospital-dev --service-name dashboard --task-definition hospital-dashboard
```

### Google Cloud

```bash
# Push to GCR
docker tag hospital-dashboard:1.0 gcr.io/your-project/hospital-dashboard:1.0
docker push gcr.io/your-project/hospital-dashboard:1.0

# Deploy to Cloud Run
gcloud run deploy hospital-dashboard \
  --image gcr.io/your-project/hospital-dashboard:1.0 \
  --platform managed \
  --region us-central1
```

### Azure

```bash
# Push to ACR
az acr build --registry your-registry --image hospital-dashboard:1.0 .

# Deploy to Container Instances
az container create \
  --resource-group your-group \
  --name hospital-dashboard \
  --image your-registry.azurecr.io/hospital-dashboard:1.0 \
  --ports 8501 \
  --environment-variables POSTGRES_HOST=your-db-host
```

---

## 💾 Database Backup & Recovery

### PostgreSQL Backup

```bash
# Full backup
pg_dump -h localhost -U postgres -d analytics > analytics_backup.sql

# Compressed backup
pg_dump -h localhost -U postgres -d analytics | gzip > analytics_backup.sql.gz

# Restore
psql -h localhost -U postgres -d analytics < analytics_backup.sql
```

### Automated Backup

Create backup script:
```bash
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +"%Y%m%d_%H%M%S")

pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB | \
  gzip > "$BACKUP_DIR/analytics_$DATE.sql.gz"

# Keep only last 30 backups
find $BACKUP_DIR -name "analytics_*.sql.gz" -mtime +30 -delete
```

Schedule with cron:
```bash
0 2 * * * /usr/local/bin/backup-db.sh
```

---

## 🔒 Security Checklist

- [ ] Use HTTPS/SSL certificates
- [ ] Enable PostgreSQL authentication
- [ ] Use strong passwords for database
- [ ] Restrict database access by IP
- [ ] Enable audit logging
- [ ] Keep dependencies updated: `pip list --outdated`
- [ ] Use secrets management for credentials
- [ ] Enable firewall rules
- [ ] Implement rate limiting
- [ ] Monitor application logs
- [ ] Regular security updates
- [ ] Backup database regularly
- [ ] Test disaster recovery

---

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
name: Deploy Dashboard

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Build Docker image
      run: docker build -t dashboard:${{ github.sha }} -f dashboard/Dockerfile .
    - name: Push to registry
      run: docker push your-registry/dashboard:${{ github.sha }}
    - name: Deploy to production
      run: kubectl set image deployment/hospital-dashboard dashboard=your-registry/dashboard:${{ github.sha }}
```

---

## 📊 Performance Optimization

### For High Traffic

1. **Increase Streamlit workers:**
   ```bash
   streamlit run app.py --logger.level=warning --client.showErrorDetails=false
   ```

2. **Database connection pooling:**
   - Configure PostgreSQL connection limits
   - Use pgBouncer for connection pooling

3. **Caching strategy:**
   - Adjust `CACHE_TTL` in config.py
   - Use Redis for distributed caching

4. **Load balancing:**
   - Set up multiple dashboard instances
   - Use Nginx/HAProxy for load balancing

### Monitoring

```bash
# Monitor resource usage
docker stats
ps aux | grep streamlit

# Check database performance
psql -h localhost -U postgres -d analytics -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables ORDER BY pg_total_relation_size DESC;"
```

---

## 🐛 Troubleshooting

### Connection Refused
```bash
# Check if PostgreSQL is running
netstat -tlnp | grep postgres

# Check dashboard logs
docker logs hospital-dashboard
tail -f /var/log/dashboard/error.log
```

### Memory Issues
```bash
# Check memory usage
free -h
docker stats

# Increase server memory or reduce cache
```

### Database Performance
```bash
# Check slow queries
psql -h localhost -U postgres -d analytics -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

---

## 📞 Support & Escalation

1. Check application logs
2. Verify database connectivity
3. Review ETL pipeline status
4. Contact database administrator
5. Check infrastructure resources

---

**Last Updated:** 2026-04-10
