# Shelfy Core POC — Design Spec

**Date:** 2026-04-17  
**Status:** Approved

---

## What We're Building

AI-powered Visual Merchandising OS POC. Three flows: planogram ingestion, AI planogram generation, shelf audit & compliance. Single brand, single category, synthetic data.

Full PRD: `/Users/adnan/Documents/Shelfy_Core_POC_PRD.md`

---

## Repository Structure

```
shelfy/                          # monorepo root
├── apps/
│   ├── backend/                 # FastAPI + Python 3.12 + uv
│   └── frontend/                # Next.js 14 + Tailwind + shadcn/ui
├── docs/superpowers/specs/
├── .env.example
├── .gitignore
└── README.md
```

---

## Backend Architecture

**Runtime:** Python 3.12, uv, FastAPI  
**Deploy:** Render (Docker)

```
apps/backend/
├── app/
│   ├── main.py                  # FastAPI app init, router registration
│   ├── config.py                # Settings from env vars (pydantic-settings)
│   ├── api/
│   │   └── routes/
│   │       ├── ingest.py        # POST /ingest/planogram
│   │       ├── planogram.py     # POST /planogram/generate, GET /planogram/{id}
│   │       └── audit.py         # POST /audit, GET /audit/{id}
│   ├── mcp/
│   │   └── server.py            # MCP server + 6 tool definitions
│   ├── repositories/
│   │   ├── base.py              # Abstract base classes
│   │   ├── brand.py             # Brand + product catalog repo (Supabase)
│   │   ├── planogram.py         # Planogram repo (Supabase)
│   │   └── audit.py             # AuditResult repo (Supabase)
│   ├── services/
│   │   ├── ingestion.py         # PDF parse → structured JSON → embeddings
│   │   ├── generation.py        # MCP agent → store-adapted planogram
│   │   └── audit.py             # Claude Vision → compliance diff
│   └── models/
│       └── schemas.py           # All Pydantic models
├── pyproject.toml
├── Dockerfile
└── .env.example
```

### MCP Tools

```python
get_brand_guidelines(brand_id: str) -> Guidelines
get_product_catalog(brand_id: str, category: str) -> list[Product]
get_store_sales_data(store_format: str, sku_list: list[str]) -> list[SalesData]
get_planogram(planogram_id: str) -> Planogram
search_similar_products(query: str, top_k: int) -> list[Product]
save_generated_planogram(brand_id: str, store_format: str, layout: dict) -> str
```

### Key Dependencies

```
anthropic, fastapi, uvicorn, supabase, pydantic-settings,
pdfplumber, pypdf, openai (embeddings), chromadb, python-multipart
```

---

## Frontend Architecture

**Runtime:** Node.js, Next.js 14 App Router, Tailwind, shadcn/ui  
**Deploy:** Vercel

```
apps/frontend/
├── app/
│   ├── layout.tsx               # Root layout + nav
│   ├── page.tsx                 # Redirect → /ingest
│   ├── ingest/page.tsx          # Drag-drop PDF upload + parsed output preview
│   ├── planogram/page.tsx       # Store format selector + shelf grid + reasoning
│   └── audit/page.tsx           # Shelf photo upload + annotated result + score
├── components/
│   ├── shelf-grid.tsx           # Planogram visual grid (rows × columns)
│   ├── file-upload.tsx          # Reusable drag-drop component
│   ├── audit-overlay.tsx        # Photo with bounding box annotations
│   └── discrepancy-list.tsx     # Prioritized compliance issues
├── lib/
│   └── api.ts                   # Typed API client (fetch wrappers)
└── package.json
```

---

## Data Flow

### Flow 1 — Ingest
```
User uploads PDF → POST /ingest/planogram
  → pdfplumber extracts text
  → Claude Vision extracts layout
  → structured JSON saved to Supabase
  → products embedded → Chroma
  → return parsed planogram preview
```

### Flow 2 — Generate
```
User selects store format → POST /planogram/generate
  → MCP agent starts
  → tools: get_brand_guidelines, get_product_catalog, get_store_sales_data
  → Claude generates layout JSON + rationale per position
  → save_generated_planogram tool saves result
  → return planogram + reasoning
```

### Flow 3 — Audit
```
User uploads shelf photo → POST /audit
  → photo saved to Supabase Storage
  → Claude Vision detects products + positions
  → diff engine compares vs target planogram
  → discrepancies categorized + scored
  → return compliance score + annotated result
```

---

## Supabase Schema

```sql
-- brands, product_catalog, stores, sales_data,
-- planograms, planogram_positions, audit_results, discrepancies
-- Storage buckets: planogram-files, shelf-photos
```

---

## Environment Variables

```
# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# AI
ANTHROPIC_API_KEY=
OPENAI_API_KEY=        # embeddings only

# App
BACKEND_URL=           # for frontend → backend calls
```

---

## Decisions Made

| Decision | Choice | Reason |
|----------|--------|--------|
| Monorepo | Yes | One engineer, shared context |
| Package manager | uv | Fast, modern, lockfile |
| Vector DB | Chroma (local) | Zero infra for POC |
| Storage | Supabase | Postgres + file buckets in one |
| Backend deploy | Render | Simple Docker, free tier |
| Frontend deploy | Vercel | Zero-config Next.js |
| Auth | None | Out of scope for POC |
