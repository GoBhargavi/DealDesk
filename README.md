# DealDesk 🏦

> **Agentic M&A Intelligence Platform for Investment Bankers**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19+-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue.svg)](https://www.typescriptlang.org/)

DealDesk is a comprehensive M&A intelligence platform that combines AI-powered analysis with modern web technologies to streamline deal lifecycle for investment bankers. Built with FastAPI, React, and LangGraph, it provides real-time insights, automated analysis, and collaborative deal management.

## ✨ Features

### 🎯 Deal Pipeline Management
- **Kanban-style board** with drag-and-drop stage transitions
- **Real-time updates** via WebSocket connections
- **Multi-stage tracking** from Origination to Closing
- **Deal analytics** with value metrics and timing insights

### 🤖 AI-Powered Analysis
- **Comparable Transactions**: Automated market analysis with valuation insights
- **DCF Modeling**: AI-assisted financial modeling with sensitivity analysis
- **Pitch Book Generation**: Streamlined creation of pitch materials
- **Document Intelligence**: Automated risk extraction and key term analysis
- **News Intelligence**: Deal-specific market sentiment and relevant news

### 🔧 Phase 2: Advanced AI Configuration
- **Bring Your Own LLM (BYOLLM)**: Support for Anthropic Claude, OpenAI GPT, Google Gemini, Azure OpenAI, and Ollama
- **Deep Search**: Multi-step web research pipeline with Tavily, Perplexity, and Exa AI providers
- **MCP Servers**: Model Context Protocol integration for external data sources (SEC EDGAR, Financial APIs, News, Slack, Custom)
- **Per-Agent Model Overrides**: Configure different LLMs for specific agents (fast models for news, powerful models for analysis)
- **Encrypted API Key Storage**: Secure credential management with Fernet encryption

### 📊 Real-time Intelligence
- **Server-Sent Events (SSE)** for streaming AI responses
- **WebSocket integration** for live collaboration
- **Redis pub/sub** for scalable real-time updates
- **Agent status monitoring** with progress tracking

### 🏗️ Modern Architecture
- **Microservices design** with Docker containerization
- **Async/await** throughout for optimal performance
- **Type-safe** frontend with TypeScript
- **Responsive UI** with TailwindCSS and modern design patterns
- **Dynamic LLM Factory**: Runtime LLM instantiation with Redis caching
- **MCP Registry**: Centralized management of external tool integrations
- **Modular Agent System**: LangGraph orchestration with tool discovery

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ and npm
- Python 3.11+
- Anthropic API key (for AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/dealdesk.git
   cd dealdesk
   ```

2. **Set up the backend**
   ```bash
   cd backend
   cp .env.example .env
   # Add your Anthropic API key to .env
   docker-compose up -d postgres redis
   pip install -r requirements.txt
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Start the services**
   ```bash
   # Terminal 1: Backend API
   cd backend
   uvicorn app.main:app --reload

   # Terminal 2: Celery Worker
   cd backend
   celery -A app.workers.document_worker worker --loglevel=info

   # Terminal 3: Frontend
   cd frontend
   npm run dev
   ```

5. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 🏛️ Architecture

### Backend Stack
- **FastAPI**: Modern, high-performance web framework
- **SQLAlchemy**: Async ORM with PostgreSQL + pgvector
- **Redis**: Pub/sub, caching, and session management
- **Celery**: Distributed task queue for document processing
- **LangGraph**: Multi-agent orchestration framework
- **LLM Factory**: Dynamic LLM instantiation with multi-provider support
- **MCP Registry**: Model Context Protocol integration hub
- **Deep Search**: Multi-step web research pipeline
- **Fernet Encryption**: Secure API key storage and management

### Frontend Stack
- **React 19**: Modern UI framework with concurrent features
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and development server
- **TailwindCSS**: Utility-first CSS framework
- **Zustand**: Lightweight state management
- **React Query**: Server state management and caching
- **Axios**: HTTP client with interceptors
- **Material-UI**: Component library for settings interface

### Infrastructure
- **Docker**: Containerization for consistent environments
- **PostgreSQL**: Primary database with pgvector for embeddings
- **Redis**: In-memory data structure store
- **WebSocket**: Real-time bidirectional communication
- **SSE**: Server-sent events for streaming responses

### Phase 2 Architectural Marvels
- **Dynamic LLM Factory**: Runtime instantiation of any supported LLM provider with Redis caching and per-agent overrides
- **MCP Registry**: Centralized hub for managing external tool integrations with automatic discovery and connection management
- **Deep Search Pipeline**: Multi-step research process with query generation, parallel search, content fetching, and AI synthesis
- **Encrypted Configuration**: Secure storage of sensitive API keys using cryptography.fernet with database encryption at rest
- **Streaming Architecture**: Server-Sent Events for real-time research progress and agent status updates
- **Modular Tool System**: LangChain tool integration with MCP client abstraction for seamless external API access

## 📁 Project Structure

```
dealdesk/
├── backend/
│   ├── app/
│   │   ├── agents/          # AI agents and orchestration
│   │   ├── api/            # API routers
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── workers/        # Celery tasks
│   │   └── main.py         # FastAPI application
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/            # API clients
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom hooks
│   │   ├── pages/          # Page components
│   │   ├── store/          # Zustand stores
│   │   └── types/          # TypeScript types
│   ├── package.json
│   └── vite.config.ts
└── docker-compose.yml
```

## 🧠 AI Agents

DealDesk includes specialized AI agents powered by Anthropic Claude:

### Comps Agent
- Analyzes comparable transactions
- Provides valuation insights
- Generates market benchmarks

### DCF Agent
- Suggests financial modeling assumptions
- Performs sensitivity analysis
- Provides valuation guidance

### News Agent
- Aggregates deal-relevant news
- Analyzes market sentiment
- Extracts key intelligence

### Document Agent
- Processes uploaded documents
- Extracts key terms and risks
- Generates executive summaries

### Orchestrator
- Coordinates multi-agent workflows
- Manages complex analysis pipelines
- Handles pitch book generation

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/dealdesk

# Redis
REDIS_URL=redis://localhost:6379

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-...

# S3 (for document storage)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_BUCKET_NAME=dealdesk-documents
AWS_REGION=us-east-1
```

### Frontend Configuration

Create a `.env.local` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 📊 API Documentation

The API is fully documented with OpenAPI/Swagger:

- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Deals
- `GET /api/v1/deals` - List all deals
- `POST /api/v1/deals` - Create new deal
- `PATCH /api/v1/deals/{id}/stage` - Move deal to new stage

#### AI Analysis
- `POST /api/v1/comps/analyze` - Start comps analysis (SSE)
- `POST /api/v1/dcf/calculate` - Calculate DCF valuation
- `POST /api/v1/pitchbook/generate` - Generate pitch book (SSE)

#### Documents
- `POST /api/v1/documents/upload` - Upload document
- `POST /api/v1/documents/{id}/analyze` - Analyze document (SSE)

## 🧪 Development

### Running Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Code Quality
```bash
# Backend linting
cd backend
black .
ruff check .

# Frontend linting
cd frontend
npm run lint
```

### Database Migrations
```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## 🚀 Deployment

### Docker Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Setup
- **Development**: Use `docker-compose.yml`
- **Production**: Use `docker-compose.prod.yml`
- **Staging**: Configure separate databases and Redis instances

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Style
- **Backend**: Follow PEP 8, use Black for formatting
- **Frontend**: Use ESLint and Prettier configurations
- **Commits**: Follow conventional commit format

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Anthropic** for the Claude AI model
- **LangChain** and **LangGraph** for agent orchestration
- **FastAPI** for the high-performance web framework
- **React** and **Vite** for the modern frontend stack

**Built with ❤️ for the investment banking community**

