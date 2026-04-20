import uuid
from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from app.models.schemas import IngestResponse
from app.services import ingestion as ingestion_service

router = APIRouter()


@router.get("/guidelines", response_model=list[dict])
async def list_guidelines(request: Request):
    result = (
        await request.app.state.db.table("brand_guidelines")
        .select("id, brand_id, raw_file_url, created_at, parsed_json")
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )
    seen = set()
    rows = []
    for r in result.data:
        if r["brand_id"] in seen:
            continue
        seen.add(r["brand_id"])
        pj = r.get("parsed_json") or {}
        rows.append({
            "id": r["id"],
            "brand_id": r["brand_id"],
            "raw_file_url": r["raw_file_url"],
            "created_at": r["created_at"],
            "products_count": len(pj.get("products", [])),
        })
    return rows


@router.get("/guidelines/{guideline_id}/products", response_model=dict)
async def get_guideline_products(guideline_id: str, request: Request):
    result = (
        await request.app.state.db.table("brand_guidelines")
        .select("parsed_json")
        .eq("id", guideline_id)
        .single()
        .execute()
    )
    if result.data is None:
        raise HTTPException(status_code=404, detail="Guideline not found")
    pj = result.data.get("parsed_json") or {}
    return {"products": pj.get("products", [])}


@router.post("/planogram", response_model=IngestResponse)
async def ingest_planogram(
    request: Request,
    brand_id: str = Form(...),
    file: UploadFile = File(...),
):
    pdf_bytes = await file.read()

    # Upload raw file to Supabase Storage
    db = request.app.state.db
    storage_path = f"{brand_id}/{uuid.uuid4()}_{file.filename}"
    await db.storage.from_("planogram-files").upload(
        storage_path, pdf_bytes, {"content-type": file.content_type or "application/pdf"}
    )
    file_url = await db.storage.from_("planogram-files").get_public_url(storage_path)

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
