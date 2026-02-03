---
title: Legal AI RAG API
emoji: ⚖️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# Legal AI RAG API

A FastAPI backend for legal document Q&A with RAG (Retrieval-Augmented Generation).

## Features

- PDF document upload and processing
- Vector search using Qdrant Cloud
- Answer generation with GPT-4o-mini
- Source citations and confidence scores

## Environment Variables

Set these as secrets in your Hugging Face Space:

- `API_KEY` - API key for authentication
- `APP_PASSWORD` - Password for frontend access
- `OPENAI_API_KEY` - OpenAI API key
- `QDRANT_URL` - Qdrant Cloud URL
- `QDRANT_API_KEY` - Qdrant Cloud API key
- `CORS_ORIGINS` - Allowed CORS origins (JSON array)

## API Documentation

Once deployed, visit `/api/v1/docs` for the interactive API documentation.
