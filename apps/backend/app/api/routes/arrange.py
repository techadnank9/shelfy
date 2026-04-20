import base64
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from app.models.schemas import Product
from app.services import arrange as arrange_service

router = APIRouter()


@router.post("/", response_model=dict)
async def arrange_shelf(
    request: Request,
    guideline_id: str = Form(...),
    file: UploadFile = File(...),
):
    db = request.app.state.db
    result = (
        await db.table("brand_guidelines")
        .select("parsed_json")
        .eq("id", guideline_id)
        .single()
        .execute()
    )
    pj = result.data.get("parsed_json") or {}
    raw_products = pj.get("products", [])

    if not raw_products:
        raise HTTPException(status_code=400, detail="No products found for this guideline")

    products = [
        Product(
            id=f"synthetic-{p['sku']}",
            brand_id=guideline_id,
            sku=p["sku"],
            name=p["name"],
            category=p.get("category", "skincare"),
            brand_tier=p.get("brand_tier", "secondary"),
        )
        for p in raw_products
    ]

    image_bytes = await file.read()

    try:
        png_bytes = await arrange_service.render_arrangement(image_bytes, products)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    image_b64 = base64.standard_b64encode(png_bytes).decode()
    return {"image_b64": image_b64}
