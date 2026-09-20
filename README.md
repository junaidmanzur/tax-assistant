# AI Tax Assistant

An AI-powered assistant for calculating Australian individual income tax. Built with a FastAPI + LangChain backend and a React frontend, with both a chat interface and a form-based calculator.

## Features

- Progressive income tax calculation using versioned tax rules (`packages/tax_rules/`)
- Medicare levy and Medicare levy surcharge
- Streaming chat interface backed by a LangChain ReAct agent (GPT-4o-mini)
- Optional ATO knowledge base search (Qdrant)

## Project Structure

```
packages/
  shared_types/   Shared request/response schemas
  tax_rules/      JSON tax rules by year
  tax_engine/     Pure tax calculation functions
services/
  agent/          LangChain agent and tools
  api_gateway/    FastAPI app
apps/
  web/            React + Vite frontend
infra/
  docker/         Dockerfiles and docker-compose
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ and pnpm
- An OpenAI API key

### Backend

```bash
pip install -r requirements.txt
cp env.example .env   # add your OPENAI_API_KEY
PYTHONPATH=packages:services uvicorn services.api_gateway.main:app --reload --host 0.0.0.0 --port 8000
```

Set `ENABLE_KNOWLEDGE_BASE=true` in `.env` to enable ATO knowledge search (requires Qdrant).

### Frontend

```bash
cd apps/web
pnpm install
echo "VITE_API_BASE=http://localhost:8000" > .env.local
pnpm dev
```

The app runs at http://localhost:5173.

### Docker

```bash
docker-compose -f infra/docker/docker-compose.yml up --build
```

## API

| Method | Endpoint           | Description                          |
| ------ | ------------------ | ------------------------------------ |
| POST   | `/api/chat/stream` | Streaming chat with the tax agent    |

Interactive docs are available at http://localhost:8000/docs.

## Deployment

A `render.yaml` is included for deploying the combined frontend and backend to [Render](https://render.com). Set `OPENAI_API_KEY` in the Render dashboard.

## Disclaimer

This tool is for informational purposes only and does not constitute tax advice.
