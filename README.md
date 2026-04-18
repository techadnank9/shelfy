# Shelfy — Visual Merchandising OS

AI-powered planogram generation and shelf audit POC.

## Structure

```
apps/
  backend/   FastAPI + Python 3.12 + uv → Render
  frontend/  Next.js 14 + Tailwind + shadcn/ui → Vercel
```

## Quick Start

### Backend
```bash
cd apps/backend
cp .env.example .env   # fill in real keys
uv sync --extra dev
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd apps/frontend
echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:8000" > .env.local
npm install
npm run dev
```

## Three Flows
1. **Ingest** — upload planogram PDF → Claude extracts products + brand rules
2. **Generate** — select store format → Claude tool_use agent builds shelf layout
3. **Audit** — upload shelf photo → Claude Vision checks compliance vs planogram
