# 📥 Installation and Setup Guide

This guide provides detailed step-by-step instructions for setting up the Chat with Data application.

## 🎯 Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Python 3.8 or higher** installed
- [ ] **Node.js 18 or higher** installed
- [ ] **Git** installed
- [ ] **Azure account** with admin permissions
- [ ] **Microsoft Fabric workspace** (for SQL endpoint access)
- [ ] **Power BI Premium workspace** (for XMLA endpoint access)
- [ ] **Anthropic Claude API key**

## 📋 Step 1: Environment Setup

### 1.1 Clone the Repository
```bash
git clone https://github.com/yourusername/chat-with-data.git
cd chat-with-data
```

### 1.2 Verify Prerequisites
```bash
# Check Python version (should be 3.8+)
python --version

# Check Node.js version (should be 18+)
node --version

# Check npm version
npm --version
```

## 🔧 Step 2: Backend Setup

### 2.1 Navigate to Backend Directory
```bash
cd backend
```

### 2.2 Create Python Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# Verify activation (should show virtual environment path)
which python
```

### 2.3 Install Python Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installation
pip list
```

**Key dependencies installed:**
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `anthropic`: Claude AI client
- `pyodbc`: SQL Server connectivity
- `pandas`: Data manipulation
- `msal`: Microsoft Authentication Library
- `sqlalchemy`: Database ORM

### 2.4 Configure Backend Environment
```bash
# Create environment file from template
cp .env.example .env

# Edit the environment file
# Windows:
notepad .env
# macOS:
open -e .env
# Linux:
nano .env
```

**Configure `.env` file:**
```env
# Anthropic Claude API
ANTHROPIC_API_KEY=sk-ant-api03-your-api-key-here

# Azure Authentication (will be configured in next step)
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

# Application Settings
LOG_LEVEL=INFO
CACHE_TTL=3600
MAX_QUERY_ROWS=1000

# Security Settings
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000
```

### 2.5 Test Backend Installation
```bash
# Start the backend server
python main.py

# You should see output like:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Chat with Data API starting up...
# INFO:     Claude available: True
# INFO:     API ready to accept requests
```

Press `Ctrl+C` to stop the server.

## 🌐 Step 3: Frontend Setup

### 3.1 Navigate to Frontend Directory
```bash
# From project root
cd frontend
```

### 3.2 Install Node.js Dependencies
```bash
# Install dependencies
npm install

# Verify installation
npm list --depth=0
```

**Key dependencies installed:**
- `next`: React framework
- `react`: UI library
- `typescript`: Type safety
- `axios`: HTTP client
- `react-markdown`: Markdown rendering
- `recharts`: Data visualization

### 3.3 Configure Frontend Environment
```bash
# Create environment file
cp .env.local.example .env.local

# Edit the environment file
# Windows:
notepad .env.local
# macOS:
open -e .env.local
# Linux:
nano .env.local
```

**Configure `.env.local` file:**
```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Analytics
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id
```

### 3.4 Test Frontend Installation
```bash
# Start the development server
npm run dev

# You should see output like:
# ▲ Next.js 14.0.0
# - Local:        http://localhost:3000
# - Ready in 2.1s
```

## 🔐 Step 4: Azure Authentication Setup

### 4.1 Create Azure App Registration

1. **Go to Azure Portal**
   - Navigate to [portal.azure.com](https://portal.azure.com)
   - Sign in with your Azure account

2. **Navigate to App Registrations**
   - Search for "App registrations" in the search bar
   - Click on "App registrations"

3. **Create New Registration**
   - Click "New registration"
   - Fill in the details:
     - **Name**: `Chat with Data App`
     - **Supported account types**: `Accounts in this organizational directory only`
     - **Redirect URI**: `Web` → `http://localhost:3000/auth/callback`
   - Click "Register"

4. **Note Down Application Details**
   - Copy the **Application (client) ID**
   - Copy the **Directory (tenant) ID**

### 4.2 Configure API Permissions

1. **Go to API Permissions**
   - In your app registration, click "API permissions"
   - Click "Add a permission"

2. **Add Power BI Permissions**
   - Click "Power BI Service"
   - Select "Delegated permissions"
   - Check the following:
     - `Dataset.ReadWrite.All`
     - `Workspace.Read.All`
   - Click "Add permissions"

3. **Add SQL Database Permissions**
   - Click "Add a permission"
   - Select "Azure SQL Database"
   - Select "Delegated permissions"
   - Check `user_impersonation`
   - Click "Add permissions"

4. **Grant Admin Consent**
   - Click "Grant admin consent for [Your Organization]"
   - Click "Yes" to confirm

### 4.3 Create Client Secret

1. **Go to Certificates & Secrets**
   - Click "Certificates & secrets"
   - Click "New client secret"

2. **Create Secret**
   - **Description**: `Chat with Data Secret`
   - **Expires**: `24 months` (recommended)
   - Click "Add"

3. **Copy Secret Value**
   - **Important**: Copy the secret value immediately (it won't be shown again)

### 4.4 Add App to Workspaces

**Critical Step**: Your Azure app must be added to both Microsoft Fabric and Power BI workspaces with appropriate permissions.

#### Microsoft Fabric Workspace Access

1. **Navigate to Fabric Workspace**
   - Go to [fabric.microsoft.com](https://fabric.microsoft.com)
   - Open your target workspace (where your Lakehouse/Warehouse is located)

2. **Add Service Principal**
   - Click on "Workspace settings" (gear icon)
   - Go to "Access" tab
   - Click "Add people or groups"
   - In the search box, enter your **Application (client) ID**
   - Select your application from the dropdown
   - Choose role: **Member** or **Admin**
     - **Member**: Can read and query data (recommended for most use cases)
     - **Admin**: Full workspace access (use only if needed)
   - Click "Add"

#### Power BI Workspace Access

1. **Navigate to Power BI Service**
   - Go to [powerbi.microsoft.com](https://powerbi.microsoft.com)
   - Open your Power BI Premium workspace

2. **Add Service Principal**
   - Click on "Workspace settings" (three dots menu → Settings)
   - Go to "Access" tab
   - Click "Add people or groups"
   - Enter your **Application (client) ID** in the search box
   - Select your application
   - Choose role: **Member** or **Admin**
     - **Member**: Can access datasets and semantic models (recommended)
     - **Admin**: Full workspace management (use only if needed)
   - Click "Add"

3. **Enable Service Principal Access** (If Required)
   - Go to Power BI Admin Portal
   - Navigate to "Tenant settings"
   - Find "Developer settings" → "Service principals can use Power BI APIs"
   - Enable this setting for your organization or specific security groups
   - Apply changes

#### Verify Workspace Access

**Test Fabric Access:**
```bash
# Use Azure CLI to test access
az rest --method GET \
  --url "https://api.fabric.microsoft.com/v1/workspaces" \
  --headers "Authorization=Bearer $(az account get-access-token --resource https://api.fabric.microsoft.com --query accessToken -o tsv)"
```

**Test Power BI Access:**
```bash
# Test Power BI API access
az rest --method GET \
  --url "https://api.powerbi.com/v1.0/myorg/groups" \
  --headers "Authorization=Bearer $(az account get-access-token --resource https://analysis.windows.net/powerbi/api --query accessToken -o tsv)"
```

### 4.5 Update Backend Environment

Update your backend `.env` file with the Azure details:

```env
# Replace with your actual values
AZURE_TENANT_ID=your-directory-tenant-id-here
AZURE_CLIENT_ID=your-application-client-id-here
AZURE_CLIENT_SECRET=your-client-secret-value-here
```

## 🗄️ Step 5: Configure Data Sources

### 5.1 Microsoft Fabric Setup

1. **Access Fabric Workspace**
   - Go to [fabric.microsoft.com](https://fabric.microsoft.com)
   - Navigate to your workspace
   - Ensure you have a Lakehouse or Warehouse

2. **Get SQL Endpoint**
   - In your Lakehouse/Warehouse, find the "SQL endpoint"
   - Copy the server name (format: `server.database.windows.net`)
   - Note the database name

3. **Test Connection**
   - Start both backend and frontend
   - Go to `http://localhost:3000`
   - Configure authentication with Azure details
   - Try connecting to your Fabric database

### 5.2 Power BI Semantic Model Setup

1. **Access Power BI Service**
   - Go to [powerbi.microsoft.com](https://powerbi.microsoft.com)
   - Navigate to your Premium workspace

2. **Enable XMLA Endpoint**
   - Go to workspace settings
   - Ensure XMLA read-write is enabled
   - Copy the XMLA endpoint URL

3. **Get Dataset Information**
   - Note your dataset/semantic model name
   - Ensure the model has proper permissions

## 🧪 Step 6: Verification and Testing

### 6.1 Test Complete Setup

1. **Start Both Services**
   ```bash
   # Terminal 1 - Backend
   cd backend
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   python main.py

   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

2. **Access Application**
   - Open browser to `http://localhost:3000`
   - You should see the "Chat with Your Data" interface

3. **Configure Authentication**
   - Click on "OAuth2 Configuration"
   - Enter your Azure details
   - Click "Save Configuration"
   - You should see "✅ Authentication configured successfully"

4. **Test Data Source Connection**
   - Select either "SQL Endpoint" or "Power BI Semantic Model"
   - Enter connection details
   - Click "Test Connection"
   - You should see "✅ Connected successfully"

5. **Test AI Chat**
   - Try a simple question like "What tables are available?"
   - You should see the AI thinking process and get a response

### 6.2 Common Verification Steps

**Backend Health Check:**
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy", "claude_available": true}
```

**Frontend Build Test:**
```bash
cd frontend
npm run build
# Should complete without errors
```

**Database Connection Test:**
```bash
# Check backend logs for connection status
# Look for: "✅ Connected to Microsoft Fabric" or similar
```

## 🎉 Step 7: First Usage

### 7.1 Try Sample Questions

**For Microsoft Fabric (SQL):**
- "What tables are in this database?"
- "Show me 5 rows from the largest table"
- "How many records are in each table?"

**For Power BI (DAX):**
- "What measures are available?"
- "Show me the tables in this model"
- "What's the structure of this semantic model?"

### 7.2 Explore Features

1. **Chat Interface**: Ask natural language questions
2. **Schema Explorer**: Browse database/model structure
3. **Data Visualization**: View auto-generated charts
4. **Query Inspector**: See generated SQL/DAX queries
5. **AI Thinking Process**: Watch the AI reasoning

## 🔍 Troubleshooting Installation

### Common Issues and Solutions

**Python Virtual Environment Issues:**
```bash
# If activation doesn't work, try:
python -m pip install virtualenv
virtualenv venv
```

**Node.js Permission Issues:**
```bash
# Use nvm for better Node.js management
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

**Package Installation Failures:**
```bash
# Clear npm cache
npm cache clean --force

# Clear pip cache
pip cache purge

# Try installing with verbose output
npm install --verbose
pip install -r requirements.txt --verbose
```

**Port Conflicts:**
```bash
# Backend running on different port
uvicorn main:app --host 0.0.0.0 --port 8001

# Frontend running on different port
npm run dev -- --port 3001

# Update .env.local accordingly
NEXT_PUBLIC_API_URL=http://localhost:8001
```

**Azure Authentication Issues:**
- Verify tenant ID is correct
- Ensure client secret hasn't expired
- Check API permissions are granted
- Verify redirect URI matches exactly

## 📝 Next Steps

After successful installation:

1. **Customize Configuration**: Adjust settings for your organization
2. **Add Data Sources**: Connect additional databases or models
3. **Test AI Capabilities**: Try complex questions and scenarios
4. **Monitor Performance**: Check logs and optimize as needed
5. **Deploy to Production**: Consider containerization and cloud deployment

## 📞 Installation Support

If you encounter issues:

1. **Check Prerequisites**: Ensure all requirements are met
2. **Review Logs**: Check both backend and frontend console output
3. **Verify Configuration**: Double-check all environment variables
4. **Test Components**: Isolate issues by testing individual components
5. **Open Issue**: Create a GitHub issue with detailed error information

---

**Installation Complete!** 🎉 You're now ready to chat with your data using AI.
