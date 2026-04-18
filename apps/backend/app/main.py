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
