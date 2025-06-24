# 🚀 Production Deployment Guide

This guide covers deploying the Chat with Data application to production environments using various deployment strategies.

## 📋 Deployment Options

1. **Azure Container Apps**
2. **Azure App Service**
3. **Traditional VPS/VM Deployment** (Recommended)
4. **Cloud Server Manual Setup**

## ☁️ Azure Container Apps Deployment

### 1. Azure Resources Setup

#### Create Resource Group and Container Registry
```bash
# Variables
RESOURCE_GROUP="chat-data-rg"
LOCATION="eastus"
ACR_NAME="chatdataacr"
CONTAINER_APP_ENV="chat-data-env"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Container Registry
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# Create Container Apps Environment
az containerapp env create \
  --name $CONTAINER_APP_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

#### Build and Push Images
```bash
# Login to ACR
az acr login --name $ACR_NAME

# Build and push backend
docker build -t $ACR_NAME.azurecr.io/chat-data-backend:latest ./backend
docker push $ACR_NAME.azurecr.io/chat-data-backend:latest

# Build and push frontend
docker build -t $ACR_NAME.azurecr.io/chat-data-frontend:latest ./frontend
docker push $ACR_NAME.azurecr.io/chat-data-frontend:latest
```

### 2. Container Apps Configuration

#### Deploy Container Apps
```bash
# Deploy backend
az containerapp create \
  --name chat-data-backend \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_APP_ENV \
  --image $ACR_NAME.azurecr.io/chat-data-backend:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server $ACR_NAME.azurecr.io \
  --registry-username $(az acr credential show -n $ACR_NAME --query username -o tsv) \
  --registry-password $(az acr credential show -n $ACR_NAME --query passwords[0].value -o tsv) \
  --secrets anthropic-api-key="your_api_key" \
  --env-vars ANTHROPIC_API_KEY=secretref:anthropic-api-key

# Deploy frontend
az containerapp create \
  --name chat-data-frontend \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_APP_ENV \
  --image $ACR_NAME.azurecr.io/chat-data-frontend:latest \
  --target-port 3000 \
  --ingress external \
  --registry-server $ACR_NAME.azurecr.io \
  --registry-username $(az acr credential show -n $ACR_NAME --query username -o tsv) \
  --registry-password $(az acr credential show -n $ACR_NAME --query passwords[0].value -o tsv)
```

## 🏢 Azure App Service Deployment

### 1. Create App Service Resources

```bash
# Create App Service Plan
az appservice plan create \
  --name chat-data-plan \
  --resource-group $RESOURCE_GROUP \
  --sku B2 \
  --is-linux

# Create Web Apps
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan chat-data-plan \
  --name chat-data-backend-app \
  --runtime "PYTHON|3.11"

az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan chat-data-plan \
  --name chat-data-frontend-app \
  --runtime "NODE|18-lts"
```

### 2. Configure App Settings

```bash
# Backend configuration
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name chat-data-backend-app \
  --settings \
    ANTHROPIC_API_KEY="your_api_key" \
    AZURE_TENANT_ID="your_tenant_id" \
    AZURE_CLIENT_ID="your_client_id" \
    AZURE_CLIENT_SECRET="your_client_secret"

# Frontend configuration
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name chat-data-frontend-app \
  --settings \
    NEXT_PUBLIC_API_URL="https://chat-data-backend-app.azurewebsites.net"
```

## 🖥️ Traditional VPS/VM Deployment (Recommended)

### 1. Server Setup

#### Install Prerequisites on Ubuntu/Debian
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip -y

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2 for process management
sudo npm install -g pm2

# Install Nginx
sudo apt install nginx -y

# Install Certbot for SSL
sudo apt install certbot python3-certbot-nginx -y
```

### 2. Application Deployment

#### Deploy Backend
```bash
# Create application directory
sudo mkdir -p /var/www/chat-data
sudo chown $USER:$USER /var/www/chat-data

# Clone repository
cd /var/www/chat-data
git clone https://github.com/yourusername/chat-with-data.git .

# Setup backend
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with production values

# Test backend
python main.py
```

#### Deploy Frontend
```bash
# Setup frontend
cd /var/www/chat-data/frontend
npm install
npm run build

# Test frontend
npm start
```

### 3. Process Management with PM2

#### PM2 Configuration Files

**Backend PM2 Config: `backend/ecosystem.config.js`**
```javascript
module.exports = {
  apps: [{
    name: 'chat-data-backend',
    script: '/var/www/chat-data/backend/venv/bin/python',
    args: 'main.py',
    cwd: '/var/www/chat-data/backend',
    instances: 2,
    exec_mode: 'cluster',
    env: {
      PORT: 8000,
      NODE_ENV: 'production'
    },
    error_file: '/var/log/pm2/chat-data-backend-error.log',
    out_file: '/var/log/pm2/chat-data-backend-out.log',
    log_file: '/var/log/pm2/chat-data-backend.log',
    time: true
  }]
}
```

**Frontend PM2 Config: `frontend/ecosystem.config.js`**
```javascript
module.exports = {
  apps: [{
    name: 'chat-data-frontend',
    script: 'npm',
    args: 'start',
    cwd: '/var/www/chat-data/frontend',
    instances: 1,
    env: {
      PORT: 3000,
      NODE_ENV: 'production'
    },
    error_file: '/var/log/pm2/chat-data-frontend-error.log',
    out_file: '/var/log/pm2/chat-data-frontend-out.log',
    log_file: '/var/log/pm2/chat-data-frontend.log',
    time: true
  }]
}
```

#### Start Applications with PM2
```bash
# Create log directory
sudo mkdir -p /var/log/pm2
sudo chown $USER:$USER /var/log/pm2

# Start backend
cd /var/www/chat-data/backend
pm2 start ecosystem.config.js

# Start frontend
cd /var/www/chat-data/frontend
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 startup script
pm2 startup
sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u $USER --hp $HOME
```

### 4. Nginx Configuration

#### Production Nginx Config
```nginx
# /etc/nginx/sites-available/chat-data
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health checks
    location /health {
        proxy_pass http://localhost:8000;
    }

    # API Documentation
    location /docs {
        proxy_pass http://localhost:8000;
    }
}
```

#### Enable Nginx Site
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/chat-data /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### 5. SSL Certificate Setup

```bash
# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Setup auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔧 Production Configuration

### 1. Environment Variables

#### Backend Production Variables
```bash
# Core Configuration
ANTHROPIC_API_KEY=your_production_api_key
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret

# Performance Settings
UVICORN_WORKERS=4
CACHE_TTL=7200
MAX_QUERY_ROWS=1000
QUERY_TIMEOUT=30

# Security Settings
SECRET_KEY=your_256_bit_secret_key
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Monitoring
LOG_LEVEL=INFO
ENABLE_METRICS=true
```

#### Frontend Production Variables
```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://yourdomain.com

# Performance
NEXT_PUBLIC_CACHE_TTL=3600
```

## 🚨 Backup and Disaster Recovery

### 1. Backup Script

```bash
#!/bin/bash
# backup.sh - Automated backup script

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/var/www/chat-data"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup application files
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz -C /var/www chat-data

# Backup Nginx configuration
tar -czf $BACKUP_DIR/nginx_backup_$DATE.tar.gz /etc/nginx/sites-available/chat-data

# Backup environment files
cp $APP_DIR/backend/.env $BACKUP_DIR/backend_env_$DATE
cp $APP_DIR/frontend/.env.local $BACKUP_DIR/frontend_env_$DATE

# Backup PM2 configuration
pm2 save
cp ~/.pm2/dump.pm2 $BACKUP_DIR/pm2_dump_$DATE.pm2

# Upload to cloud storage (optional)
# aws s3 cp $BACKUP_DIR/ s3://your-backup-bucket/chat-data/ --recursive

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*_env_*" -mtime +30 -delete
```

### 2. Update and Deployment Script

```bash
#!/bin/bash
# deploy.sh - Production deployment script

echo "🚀 Starting production deployment..."

APP_DIR="/var/www/chat-data"
cd $APP_DIR

# Pull latest changes
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Update frontend
cd frontend
npm install
npm run build
cd ..

# Restart applications
pm2 restart all

# Reload Nginx
sudo nginx -s reload

echo "✅ Deployment completed successfully!"
```

## 📊 Monitoring and Logging

### 1. Log Management

#### Logrotate Configuration
```bash
# /etc/logrotate.d/chat-data
/var/log/pm2/*.log {
    daily
    missingok
    rotate 52
    compress
    notifempty
    create 644 $USER $USER
    postrotate
        pm2 reloadLogs
    endscript
}
```

### 2. Health Monitoring

#### Simple Health Check Script
```bash
#!/bin/bash
# health-check.sh

# Check backend
if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "Backend is down, restarting..."
    pm2 restart chat-data-backend
fi

# Check frontend
if ! curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "Frontend is down, restarting..."
    pm2 restart chat-data-frontend
fi
```

#### Add to Crontab
```bash
# Add to crontab
*/5 * * * * /path/to/health-check.sh
```

## 🎯 Final Deployment Checklist

### Pre-Deployment
- [ ] Server configured with Python 3.11 and Node.js 18
- [ ] All environment variables configured
- [ ] SSL certificates installed and validated
- [ ] Database connections tested
- [ ] AI service API keys validated
- [ ] PM2 process management configured
- [ ] Nginx reverse proxy configured
- [ ] Firewall rules configured

### Deployment
- [ ] Application code deployed
- [ ] Dependencies installed
- [ ] PM2 processes started
- [ ] Nginx configuration activated
- [ ] SSL certificates configured
- [ ] Backup procedures implemented
- [ ] Monitoring scripts configured

### Post-Deployment
- [ ] Verify application functionality
- [ ] Test authentication flows
- [ ] Validate data source connections
- [ ] Monitor performance metrics
- [ ] Test backup and recovery procedures
- [ ] Configure automated health checks
- [ ] Document maintenance procedures

---

🎉 **Congratulations!** Your Chat with Data application is now deployed to production with enterprise-grade reliability and performance.

### Prerequisites
- Docker and Docker Compose installed
- Production domain/subdomain configured
- SSL certificate (Let's Encrypt recommended)

### 1. Create Production Docker Files

#### Backend Dockerfile
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    unixodbc-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### Frontend Dockerfile
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code and build
COPY . .
RUN npm run build

# Production image
FROM node:18-alpine AS runner

WORKDIR /app

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

### 2. Docker Compose Configuration

#### Production docker-compose.yml
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    container_name: chat-data-backend
    restart: unless-stopped
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - AZURE_TENANT_ID=${AZURE_TENANT_ID}
      - AZURE_CLIENT_ID=${AZURE_CLIENT_ID}
      - AZURE_CLIENT_SECRET=${AZURE_CLIENT_SECRET}
      - LOG_LEVEL=INFO
      - CORS_ORIGINS=https://yourdomain.com
    volumes:
      - ./logs:/app/logs
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: chat-data-frontend
    restart: unless-stopped
    environment:
      - NEXT_PUBLIC_API_URL=https://api.yourdomain.com
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    container_name: chat-data-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - backend
      - frontend
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    container_name: chat-data-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  redis_data:
    driver: local
```

### 3. Nginx Configuration

#### Production Nginx Config
```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=10r/m;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Frontend (Main App)
    server {
        listen 80;
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;

        # Redirect HTTP to HTTPS
        if ($scheme != "https") {
            return 301 https://$host$request_uri;
        }

        # Security Headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
        }
    }

    # Backend API
    server {
        listen 80;
        listen 443 ssl http2;
        server_name api.yourdomain.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;

        # Redirect HTTP to HTTPS
        if ($scheme != "https") {
            return 301 https://$host$request_uri;
        }

        # API Rate Limiting
        location /api/auth {
            limit_req zone=auth burst=5 nodelay;
            proxy_pass http://backend;
            include proxy_params;
        }

        location /api {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
            include proxy_params;
        }

        location /health {
            proxy_pass http://backend;
            include proxy_params;
        }

        location /docs {
            proxy_pass http://backend;
            include proxy_params;
        }
    }
}
```

#### Proxy Parameters
```nginx
# nginx/proxy_params
proxy_http_version 1.1;
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection 'upgrade';
proxy_cache_bypass $http_upgrade;
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
```

### 4. Environment Configuration

#### Production Environment File
```bash
# .env.prod
# AI Service
ANTHROPIC_API_KEY=your_production_claude_api_key

# Azure Authentication
AZURE_TENANT_ID=your_production_tenant_id
AZURE_CLIENT_ID=your_production_client_id
AZURE_CLIENT_SECRET=your_production_client_secret

# Redis Configuration
REDIS_PASSWORD=your_strong_redis_password
REDIS_URL=redis://redis:6379

# Security
SECRET_KEY=your_very_strong_secret_key_here
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Performance
CACHE_TTL=7200
MAX_QUERY_ROWS=1000
WORKER_PROCESSES=4

# Monitoring
LOG_LEVEL=INFO
ENABLE_METRICS=true
```

### 5. Deployment Script

#### deploy.sh
```bash
#!/bin/bash
# deploy.sh - Production deployment script

set -e

echo "🚀 Starting production deployment..."

# Load environment variables
source .env.prod

# Pre-deployment checks
echo "📋 Running pre-deployment checks..."

# Check if domain is accessible
if ! curl -sSf https://yourdomain.com > /dev/null 2>&1; then
    echo "⚠️  Warning: Domain not accessible, continuing anyway..."
fi

# Check SSL certificates
if [ ! -f "./nginx/ssl/fullchain.pem" ]; then
    echo "❌ SSL certificate not found. Please install SSL certificates first."
    exit 1
fi

# Build and deploy
echo "🔨 Building containers..."
docker-compose -f docker-compose.prod.yml build --no-cache

echo "⬇️  Pulling latest base images..."
docker-compose -f docker-compose.prod.yml pull

echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

echo "🚀 Starting new containers..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "🏥 Waiting for services to be healthy..."
timeout 120 bash -c 'until docker-compose -f docker-compose.prod.yml ps | grep healthy; do sleep 5; done'

# Run health checks
echo "🧪 Running health checks..."
if curl -sSf https://api.yourdomain.com/health; then
    echo "✅ Backend health check passed"
else
    echo "❌ Backend health check failed"
    exit 1
fi

if curl -sSf https://yourdomain.com; then
    echo "✅ Frontend health check passed"
else
    echo "❌ Frontend health check failed"
    exit 1
fi

echo "🎉 Deployment completed successfully!"
echo "🌐 Application is available at: https://yourdomain.com"
echo "📊 API documentation: https://api.yourdomain.com/docs"
```

## ☁️ Azure Container Apps Deployment

### 1. Azure Resources Setup

#### Create Resource Group and Container Registry
```bash
# Variables
RESOURCE_GROUP="chat-data-rg"
LOCATION="eastus"
ACR_NAME="chatdataacr"
CONTAINER_APP_ENV="chat-data-env"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Container Registry
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# Create Container Apps Environment
az containerapp env create \
  --name $CONTAINER_APP_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

#### Build and Push Images
```bash
# Login to ACR
az acr login --name $ACR_NAME

# Build and push backend
docker build -t $ACR_NAME.azurecr.io/chat-data-backend:latest ./backend
docker push $ACR_NAME.azurecr.io/chat-data-backend:latest

# Build and push frontend
docker build -t $ACR_NAME.azurecr.io/chat-data-frontend:latest ./frontend
docker push $ACR_NAME.azurecr.io/chat-data-frontend:latest
```

### 2. Container Apps Configuration

#### Backend Container App
```yaml
# azure-backend.yaml
apiVersion: apps/v1
kind: ContainerApp
metadata:
  name: chat-data-backend
spec:
  environmentId: /subscriptions/{subscription-id}/resourceGroups/chat-data-rg/providers/Microsoft.App/managedEnvironments/chat-data-env
  configuration:
    ingress:
      external: true
      targetPort: 8000
      corsPolicy:
        allowedOrigins:
          - "https://yourdomain.com"
    secrets:
      - name: anthropic-api-key
        value: "your_api_key"
      - name: azure-client-secret
        value: "your_client_secret"
  template:
    containers:
      - image: chatdataacr.azurecr.io/chat-data-backend:latest
        name: backend
        env:
          - name: ANTHROPIC_API_KEY
            secretRef: anthropic-api-key
          - name: AZURE_TENANT_ID
            value: "your_tenant_id"
          - name: AZURE_CLIENT_ID
            value: "your_client_id"
          - name: AZURE_CLIENT_SECRET
            secretRef: azure-client-secret
        resources:
          cpu: 1.0
          memory: 2Gi
    scale:
      minReplicas: 1
      maxReplicas: 10
      rules:
        - name: http-scaling
          http:
            concurrentRequests: 100
```

#### Deploy Container Apps
```bash
# Deploy backend
az containerapp create \
  --name chat-data-backend \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_APP_ENV \
  --image $ACR_NAME.azurecr.io/chat-data-backend:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server $ACR_NAME.azurecr.io \
  --registry-username $(az acr credential show -n $ACR_NAME --query username -o tsv) \
  --registry-password $(az acr credential show -n $ACR_NAME --query passwords[0].value -o tsv) \
  --secrets anthropic-api-key="your_api_key" \
  --env-vars ANTHROPIC_API_KEY=secretref:anthropic-api-key

# Deploy frontend
az containerapp create \
  --name chat-data-frontend \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINER_APP_ENV \
  --image $ACR_NAME.azurecr.io/chat-data-frontend:latest \
  --target-port 3000 \
  --ingress external \
  --registry-server $ACR_NAME.azurecr.io \
  --registry-username $(az acr credential show -n $ACR_NAME --query username -o tsv) \
  --registry-password $(az acr credential show -n $ACR_NAME --query passwords[0].value -o tsv)
```

## 🏢 Azure App Service Deployment

### 1. Create App Service Resources

```bash
# Create App Service Plan
az appservice plan create \
  --name chat-data-plan \
  --resource-group $RESOURCE_GROUP \
  --sku B2 \
  --is-linux

# Create Web Apps
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan chat-data-plan \
  --name chat-data-backend-app \
  --deployment-container-image-name $ACR_NAME.azurecr.io/chat-data-backend:latest

az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan chat-data-plan \
  --name chat-data-frontend-app \
  --deployment-container-image-name $ACR_NAME.azurecr.io/chat-data-frontend:latest
```

### 2. Configure App Settings

```bash
# Backend configuration
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name chat-data-backend-app \
  --settings \
    ANTHROPIC_API_KEY="your_api_key" \
    AZURE_TENANT_ID="your_tenant_id" \
    AZURE_CLIENT_ID="your_client_id" \
    AZURE_CLIENT_SECRET="your_client_secret" \
    WEBSITES_PORT=8000

# Frontend configuration
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name chat-data-frontend-app \
  --settings \
    NEXT_PUBLIC_API_URL="https://chat-data-backend-app.azurewebsites.net" \
    WEBSITES_PORT=3000
```

## 🔧 Production Configuration

### 1. Environment Variables

#### Backend Production Variables
```bash
# Core Configuration
ANTHROPIC_API_KEY=your_production_api_key
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret

# Performance Settings
UVICORN_WORKERS=4
UVICORN_MAX_WORKERS=8
CACHE_TTL=7200
MAX_QUERY_ROWS=1000
QUERY_TIMEOUT=30

# Security Settings
SECRET_KEY=your_256_bit_secret_key
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
ALLOWED_HOSTS=api.yourdomain.com,yourdomain.com

# Monitoring
LOG_LEVEL=INFO
ENABLE_METRICS=true
SENTRY_DSN=your_sentry_dsn  # Optional
```

#### Frontend Production Variables
```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://api.yourdomain.com

# Analytics (Optional)
NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
NEXT_PUBLIC_HOTJAR_ID=your_hotjar_id

# Performance
NEXT_PUBLIC_ENABLE_SW=true  # Service Worker
NEXT_PUBLIC_CACHE_TTL=3600
```

### 2. SSL Certificate Setup (Let's Encrypt)

#### Automatic SSL with Certbot
```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificates
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. Monitoring and Logging

#### Log Aggregation with ELK Stack
```yaml
# monitoring/docker-compose.monitoring.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    volumes:
      - ./logstash/config:/usr/share/logstash/pipeline

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200

volumes:
  elasticsearch_data:
```

#### Application Performance Monitoring
```python
# backend/monitoring.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

# Initialize Sentry (Optional)
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[
        FastApiIntegration(auto_enabling_integrations=False),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
)

# Custom metrics
from prometheus_client import Counter, Histogram, generate_latest

query_counter = Counter('queries_total', 'Total queries processed', ['type', 'status'])
query_duration = Histogram('query_duration_seconds', 'Query execution time')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    query_duration.observe(duration)
    
    return response
```

## 🔒 Security Hardening

### 1. Network Security

#### Firewall Configuration
```bash
# Configure UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Rate limiting with fail2ban
sudo apt-get install fail2ban

# Configure fail2ban
sudo tee /etc/fail2ban/jail.local <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
EOF
```

### 2. Container Security

#### Security Scanning
```bash
# Scan images for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image chatdataacr.azurecr.io/chat-data-backend:latest

# Use distroless images for production
FROM gcr.io/distroless/python3-debian11
```

### 3. Application Security

#### Security Headers and CORS
```python
# backend/security.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["yourdomain.com", "api.yourdomain.com"]
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

## 📊 Performance Optimization

### 1. Caching Strategy

#### Redis Configuration
```python
# backend/cache.py
import redis
import json
from typing import Optional, Any

class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True
        )
    
    async def get(self, key: str) -> Optional[Any]:
        value = self.redis_client.get(key)
        return json.loads(value) if value else None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        self.redis_client.setex(key, ttl, json.dumps(value))
```

### 2. Database Connection Pooling

```python
# backend/database.py
from sqlalchemy.pool import QueuePool

engine = create_engine(
    connection_string,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### 3. CDN Configuration

#### CloudFlare Setup
```javascript
// cloudflare-worker.js
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const cache = caches.default
  const cacheKey = new Request(request.url, request)
  const response = await cache.match(cacheKey)

  if (response) {
    return response
  }

  const fetchResponse = await fetch(request)
  
  // Cache static assets
  if (request.url.includes('/static/') || request.url.includes('/_next/')) {
    const responseToCache = fetchResponse.clone()
    event.waitUntil(cache.put(cacheKey, responseToCache))
  }

  return fetchResponse
}
```

## 🚨 Backup and Disaster Recovery

### 1. Database Backup

```bash
#!/bin/bash
# backup.sh - Automated backup script

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup Redis data
docker exec chat-data-redis redis-cli --rdb $BACKUP_DIR/redis_backup_$DATE.rdb

# Backup application logs
tar -czf $BACKUP_DIR/logs_backup_$DATE.tar.gz ./logs/

# Upload to cloud storage (AWS S3 example)
aws s3 cp $BACKUP_DIR/ s3://your-backup-bucket/chat-data/ --recursive

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "*.rdb" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### 2. Disaster Recovery Plan

#### Recovery Procedures
```bash
#!/bin/bash
# recovery.sh - Disaster recovery script

echo "🚨 Starting disaster recovery..."

# Pull latest backups
aws s3 sync s3://your-backup-bucket/chat-data/ ./backups/

# Restore Redis data
docker exec chat-data-redis redis-cli FLUSHALL
docker cp ./backups/redis_backup_latest.rdb chat-data-redis:/data/dump.rdb
docker restart chat-data-redis

# Restore application configuration
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

echo "✅ Disaster recovery completed"
```

## 📈 Monitoring and Alerting

### 1. Health Checks

```python
# backend/health.py
from fastapi import APIRouter, HTTPException
import psutil
import redis

router = APIRouter()

@router.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
        "performance": {}
    }
    
    # Check services
    try:
        # Check Claude API
        health_status["services"]["claude"] = claude_service.is_available()
        
        # Check Redis
        redis_client.ping()
        health_status["services"]["redis"] = True
        
        # Check database connections
        health_status["services"]["fabric"] = fabric_service.is_connected()
        health_status["services"]["powerbi"] = semantic_model_service.is_connected()
        
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["error"] = str(e)
    
    # Performance metrics
    health_status["performance"] = {
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent
    }
    
    return health_status
```

### 2. Prometheus Metrics

```python
# backend/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
active_connections = Gauge('active_database_connections', 'Active database connections')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    request_count.labels(method=request.method, endpoint=request.url.path).inc()
    request_duration.observe(duration)
    
    return response
```

### 3. Alerting Configuration

```yaml
# alerting/alerts.yml
groups:
  - name: chat-data-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          
      - alert: HighMemoryUsage
        expr: memory_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
```

## 🎯 Final Deployment Checklist

### Pre-Deployment
- [ ] All environment variables configured
- [ ] SSL certificates installed and validated
- [ ] Database connections tested
- [ ] AI service API keys validated
- [ ] Security scanning completed
- [ ] Performance testing completed
- [ ] Backup procedures tested

### Deployment
- [ ] Build and push container images
- [ ] Deploy infrastructure components
- [ ] Deploy application containers
- [ ] Configure load balancer/reverse proxy
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation
- [ ] Test all endpoints

### Post-Deployment
- [ ] Verify application functionality
- [ ] Test authentication flows
- [ ] Validate data source connections
- [ ] Monitor performance metrics
- [ ] Set up automated backups
- [ ] Configure alerting notifications
- [ ] Document runbook procedures

---

🎉 **Congratulations!** Your Chat with Data application is now deployed to production with enterprise-grade security, monitoring, and scalability features.
