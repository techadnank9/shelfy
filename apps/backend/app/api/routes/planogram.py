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
