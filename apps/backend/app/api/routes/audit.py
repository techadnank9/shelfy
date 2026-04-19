import uuid
from fastapi import APIRouter, UploadFile, File, Form, Request
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
    storage_path = f"{planogram_id}/{uuid.uuid4()}_{file.filename}"
    await db.storage.from_("shelf-photos").upload(
        storage_path, photo_bytes, {"content-type": file.content_type or "image/jpeg"}
    )
    photo_url = await db.storage.from_("shelf-photos").get_public_url(storage_path)

    result = await audit_service.run_shelf_audit(planogram_id, photo_url, planogram)
    return AuditResponse(result=result)


@router.get("/{audit_id}", response_model=AuditResponse)
async def get_audit(audit_id: str, request: Request):
    result = await request.app.state.audit_repo.get(audit_id)
    return AuditResponse(result=result)
