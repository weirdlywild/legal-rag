# Legal AI RAG POC

A Proof of Concept Legal AI Assistant demonstrating high-quality legal reasoning with grounded answers, citations, and source attribution.

## Architecture

```
[Vercel - Free Tier]
  └── Next.js Frontend
        └── OpenAPI-generated TypeScript client

[Render - Free Tier]
  └── FastAPI Backend
        ├── sentence-transformers (all-MiniLM-L6-v2)
        ├── OpenAI GPT-4o (answer generation ONLY)
        └── pymupdf4llm (PDF parsing)

[Qdrant Cloud - Free Tier]
  └── Managed vector database (1GB free)
```

## Features

- Upload legal PDF documents (max 2 docs, 80 pages each)
- Ask natural language questions about documents
- Receive grounded answers with:
  - Clause/section-level citations
  - Page numbers
  - Quoted source text
- Strict hallucination prevention
- Cost tracking and daily limits

## Quick Start

### Prerequisites

1. **OpenAI API Key**: Sign up at https://platform.openai.com
2. **Qdrant Cloud Account**: Sign up at https://cloud.qdrant.io (free tier)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env with your API keys

# Run development server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file and configure
cp .env.example .env.local
# Edit .env.local with your API URL and key

# Run development server
npm run dev
```

## Environment Variables

### Backend (.env)

```
ENVIRONMENT=development
API_KEY=your-secure-api-key
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-key
CORS_ORIGINS=["http://localhost:3000"]
```

### Frontend (.env.local)

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_API_KEY=your-secure-api-key
```

## Deployment

### Backend on Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set the following:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables in Render dashboard

### Frontend on Vercel

1. Import your GitHub repository on Vercel
2. Set the following:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Next.js
3. Add environment variables:
   - `NEXT_PUBLIC_API_URL`: Your Render backend URL
   - `NEXT_PUBLIC_API_KEY`: Your API key

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/health | Health check |
| GET | /api/v1/health/ready | Readiness check |
| GET | /api/v1/documents | List documents |
| POST | /api/v1/documents | Upload PDF |
| GET | /api/v1/documents/{id} | Document details |
| DELETE | /api/v1/documents/{id} | Delete document |
| POST | /api/v1/query | Ask question |
| GET | /api/v1/system/info | System limits |
| GET | /api/v1/system/usage | Usage stats |

## Cost Model

- **OpenAI GPT-4o**: ~$0.01-0.02 per query
- **Daily safeguards**: 100 queries max, $1.00 max
- **Qdrant Cloud**: Free tier (1GB)
- **Render/Vercel**: Free tier

## Known Limitations

- **Cold starts**: ~30s delay after 15min idle on Render
- **512MB RAM**: Limits model choice on Render free tier
- **Single API key**: Basic auth, no user-level multi-tenancy
- **Qdrant Cloud 1GB**: Sufficient for POC (1-2 docs)

## Disclaimer

This is a Proof of Concept for demonstration purposes only. Answers are AI-generated and should be verified against source documents. This is not legal advice. Always consult qualified legal counsel for legal matters.

## License

MIT
