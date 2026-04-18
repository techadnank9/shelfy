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
