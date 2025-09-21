# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI Tax Assistant MVP with a monorepo-style architecture consisting of a FastAPI backend with LangChain agent integration and a React frontend. The system calculates Australian individual income tax using configurable tax rules and provides both a chat interface and form-based interaction.

## Development Commands

### Backend (Python)
- **Install dependencies**: `pip install -r requirements.txt`
- **Run API server**: `PYTHONPATH=packages:services uvicorn services.api_gateway.main:app --reload --host 0.0.0.0 --port 8000`
- **Environment**: Requires `OPENAI_API_KEY` in `.env` file

### Frontend (React + Vite)
- **Install dependencies**: `cd apps/web && pnpm install`
- **Development server**: `cd apps/web && pnpm dev` (runs on port 5173 with API proxy)
- **Build**: `cd apps/web && pnpm build` (TypeScript compilation + Vite build)
- **Preview**: `cd apps/web && pnpm preview`
- **Environment**: Create `apps/web/.env.local` with `VITE_API_BASE=http://localhost:8000`

### Docker (Production)
- **Build and run**: `docker-compose -f infra/docker/docker-compose.yml up --build`
- **Run detached**: `docker-compose -f infra/docker/docker-compose.yml up -d --build`
- **Stop services**: `docker-compose -f infra/docker/docker-compose.yml down`

## Architecture

The project follows a monorepo structure with clear separation of concerns:

```
tax-assistant/
├── packages/                    # Shared packages
│   ├── shared_types/           # Zod/Pydantic/TypeScript schemas
│   ├── tax_rules/              # JSON tax rules, versioned by year
│   └── tax_engine/             # Pure tax calculation functions
├── services/                    # Backend services
│   ├── agent/                  # LLM agent orchestration
│   └── api_gateway/            # REST API endpoints
├── apps/                       # Frontend applications
│   └── web/                    # React web application
└── infra/                      # Infrastructure configuration
    └── docker/                 # Docker containers and compose
```

### Packages (Shared)
- **`packages/shared_types/`**: Common type definitions and schemas for requests/responses
- **`packages/tax_rules/`**: JSON configuration files containing tax rules by year
- **`packages/tax_engine/`**: Pure, deterministic tax calculation functions (unit-testable)

### Services (Backend)
- **`services/agent/`**: LangChain ReAct agent with GPT-4o-mini, tool definitions, and orchestration
- **`services/api_gateway/`**: FastAPI app with `/chat` and `/chat/stream` endpoints

### Apps (Frontend)
- **`apps/web/src/App.tsx`**: Main layout with chat and form panels
- **`apps/web/src/components/chat/`**: Chat interface connected to streaming backend
- **`apps/web/src/components/form/`**: Tax calculation form
- **`apps/web/src/types/`**: TypeScript types (mirrors shared-types)
- **Path aliases**: `@components`, `@types`, `@lib` configured in `vite.config.ts`

### Infrastructure
- **`infra/docker/`**: Docker containers for api-gateway and web services
- **Docker Compose**: Orchestrates both services for local development

### Key Integration Points
- Agent service uses tax-engine package for calculations
- API gateway imports agent service and shared types
- Frontend consumes API via REST endpoints and Server-Sent Events
- Tax rules are loaded dynamically from packages/tax-rules
- All services can be run individually or via Docker Compose

### Tax Calculation Logic
- Progressive marginal tax rates from `packages/tax_rules/tax_rules_2024.json`
- Medicare levy (2% of income)
- Medicare levy surcharge (MLS) based on income tiers and private health status
- Returns: base tax, Medicare levy, MLS, total tax, and take-home pay

## Important Notes
- The system is designed for Australian tax calculations only
- Tax rules are year-specific and loaded from JSON files in packages/tax_rules
- Frontend uses Tailwind CSS for styling
- Backend uses LangChain for AI agent functionality with OpenAI GPT models
- All services can run independently or via Docker for production deployment
- PYTHONPATH must include packages/ directory when running services locally

## Git Commit Rules

-  Commit messages should be clean and professional without any AI attribution or co-authorship notices
-  Focus commit messages on what changed and why, not on who or what created the code

## Proposed Changes Rules

- Always show sketch for frontend UI/UX changes
- Always suggest responsive UI changes
- Show flow diagrams for proposed backend or architecture changes
