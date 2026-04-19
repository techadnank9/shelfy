import json
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
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw.strip())

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
