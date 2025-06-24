# 📁 Complete File Structure for Local Setup

Here are all the files users need to set up the webapp locally. You can upload these directly to your GitHub repository.

## 🗂️ Repository Structure

```
chat-with-data/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── claude_service.py
│   │   ├── enhanced_multi_agent_service.py
│   │   ├── fabric_service.py
│   │   ├── semantic_model_service.py
│   │   └── knowledge_base_service.py
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── components/
│   │   │   ├── EnhancedChatInterface.tsx
│   │   │   ├── FabricConnection.tsx
│   │   │   ├── PowerBIMCPConnection.tsx
│   │   │   ├── OAuth2Config.tsx
│   │   │   ├── ConfigStatus.tsx
│   │   │   └── SchemaExplorer.tsx
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── package.json
│   ├── package-lock.json
│   ├── next.config.js
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── .env.local.example
├── .gitignore
├── setup.sh
├── README.md
├── INSTALLATION.md
├── ARCHITECTURE.md
├── API.md
├── DEPLOYMENT.md
└── LICENSE
```

## 📄 Essential Configuration Files

### 1. Backend Environment Template

**File: `backend/.env.example`**
```env
# ===========================================
# CHAT WITH DATA - BACKEND CONFIGURATION
# ===========================================

# AI Service Configuration
ANTHROPIC_API_KEY=your_claude_api_key_here

# Azure Authentication
# Get these from your Azure App Registration
AZURE_TENANT_ID=your_azure_tenant_id_here
AZURE_CLIENT_ID=your_azure_client_id_here
AZURE_CLIENT_SECRET=your_azure_client_secret_here

# Application Settings
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000

# Performance Settings
CACHE_TTL=3600
MAX_QUERY_ROWS=1000
QUERY_TIMEOUT=30

# Security (Generate a strong secret key)
SECRET_KEY=your_secret_key_here_generate_a_strong_one

# Development Settings
DEBUG=true
RELOAD=true
```

### 2. Frontend Environment Template

**File: `frontend/.env.local.example`**
```env
# ===========================================
# CHAT WITH DATA - FRONTEND CONFIGURATION
# ===========================================

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Analytics and Monitoring
# NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
# NEXT_PUBLIC_HOTJAR_ID=your_hotjar_id

# Development Settings
NODE_ENV=development
```

### 3. Package.json for Frontend

**File: `frontend/package.json`**
```json
{
  "name": "chat-with-data-frontend",
  "version": "1.0.0",
  "description": "AI-powered chat interface for Microsoft Fabric and Power BI",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "react-markdown": "^9.0.0",
    "recharts": "^2.8.0",
    "lucide-react": "^0.263.1"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.2.0",
    "eslint": "^8.0.0",
    "eslint-config-next": "^14.0.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  },
  "keywords": [
    "ai",
    "chat",
    "data",
    "microsoft-fabric",
    "power-bi",
    "claude",
    "analytics"
  ],
  "author": "Your Name",
  "license": "MIT"
}
```

### 4. Requirements.txt for Backend

**File: `backend/requirements.txt`**
```txt
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0

# Environment and Configuration
python-dotenv==1.0.0

# AI and LLM
anthropic==0.7.7

# Database and Data
pyodbc==5.0.1
pandas==2.1.3
sqlalchemy==2.0.23

# Microsoft Azure
msal==1.25.0
azure-identity==1.15.0
azure-core==1.29.5

# Data Visualization and Processing
matplotlib==3.8.2
seaborn==0.13.0

# HTTP and API
requests==2.31.0
httpx==0.25.2

# Caching and Performance
redis==5.0.1
aioredis==2.0.1

# Monitoring and Logging
sentry-sdk[fastapi]==1.38.0
prometheus-client==0.19.0

# Development and Testing
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
isort==5.12.0
```

### 5. Frontend TypeScript Configuration

**File: `frontend/tsconfig.json`**
```json
{
  "compilerOptions": {
    "lib": ["dom", "dom.iterable", "es6"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "baseUrl": ".",
    "paths": {
      "@/*": ["./app/*"],
      "@/components/*": ["./app/components/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### 6. Next.js Configuration

**File: `frontend/next.config.js`**
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    appDir: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
      },
    ]
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ]
  },
}

module.exports = nextConfig
```

### 7. Tailwind CSS Configuration

**File: `frontend/tailwind.config.js`**
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        secondary: {
          50: '#f8fafc',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
```

### 8. Git Ignore File

**File: `.gitignore`**
```gitignore
# Dependencies
node_modules/
*/node_modules/

# Environment variables
.env
.env.local
.env.production
.env.staging
*.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
venv/
env/

# Next.js
.next/
out/
*.tsbuildinfo

# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/

# nyc test coverage
.nyc_output

# Dependency directories
jspm_packages/

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# dotenv environment variables file
.env.test

# parcel-bundler cache (https://parceljs.org/)
.cache
.parcel-cache

# next.js build output
.next

# nuxt.js build output
.nuxt

# vuepress build output
.vuepress/dist

# Serverless directories
.serverless

# FuseBox cache
.fusebox/

# DynamoDB Local files
.dynamodb/

# TernJS port file
.tern-port

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
logs/
*.log

# Cache
.cache/
```

## 🚀 Quick Start Script for Users

**File: `setup.sh`** (Make it executable with `chmod +x setup.sh`)
```bash
#!/bin/bash

# Chat with Data - Quick Setup Script
echo "🚀 Setting up Chat with Data Application..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

print_status "Prerequisites check completed!"

# Setup environment files
print_status "Setting up environment files..."

# Backend environment
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    print_status "Created backend/.env from template"
    print_warning "Please edit backend/.env with your configuration"
else
    print_warning "backend/.env already exists"
fi

# Frontend environment
if [ ! -f "frontend/.env.local" ]; then
    cp frontend/.env.local.example frontend/.env.local
    print_status "Created frontend/.env.local from template"
else
    print_warning "frontend/.env.local already exists"
fi

# Backend setup
print_status "Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Created Python virtual environment"
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # macOS/Linux
    source venv/bin/activate
fi

pip install --upgrade pip
pip install -r requirements.txt
print_status "Installed Python dependencies"

cd ..

# Frontend setup
print_status "Setting up frontend..."
cd frontend

npm install
print_status "Installed Node.js dependencies"

cd ..

print_status "Setup completed!"
echo
print_status "🎉 Installation successful!"
echo
print_warning "⚠️  IMPORTANT: Before running the application:"
print_warning "1. Edit backend/.env with your Azure credentials and Claude API key"
print_warning "2. Follow the Azure setup guide in INSTALLATION.md"
print_warning "3. Add your app to Microsoft Fabric and Power BI workspaces"
echo
print_status "To start the application:"
echo
echo "1. Start backend (Terminal 1):"
echo "   cd backend"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "   venv\\Scripts\\activate"
else
    echo "   source venv/bin/activate"
fi
echo "   python main.py"
echo
echo "2. Start frontend (Terminal 2):"
echo "   cd frontend"
echo "   npm run dev"
echo
print_status "Then visit: http://localhost:3000"
print_status "API docs will be at: http://localhost:8000/docs"
echo
print_status "For detailed setup instructions, see INSTALLATION.md"
```

## 📋 Simple README for Quick Start

Add this section to your main README.md:

```markdown
## 🚀 Quick Local Setup

### Option 1: Automated Setup (Recommended)
```bash
# Clone the repository
git clone https://github.com/yourusername/chat-with-data.git
cd chat-with-data

# Run the setup script
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

**Backend Setup:**
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your configuration

# Start backend
python main.py
```

**Frontend Setup:**
```bash
cd frontend

# Install dependencies
npm install

# Copy and configure environment
cp .env.local.example .env.local
# Edit .env.local with your configuration

# Start frontend
npm run dev
```

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📝 Configuration Required

After setup, you must:
1. Configure Azure App Registration (see INSTALLATION.md)
2. Add your Claude API key to backend/.env
3. Add your Azure credentials to backend/.env
4. Add the app to your Microsoft Fabric and Power BI workspaces
```

## 🎯 What Users Need to Do

After downloading your repository, users only need to:

1. **Clone the repo** and run the setup script
2. **Configure environment variables** in the `.env` files
3. **Set up Azure App Registration** (following your INSTALLATION.md)
4. **Add the app to workspaces** (as per your updated instructions)
5. **Start the application** with two simple commands

The setup script handles all the Python virtual environment creation, dependency installation, and environment file setup automatically! This makes it incredibly easy for users to get started with your sophisticated AI-powered data chat application.

## 🔧 Two-Terminal Startup

Once configured, users just need:

**Terminal 1 (Backend):**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python main.py
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

That's it! No Docker complexity, just simple Python and Node.js commands that any developer can understand and troubleshoot.



## 📄 Essential Configuration Files

### 1. Backend Environment Template

**File: `backend/.env.example`**
```env
# ===========================================
# CHAT WITH DATA - BACKEND CONFIGURATION
# ===========================================

# AI Service Configuration
ANTHROPIC_API_KEY=your_claude_api_key_here

# Azure Authentication
# Get these from your Azure App Registration
AZURE_TENANT_ID=your_azure_tenant_id_here
AZURE_CLIENT_ID=your_azure_client_id_here
AZURE_CLIENT_SECRET=your_azure_client_secret_here

# Application Settings
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000

# Performance Settings
CACHE_TTL=3600
MAX_QUERY_ROWS=1000
QUERY_TIMEOUT=30

# Security (Generate a strong secret key)
SECRET_KEY=your_secret_key_here_generate_a_strong_one

# Development Settings
DEBUG=true
RELOAD=true
```

### 2. Frontend Environment Template

**File: `frontend/.env.local.example`**
```env
# ===========================================
# CHAT WITH DATA - FRONTEND CONFIGURATION
# ===========================================

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Analytics and Monitoring
# NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
# NEXT_PUBLIC_HOTJAR_ID=your_hotjar_id

# Development Settings
NODE_ENV=development
```

### 3. Package.json for Frontend

**File: `frontend/package.json`**
```json
{
  "name": "chat-with-data-frontend",
  "version": "1.0.0",
  "description": "AI-powered chat interface for Microsoft Fabric and Power BI",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "react-markdown": "^9.0.0",
    "recharts": "^2.8.0",
    "lucide-react": "^0.263.1"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.2.0",
    "eslint": "^8.0.0",
    "eslint-config-next": "^14.0.0",
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  },
  "keywords": [
    "ai",
    "chat",
    "data",
    "microsoft-fabric",
    "power-bi",
    "claude",
    "analytics"
  ],
  "author": "Your Name",
  "license": "MIT"
}
```

### 4. Requirements.txt for Backend

**File: `backend/requirements.txt`**
```txt
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0

# Environment and Configuration
python-dotenv==1.0.0

# AI and LLM
anthropic==0.7.7

# Database and Data
pyodbc==5.0.1
pandas==2.1.3
sqlalchemy==2.0.23

# Microsoft Azure
msal==1.25.0
azure-identity==1.15.0
azure-core==1.29.5

# Data Visualization and Processing
matplotlib==3.8.2
seaborn==0.13.0

# HTTP and API
requests==2.31.0
httpx==0.25.2

# Caching and Performance
redis==5.0.1
aioredis==2.0.1

# Monitoring and Logging
sentry-sdk[fastapi]==1.38.0
prometheus-client==0.19.0

# Development and Testing
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
isort==5.12.0
```

### 5. Docker Compose for Local Development

**File: `docker-compose.dev.yml`**
```yaml
version: '3.8'

services:
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    container_name: chat-data-backend-dev
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - AZURE_TENANT_ID=${AZURE_TENANT_ID}
      - AZURE_CLIENT_ID=${AZURE_CLIENT_ID}
      - AZURE_CLIENT_SECRET=${AZURE_CLIENT_SECRET}
      - DEBUG=true
      - RELOAD=true
      - CORS_ORIGINS=http://localhost:3000
    volumes:
      - ./backend:/app
      - backend_cache:/app/.cache
    networks:
      - dev-network
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: chat-data-frontend-dev
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NODE_ENV=development
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    networks:
      - dev-network
    depends_on:
      - backend

  redis:
    image: redis:7-alpine
    container_name: chat-data-redis-dev
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - dev-network
    command: redis-server --appendonly yes

networks:
  dev-network:
    driver: bridge

volumes:
  backend_cache:
  redis_data:
```

### 6. Frontend TypeScript Configuration

**File: `frontend/tsconfig.json`**
```json
{
  "compilerOptions": {
    "lib": ["dom", "dom.iterable", "es6"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "baseUrl": ".",
    "paths": {
      "@/*": ["./app/*"],
      "@/components/*": ["./app/components/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### 7. Next.js Configuration

**File: `frontend/next.config.js`**
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    appDir: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
      },
    ]
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ]
  },
}

module.exports = nextConfig
```

### 8. Tailwind CSS Configuration

**File: `frontend/tailwind.config.js`**
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        secondary: {
          50: '#f8fafc',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
```

### 9. Git Ignore File

**File: `.gitignore`**
```gitignore
# Dependencies
node_modules/
*/node_modules/

# Environment variables
.env
.env.local
.env.production
.env.staging
*.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
venv/
env/

# Next.js
.next/
out/
*.tsbuildinfo

# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/

# nyc test coverage
.nyc_output

# Dependency directories
jspm_packages/

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# dotenv environment variables file
.env.test

# parcel-bundler cache (https://parceljs.org/)
.cache
.parcel-cache

# next.js build output
.next

# nuxt.js build output
.nuxt

# vuepress build output
.vuepress/dist

# Serverless directories
.serverless

# FuseBox cache
.fusebox/

# DynamoDB Local files
.dynamodb/

# TernJS port file
.tern-port

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Docker
docker-compose.override.yml

# Logs
logs/
*.log

# Cache
.cache/
```

### 10. Docker Development Dockerfile for Frontend

**File: `frontend/Dockerfile.dev`**
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Create next.js cache directory
RUN mkdir -p .next

# Expose port
EXPOSE 3000

# Start development server
CMD ["npm", "run", "dev"]
```

## 🚀 Quick Start Script for Users

**File: `setup.sh`** (Make it executable with `chmod +x setup.sh`)
```bash
#!/bin/bash

# Chat with Data - Quick Setup Script
echo "🚀 Setting up Chat with Data Application..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

# Check Docker (optional)
if ! command -v docker &> /dev/null; then
    print_warning "Docker is not installed. Manual setup will be used."
    USE_DOCKER=false
else
    print_status "Docker found. You can use Docker setup if preferred."
    USE_DOCKER=true
fi

print_status "Prerequisites check completed!"

# Setup environment files
print_status "Setting up environment files..."

# Backend environment
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    print_status "Created backend/.env from template"
    print_warning "Please edit backend/.env with your configuration"
else
    print_warning "backend/.env already exists"
fi

# Frontend environment
if [ ! -f "frontend/.env.local" ]; then
    cp frontend/.env.local.example frontend/.env.local
    print_status "Created frontend/.env.local from template"
else
    print_warning "frontend/.env.local already exists"
fi

# Ask user for setup preference
echo
echo "Choose setup method:"
echo "1) Docker Compose (Recommended - easier setup)"
echo "2) Manual setup (More control)"
echo
read -p "Enter your choice (1 or 2): " choice

if [ "$choice" = "1" ] && [ "$USE_DOCKER" = true ]; then
    print_status "Setting up with Docker Compose..."
    
    # Build and start containers
    docker-compose -f docker-compose.dev.yml up --build -d
    
    print_status "Containers are starting up..."
    print_status "Frontend will be available at: http://localhost:3000"
    print_status "Backend API will be available at: http://localhost:8000"
    print_status "API Documentation: http://localhost:8000/docs"
    
elif [ "$choice" = "2" ]; then
    print_status "Setting up manually..."
    
    # Backend setup
    print_status "Setting up backend..."
    cd backend
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_status "Created Python virtual environment"
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt
    print_status "Installed Python dependencies"
    
    cd ..
    
    # Frontend setup
    print_status "Setting up frontend..."
    cd frontend
    
    npm install
    print_status "Installed Node.js dependencies"
    
    cd ..
    
    print_status "Setup completed!"
    echo
    print_status "To start the application:"
    echo "1. Start backend:"
    echo "   cd backend"
    echo "   source venv/bin/activate"
    echo "   python main.py"
    echo
    echo "2. Start frontend (in another terminal):"
    echo "   cd frontend"
    echo "   npm run dev"
    echo
    print_status "Then visit: http://localhost:3000"
    
else
    print_error "Invalid choice or Docker not available"
    exit 1
fi

echo
print_status "🎉 Setup completed!"
print_warning "Don't forget to:"
print_warning "1. Configure your Azure App Registration"
print_warning "2. Add your API keys to the .env files"
print_warning "3. Add the app to your Microsoft Fabric and Power BI workspaces"
print_warning "4. Check the INSTALLATION.md for detailed configuration steps"
```

## 📋 Simple README for Quick Start

Add this section to your main README.md:

```markdown
## 🚀 Quick Local Setup

### Option 1: Automated Setup (Recommended)
```bash
# Clone the repository
git clone https://github.com/yourusername/chat-with-data.git
cd chat-with-data

# Run the setup script
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

**Backend Setup:**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your configuration

# Start backend
python main.py
```

**Frontend Setup:**
```bash
cd frontend

# Install dependencies
npm install

# Copy and configure environment
cp .env.local.example .env.local
# Edit .env.local with your configuration

# Start frontend
npm run dev
```

### Option 3: Docker Compose
```bash
# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local

# Edit the .env files with your configuration

# Start with Docker
docker-compose -f docker-compose.dev.yml up --build
```

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
```

## 🎯 What Users Need to Do

After downloading your repository, users only need to:

1. **Clone the repo** and run the setup script
2. **Configure environment variables** in the `.env` files
3. **Set up Azure App Registration** (following your INSTALLATION.md)
4. **Add the app to workspaces** (as per your updated instructions)
5. **Start the application**

The setup script automates everything else! This makes it incredibly easy for users to get started with your sophisticated AI-powered data chat application.
