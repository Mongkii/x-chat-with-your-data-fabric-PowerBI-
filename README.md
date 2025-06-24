# 💬 Chat with Your Data

An intelligent AI-powered application that lets you chat with your Microsoft Fabric databases and Power BI semantic models using natural language. Built with FastAPI (Python backend) and Next.js (React frontend).

## 🚀 Features

### Core Capabilities
- **Natural Language Queries**: Ask questions in plain English
- **Dual Data Source Support**: Works with both Microsoft Fabric (T-SQL) and Power BI (DAX)
- **AI-Powered Query Generation**: Automatically generates optimized SQL/DAX queries
- **Self-Correcting AI**: Automatically fixes query errors and retries
- **Interactive Chat Interface**: Real-time conversation with your data
- **Data Visualization**: Auto-generates charts and graphs
- **Schema Explorer**: Browse your database/model structure

### AI Intelligence
- **Context-Aware**: Remembers conversation history for follow-up questions
- **Smart Query Optimization**: Generates efficient queries with proper limits and joins
- **Error Recovery**: Analyzes errors and automatically corrects queries
- **Business Logic Understanding**: Interprets business terminology and relationships

### Technical Features
- **OAuth2 Authentication**: Secure authentication with Azure/Microsoft
- **Performance Optimized**: Caching, connection pooling, and smart query limits
- **Real-time Feedback**: Shows AI thinking process and query attempts
- **Export Capabilities**: Download results as CSV/Excel
- **Responsive Design**: Works on desktop and mobile

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend      │    │  Data Sources   │
│   (Next.js)     │◄──►│   (FastAPI)      │◄──►│                 │
│                 │    │                  │    │ • Microsoft     │
│ • Chat UI       │    │ • AI Agents      │    │   Fabric        │
│ • Visualizations│    │ • Query Engine   │    │ • Power BI      │
│ • Schema Explorer│    │ • Auth Service   │    │   Semantic      │
└─────────────────┘    └──────────────────┘    │   Models        │
                                                └─────────────────┘
```

### Backend Architecture
- **Enhanced Multi-Agent Service**: Core AI orchestration
- **Fabric Service**: Microsoft Fabric database connections
- **Semantic Model Service**: Power BI semantic model connections
- **Claude Service**: AI query generation and analysis
- **Auth Service**: OAuth2 authentication management

### Frontend Architecture
- **EnhancedChatInterface**: Main conversational UI
- **Data Visualization**: Intelligent chart generation
- **Schema Explorers**: Database/model structure browsing
- **Connection Management**: Service configuration and testing

## 📋 Prerequisites

### Software Requirements
- **Python 3.8+**
- **Node.js 18+**
- **npm or yarn**

### Microsoft Requirements
- **Azure Active Directory App Registration**
- **Microsoft Fabric Workspace** (for SQL endpoint)
- **Power BI Premium Workspace** (for XMLA endpoint)
- **Appropriate licensing and permissions**

### AI Service
- **Anthropic Claude API Key** (for AI capabilities)

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

Built with ❤️ by [Your Name/Organization]
