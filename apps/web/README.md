# AI Tax Assistant — Frontend (Vite + React + TS + Tailwind)

This repo implements your mockup (chat + form) and **hooks the form up to a backend API**.

## Quick start

```bash
# 1) scaffold (or just use these files directly)
pnpm create vite ai-tax-assistant-frontend --template react-ts
cd ai-tax-assistant-frontend

# 2) install deps
pnpm i
pnpm add -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# 3) replace the generated configs and src with this project
# 4) run
pnpm dev
```

## API hookup

- The form calls `POST {API_BASE}/api/calc`.
- Configure the base with **`VITE_API_BASE`** (e.g. `http://localhost:8000`).
- During `pnpm dev` we also proxy `/api` to `VITE_PROXY_TARGET` (defaults to `http://localhost:8000`).

### Request
```json
{
  "income": 85000,
  "hasPrivateHealth": true,
  "taxYear": "2024–25"
}
```

### Response
```json
{
  "baseTax": 21592,
  "medicareLevy": 1700,
  "totalTax": 23292
}
```

> Adjust to match your backend exactly. Types live in `src/types/tax.ts`.

## Env
Create `.env.local`:
```
VITE_API_BASE=http://localhost:8000
VITE_PROXY_TARGET=http://localhost:8000
```

## Files of note
- `src/components/form/FormPanel.tsx` — calls `/api/calc`, handles loading/errors
- `src/components/chat/*` — static demo chat (wire to your chat backend later)
- `vite.config.ts` — dev proxy for `/api`

## License
MVP scaffold for internal use.