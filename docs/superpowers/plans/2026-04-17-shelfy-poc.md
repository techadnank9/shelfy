# Shelfy Core POC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working POC with three flows — planogram ingestion, AI generation, and shelf audit — deployable to Render (backend) and Vercel (frontend).

**Architecture:** FastAPI backend with Supabase (Postgres + Storage), Chroma for local vector search, and Claude for all AI tasks (document parsing, planogram generation via tool_use, shelf vision audit). Next.js 14 frontend with three views. Repository pattern throughout so Supabase swaps out without touching service logic.

**Tech Stack:** Python 3.12 + uv + FastAPI + Supabase + Chroma + Anthropic SDK + OpenAI embeddings / Next.js 14 + Tailwind + shadcn/ui + TanStack Query

---

## File Map

```
shelfy/
├── .gitignore
├── .env.example
├── README.md
├── apps/
│   ├── backend/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── .env.example
│   │   ├── app/
│   │   │   ├── main.py                        # FastAPI app, lifespan, routers
│   │   │   ├── config.py                      # pydantic-settings from env
│   │   │   ├── deps.py                        # FastAPI dependency injectors
│   │   │   ├── models/
│   │   │   │   └── schemas.py                 # All Pydantic models
│   │   │   ├── repositories/
│   │   │   │   ├── base.py                    # Abstract base classes
│   │   │   │   ├── brand.py                   # SupabaseBrandRepository
│   │   │   │   ├── planogram.py               # SupabasePlanogramRepository
│   │   │   │   └── audit.py                   # SupabaseAuditRepository
│   │   │   ├── services/
│   │   │   │   ├── ingestion.py               # PDF parse → structured JSON → embeddings
│   │   │   │   ├── generation.py              # Claude tool_use agentic loop → planogram
│   │   │   │   ├── audit.py                   # Claude Vision → compliance diff
│   │   │   │   └── embeddings.py              # OpenAI embed + Chroma CRUD
│   │   │   └── api/
│   │   │       └── routes/
│   │   │           ├── ingest.py              # POST /ingest/planogram
│   │   │           ├── planogram.py           # POST /planogram/generate, GET /planogram/{id}
│   │   │           └── audit.py               # POST /audit, GET /audit/{id}
│   │   └── tests/
│   │       ├── conftest.py                    # Fixtures: mock supabase, mock anthropic
│   │       ├── test_ingestion.py
│   │       ├── test_generation.py
│   │       └── test_audit.py
│   └── frontend/
│       ├── package.json
│       ├── next.config.ts
│       ├── tailwind.config.ts
│       ├── tsconfig.json
│       ├── components.json
│       ├── app/
│       │   ├── layout.tsx                     # Root layout + nav
│       │   ├── page.tsx                       # Redirect → /ingest
│       │   ├── ingest/page.tsx
│       │   ├── planogram/page.tsx
│       │   └── audit/page.tsx
│       ├── components/
│       │   ├── nav.tsx
│       │   ├── file-upload.tsx                # Reusable drag-drop
│       │   ├── shelf-grid.tsx                 # Planogram visual grid
│       │   ├── audit-overlay.tsx              # Photo + bounding boxes
│       │   └── discrepancy-list.tsx           # Sorted compliance issues
│       └── lib/
│           └── api.ts                         # Typed fetch wrappers
└── docs/superpowers/
    ├── specs/2026-04-17-shelfy-poc-design.md
    └── plans/2026-04-17-shelfy-poc.md
```

---

## Task 1: Monorepo scaffold + git init

**Files:**
- Create: `shelfy/.gitignore`
- Create: `shelfy/.env.example`
- Create: `shelfy/README.md`

- [ ] **Step 1: Create directory structure**

```bash
cd /Users/adnan/Documents/shelfy
mkdir -p apps/backend/app/models \
         apps/backend/app/repositories \
         apps/backend/app/services \
         apps/backend/app/api/routes \
         apps/backend/tests \
         apps/frontend
```

- [ ] **Step 2: Create root .gitignore**

```
# Python
__pycache__/
*.py[cod]
.venv/
.env
*.egg-info/
dist/
.pytest_cache/
.chroma/

# Node
node_modules/
.next/
.vercel/

# Misc
.DS_Store
*.log
```

Save to `shelfy/.gitignore`.

- [ ] **Step 3: Create root .env.example**

```
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# AI
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# App
BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

Save to `shelfy/.env.example`.

- [ ] **Step 4: Git init + first commit**

```bash
cd /Users/adnan/Documents/shelfy
git init
git add .
git commit -m "chore: monorepo scaffold"
```

---

## Task 2: Backend Python project setup

**Files:**
- Create: `apps/backend/pyproject.toml`
- Create: `apps/backend/app/__init__.py`
- Create: `apps/backend/app/config.py`
- Create: `apps/backend/app/deps.py`
- Create: `apps/backend/tests/conftest.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "shelfy-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "anthropic>=0.40.0",
    "openai>=1.55.0",
    "supabase>=2.10.0",
    "pydantic-settings>=2.6.0",
    "pdfplumber>=0.11.4",
    "pypdf>=5.1.0",
    "chromadb>=0.5.20",
    "python-multipart>=0.0.18",
    "httpx>=0.28.0",
    "Pillow>=11.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-mock>=3.14.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

Save to `apps/backend/pyproject.toml`.

- [ ] **Step 2: Install dependencies**

```bash
cd /Users/adnan/Documents/shelfy/apps/backend
uv sync --extra dev
```

Expected: lock file created, `.venv/` populated.

- [ ] **Step 3: Create config.py**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    anthropic_api_key: str
    openai_api_key: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
```

Save to `apps/backend/app/config.py`.

- [ ] **Step 4: Create deps.py**

```python
from functools import lru_cache
from supabase import AsyncClient, create_async_client
from app.config import settings


@lru_cache
def get_settings():
    return settings


async def get_supabase() -> AsyncClient:
    return await create_async_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )
```

Save to `apps/backend/app/deps.py`.

- [ ] **Step 5: Create tests/conftest.py**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    client.table = MagicMock(return_value=client)
    client.select = MagicMock(return_value=client)
    client.insert = MagicMock(return_value=client)
    client.eq = MagicMock(return_value=client)
    client.order = MagicMock(return_value=client)
    client.limit = MagicMock(return_value=client)
    client.execute = AsyncMock(return_value=MagicMock(data=[]))
    return client


@pytest.fixture
def mock_anthropic(mocker):
    return mocker.patch("anthropic.AsyncAnthropic")


@pytest.fixture
def mock_openai(mocker):
    return mocker.patch("openai.AsyncOpenAI")
```

Save to `apps/backend/tests/conftest.py`.

- [ ] **Step 6: Create empty __init__.py files**

```bash
touch apps/backend/app/__init__.py \
      apps/backend/app/models/__init__.py \
      apps/backend/app/repositories/__init__.py \
      apps/backend/app/services/__init__.py \
      apps/backend/app/api/__init__.py \
      apps/backend/app/api/routes/__init__.py \
      apps/backend/tests/__init__.py
```

- [ ] **Step 7: Commit**

```bash
cd /Users/adnan/Documents/shelfy
git add apps/backend/
git commit -m "feat: backend python project setup"
```

---

## Task 3: Pydantic schemas

**Files:**
- Create: `apps/backend/app/models/schemas.py`

- [ ] **Step 1: Write schemas**

```python
from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class StoreFormat(str, Enum):
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"


class DiscrepancyType(str, Enum):
    MISSING = "MISSING"
    WRONG_POSITION = "WRONG_POSITION"
    WRONG_FACINGS = "WRONG_FACINGS"
    UNEXPECTED = "UNEXPECTED"


class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Product(BaseModel):
    id: str
    brand_id: str
    sku: str
    name: str
    category: str
    brand_tier: str  # hero | secondary | new


class SalesData(BaseModel):
    sku: str
    brand_id: str
    store_format: StoreFormat
    units_sold: int
    period: str


class PlanogramPosition(BaseModel):
    shelf_index: int
    column_index: int
    sku: str
    facings: int
    rationale: Optional[str] = None


class Planogram(BaseModel):
    id: str
    brand_id: str
    store_format: StoreFormat
    status: str
    generated_at: datetime
    positions: list[PlanogramPosition] = []


class Discrepancy(BaseModel):
    type: DiscrepancyType
    sku: str
    expected_position: Optional[str] = None
    detected_position: Optional[str] = None
    severity: Severity


class AuditResult(BaseModel):
    id: str
    planogram_id: str
    photo_url: str
    compliance_score: float
    discrepancies: list[Discrepancy] = []
    audited_at: datetime


# ── Request / Response ────────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    guideline_id: str
    brand_id: str
    products_parsed: int
    parsed_products: list[dict]


class GenerateRequest(BaseModel):
    brand_id: str
    store_format: StoreFormat


class GenerateResponse(BaseModel):
    planogram: Planogram


class AuditResponse(BaseModel):
    result: AuditResult
```

Save to `apps/backend/app/models/schemas.py`.

- [ ] **Step 2: Verify schemas import cleanly**

```bash
cd /Users/adnan/Documents/shelfy/apps/backend
uv run python -c "from app.models.schemas import Planogram, AuditResult, StoreFormat; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
cd /Users/adnan/Documents/shelfy
git add apps/backend/app/models/
git commit -m "feat: pydantic schemas"
```

---

## Task 4: Supabase SQL schema + seed data

**Files:**
- Create: `apps/backend/sql/001_schema.sql`
- Create: `apps/backend/sql/002_seed.sql`

- [ ] **Step 1: Create SQL schema**

```sql
-- 001_schema.sql
-- Run this in Supabase SQL editor

CREATE TABLE IF NOT EXISTS brands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS brand_guidelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE,
    raw_file_url TEXT,
    parsed_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE,
    sku TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    brand_tier TEXT NOT NULL CHECK (brand_tier IN ('hero', 'secondary', 'new')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (brand_id, sku)
);

CREATE TABLE IF NOT EXISTS sales_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE,
    store_format TEXT NOT NULL CHECK (store_format IN ('SMALL', 'MEDIUM', 'LARGE')),
    sku TEXT NOT NULL,
    units_sold INTEGER NOT NULL,
    period TEXT NOT NULL DEFAULT 'Q4-2024'
);

CREATE TABLE IF NOT EXISTS planograms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE,
    store_format TEXT NOT NULL CHECK (store_format IN ('SMALL', 'MEDIUM', 'LARGE')),
    status TEXT NOT NULL DEFAULT 'draft',
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS planogram_positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    planogram_id UUID REFERENCES planograms(id) ON DELETE CASCADE,
    shelf_index INTEGER NOT NULL,
    column_index INTEGER NOT NULL,
    sku TEXT NOT NULL,
    facings INTEGER NOT NULL DEFAULT 1,
    rationale TEXT,
    UNIQUE (planogram_id, shelf_index, column_index)
);

CREATE TABLE IF NOT EXISTS audit_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    planogram_id UUID REFERENCES planograms(id) ON DELETE CASCADE,
    photo_url TEXT NOT NULL,
    compliance_score FLOAT,
    audited_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS discrepancies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id UUID REFERENCES audit_results(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('MISSING', 'WRONG_POSITION', 'WRONG_FACINGS', 'UNEXPECTED')),
    sku TEXT NOT NULL,
    expected_position TEXT,
    detected_position TEXT,
    severity TEXT NOT NULL CHECK (severity IN ('HIGH', 'MEDIUM', 'LOW'))
);
```

Save to `apps/backend/sql/001_schema.sql`.

- [ ] **Step 2: Create seed data SQL**

```sql
-- 002_seed.sql
-- One demo brand: LumiSkin (skincare)

INSERT INTO brands (id, name, category) VALUES
    ('11111111-1111-1111-1111-111111111111', 'LumiSkin', 'skincare')
ON CONFLICT DO NOTHING;

INSERT INTO products (brand_id, sku, name, category, brand_tier) VALUES
    ('11111111-1111-1111-1111-111111111111', 'LS-001', 'Vitamin C Brightening Serum', 'skincare', 'hero'),
    ('11111111-1111-1111-1111-111111111111', 'LS-002', 'Hydra-Boost Moisturizer SPF30', 'skincare', 'hero'),
    ('11111111-1111-1111-1111-111111111111', 'LS-003', 'Retinol Night Cream', 'skincare', 'secondary'),
    ('11111111-1111-1111-1111-111111111111', 'LS-004', 'Gentle Foaming Cleanser', 'skincare', 'secondary'),
    ('11111111-1111-1111-1111-111111111111', 'LS-005', 'Hyaluronic Acid Eye Cream', 'skincare', 'secondary'),
    ('11111111-1111-1111-1111-111111111111', 'LS-006', 'AHA Exfoliating Toner', 'skincare', 'new'),
    ('11111111-1111-1111-1111-111111111111', 'LS-007', 'Niacinamide Pore Serum', 'skincare', 'new'),
    ('11111111-1111-1111-1111-111111111111', 'LS-008', 'SPF50 Daily Shield', 'skincare', 'secondary')
ON CONFLICT DO NOTHING;

-- SMALL store sales
INSERT INTO sales_data (brand_id, store_format, sku, units_sold) VALUES
    ('11111111-1111-1111-1111-111111111111', 'SMALL', 'LS-001', 87),
    ('11111111-1111-1111-1111-111111111111', 'SMALL', 'LS-002', 72),
    ('11111111-1111-1111-1111-111111111111', 'SMALL', 'LS-003', 41),
    ('11111111-1111-1111-1111-111111111111', 'SMALL', 'LS-004', 55),
    ('11111111-1111-1111-1111-111111111111', 'SMALL', 'LS-005', 29),
    ('11111111-1111-1111-1111-111111111111', 'SMALL', 'LS-006', 18),
    ('11111111-1111-1111-1111-111111111111', 'SMALL', 'LS-007', 22),
    ('11111111-1111-1111-1111-111111111111', 'SMALL', 'LS-008', 35);

-- MEDIUM store sales
INSERT INTO sales_data (brand_id, store_format, sku, units_sold) VALUES
    ('11111111-1111-1111-1111-111111111111', 'MEDIUM', 'LS-001', 134),
    ('11111111-1111-1111-1111-111111111111', 'MEDIUM', 'LS-002', 121),
    ('11111111-1111-1111-1111-111111111111', 'MEDIUM', 'LS-003', 89),
    ('11111111-1111-1111-1111-111111111111', 'MEDIUM', 'LS-004', 76),
    ('11111111-1111-1111-1111-111111111111', 'MEDIUM', 'LS-005', 58),
    ('11111111-1111-1111-1111-111111111111', 'MEDIUM', 'LS-006', 44),
    ('11111111-1111-1111-1111-111111111111', 'MEDIUM', 'LS-007', 51),
    ('11111111-1111-1111-1111-111111111111', 'MEDIUM', 'LS-008', 67);

-- LARGE store sales
INSERT INTO sales_data (brand_id, store_format, sku, units_sold) VALUES
    ('11111111-1111-1111-1111-111111111111', 'LARGE', 'LS-001', 210),
    ('11111111-1111-1111-1111-111111111111', 'LARGE', 'LS-002', 195),
    ('11111111-1111-1111-1111-111111111111', 'LARGE', 'LS-003', 142),
    ('11111111-1111-1111-1111-111111111111', 'LARGE', 'LS-004', 118),
    ('11111111-1111-1111-1111-111111111111', 'LARGE', 'LS-005', 99),
    ('11111111-1111-1111-1111-111111111111', 'LARGE', 'LS-006', 88),
    ('11111111-1111-1111-1111-111111111111', 'LARGE', 'LS-007', 93),
    ('11111111-1111-1111-1111-111111111111', 'LARGE', 'LS-008', 107);
```

Save to `apps/backend/sql/002_seed.sql`.

- [ ] **Step 3: Run schema in Supabase SQL editor**

Copy-paste `001_schema.sql` then `002_seed.sql` into the Supabase dashboard SQL editor and run both. Verify tables appear in the Table Editor.

- [ ] **Step 4: Create Supabase Storage buckets**

In Supabase dashboard → Storage → New bucket:
- `planogram-files` (public: false)
- `shelf-photos` (public: true — needed so Claude Vision can fetch via URL)

- [ ] **Step 5: Commit**

```bash
cd /Users/adnan/Documents/shelfy
git add apps/backend/sql/
git commit -m "feat: supabase schema and seed data"
```

---

## Task 5: Repository base classes + brand repository

**Files:**
- Create: `apps/backend/app/repositories/base.py`
- Create: `apps/backend/app/repositories/brand.py`
- Create: `apps/backend/tests/test_brand_repo.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_brand_repo.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.repositories.brand import SupabaseBrandRepository
from app.models.schemas import Product


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    table_mock = MagicMock()
    table_mock.select = MagicMock(return_value=table_mock)
    table_mock.insert = MagicMock(return_value=table_mock)
    table_mock.eq = MagicMock(return_value=table_mock)
    table_mock.order = MagicMock(return_value=table_mock)
    table_mock.limit = MagicMock(return_value=table_mock)
    table_mock.execute = AsyncMock()
    client.table = MagicMock(return_value=table_mock)
    return client, table_mock


@pytest.mark.asyncio
async def test_get_product_catalog_returns_products(mock_supabase):
    client, table_mock = mock_supabase
    table_mock.execute.return_value = MagicMock(data=[
        {"id": "p1", "brand_id": "b1", "sku": "LS-001",
         "name": "Vitamin C Serum", "category": "skincare", "brand_tier": "hero"},
    ])
    repo = SupabaseBrandRepository(client)
    products = await repo.get_product_catalog("b1", "skincare")
    assert len(products) == 1
    assert products[0].sku == "LS-001"
    assert isinstance(products[0], Product)


@pytest.mark.asyncio
async def test_get_guidelines_raises_when_missing(mock_supabase):
    client, table_mock = mock_supabase
    table_mock.execute.return_value = MagicMock(data=[])
    repo = SupabaseBrandRepository(client)
    with pytest.raises(ValueError, match="No guidelines"):
        await repo.get_guidelines("b1")
```

Save to `apps/backend/tests/test_brand_repo.py`.

- [ ] **Step 2: Run test to see it fail**

```bash
cd /Users/adnan/Documents/shelfy/apps/backend
uv run pytest tests/test_brand_repo.py -v
```

Expected: `ImportError` — module not found.

- [ ] **Step 3: Write base.py**

```python
from abc import ABC, abstractmethod
from app.models.schemas import Product, Planogram, AuditResult, SalesData


class BrandRepository(ABC):
    @abstractmethod
    async def get_guidelines(self, brand_id: str) -> dict: ...

    @abstractmethod
    async def get_product_catalog(self, brand_id: str, category: str) -> list[Product]: ...

    @abstractmethod
    async def save_guideline(self, brand_id: str, file_url: str, parsed_json: dict) -> str: ...


class SalesRepository(ABC):
    @abstractmethod
    async def get_store_sales(self, brand_id: str, store_format: str) -> list[SalesData]: ...


class PlanogramRepository(ABC):
    @abstractmethod
    async def save(self, brand_id: str, store_format: str, positions: list[dict]) -> Planogram: ...

    @abstractmethod
    async def get(self, planogram_id: str) -> Planogram: ...


class AuditRepository(ABC):
    @abstractmethod
    async def save(self, planogram_id: str, photo_url: str,
                   compliance_score: float, discrepancies: list[dict]) -> AuditResult: ...

    @abstractmethod
    async def get(self, audit_id: str) -> AuditResult: ...
```

Save to `apps/backend/app/repositories/base.py`.

- [ ] **Step 4: Write brand.py**

```python
from supabase import AsyncClient
from app.repositories.base import BrandRepository, SalesRepository
from app.models.schemas import Product, SalesData, StoreFormat


class SupabaseBrandRepository(BrandRepository):
    def __init__(self, client: AsyncClient):
        self._db = client

    async def get_guidelines(self, brand_id: str) -> dict:
        result = (
            await self._db.table("brand_guidelines")
            .select("parsed_json")
            .eq("brand_id", brand_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if not result.data:
            raise ValueError(f"No guidelines found for brand {brand_id}")
        return result.data[0]["parsed_json"]

    async def get_product_catalog(self, brand_id: str, category: str) -> list[Product]:
        result = (
            await self._db.table("products")
            .select("*")
            .eq("brand_id", brand_id)
            .eq("category", category)
            .execute()
        )
        return [Product(**row) for row in result.data]

    async def save_guideline(self, brand_id: str, file_url: str, parsed_json: dict) -> str:
        result = (
            await self._db.table("brand_guidelines")
            .insert({"brand_id": brand_id, "raw_file_url": file_url, "parsed_json": parsed_json})
            .execute()
        )
        return result.data[0]["id"]


class SupabaseSalesRepository(SalesRepository):
    def __init__(self, client: AsyncClient):
        self._db = client

    async def get_store_sales(self, brand_id: str, store_format: str) -> list[SalesData]:
        result = (
            await self._db.table("sales_data")
            .select("*")
            .eq("brand_id", brand_id)
            .eq("store_format", store_format)
            .execute()
        )
        return [SalesData(**row) for row in result.data]
```

Save to `apps/backend/app/repositories/brand.py`.

- [ ] **Step 5: Run tests — expect pass**

```bash
cd /Users/adnan/Documents/shelfy/apps/backend
uv run pytest tests/test_brand_repo.py -v
```

Expected: `2 passed`

- [ ] **Step 6: Commit**

```bash
cd /Users/adnan/Documents/shelfy
git add apps/backend/app/repositories/ apps/backend/tests/test_brand_repo.py
git commit -m "feat: repository base classes and brand repository"
```

---

## Task 6: Planogram + audit repositories

**Files:**
- Create: `apps/backend/app/repositories/planogram.py`
- Create: `apps/backend/app/repositories/audit.py`
- Create: `apps/backend/tests/test_planogram_repo.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_planogram_repo.py
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from app.repositories.planogram import SupabasePlanogramRepository
from app.models.schemas import Planogram, StoreFormat


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    tm = MagicMock()
    tm.select = MagicMock(return_value=tm)
    tm.insert = MagicMock(return_value=tm)
    tm.eq = MagicMock(return_value=tm)
    tm.execute = AsyncMock()
    client.table = MagicMock(return_value=tm)
    return client, tm


@pytest.mark.asyncio
async def test_save_planogram_returns_planogram(mock_supabase):
    client, tm = mock_supabase
    now = datetime.now(timezone.utc).isoformat()
    tm.execute.side_effect = [
        MagicMock(data=[{"id": "pg-1", "brand_id": "b1",
                         "store_format": "SMALL", "status": "draft",
                         "generated_at": now}]),
        MagicMock(data=[]),  # positions insert
    ]
    repo = SupabasePlanogramRepository(client)
    planogram = await repo.save("b1", "SMALL", [
        {"shelf_index": 0, "column_index": 0, "sku": "LS-001", "facings": 2, "rationale": "top seller"}
    ])
    assert planogram.id == "pg-1"
    assert planogram.store_format == StoreFormat.SMALL


@pytest.mark.asyncio
async def test_get_planogram_raises_when_missing(mock_supabase):
    client, tm = mock_supabase
    tm.execute.return_value = MagicMock(data=[])
    repo = SupabasePlanogramRepository(client)
    with pytest.raises(ValueError, match="Planogram not found"):
        await repo.get("nonexistent-id")
```

Save to `apps/backend/tests/test_planogram_repo.py`.

- [ ] **Step 2: Run to see fail**

```bash
cd /Users/adnan/Documents/shelfy/apps/backend
uv run pytest tests/test_planogram_repo.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Write planogram.py**

```python
from datetime import datetime, timezone
from supabase import AsyncClient
from app.repositories.base import PlanogramRepository
from app.models.schemas import Planogram, PlanogramPosition, StoreFormat


class SupabasePlanogramRepository(PlanogramRepository):
    def __init__(self, client: AsyncClient):
        self._db = client

    async def save(self, brand_id: str, store_format: str, positions: list[dict]) -> Planogram:
        pg_result = (
            await self._db.table("planograms")
            .insert({"brand_id": brand_id, "store_format": store_format, "status": "draft"})
            .execute()
        )
        row = pg_result.data[0]
        planogram_id = row["id"]

        if positions:
            pos_rows = [{"planogram_id": planogram_id, **p} for p in positions]
            await self._db.table("planogram_positions").insert(pos_rows).execute()

        return Planogram(
            id=planogram_id,
            brand_id=brand_id,
            store_format=StoreFormat(store_format),
            status=row["status"],
            generated_at=datetime.fromisoformat(row["generated_at"]),
            positions=[PlanogramPosition(**p) for p in positions],
        )

    async def get(self, planogram_id: str) -> Planogram:
        pg = (
            await self._db.table("planograms")
            .select("*")
            .eq("id", planogram_id)
            .execute()
        )
        if not pg.data:
            raise ValueError(f"Planogram not found: {planogram_id}")

        pos = (
            await self._db.table("planogram_positions")
            .select("*")
            .eq("planogram_id", planogram_id)
            .execute()
        )
        row = pg.data[0]
        return Planogram(
            id=row["id"],
            brand_id=row["brand_id"],
            store_format=StoreFormat(row["store_format"]),
            status=row["status"],
            generated_at=datetime.fromisoformat(row["generated_at"]),
            positions=[PlanogramPosition(**p) for p in pos.data],
        )
```

Save to `apps/backend/app/repositories/planogram.py`.

- [ ] **Step 4: Write audit.py**

```python
from datetime import datetime
from supabase import AsyncClient
from app.repositories.base import AuditRepository
from app.models.schemas import AuditResult, Discrepancy, DiscrepancyType, Severity


class SupabaseAuditRepository(AuditRepository):
    def __init__(self, client: AsyncClient):
        self._db = client

    async def save(self, planogram_id: str, photo_url: str,
                   compliance_score: float, discrepancies: list[dict]) -> AuditResult:
        audit = (
            await self._db.table("audit_results")
            .insert({
                "planogram_id": planogram_id,
                "photo_url": photo_url,
                "compliance_score": compliance_score,
            })
            .execute()
        )
        audit_id = audit.data[0]["id"]

        if discrepancies:
            disc_rows = [{"audit_id": audit_id, **d} for d in discrepancies]
            await self._db.table("discrepancies").insert(disc_rows).execute()

        return AuditResult(
            id=audit_id,
            planogram_id=planogram_id,
            photo_url=photo_url,
            compliance_score=compliance_score,
            discrepancies=[
                Discrepancy(
                    type=DiscrepancyType(d["type"]),
                    sku=d["sku"],
                    expected_position=d.get("expected_position"),
                    detected_position=d.get("detected_position"),
                    severity=Severity(d["severity"]),
                )
                for d in discrepancies
            ],
            audited_at=datetime.fromisoformat(audit.data[0]["audited_at"]),
        )

    async def get(self, audit_id: str) -> AuditResult:
        audit = (
            await self._db.table("audit_results")
            .select("*")
            .eq("id", audit_id)
            .execute()
        )
        if not audit.data:
            raise ValueError(f"Audit not found: {audit_id}")

        discs = (
            await self._db.table("discrepancies")
            .select("*")
            .eq("audit_id", audit_id)
            .execute()
        )
        row = audit.data[0]
        return AuditResult(
            id=row["id"],
            planogram_id=row["planogram_id"],
            photo_url=row["photo_url"],
            compliance_score=row["compliance_score"],
            discrepancies=[
                Discrepancy(
                    type=DiscrepancyType(d["type"]),
                    sku=d["sku"],
                    expected_position=d.get("expected_position"),
                    detected_position=d.get("detected_position"),
                    severity=Severity(d["severity"]),
                )
                for d in discs.data
            ],
            audited_at=datetime.fromisoformat(row["audited_at"]),
        )
```

Save to `apps/backend/app/repositories/audit.py`.

- [ ] **Step 5: Run tests**

```bash
cd /Users/adnan/Documents/shelfy/apps/backend
uv run pytest tests/test_planogram_repo.py -v
```

Expected: `2 passed`

- [ ] **Step 6: Commit**

```bash
cd /Users/adnan/Documents/shelfy
git add apps/backend/app/repositories/ apps/backend/tests/
git commit -m "feat: planogram and audit repositories"
```

---

## Task 7: Embeddings service

**Files:**
- Create: `apps/backend/app/services/embeddings.py`

- [ ] **Step 1: Write embeddings.py**

```python
import chromadb
from openai import AsyncOpenAI
from app.config import settings
from app.models.schemas import Product

_chroma = chromadb.Client()
_collection = _chroma.get_or_create_collection("products")
_openai = AsyncOpenAI(api_key=settings.openai_api_key)


async def embed_products(products: list[Product]) -> None:
    if not products:
        return
    texts = [f"{p.name} {p.category} {p.brand_tier} {p.sku}" for p in products]
    response = await _openai.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    embeddings = [item.embedding for item in response.data]
    _collection.upsert(
        ids=[p.sku for p in products],
        embeddings=embeddings,
        metadatas=[p.model_dump() for p in products],
        documents=texts,
    )


async def search_similar(query: str, top_k: int = 5) -> list[dict]:
    response = await _openai.embeddings.create(
        model="text-embedding-3-small",
        input=[query],
    )
    query_embedding = response.data[0].embedding
    results = _collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )
    return results["metadatas"][0] if results["metadatas"] else []
```

Save to `apps/backend/app/services/embeddings.py`.

- [ ] **Step 2: Commit**

```bash
cd /Users/adnan/Documents/shelfy
git add apps/backend/app/services/embeddings.py
git commit -m "feat: embeddings service with chroma"
```

---

## Task 8: Ingestion service

**Files:**
- Create: `apps/backend/app/services/ingestion.py`
- Create: `apps/backend/tests/test_ingestion.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_ingestion.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.ingestion import parse_planogram_pdf


@pytest.mark.asyncio
async def test_parse_planogram_pdf_returns_products():
    sample_pdf_bytes = b"%PDF-1.4 fake pdf content"

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='''{
        "brand_rules": {"eye_level": "hero products only"},
        "products": [
            {"sku": "LS-001", "name": "Vitamin C Serum", "category": "skincare",
             "brand_tier": "hero", "default_facings": 2},
            {"sku": "LS-002", "name": "Moisturizer", "category": "skincare",
             "brand_tier": "hero", "default_facings": 2}
        ]
    }''')]

    with patch("app.services.ingestion.anthropic_client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        with patch("app.services.ingestion.embed_products", new_callable=AsyncMock):
            result = await parse_planogram_pdf(sample_pdf_bytes, "b1")

    assert result["products_parsed"] == 2
    assert result["parsed_products"][0]["sku"] == "LS-001"
```

Save to `apps/backend/tests/test_ingestion.py`.

- [ ] **Step 2: Run to see fail**

```bash
cd /Users/adnan/Documents/shelfy/apps/backend
uv run pytest tests/test_ingestion.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Write ingestion.py**

```python
import json
import base64
import pdfplumber
import anthropic
from io import BytesIO
from app.config import settings
from app.services.embeddings import embed_products
from app.models.schemas import Product

anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

EXTRACT_SYSTEM = """You are a retail planogram analyst. Extract structured product and brand rule data from the provided planogram document.

Return ONLY valid JSON with this exact structure:
{
  "brand_rules": {
    "eye_level": "description of eye-level placement rule",
    "hero_placement": "where hero products go",
    "new_product_placement": "where new products go"
  },
  "products": [
    {
      "sku": "product SKU or code",
      "name": "full product name",
      "category": "skincare",
      "brand_tier": "hero | secondary | new",
      "default_facings": 1
    }
  ]
}"""


async def parse_planogram_pdf(pdf_bytes: bytes, brand_id: str) -> dict:
    text = _extract_pdf_text(pdf_bytes)

    message = await anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        system=EXTRACT_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Extract planogram data from this document:\n\n{text[:8000]}"
        }],
    )

    raw = message.content[0].text
    data = json.loads(raw)

    products = [
        Product(
            id=f"synthetic-{p['sku']}",
            brand_id=brand_id,
            sku=p["sku"],
            name=p["name"],
            category=p.get("category", "skincare"),
            brand_tier=p.get("brand_tier", "secondary"),
        )
        for p in data.get("products", [])
    ]

    await embed_products(products)

    return {
        "brand_rules": data.get("brand_rules", {}),
        "products_parsed": len(products),
        "parsed_products": [p.model_dump() for p in products],
        "raw_json": data,
    }


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)
```

Save to `apps/backend/app/services/ingestion.py`.

- [ ] **Step 4: Run tests**

```bash
cd /Users/adnan/Documents/shelfy/apps/backend
uv run pytest tests/test_ingestion.py -v
```

Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
cd /Users/adnan/Documents/shelfy
git add apps/backend/app/services/ingestion.py apps/backend/tests/test_ingestion.py
git commit -m "feat: ingestion service with claude extraction"
```

---

## Task 9: Generation service (Claude tool_use)

**Files:**
- Create: `apps/backend/app/services/generation.py`
- Create: `apps/backend/tests/test_generation.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_generation.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.generation import generate_planogram
from app.models.schemas import Planogram, StoreFormat


@pytest.mark.asyncio
async def test_generate_planogram_returns_planogram():
    mock_positions = [
        {"shelf_index": 0, "column_index": 0, "sku": "LS-001",
         "facings": 2, "rationale": "Top seller, eye level"},
        {"shelf_index": 0, "column_index": 1, "sku": "LS-002",
         "facings": 2, "rationale": "Hero product, eye level"},
    ]
    mock_planogram = Planogram(
        id="pg-test",
        brand_id="b1",
        store_format=StoreFormat.SMALL,
        status="draft",
        generated_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        positions=[],
    )

    with patch("app.services.generation.run_generation_agent",
               new_callable=AsyncMock, return_value=mock_positions):
        with patch("app.services.generation.planogram_repo") as mock_repo:
            mock_repo.save = AsyncMock(return_value=mock_planogram)
            result = await generate_planogram("b1", "SMALL")

    assert isinstance(result, Planogram)
    assert result.id == "pg-test"
```

Save to `apps/backend/tests/test_generation.py`.

- [ ] **Step 2: Run to see fail**

```bash
cd /Users/adnan/Documents/shelfy/apps/backend
uv run pytest tests/test_generation.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Write generation.py**

```python
import json
import anthropic
from app.config import settings
from app.models.schemas import Planogram, StoreFormat
from app.repositories.planogram import SupabasePlanogramRepository
from app.repositories.brand import SupabaseBrandRepository, SupabaseSalesRepository
from app.services.embeddings import search_similar

anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

# These are injected at app startup via main.py lifespan
planogram_repo: SupabasePlanogramRepository = None  # type: ignore
brand_repo: SupabaseBrandRepository = None           # type: ignore
sales_repo: SupabaseSalesRepository = None           # type: ignore

TOOLS = [
    {
        "name": "get_brand_guidelines",
        "description": "Get parsed brand guidelines including placement rules and brand hierarchy.",
        "input_schema": {
            "type": "object",
            "properties": {"brand_id": {"type": "string"}},
            "required": ["brand_id"],
        },
    },
    {
        "name": "get_product_catalog",
        "description": "Get all products for a brand in a given category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "brand_id": {"type": "string"},
                "category": {"type": "string"},
            },
            "required": ["brand_id", "category"],
        },
    },
    {
        "name": "get_store_sales_data",
        "description": "Get sales data for all products in a specific store format.",
        "input_schema": {
            "type": "object",
            "properties": {
                "brand_id": {"type": "string"},
                "store_format": {"type": "string", "enum": ["SMALL", "MEDIUM", "LARGE"]},
            },
            "required": ["brand_id", "store_format"],
        },
    },
    {
        "name": "search_similar_products",
        "description": "Semantic search over product catalog.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "submit_planogram",
        "description": "Submit the final generated planogram positions. Call this last.",
        "input_schema": {
            "type": "object",
            "properties": {
                "positions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "shelf_index": {"type": "integer"},
                            "column_index": {"type": "integer"},
                            "sku": {"type": "string"},
                            "facings": {"type": "integer"},
                            "rationale": {"type": "string"},
                        },
                        "required": ["shelf_index", "column_index", "sku", "facings", "rationale"],
                    },
                }
            },
            "required": ["positions"],
        },
    },
]

SYSTEM = """You are an expert visual merchandising AI for beauty retail brands.
Generate a store-specific planogram based on brand guidelines and sales performance data.

Rules:
- Eye level (shelf 1) = highest-selling hero products
- Shelf 0 (top) = new products and secondary items
- Shelf 2 (bottom) = bulkier secondary items
- Allocate more facings to higher-selling products
- Always call get_brand_guidelines, get_product_catalog, and get_store_sales_data before generating
- Call submit_planogram last with all shelf positions"""


async def _execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "get_brand_guidelines":
        result = await brand_repo.get_guidelines(tool_input["brand_id"])
        return json.dumps(result)

    if tool_name == "get_product_catalog":
        products = await brand_repo.get_product_catalog(
            tool_input["brand_id"], tool_input["category"]
        )
        return json.dumps([p.model_dump() for p in products])

    if tool_name == "get_store_sales_data":
        sales = await sales_repo.get_store_sales(
            tool_input["brand_id"], tool_input["store_format"]
        )
        return json.dumps([s.model_dump() for s in sales])

    if tool_name == "search_similar_products":
        results = await search_similar(tool_input["query"], tool_input.get("top_k", 5))
        return json.dumps(results)

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


async def run_generation_agent(brand_id: str, store_format: str) -> list[dict]:
    messages = [{
        "role": "user",
        "content": (
            f"Generate a planogram for brand_id={brand_id}, "
            f"store_format={store_format}. "
            "Use the available tools to gather all data, then call submit_planogram."
        ),
    }]

    while True:
        response = await anthropic_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        tool_results = []
        submitted_positions = None

        for block in response.content:
            if block.type != "tool_use":
                continue
            if block.name == "submit_planogram":
                submitted_positions = block.input["positions"]
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps({"status": "saved"}),
                })
            else:
                result = await _execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        if submitted_positions is not None:
            return submitted_positions

        messages.append({"role": "user", "content": tool_results})

    return []


async def generate_planogram(brand_id: str, store_format: str) -> Planogram:
    positions = await run_generation_agent(brand_id, store_format)
    return await planogram_repo.save(brand_id, store_format, positions)
```

Save to `apps/backend/app/services/generation.py`.

- [ ] **Step 4: Run tests**

```bash
cd /Users/adnan/Documents/shelfy/apps/backend
uv run pytest tests/test_generation.py -v
```

Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
cd /Users/adnan/Documents/shelfy
git add apps/backend/app/services/generation.py apps/backend/tests/test_generation.py
git commit -m "feat: generation service with claude tool_use agent"
```

---

## Task 10: Audit service

**Files:**
- Create: `apps/backend/app/services/audit.py`
- Create: `apps/backend/tests/test_audit.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_audit.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.audit import run_shelf_audit
from app.models.schemas import AuditResult, StoreFormat, Planogram, PlanogramPosition


@pytest.fixture
def sample_planogram():
    from datetime import datetime, timezone
    return Planogram(
        id="pg-1",
        brand_id="b1",
        store_format=StoreFormat.SMALL,
        status="draft",
        generated_at=datetime.now(timezone.utc),
        positions=[
            PlanogramPosition(shelf_index=1, column_index=0, sku="LS-001", facings=2,
                              rationale="hero"),
            PlanogramPosition(shelf_index=1, column_index=1, sku="LS-002", facings=2,
                              rationale="hero"),
        ],
    )


@pytest.mark.asyncio
async def test_run_shelf_audit_returns_result(sample_planogram):
    mock_vision_response = MagicMock()
    mock_vision_response.content = [MagicMock(text='''{
        "detected_products": [
            {"sku": "LS-001", "shelf_index": 1, "column_index": 0, "facings": 2, "confidence": 0.92},
            {"sku": "LS-003", "shelf_index": 1, "column_index": 1, "facings": 1, "confidence": 0.85}
        ]
    }''')]

    mock_audit_result = MagicMock(spec=AuditResult)
    mock_audit_result.compliance_score = 50.0

    with patch("app.services.audit.anthropic_client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_vision_response)
        with patch("app.services.audit.audit_repo") as mock_repo:
            mock_repo.save = AsyncMock(return_value=mock_audit_result)
            result = await run_shelf_audit("pg-1", "https://example.com/shelf.jpg",
                                           sample_planogram)

    assert result.compliance_score == 50.0
```

Save to `apps/backend/tests/test_audit.py`.

- [ ] **Step 2: Run to see fail**

```bash
cd /Users/adnan/Documents/shelfy/apps/backend
uv run pytest tests/test_audit.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Write audit.py**

```python
import json
import anthropic
from app.config import settings
from app.models.schemas import AuditResult, Planogram, DiscrepancyType, Severity
from app.repositories.audit import SupabaseAuditRepository

anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
audit_repo: SupabaseAuditRepository = None  # type: ignore

VISION_SYSTEM = """You are a retail shelf audit AI. Analyze the shelf photo and identify all visible beauty products.

Return ONLY valid JSON:
{
  "detected_products": [
    {
      "sku": "product SKU if identifiable, else describe the product",
      "shelf_index": 0,
      "column_index": 0,
      "facings": 1,
      "confidence": 0.85
    }
  ]
}

shelf_index: 0 = top shelf, 1 = eye level, 2 = bottom shelf
column_index: left to right, starting at 0
facings: number of product units visible facing forward"""


def _calculate_compliance(
    detected: list[dict],
    planogram: Planogram,
) -> tuple[float, list[dict]]:
    target = {(p.shelf_index, p.column_index): p for p in planogram.positions}
    detected_skus = {d["sku"]: d for d in detected}
    target_skus = {p.sku: p for p in planogram.positions}

    discrepancies = []

    for sku, pos in target_skus.items():
        if sku not in detected_skus:
            discrepancies.append({
                "type": DiscrepancyType.MISSING,
                "sku": sku,
                "expected_position": f"shelf {pos.shelf_index}, col {pos.column_index}",
                "detected_position": None,
                "severity": Severity.HIGH if pos.brand_tier_from_sku(sku) == "hero" else Severity.MEDIUM
                if hasattr(pos, "brand_tier_from_sku") else Severity.MEDIUM,
            })
        else:
            det = detected_skus[sku]
            if (det["shelf_index"] != pos.shelf_index or
                    det["column_index"] != pos.column_index):
                discrepancies.append({
                    "type": DiscrepancyType.WRONG_POSITION,
                    "sku": sku,
                    "expected_position": f"shelf {pos.shelf_index}, col {pos.column_index}",
                    "detected_position": f"shelf {det['shelf_index']}, col {det['column_index']}",
                    "severity": Severity.MEDIUM,
                })
            elif det.get("facings", 1) < pos.facings:
                discrepancies.append({
                    "type": DiscrepancyType.WRONG_FACINGS,
                    "sku": sku,
                    "expected_position": f"shelf {pos.shelf_index}, col {pos.column_index}",
                    "detected_position": f"shelf {det['shelf_index']}, col {det['column_index']}",
                    "severity": Severity.LOW,
                })

    for sku in detected_skus:
        if sku not in target_skus:
            det = detected_skus[sku]
            discrepancies.append({
                "type": DiscrepancyType.UNEXPECTED,
                "sku": sku,
                "expected_position": None,
                "detected_position": f"shelf {det['shelf_index']}, col {det['column_index']}",
                "severity": Severity.LOW,
            })

    total = len(planogram.positions)
    issues = len([d for d in discrepancies
                  if d["type"] in (DiscrepancyType.MISSING, DiscrepancyType.WRONG_POSITION)])
    score = max(0.0, 100.0 * (1 - issues / total)) if total > 0 else 0.0

    return score, discrepancies


async def run_shelf_audit(
    planogram_id: str,
    photo_url: str,
    planogram: Planogram,
) -> AuditResult:
    response = await anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        system=VISION_SYSTEM,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "url", "url": photo_url},
                },
                {
                    "type": "text",
                    "text": (
                        "Identify all products on this retail shelf. "
                        f"Target SKUs to look for: "
                        f"{[p.sku for p in planogram.positions]}"
                    ),
                },
            ],
        }],
    )

    raw = response.content[0].text
    data = json.loads(raw)
    detected = data.get("detected_products", [])

    score, discrepancies = _calculate_compliance(detected, planogram)

    return await audit_repo.save(planogram_id, photo_url, score, discrepancies)
```

Save to `apps/backend/app/services/audit.py`.

- [ ] **Step 4: Fix severity lookup — remove invalid method call in audit.py**

The `brand_tier_from_sku` call doesn't exist. Replace the severity logic in `_calculate_compliance`:

```python
# Replace this block inside the MISSING discrepancy:
"severity": Severity.HIGH if pos.brand_tier_from_sku(sku) == "hero" else Severity.MEDIUM
if hasattr(pos, "brand_tier_from_sku") else Severity.MEDIUM,
```

With:
```python
"severity": Severity.HIGH,
```

- [ ] **Step 5: Run tests**

```bash
cd /Users/adnan/Documents/shelfy/apps/backend
uv run pytest tests/test_audit.py -v
```

Expected: `1 passed`

- [ ] **Step 6: Commit**

```bash
cd /Users/adnan/Documents/shelfy
git add apps/backend/app/services/audit.py apps/backend/tests/test_audit.py
git commit -m "feat: audit service with claude vision and compliance diff"
```

---

## Task 11: FastAPI app + routes

**Files:**
- Create: `apps/backend/app/main.py`
- Create: `apps/backend/app/api/routes/ingest.py`
- Create: `apps/backend/app/api/routes/planogram.py`
- Create: `apps/backend/app/api/routes/audit.py`

- [ ] **Step 1: Write main.py**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_async_client

from app.config import settings
from app.repositories.brand import SupabaseBrandRepository, SupabaseSalesRepository
from app.repositories.planogram import SupabasePlanogramRepository
from app.repositories.audit import SupabaseAuditRepository
from app.api.routes import ingest, planogram, audit
import app.services.generation as gen_service
import app.services.audit as audit_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = await create_async_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )
    gen_service.brand_repo = SupabaseBrandRepository(db)
    gen_service.sales_repo = SupabaseSalesRepository(db)
    gen_service.planogram_repo = SupabasePlanogramRepository(db)
    audit_service.audit_repo = SupabaseAuditRepository(db)

    app.state.db = db
    app.state.brand_repo = gen_service.brand_repo
    app.state.sales_repo = gen_service.sales_repo
    app.state.planogram_repo = gen_service.planogram_repo
    app.state.audit_repo = audit_service.audit_repo

    yield


app = FastAPI(title="Shelfy API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
app.include_router(planogram.router, prefix="/planogram", tags=["planogram"])
app.include_router(audit.router, prefix="/audit", tags=["audit"])


@app.get("/health")
async def health():
    return {"status": "ok"}
```

Save to `apps/backend/app/main.py`.

- [ ] **Step 2: Write ingest route**

```python
# app/api/routes/ingest.py
from fastapi import APIRouter, UploadFile, File, Form, Request
from app.models.schemas import IngestResponse
from app.services import ingestion as ingestion_service

router = APIRouter()


@router.post("/planogram", response_model=IngestResponse)
async def ingest_planogram(
    request: Request,
    brand_id: str = Form(...),
    file: UploadFile = File(...),
):
    pdf_bytes = await file.read()

    # Upload raw file to Supabase Storage
    db = request.app.state.db
    storage_path = f"{brand_id}/{file.filename}"
    await db.storage.from_("planogram-files").upload(
        storage_path, pdf_bytes, {"content-type": file.content_type or "application/pdf"}
    )
    file_url = db.storage.from_("planogram-files").get_public_url(storage_path)

    result = await ingestion_service.parse_planogram_pdf(pdf_bytes, brand_id)

    brand_repo = request.app.state.brand_repo
    guideline_id = await brand_repo.save_guideline(
        brand_id, file_url, result["raw_json"]
    )

    return IngestResponse(
        guideline_id=guideline_id,
        brand_id=brand_id,
        products_parsed=result["products_parsed"],
        parsed_products=result["parsed_products"],
    )
```

Save to `apps/backend/app/api/routes/ingest.py`.

- [ ] **Step 3: Write planogram route**

```python
# app/api/routes/planogram.py
from fastapi import APIRouter, Request
from app.models.schemas import GenerateRequest, GenerateResponse
from app.services import generation as gen_service

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
async def generate_planogram(body: GenerateRequest):
    planogram = await gen_service.generate_planogram(
        body.brand_id, body.store_format.value
    )
    return GenerateResponse(planogram=planogram)


@router.get("/{planogram_id}", response_model=GenerateResponse)
async def get_planogram(planogram_id: str, request: Request):
    planogram = await request.app.state.planogram_repo.get(planogram_id)
    return GenerateResponse(planogram=planogram)
```

Save to `apps/backend/app/api/routes/planogram.py`.

- [ ] **Step 4: Write audit route**

```python
# app/api/routes/audit.py
from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from app.models.schemas import AuditResponse
from app.services import audit as audit_service

router = APIRouter()


@router.post("/", response_model=AuditResponse)
async def run_audit(
    request: Request,
    planogram_id: str = Form(...),
    file: UploadFile = File(...),
):
    db = request.app.state.db
    planogram_repo = request.app.state.planogram_repo

    planogram = await planogram_repo.get(planogram_id)

    photo_bytes = await file.read()
    storage_path = f"{planogram_id}/{file.filename}"
    await db.storage.from_("shelf-photos").upload(
        storage_path, photo_bytes, {"content-type": file.content_type or "image/jpeg"}
    )
    photo_url = db.storage.from_("shelf-photos").get_public_url(storage_path)

    result = await audit_service.run_shelf_audit(planogram_id, photo_url, planogram)
    return AuditResponse(result=result)


@router.get("/{audit_id}", response_model=AuditResponse)
async def get_audit(audit_id: str, request: Request):
    result = await request.app.state.audit_repo.get(audit_id)
    return AuditResponse(result=result)
```

Save to `apps/backend/app/api/routes/audit.py`.

- [ ] **Step 5: Smoke test — start server**

```bash
cd /Users/adnan/Documents/shelfy/apps/backend
cp ../../.env.example .env  # fill in real keys before running
uv run uvicorn app.main:app --reload --port 8000
```

Expected: server starts, visit `http://localhost:8000/docs` to see Swagger UI with all routes.

- [ ] **Step 6: Run all tests**

```bash
cd /Users/adnan/Documents/shelfy/apps/backend
uv run pytest -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
cd /Users/adnan/Documents/shelfy
git add apps/backend/app/
git commit -m "feat: fastapi app with ingest, planogram, audit routes"
```

---

## Task 12: Dockerfile + Render config

**Files:**
- Create: `apps/backend/Dockerfile`
- Create: `apps/backend/.env.example`

- [ ] **Step 1: Write Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
RUN uv sync --no-dev

COPY app/ ./app/

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Save to `apps/backend/Dockerfile`.

- [ ] **Step 2: Write backend .env.example**

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

Save to `apps/backend/.env.example`.

- [ ] **Step 3: Render deployment**

In Render dashboard:
1. New Web Service → connect GitHub repo
2. Root directory: `apps/backend`
3. Build command: `docker build -t shelfy-backend .`
4. Start command: (from Dockerfile)
5. Add all env vars from `.env.example`

- [ ] **Step 4: Commit**

```bash
cd /Users/adnan/Documents/shelfy
git add apps/backend/Dockerfile apps/backend/.env.example
git commit -m "feat: dockerfile and render deploy config"
```

---

## Task 13: Frontend scaffold

**Files:**
- Create: `apps/frontend/` (Next.js project)

- [ ] **Step 1: Scaffold Next.js**

```bash
cd /Users/adnan/Documents/shelfy/apps
npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --no-src-dir \
  --import-alias "@/*"
```

- [ ] **Step 2: Install shadcn/ui**

```bash
cd /Users/adnan/Documents/shelfy/apps/frontend
npx shadcn@latest init
# Choose: Default style, Slate base color, CSS variables yes
npx shadcn@latest add button card badge progress separator tabs
```

- [ ] **Step 3: Install additional deps**

```bash
npm install @tanstack/react-query axios
```

- [ ] **Step 4: Create lib/api.ts**

```typescript
// lib/api.ts
const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export interface Product {
  id: string;
  brand_id: string;
  sku: string;
  name: string;
  category: string;
  brand_tier: string;
}

export interface PlanogramPosition {
  shelf_index: number;
  column_index: number;
  sku: string;
  facings: number;
  rationale?: string;
}

export interface Planogram {
  id: string;
  brand_id: string;
  store_format: "SMALL" | "MEDIUM" | "LARGE";
  status: string;
  generated_at: string;
  positions: PlanogramPosition[];
}

export interface Discrepancy {
  type: "MISSING" | "WRONG_POSITION" | "WRONG_FACINGS" | "UNEXPECTED";
  sku: string;
  expected_position?: string;
  detected_position?: string;
  severity: "HIGH" | "MEDIUM" | "LOW";
}

export interface AuditResult {
  id: string;
  planogram_id: string;
  photo_url: string;
  compliance_score: number;
  discrepancies: Discrepancy[];
  audited_at: string;
}

export async function ingestPlanogram(
  brandId: string,
  file: File
): Promise<{ guideline_id: string; brand_id: string; products_parsed: number; parsed_products: Product[] }> {
  const form = new FormData();
  form.append("brand_id", brandId);
  form.append("file", file);
  const res = await fetch(`${BACKEND}/ingest/planogram`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function generatePlanogram(
  brandId: string,
  storeFormat: "SMALL" | "MEDIUM" | "LARGE"
): Promise<{ planogram: Planogram }> {
  const res = await fetch(`${BACKEND}/planogram/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ brand_id: brandId, store_format: storeFormat }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getPlanogram(planogramId: string): Promise<{ planogram: Planogram }> {
  const res = await fetch(`${BACKEND}/planogram/${planogramId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function runAudit(
  planogramId: string,
  file: File
): Promise<{ result: AuditResult }> {
  const form = new FormData();
  form.append("planogram_id", planogramId);
  form.append("file", file);
  const res = await fetch(`${BACKEND}/audit/`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
```

Save to `apps/frontend/lib/api.ts`.

- [ ] **Step 5: Set up TanStack Query provider in layout**

```typescript
// app/providers.tsx
"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
```

Save to `apps/frontend/app/providers.tsx`.

- [ ] **Step 6: Update root layout**

```typescript
// app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Nav } from "@/components/nav";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Shelfy — Visual Merchandising OS",
  description: "AI-powered planogram generation and shelf audit",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <Nav />
          <main className="min-h-screen bg-gray-50">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
```

Save to `apps/frontend/app/layout.tsx`.

- [ ] **Step 7: Create nav component**

```typescript
// components/nav.tsx
import Link from "next/link";

export function Nav() {
  return (
    <nav className="border-b bg-white px-6 py-4 flex items-center gap-8">
      <span className="font-bold text-lg tracking-tight">Shelfy</span>
      <div className="flex gap-6 text-sm">
        <Link href="/ingest" className="text-gray-600 hover:text-gray-900">Ingest</Link>
        <Link href="/planogram" className="text-gray-600 hover:text-gray-900">Planogram</Link>
        <Link href="/audit" className="text-gray-600 hover:text-gray-900">Audit</Link>
      </div>
      <span className="ml-auto text-xs text-gray-400 bg-yellow-100 px-2 py-1 rounded">
        POC — Synthetic Data
      </span>
    </nav>
  );
}
```

Save to `apps/frontend/components/nav.tsx`.

- [ ] **Step 8: Create root page redirect**

```typescript
// app/page.tsx
import { redirect } from "next/navigation";
export default function Home() {
  redirect("/ingest");
}
```

Save to `apps/frontend/app/page.tsx`.

- [ ] **Step 9: Verify frontend starts**

```bash
cd /Users/adnan/Documents/shelfy/apps/frontend
npm run dev
```

Visit `http://localhost:3000` — should redirect to `/ingest` (404 page is fine at this point).

- [ ] **Step 10: Commit**

```bash
cd /Users/adnan/Documents/shelfy
git add apps/frontend/
git commit -m "feat: next.js frontend scaffold with nav and api client"
```

---

## Task 14: FileUpload component

**Files:**
- Create: `apps/frontend/components/file-upload.tsx`

- [ ] **Step 1: Write component**

```typescript
// components/file-upload.tsx
"use client";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

interface FileUploadProps {
  accept: Record<string, string[]>;
  label: string;
  onFile: (file: File) => void;
  disabled?: boolean;
}

export function FileUpload({ accept, label, onFile, disabled }: FileUploadProps) {
  const [fileName, setFileName] = useState<string | null>(null);

  const onDrop = useCallback(
    (files: File[]) => {
      if (files[0]) {
        setFileName(files[0].name);
        onFile(files[0]);
      }
    },
    [onFile]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxFiles: 1,
    disabled,
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
        ${isDragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"}
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
    >
      <input {...getInputProps()} />
      {fileName ? (
        <p className="text-sm text-gray-700">
          <span className="font-medium">Selected:</span> {fileName}
        </p>
      ) : (
        <p className="text-sm text-gray-500">
          {isDragActive ? "Drop here..." : label}
        </p>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Install react-dropzone**

```bash
cd /Users/adnan/Documents/shelfy/apps/frontend
npm install react-dropzone
```

- [ ] **Step 3: Commit**

```bash
cd /Users/adnan/Documents/shelfy
git add apps/frontend/components/file-upload.tsx apps/frontend/package.json apps/frontend/package-lock.json
git commit -m "feat: file upload drag-drop component"
```

---

## Task 15: ShelfGrid component

**Files:**
- Create: `apps/frontend/components/shelf-grid.tsx`

- [ ] **Step 1: Write component**

```typescript
// components/shelf-grid.tsx
import { PlanogramPosition } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

interface ShelfGridProps {
  positions: PlanogramPosition[];
  shelves?: number;
  columns?: number;
}

const TIER_COLORS: Record<string, string> = {
  hero: "bg-blue-100 border-blue-300 text-blue-800",
  secondary: "bg-gray-100 border-gray-300 text-gray-700",
  new: "bg-green-100 border-green-300 text-green-800",
};

export function ShelfGrid({ positions, shelves = 3, columns = 6 }: ShelfGridProps) {
  const grid: Record<string, PlanogramPosition> = {};
  for (const pos of positions) {
    grid[`${pos.shelf_index}-${pos.column_index}`] = pos;
  }

  const shelfLabels = ["Top", "Eye Level", "Bottom"];

  return (
    <div className="space-y-2">
      {Array.from({ length: shelves }, (_, si) => (
        <div key={si} className="flex items-center gap-2">
          <span className="text-xs text-gray-400 w-16 text-right">
            {shelfLabels[si] ?? `Shelf ${si}`}
          </span>
          <div className="flex gap-1 flex-1 bg-gray-200 p-1 rounded">
            {Array.from({ length: columns }, (_, ci) => {
              const pos = grid[`${si}-${ci}`];
              return (
                <div
                  key={ci}
                  className={`flex-1 min-h-[80px] border rounded p-1 text-xs flex flex-col justify-between
                    ${pos ? TIER_COLORS[pos.sku.split("-")[0]?.toLowerCase() ?? "secondary"] ?? TIER_COLORS.secondary : "bg-white border-gray-200"}`}
                >
                  {pos ? (
                    <>
                      <div className="font-mono font-bold">{pos.sku}</div>
                      <div className="text-gray-500 text-[10px] line-clamp-2">{pos.rationale}</div>
                      <div className="text-[10px]">×{pos.facings}</div>
                    </>
                  ) : (
                    <div className="text-gray-300 text-center mt-4">—</div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
```

Save to `apps/frontend/components/shelf-grid.tsx`.

- [ ] **Step 2: Commit**

```bash
cd /Users/adnan/Documents/shelfy
git add apps/frontend/components/shelf-grid.tsx
git commit -m "feat: shelf grid component for planogram visualization"
```

---

## Task 16: DiscrepancyList + AuditOverlay components

**Files:**
- Create: `apps/frontend/components/discrepancy-list.tsx`
- Create: `apps/frontend/components/audit-overlay.tsx`

- [ ] **Step 1: Write discrepancy-list.tsx**

```typescript
// components/discrepancy-list.tsx
import { Discrepancy } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

const SEVERITY_COLOR: Record<string, string> = {
  HIGH: "destructive",
  MEDIUM: "secondary",
  LOW: "outline",
};

const TYPE_LABEL: Record<string, string> = {
  MISSING: "Missing",
  WRONG_POSITION: "Wrong Position",
  WRONG_FACINGS: "Wrong Facings",
  UNEXPECTED: "Unexpected",
};

interface DiscrepancyListProps {
  discrepancies: Discrepancy[];
}

export function DiscrepancyList({ discrepancies }: DiscrepancyListProps) {
  const sorted = [...discrepancies].sort((a, b) => {
    const order = { HIGH: 0, MEDIUM: 1, LOW: 2 };
    return order[a.severity] - order[b.severity];
  });

  if (sorted.length === 0) {
    return (
      <p className="text-sm text-green-600 font-medium">
        No discrepancies — shelf is fully compliant.
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {sorted.map((d, i) => (
        <li key={i} className="flex items-start gap-3 p-3 bg-white border rounded-lg">
          <Badge variant={SEVERITY_COLOR[d.severity] as any}>{d.severity}</Badge>
          <div className="flex-1 text-sm">
            <span className="font-medium">{TYPE_LABEL[d.type]}</span>
            {" — "}
            <span className="font-mono">{d.sku}</span>
            {d.expected_position && (
              <div className="text-xs text-gray-500 mt-0.5">
                Expected: {d.expected_position}
                {d.detected_position ? ` · Found: ${d.detected_position}` : ""}
              </div>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}
```

Save to `apps/frontend/components/discrepancy-list.tsx`.

- [ ] **Step 2: Write audit-overlay.tsx**

```typescript
// components/audit-overlay.tsx
"use client";
import Image from "next/image";
import { AuditResult } from "@/lib/api";
import { Progress } from "@/components/ui/progress";

interface AuditOverlayProps {
  photoUrl: string;
  result: AuditResult;
}

export function AuditOverlay({ photoUrl, result }: AuditOverlayProps) {
  const score = Math.round(result.compliance_score);
  const scoreColor =
    score >= 80 ? "text-green-600" : score >= 60 ? "text-yellow-600" : "text-red-600";

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <span className={`text-4xl font-bold ${scoreColor}`}>{score}%</span>
        <div className="flex-1">
          <p className="text-sm text-gray-500 mb-1">Compliance Score</p>
          <Progress value={score} className="h-3" />
        </div>
      </div>
      <div className="relative rounded-lg overflow-hidden border">
        <img
          src={photoUrl}
          alt="Audited shelf"
          className="w-full object-cover"
          style={{ maxHeight: 480 }}
        />
        <div className="absolute top-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded">
          {result.discrepancies.length} issue{result.discrepancies.length !== 1 ? "s" : ""} found
        </div>
      </div>
    </div>
  );
}
```

Save to `apps/frontend/components/audit-overlay.tsx`.

- [ ] **Step 3: Commit**

```bash
cd /Users/adnan/Documents/shelfy
git add apps/frontend/components/
git commit -m "feat: discrepancy list and audit overlay components"
```

---

## Task 17: Ingest page

**Files:**
- Create: `apps/frontend/app/ingest/page.tsx`

- [ ] **Step 1: Write page**

```typescript
// app/ingest/page.tsx
"use client";
import { useState } from "react";
import { FileUpload } from "@/components/file-upload";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ingestPlanogram, type Product } from "@/lib/api";

const DEMO_BRAND_ID = "11111111-1111-1111-1111-111111111111";

export default function IngestPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    guideline_id: string;
    products_parsed: number;
    parsed_products: Product[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const data = await ingestPlanogram(DEMO_BRAND_ID, file);
      setResult(data);
    } catch (e: any) {
      setError(e.message ?? "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Ingest Planogram</h1>
        <p className="text-gray-500 text-sm mt-1">
          Upload your brand planogram PDF. We'll extract products and placement rules.
        </p>
      </div>

      <Card>
        <CardContent className="pt-6 space-y-4">
          <FileUpload
            accept={{ "application/pdf": [".pdf"], "image/*": [".png", ".jpg", ".jpeg"] }}
            label="Drop your planogram PDF or image here, or click to browse"
            onFile={setFile}
            disabled={loading}
          />
          <Button onClick={handleSubmit} disabled={!file || loading} className="w-full">
            {loading ? "Parsing planogram..." : "Upload & Parse"}
          </Button>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Parsed {result.products_parsed} products
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b">
                    <th className="pb-2 pr-4">SKU</th>
                    <th className="pb-2 pr-4">Name</th>
                    <th className="pb-2 pr-4">Tier</th>
                    <th className="pb-2">Category</th>
                  </tr>
                </thead>
                <tbody>
                  {result.parsed_products.map((p) => (
                    <tr key={p.sku} className="border-b last:border-0">
                      <td className="py-2 pr-4 font-mono">{p.sku}</td>
                      <td className="py-2 pr-4">{p.name}</td>
                      <td className="py-2 pr-4">{p.brand_tier}</td>
                      <td className="py-2">{p.category}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
```

Save to `apps/frontend/app/ingest/page.tsx`.

- [ ] **Step 2: Commit**

```bash
cd /Users/adnan/Documents/shelfy
git add apps/frontend/app/ingest/
git commit -m "feat: ingest page"
```

---

## Task 18: Planogram page

**Files:**
- Create: `apps/frontend/app/planogram/page.tsx`

- [ ] **Step 1: Write page**

```typescript
// app/planogram/page.tsx
"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ShelfGrid } from "@/components/shelf-grid";
import { generatePlanogram, type Planogram } from "@/lib/api";

const DEMO_BRAND_ID = "11111111-1111-1111-1111-111111111111";
const STORE_FORMATS = ["SMALL", "MEDIUM", "LARGE"] as const;

export default function PlanogramPage() {
  const [format, setFormat] = useState<"SMALL" | "MEDIUM" | "LARGE">("SMALL");
  const [loading, setLoading] = useState(false);
  const [planogram, setPlanogram] = useState<Planogram | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const data = await generatePlanogram(DEMO_BRAND_ID, format);
      setPlanogram(data.planogram);
      localStorage.setItem("shelfy_planogram_id", data.planogram.id);
    } catch (e: any) {
      setError(e.message ?? "Generation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-5xl mx-auto p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Generate Planogram</h1>
        <p className="text-gray-500 text-sm mt-1">
          AI generates a store-adapted shelf layout based on brand rules and sales data.
        </p>
      </div>

      <Card>
        <CardContent className="pt-6 flex gap-4 items-end">
          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700">Store Format</label>
            <div className="flex gap-2">
              {STORE_FORMATS.map((f) => (
                <Button
                  key={f}
                  variant={format === f ? "default" : "outline"}
                  size="sm"
                  onClick={() => setFormat(f)}
                >
                  {f}
                </Button>
              ))}
            </div>
          </div>
          <Button onClick={handleGenerate} disabled={loading}>
            {loading ? "Generating..." : "Generate Planogram"}
          </Button>
        </CardContent>
      </Card>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {planogram && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center justify-between">
              <span>{format} store — {planogram.positions.length} positions</span>
              <span className="text-xs font-mono text-gray-400">{planogram.id}</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ShelfGrid positions={planogram.positions} />
            <div className="mt-6 space-y-2">
              <h3 className="text-sm font-medium text-gray-700">Placement Rationale</h3>
              {planogram.positions.map((pos, i) => (
                <div key={i} className="text-xs text-gray-600 flex gap-2">
                  <span className="font-mono text-gray-400">
                    [{pos.shelf_index},{pos.column_index}]
                  </span>
                  <span className="font-mono font-medium">{pos.sku}</span>
                  <span>{pos.rationale}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
```

Save to `apps/frontend/app/planogram/page.tsx`.

- [ ] **Step 2: Commit**

```bash
cd /Users/adnan/Documents/shelfy
git add apps/frontend/app/planogram/
git commit -m "feat: planogram generation page"
```

---

## Task 19: Audit page

**Files:**
- Create: `apps/frontend/app/audit/page.tsx`

- [ ] **Step 1: Write page**

```typescript
// app/audit/page.tsx
"use client";
import { useState, useEffect } from "react";
import { FileUpload } from "@/components/file-upload";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AuditOverlay } from "@/components/audit-overlay";
import { DiscrepancyList } from "@/components/discrepancy-list";
import { runAudit, type AuditResult } from "@/lib/api";

export default function AuditPage() {
  const [planogramId, setPlanogramId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AuditResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem("shelfy_planogram_id");
    if (saved) setPlanogramId(saved);
  }, []);

  async function handleAudit() {
    if (!file || !planogramId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await runAudit(planogramId, file);
      setResult(data.result);
    } catch (e: any) {
      setError(e.message ?? "Audit failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Shelf Audit</h1>
        <p className="text-gray-500 text-sm mt-1">
          Upload a shelf photo to check compliance against the target planogram.
        </p>
      </div>

      <Card>
        <CardContent className="pt-6 space-y-4">
          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700">Planogram ID</label>
            <input
              className="w-full border rounded px-3 py-2 text-sm font-mono"
              value={planogramId}
              onChange={(e) => setPlanogramId(e.target.value)}
              placeholder="Paste planogram ID from the Planogram page"
            />
            {planogramId && (
              <p className="text-xs text-green-600">Using saved planogram ID</p>
            )}
          </div>
          <FileUpload
            accept={{ "image/*": [".jpg", ".jpeg", ".png", ".webp"] }}
            label="Drop shelf photo here, or click to browse"
            onFile={setFile}
            disabled={loading}
          />
          <Button
            onClick={handleAudit}
            disabled={!file || !planogramId || loading}
            className="w-full"
          >
            {loading ? "Auditing shelf..." : "Run Audit"}
          </Button>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <>
          <AuditOverlay photoUrl={result.photo_url} result={result} />
          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                {result.discrepancies.length} discrepanc
                {result.discrepancies.length === 1 ? "y" : "ies"} found
              </CardTitle>
            </CardHeader>
            <CardContent>
              <DiscrepancyList discrepancies={result.discrepancies} />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
```

Save to `apps/frontend/app/audit/page.tsx`.

- [ ] **Step 2: Commit**

```bash
cd /Users/adnan/Documents/shelfy
git add apps/frontend/app/audit/
git commit -m "feat: audit page with compliance result"
```

---

## Task 20: End-to-end smoke test

- [ ] **Step 1: Start backend**

```bash
cd /Users/adnan/Documents/shelfy/apps/backend
cp .env.example .env
# Fill in real SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY
uv run uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 2: Start frontend**

```bash
cd /Users/adnan/Documents/shelfy/apps/frontend
echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:8000" > .env.local
npm run dev
```

- [ ] **Step 3: Verify health endpoint**

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 4: Run all backend tests**

```bash
cd /Users/adnan/Documents/shelfy/apps/backend
uv run pytest -v
```

Expected: all tests pass.

- [ ] **Step 5: Manual flow test**

1. Open `http://localhost:3000/ingest`
2. Upload a PDF (any PDF works — backend will extract what it can)
3. Verify product table appears
4. Navigate to `/planogram` → select SMALL → Generate
5. Verify shelf grid renders with positions
6. Navigate to `/audit` → planogram ID auto-filled
7. Upload a photo → verify compliance score appears

- [ ] **Step 6: Final commit**

```bash
cd /Users/adnan/Documents/shelfy
git add .
git commit -m "feat: complete shelfy poc — ingest, generate, audit"
```

---

## Self-Review Notes

**Spec coverage check:**
- ✅ Planogram ingestion (Task 8 + 11 + 17)
- ✅ AI generation with MCP-style tool_use (Task 9 + 11 + 18)
- ✅ Shelf audit with Claude Vision (Task 10 + 11 + 19)
- ✅ Dashboard with 3 views (Tasks 17-19)
- ✅ Supabase Postgres + Storage (Tasks 4-6)
- ✅ Repository pattern for pluggability (Task 5-6)
- ✅ Render Dockerfile (Task 12)
- ✅ Seed data (Task 4)

**Type consistency verified:**
- `PlanogramPosition` fields match across schemas.py → repositories → components
- `AuditResult` fields match across schemas.py → repositories → api client → components
- `StoreFormat` enum values ("SMALL"|"MEDIUM"|"LARGE") consistent backend + frontend

**Known limitation:**
- `audit.py` severity for MISSING discrepancies defaults to HIGH (simplified — production would look up brand_tier per SKU)
- Chroma runs in-process (ephemeral on Render restarts — production needs Pinecone)
