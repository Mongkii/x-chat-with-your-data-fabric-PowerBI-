# 💬 Chat with Your Data

An intelligent AI-powered application that lets you chat with your Microsoft Fabric databases and Power BI semantic models using natural language. Built with FastAPI (Python backend) and Next.js (React frontend).

![Chat with Data Demo](Chat With Your Data.png)

## 🚀 What This App Does

- **Ask Questions in Plain English**: "Show me top 10 customers by revenue" or "What are sales trends this month?"
- **AI Generates SQL/DAX**: Automatically creates optimized queries for your data
- **Self-Correcting**: If a query fails, AI analyzes the error and fixes it automatically
- **Real-Time Insights**: Get instant answers with beautiful charts and tables
- **Two Data Sources**: Works with Microsoft Fabric (SQL) and Power BI (DAX)

## 🎯 Quick Demo

1. **Connect** to your Microsoft Fabric or Power BI
2. **Ask** "What tables do I have?"
3. **Watch** the AI generate and execute queries
4. **Get** instant results with visualizations

## 📋 What You Need Before Starting

### Required Software
- **Python 3.8 or higher** ([Download here](https://python.org))
- **Node.js 18 or higher** ([Download here](https://nodejs.org))
- **Git** ([Download here](https://git-scm.com))

### Required Accounts & Services
- **Azure account** with admin permissions
- **Microsoft Fabric workspace** (for SQL data) OR **Power BI Premium workspace** (for semantic models)
- **Anthropic Claude API key** ([Get one here](https://console.anthropic.com))

## 🚀 Easy Setup (5 Minutes)

### Step 1: Download the Code
```bash
git clone https://github.com/yourusername/chat-with-data.git
cd chat-with-data
```

### Step 2: Run the Setup Script
```bash
# Make the script executable (Mac/Linux)
chmod +x setup.sh

# Run the automated setup
./setup.sh
```

**Windows users:** Run these commands instead:
```cmd
# Copy environment files
copy backend\.env.example backend\.env
copy frontend\.env.local.example frontend\.env.local

# Setup backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd ..

# Setup frontend
cd frontend
npm install
cd ..
```

## 🔑 Step 3: Get Your API Keys

### Get Claude AI API Key
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up for an account
3. Go to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-ant-api03-`)

### Setup Azure App Registration
1. Go to [portal.azure.com](https://portal.azure.com)
2. Search for "App registrations" → Click "New registration"
3. Fill in:
   - **Name**: `Chat with Data App`
   - **Account types**: `Single tenant`
   - **Redirect URI**: `Web` → `http://localhost:3000`
4. Click "Register"
5. **Copy these 3 values**:
   - **Application (client) ID**
   - **Directory (tenant) ID**
   - **Client Secret** (go to "Certificates & secrets" → "New client secret")

### Add API Permissions
1. In your app registration, go to "API permissions"
2. Click "Add a permission"
3. Add these permissions:
   - **Power BI Service** → `Dataset.ReadWrite.All`, `Workspace.Read.All`
   - **Azure SQL Database** → `user_impersonation`
4. Click "Grant admin consent"

## ⚙️ Step 4: Configure Environment

### Edit Backend Configuration
Open `backend/.env` in any text editor and fill in:
```env
# Your Claude AI API key
ANTHROPIC_API_KEY=sk-ant-api03-your-api-key-here

# Your Azure app registration details
AZURE_TENANT_ID=your-tenant-id-here
AZURE_CLIENT_ID=your-client-id-here
AZURE_CLIENT_SECRET=your-client-secret-here

# Leave these as they are
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
```

### Edit Frontend Configuration
The `frontend/.env.local` file should already be correct:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🏢 Step 5: Add App to Your Workspaces

### For Microsoft Fabric
1. Go to [fabric.microsoft.com](https://fabric.microsoft.com)
2. Open your workspace
3. Click "Workspace settings" (gear icon)
4. Go to "Access" → "Add people or groups"
5. Enter your **Application (client) ID**
6. Select **Member** role
7. Click "Add"

### For Power BI
1. Go to [powerbi.microsoft.com](https://powerbi.microsoft.com)
2. Open your Premium workspace
3. Click workspace menu (three dots) → "Settings"
4. Go to "Access" → "Add people or groups"
5. Enter your **Application (client) ID**
6. Select **Member** role
7. Click "Add"

## 🎉 Step 6: Start the Application

### Open Two Terminal Windows

**Terminal 1 - Start Backend:**
```bash
cd backend

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Start backend server
python main.py
```
You should see: `✅ Chat with Data API ready to accept requests`

**Terminal 2 - Start Frontend:**
```bash
cd frontend

# Start frontend
npm run dev
```
You should see: `▲ Next.js ready on http://localhost:3000`

## 🌐 Step 7: Test the Application

1. **Open your browser** and go to `http://localhost:3000`

2. **Configure Authentication**:
   - You'll see the main page
   - The authentication should show as "✅ Configured" (if not, click "Configure OAuth2" and enter your Azure details)

3. **Connect to Your Data**:
   - Choose either "SQL Endpoint" (for Fabric) or "Power BI Semantic Model"
   - For **Fabric**: Enter your workspace SQL endpoint URL and database name
   - For **Power BI**: Enter your XMLA endpoint URL and dataset name
   - Click "Test Connection" - you should see "✅ Connected successfully"

4. **Start Chatting**:
   - Try asking: "What tables are available?"
   - Try asking: "Show me 5 rows from the largest table"
   - Watch the AI generate queries and return results!

## 💡 Example Questions to Try

### For Microsoft Fabric (SQL):
- "What tables do I have in this database?"
- "Show me the top 10 customers by revenue"
- "What are the sales trends by month this year?"
- "How many orders were placed last week?"

### For Power BI (DAX):
- "What measures are available in this model?"
- "Show me sales by product category"
- "Compare this year's revenue to last year"
- "What's the total revenue for each region?"

## 🔍 Troubleshooting

### Backend Won't Start
- **Error**: `ModuleNotFoundError`
  - **Fix**: Make sure virtual environment is activated and run `pip install -r requirements.txt`

- **Error**: `Claude is not available`
  - **Fix**: Check your `ANTHROPIC_API_KEY` in `backend/.env`

### Frontend Won't Start
- **Error**: `Cannot find module`
  - **Fix**: Run `npm install` in the frontend directory

### Authentication Issues
- **Error**: "Authentication not configured"
  - **Fix**: Check your Azure credentials in `backend/.env`
  - **Fix**: Make sure you've added the app to your workspaces

### Connection Issues
- **Error**: "Connection failed"
  - **Fix**: Verify your workspace URLs are correct
  - **Fix**: Make sure the app has Member permissions in the workspace
  - **Fix**: Check if your workspace is Premium (required for Power BI XMLA)

## 📱 Application Features

### Chat Interface
- Real-time conversation with your data
- Shows AI thinking process
- Displays query attempts and corrections
- Conversation history for follow-up questions

### Data Visualization
- Auto-generated charts based on your questions
- Interactive data tables
- Export capabilities for results

### Schema Explorer
- Browse your database/model structure
- View table relationships
- Explore available measures and columns

## 🛠️ Advanced Configuration

### Performance Settings
Edit `backend/.env` to adjust:
```env
MAX_QUERY_ROWS=1000        # Maximum rows returned
QUERY_TIMEOUT=30          # Query timeout in seconds
CACHE_TTL=3600           # Cache duration in seconds
```

### Security Settings
For production deployment, generate a strong secret key:
```env
SECRET_KEY=your-very-strong-secret-key-here
```

## 📚 Additional Resources

- **API Documentation**: Visit `http://localhost:8000/docs` when backend is running
- **Detailed Setup Guide**: See [INSTALLATION.md](INSTALLATION.md)
- **Architecture Overview**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Deployment Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)

## 🤝 Getting Help

If you encounter issues:

1. **Check the troubleshooting section above**
2. **Review the logs** in your terminal windows
3. **Verify your configuration** files have the correct values
4. **Test your Azure app permissions** in the Azure portal
5. **Open an issue** on GitHub with error details

## 🎯 What's Next?

Once you have the basic setup working:

1. **Explore Advanced Features**: Try complex queries and follow-up questions
2. **Connect Multiple Data Sources**: Set up both Fabric and Power BI connections
3. **Customize the Interface**: Modify the React components to fit your needs
4. **Deploy to Production**: Follow the deployment guide for cloud hosting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ using Anthropic Claude, Microsoft Fabric, Power BI, FastAPI, and Next.js**

**⭐ If this project helps you, please give it a star on GitHub!**

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/chat-with-data.git
cd chat-with-data
```

### 2. Automated Setup (Recommended)
```bash
# Run the setup script
chmod +x setup.sh
./setup.sh
```

### 3. Manual Setup (Alternative)

**Backend Setup:**
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your configuration (see Configuration section)

# Start backend
python main.py
```

**Frontend Setup:**
```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local
# Edit .env.local with your configuration

# Start frontend
npm run dev
```

### 4. Access Application
- Open browser to `http://localhost:3000`
- Configure authentication
- Connect to your data source
- Start chatting with your data!

## ⚙️ Configuration

### Backend Environment (.env)
```env
# AI Service
ANTHROPIC_API_KEY=your_claude_api_key_here

# Azure Authentication
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret

# Optional: Logging
LOG_LEVEL=INFO
```

### Frontend Environment (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Azure App Registration Setup
1. Go to Azure Portal → App Registrations
2. Create new registration
3. Configure API permissions:
   - Power BI Service: `Dataset.ReadWrite.All`
   - SQL Database: `user_impersonation`
4. Generate client secret
5. Note down Tenant ID, Client ID, and Client Secret

## 📊 Supported Data Sources

### Microsoft Fabric
- **SQL Endpoints**: Lakehouse and Warehouse SQL endpoints
- **Authentication**: Azure AD OAuth2
- **Query Language**: T-SQL
- **Features**: Full schema discovery, table relationships, query optimization

### Power BI Semantic Models
- **XMLA Endpoints**: Premium workspace semantic models
- **Authentication**: Azure AD OAuth2
- **Query Language**: DAX
- **Features**: Measure discovery, table relationships, model metadata

## 🤖 AI Capabilities

### Query Generation
- Converts natural language to SQL/DAX
- Understands business terminology
- Applies proper query optimization
- Handles complex joins and aggregations

### Self-Correction
- Analyzes query execution errors
- Automatically fixes syntax issues
- Retries with corrected queries
- Learns from failed attempts

### Context Awareness
- Remembers conversation history
- Handles follow-up questions
- Maintains query context
- Suggests related questions

## 🎯 Usage Examples

### Sample Questions

**For Microsoft Fabric (SQL):**
- "Show me the top 10 customers by revenue"
- "What are the sales trends by month this year?"
- "Compare product performance across regions"
- "Find customers who haven't ordered in 90 days"

**For Power BI (DAX):**
- "What are our key performance measures?"
- "Show sales by product category"
- "Compare this year's revenue to last year"
- "What's the relationship between sales and customer satisfaction?"

### Advanced Features
- **Follow-up Questions**: "What about the previous month?"
- **Filters**: "Show only products with revenue > $100K"
- **Comparisons**: "How does this compare to last year?"
- **Drill-downs**: "Break that down by region"

## 🔧 Development

### Project Structure
```
chat-with-data/
├── backend/
│   ├── app/
│   │   ├── auth_service.py
│   │   ├── claude_service.py
│   │   ├── enhanced_multi_agent_service.py
│   │   ├── fabric_service.py
│   │   └── semantic_model_service.py
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── components/
│   │   │   ├── EnhancedChatInterface.tsx
│   │   │   ├── FabricConnection.tsx
│   │   │   └── PowerBIMCPConnection.tsx
│   │   └── page.tsx
│   └── package.json
└── README.md
```

### Key Components

**Backend Services:**
- `enhanced_multi_agent_service.py`: Core AI orchestration and query generation
- `fabric_service.py`: Microsoft Fabric database connections and operations
- `semantic_model_service.py`: Power BI semantic model connections and DAX execution
- `claude_service.py`: AI service integration and prompt management
- `auth_service.py`: OAuth2 authentication and token management

**Frontend Components:**
- `EnhancedChatInterface.tsx`: Main chat interface with AI thinking process
- `FabricConnection.tsx`: Microsoft Fabric connection configuration
- `PowerBIMCPConnection.tsx`: Power BI semantic model connection setup
- `SchemaExplorer.tsx`: Database/model structure browser

### API Endpoints

**Core Endpoints:**
- `POST /api/chat/unified`: Main chat endpoint for natural language queries
- `GET /api/connection/status`: Check connection status
- `POST /api/fabric/connect`: Connect to Microsoft Fabric
- `POST /api/powerbi/connect`: Connect to Power BI semantic model

**Authentication:**
- `POST /api/auth/configure`: Configure OAuth2 settings
- `GET /api/auth/status`: Check authentication status

## 🐛 Troubleshooting

### Common Issues

**"Claude is not available"**
- Check `ANTHROPIC_API_KEY` in backend `.env`
- Verify API key is valid and has sufficient credits

**"Authentication not configured"**
- Ensure Azure app registration is complete
- Check tenant ID, client ID, and client secret
- Verify API permissions are granted

**"Connection failed"**
- Verify data source URLs and credentials
- Check network connectivity
- Ensure proper licenses for Fabric/Power BI Premium

**"Query generation failed"**
- Check if schema was discovered correctly
- Verify AI service is responding
- Review error logs for specific issues

### Debug Mode
Enable detailed logging by setting `LOG_LEVEL=DEBUG` in backend `.env`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Anthropic Claude**: AI-powered query generation
- **Microsoft**: Fabric and Power BI platform support
- **FastAPI**: High-performance backend framework
- **Next.js**: React-based frontend framework

## 📞 Support

For support and questions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review Azure and Microsoft Fabric documentation

---

Built with ❤️ by Sulaiman Ahmed
