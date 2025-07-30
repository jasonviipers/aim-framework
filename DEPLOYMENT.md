# AIM Framework Deployment Guide

This guide provides comprehensive instructions for deploying the AIM Framework in production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [Configuration](#configuration)
4. [Docker Deployment](#docker-deployment)
5. [Production Deployment](#production-deployment)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Security Considerations](#security-considerations)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Python**: 3.8 or higher
- **Memory**: Minimum 2GB RAM (4GB+ recommended)
- **Storage**: 1GB+ available disk space
- **Network**: Open ports for API access (default: 5000)

### Dependencies

- Docker (for containerized deployment)
- Docker Compose (for orchestrated deployment)
- Nginx (for reverse proxy, optional)
- SSL certificates (for HTTPS, recommended)

## Installation Methods

### 1. PyPI Installation

```bash
# Install from PyPI
pip install aim-framework

# Install with API dependencies
pip install aim-framework[api]

# Install with all optional dependencies
pip install aim-framework[api,visualization,dev]
```

### 2. Source Installation

```bash
# Clone the repository
git clone https://github.com/jasonviipers/aim-framework.git
cd aim-framework

# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### 3. Docker Installation

```bash
# Pull the official image
docker pull jasonviipers/aim-framework:latest

# Or build from source
docker build -t aim-framework .
```

## Configuration

### Basic Configuration

Create a configuration file `config/config.json`:

```json
{
  "framework": {
    "name": "AIM Framework Production",
    "version": "1.0.0",
    "log_level": "INFO"
  },
  "api": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false,
    "cors_enabled": true
  },
  "security": {
    "allowed_origins": ["https://yourdomain.com"],
    "api_key_required": true,
    "rate_limit": {
      "requests_per_minute": 60,
      "burst_size": 10
    }
  },
  "logging": {
    "level": "INFO",
    "file": "/app/logs/aim.log",
    "max_file_size": 10485760,
    "backup_count": 5
  },
  "agents": {
    "max_concurrent_requests": 100,
    "request_timeout": 30.0,
    "health_check_interval": 60
  }
}
```

### Environment Variables

Set these environment variables for production:

```bash
export AIM_CONFIG_FILE=/path/to/config.json
export AIM_LOG_LEVEL=INFO
export AIM_API_HOST=0.0.0.0
export AIM_API_PORT=5000
export AIM_SECRET_KEY=your-secret-key-here
```

## Docker Deployment

### Single Container

```bash
# Run with default configuration
docker run -d \
  --name aim-framework \
  -p 5000:5000 \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/logs:/app/logs \
  jasonviipers/aim-framework:latest

# Run with custom configuration
docker run -d \
  --name aim-framework \
  -p 5000:5000 \
  -e AIM_LOG_LEVEL=INFO \
  -e AIM_API_HOST=0.0.0.0 \
  -e AIM_API_PORT=5000 \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  jasonviipers/aim-framework:latest
```

### Docker Compose

Use the provided `docker-compose.yml`:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f aim-server

# Stop services
docker-compose down

# Update and restart
docker-compose pull
docker-compose up -d
```

## Production Deployment

### 1. Using Gunicorn (Recommended)

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn --bind 0.0.0.0:5000 \
         --workers 4 \
         --worker-class aiohttp.GunicornWebWorker \
         --timeout 30 \
         --keepalive 2 \
         --max-requests 1000 \
         --max-requests-jitter 100 \
         aim.api.wsgi:application
```

### 2. Systemd Service

Create `/etc/systemd/system/aim-framework.service`:

```ini
[Unit]
Description=AIM Framework API Server
After=network.target

[Service]
Type=exec
User=aim
Group=aim
WorkingDirectory=/opt/aim-framework
Environment=PATH=/opt/aim-framework/venv/bin
Environment=AIM_CONFIG_FILE=/opt/aim-framework/config/config.json
ExecStart=/opt/aim-framework/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 aim.api.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable aim-framework
sudo systemctl start aim-framework
sudo systemctl status aim-framework
```

### 3. Nginx Reverse Proxy

Use the provided `nginx.conf` or create your own:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring and Logging

### Health Checks

The framework provides a health check endpoint:

```bash
curl http://localhost:5000/health
```

Response:
```json
{
  "status": "healthy",
  "framework_initialized": true,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Metrics Endpoint

Monitor performance metrics:

```bash
curl http://localhost:5000/metrics
```

### Log Configuration

Configure structured logging in your config file:

```json
{
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "/app/logs/aim.log",
    "max_file_size": 10485760,
    "backup_count": 5,
    "structured": true
  }
}
```

### External Monitoring

Integrate with monitoring tools:

- **Prometheus**: Use the `/metrics` endpoint
- **Grafana**: Create dashboards for visualization
- **ELK Stack**: Aggregate and analyze logs
- **New Relic/DataDog**: Application performance monitoring

## Security Considerations

### 1. API Security

- Enable HTTPS in production
- Use API keys for authentication
- Implement rate limiting
- Validate all input data
- Set appropriate CORS policies

### 2. Network Security

- Use firewalls to restrict access
- Deploy in private networks when possible
- Use VPN for administrative access
- Monitor network traffic

### 3. Container Security

- Use non-root users in containers
- Scan images for vulnerabilities
- Keep base images updated
- Use secrets management for sensitive data

### 4. Data Security

- Encrypt data at rest
- Use secure communication protocols
- Implement proper access controls
- Regular security audits

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Check what's using the port
lsof -i :5000

# Kill the process
kill -9 <PID>
```

#### 2. Permission Denied

```bash
# Fix file permissions
chmod +x aim-server
chown -R aim:aim /opt/aim-framework
```

#### 3. Memory Issues

```bash
# Check memory usage
free -h
docker stats

# Increase container memory limit
docker run --memory=4g aim-framework
```

#### 4. Configuration Errors

```bash
# Validate configuration
python -c "from aim.utils.config import Config; Config('config.json').validate()"

# Check logs for errors
tail -f /app/logs/aim.log
```

### Performance Tuning

#### 1. Worker Processes

Adjust the number of worker processes based on CPU cores:

```bash
# Rule of thumb: 2 * CPU cores + 1
gunicorn --workers 9 aim.api.wsgi:application
```

#### 2. Database Optimization

- Use connection pooling
- Optimize queries
- Add appropriate indexes
- Monitor slow queries

#### 3. Caching

- Enable Redis for session storage
- Implement response caching
- Use CDN for static assets

### Getting Help

- **Documentation**: https://aim-framework.readthedocs.io/
- **Issues**: https://github.com/jasonviipers/aim-framework/issues
- **Discussions**: https://github.com/jasonviipers/aim-framework/discussions
- **Email**: support@jasonviipers.com

## Deployment Checklist

Before going to production:

- [ ] Configuration reviewed and validated
- [ ] SSL certificates installed and configured
- [ ] Firewall rules configured
- [ ] Monitoring and alerting set up
- [ ] Backup strategy implemented
- [ ] Load testing completed
- [ ] Security scan performed
- [ ] Documentation updated
- [ ] Team trained on operations
- [ ] Rollback plan prepared