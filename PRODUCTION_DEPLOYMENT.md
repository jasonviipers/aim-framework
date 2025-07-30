# AIM Framework - Production Deployment Guide

This guide provides comprehensive instructions for deploying the AIM Framework in production environments.

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd aim-framework-package

# Build and run with Docker Compose
docker-compose up -d

# Check status
docker-compose ps
```

### Using Python Package

```bash
# Install from PyPI
pip install aim-framework

# Initialize a new project
aim-init my-project
cd my-project

# Start the server
aim-server --config config/production.json
```

## Deployment Methods

### 1. Docker Deployment

#### Single Container
```bash
# Build the image
docker build -t aim-framework:latest .

# Run the container
docker run -d \
  --name aim-framework \
  -p 5000:5000 \
  -v $(pwd)/config:/app/config \
  -v aim-logs:/app/logs \
  -v aim-data:/app/data \
  --restart unless-stopped \
  aim-framework:latest
```

#### Docker Compose (Production)
```bash
# Start all services
docker-compose -f docker-compose.yml up -d

# Scale the application
docker-compose up -d --scale aim-server=3

# View logs
docker-compose logs -f aim-server
```

### 2. Systemd Service

```bash
# Run the deployment script
python deploy.py --environment production --method systemd

# Manual service management
sudo systemctl start aim-framework
sudo systemctl enable aim-framework
sudo systemctl status aim-framework
```

### 3. Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aim-framework
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aim-framework
  template:
    metadata:
      labels:
        app: aim-framework
    spec:
      containers:
      - name: aim-framework
        image: aim-framework:latest
        ports:
        - containerPort: 5000
        env:
        - name: AIM_CONFIG_FILE
          value: "/app/config/production.json"
        volumeMounts:
        - name: config
          mountPath: /app/config
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: config
        configMap:
          name: aim-config
      - name: logs
        persistentVolumeClaim:
          claimName: aim-logs
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AIM_CONFIG_FILE` | Path to configuration file | `config/config.json` |
| `AIM_LOG_LEVEL` | Logging level | `INFO` |
| `AIM_API_HOST` | API server host | `0.0.0.0` |
| `AIM_API_PORT` | API server port | `5000` |
| `AIM_WORKERS` | Number of worker processes | `4` |
| `AIM_DB_URL` | Database connection URL | `sqlite:///data/aim.db` |
| `AIM_REDIS_URL` | Redis connection URL | `redis://localhost:6379` |

### Production Configuration

Create `config/production.json`:

```json
{
  "framework": {
    "name": "AIM Framework Production",
    "version": "1.0.0",
    "environment": "production"
  },
  "api": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false,
    "workers": 4
  },
  "security": {
    "api_key_required": true,
    "rate_limit": "100/minute",
    "cors_enabled": true,
    "allowed_origins": ["https://yourdomain.com"]
  },
  "logging": {
    "level": "INFO",
    "file": "/app/logs/aim.log",
    "max_file_size": 10485760,
    "backup_count": 5
  },
  "database": {
    "url": "postgresql://user:pass@localhost/aim",
    "pool_size": 10
  },
  "redis": {
    "enabled": true,
    "host": "localhost",
    "port": 6379
  }
}
```

## Load Balancing with Nginx

### Nginx Configuration

```nginx
upstream aim_backend {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    location / {
        proxy_pass http://aim_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    location /health {
        proxy_pass http://aim_backend;
        access_log off;
    }
}
```

## Monitoring and Observability

### Health Checks

```bash
# Basic health check
curl http://localhost:5000/health

# Detailed metrics
curl http://localhost:5000/metrics

# Performance test
python -m aim.utils.performance_test --url http://localhost:5000
```

### Logging

Logs are structured in JSON format for easy parsing:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "aim.api.server",
  "message": "Request processed",
  "request_id": "req-123",
  "user_id": "user-456",
  "response_time": 0.045,
  "status_code": 200
}
```

### Metrics Collection

The framework exposes Prometheus-compatible metrics:

```
# HELP aim_requests_total Total number of requests
# TYPE aim_requests_total counter
aim_requests_total{method="GET",endpoint="/health",status="200"} 1234

# HELP aim_request_duration_seconds Request duration in seconds
# TYPE aim_request_duration_seconds histogram
aim_request_duration_seconds_bucket{le="0.1"} 800
aim_request_duration_seconds_bucket{le="0.5"} 950
aim_request_duration_seconds_bucket{le="1.0"} 990
```

## Security

### SSL/TLS Configuration

```bash
# Generate self-signed certificate for testing
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Use Let's Encrypt for production
certbot --nginx -d api.yourdomain.com
```

### API Key Management

```python
from aim.utils.security import APIKeyManager

# Generate API key
manager = APIKeyManager("your-secret-key")
api_key = manager.generate_api_key("user123", expiry_days=365)

# Validate API key
valid, user_id = manager.validate_api_key(api_key)
```

### Rate Limiting

Configure rate limits in your production config:

```json
{
  "security": {
    "rate_limit": {
      "requests_per_minute": 100,
      "burst_size": 20,
      "per_user_limit": 1000
    }
  }
}
```

## Database Setup

### PostgreSQL (Recommended)

```sql
-- Create database and user
CREATE DATABASE aim_production;
CREATE USER aim_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE aim_production TO aim_user;

-- Connection string
postgresql://aim_user:secure_password@localhost:5432/aim_production
```

### Redis (Optional)

```bash
# Install Redis
sudo apt-get install redis-server

# Configure Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Test connection
redis-cli ping
```

## Backup and Recovery

### Automated Backups

```bash
# Create backup
python deploy.py --backup

# Restore from backup
tar -xzf backups/aim_backup_20240115_103000.tar.gz
```

### Database Backups

```bash
# PostgreSQL backup
pg_dump -h localhost -U aim_user aim_production > backup.sql

# Restore
psql -h localhost -U aim_user aim_production < backup.sql
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   sudo lsof -i :5000
   sudo kill -9 <PID>
   ```

2. **Permission denied**
   ```bash
   sudo chown -R aim:aim /app
   sudo chmod -R 755 /app
   ```

3. **Database connection failed**
   ```bash
   # Check database status
   sudo systemctl status postgresql
   
   # Test connection
   psql -h localhost -U aim_user -d aim_production
   ```

4. **High memory usage**
   ```bash
   # Monitor memory
   htop
   
   # Adjust worker count
   export AIM_WORKERS=2
   ```

### Log Analysis

```bash
# View recent errors
tail -f /app/logs/aim.log | grep ERROR

# Search for specific patterns
grep "request_id" /app/logs/aim.log | jq .

# Monitor performance
tail -f /app/logs/aim.log | grep "response_time" | jq .response_time
```

## Performance Tuning

### Gunicorn Configuration

```python
# gunicorn.conf.py
bind = "0.0.0.0:5000"
workers = 4
worker_class = "aiohttp.GunicornWebWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
```

### System Optimization

```bash
# Increase file descriptor limits
echo "aim soft nofile 65536" >> /etc/security/limits.conf
echo "aim hard nofile 65536" >> /etc/security/limits.conf

# Optimize TCP settings
echo "net.core.somaxconn = 1024" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 1024" >> /etc/sysctl.conf
sysctl -p
```

## Scaling

### Horizontal Scaling

```bash
# Docker Compose scaling
docker-compose up -d --scale aim-server=5

# Kubernetes scaling
kubectl scale deployment aim-framework --replicas=5
```

### Vertical Scaling

```bash
# Increase memory limit
docker run -m 2g aim-framework:latest

# Kubernetes resource limits
resources:
  limits:
    memory: "2Gi"
    cpu: "1000m"
  requests:
    memory: "1Gi"
    cpu: "500m"
```

## Maintenance

### Rolling Updates

```bash
# Docker Compose rolling update
docker-compose pull
docker-compose up -d --no-deps aim-server

# Kubernetes rolling update
kubectl set image deployment/aim-framework aim-framework=aim-framework:v1.1.0
```

### Health Monitoring

```bash
# Automated health check script
#!/bin/bash
while true; do
    if ! curl -f http://localhost:5000/health; then
        echo "Health check failed, restarting service"
        systemctl restart aim-framework
    fi
    sleep 60
done
```

## Support

For deployment issues and support:

- Documentation: https://aim-framework.readthedocs.io
- Issues: https://github.com/aim-framework/issues
- Community: https://discord.gg/aim-framework
- Email: support@aimframework.com