# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI Tax Assistant MVP consisting of a FastAPI backend with LangChain agent integration and a React frontend. The system calculates Australian individual income tax using configurable tax rules and provides both a chat interface and form-based interaction.

## Development Commands

### Backend (Python)
- **Install dependencies**: `pip install -r requirements.txt`
- **Run API server**: `uvicorn api.main:app --reload --host 0.0.0.0 --port 8000`
- **Environment**: Requires `OPENAI_API_KEY` in `.env` file

### Frontend (React + Vite)
- **Install dependencies**: `pnpm install`
- **Development server**: `pnpm dev` (runs on port 5173 with API proxy)
- **Build**: `pnpm build` (TypeScript compilation + Vite build)
- **Preview**: `pnpm preview`
- **Environment**: Create `.env.local` with `VITE_API_BASE=http://localhost:8000`

## Architecture

### Backend Structure
- **`api/main.py`**: FastAPI app with `/chat` and `/chat/stream` endpoints
- **`agent/agent_runner.py`**: LangChain ReAct agent using GPT-4o-mini with memory
- **`agent/tools/tax_tool.py`**: Core tax calculation tool with Australian tax logic
- **`rules/tax_rules_2024.json`**: Configurable tax rules (marginal rates, Medicare levy, MLS)

### Frontend Structure
- **`src/App.tsx`**: Main layout with chat and form panels
- **`src/components/chat/`**: Static demo chat interface (not yet connected to backend)
- **`src/components/form/FormPanel.tsx`**: Tax calculation form that calls `/api/calc`
- **`src/types/tax.ts`**: TypeScript types for tax calculations
- **Path aliases**: `@components`, `@types`, `@lib` configured in `vite.config.ts`

### Key Integration Points
- Frontend form calls backend via `/api/calc` endpoint (proxied during dev)
- Agent uses `calculate_tax` tool to process tax calculations
- Tax rules are loaded dynamically from JSON files in `rules/` directory
- Chat interface is currently static but structured for future backend integration

### Tax Calculation Logic
- Progressive marginal tax rates from `rules/tax_rules_2024.json`
- Medicare levy (2% of income)
- Medicare levy surcharge (MLS) based on income tiers and private health status
- Returns: base tax, Medicare levy, MLS, total tax, and take-home pay

## Important Notes
- The system is designed for Australian tax calculations only
- Tax rules are year-specific and loaded from JSON files
- Frontend uses Tailwind CSS for styling
- Backend uses LangChain for AI agent functionality with OpenAI GPT models
- Development setup requires both frontend and backend running simultaneously