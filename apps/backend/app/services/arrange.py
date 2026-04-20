import base64
import json
import re
from io import BytesIO

import anthropic
from PIL import Image, ImageDraw, ImageFont

from app.config import settings
from app.models.schemas import Product

anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

TIER_COLORS = {
    "hero": "#EF4444",
    "secondary": "#3B82F6",
    "new": "#22C55E",
}

ARRANGE_PROMPT = """You are a retail shelf layout assistant. Analyze this empty shelf image.

Identify all shelf rows and columns (slots). Then place these products on the shelf according to their brand tier (hero products at eye level, new products at ends).

Products (SKU | Name | Tier):
{product_list}

Return ONLY valid JSON — an array of placements:
[{{"sku": "...", "name": "...", "tier": "...", "x": 10, "y": 20, "w": 80, "h": 60}}, ...]

x, y, w, h are pixel coordinates on the image. Cover all visible shelf slots."""


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


async def render_arrangement(image_bytes: bytes, products: list[Product]) -> bytes:
    if not products:
        raise ValueError("No products found for this guideline")

    try:
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
    except Exception:
        raise ValueError("Invalid image file")

    # Detect format for Claude Vision
    fmt = img.format  # e.g., "PNG", "JPEG", "WEBP", None
    mime_map = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp", "GIF": "image/gif"}
    media_type = mime_map.get(fmt or "", "")
    if not media_type:
        # Re-encode to JPEG for unknown formats
        buf = BytesIO()
        img.save(buf, format="JPEG")
        image_bytes = buf.getvalue()
        media_type = "image/jpeg"

    img_b64 = base64.standard_b64encode(image_bytes).decode()

    product_list = "\n".join(
        f"{p.sku} | {p.name} | {p.brand_tier}" for p in products
    )
    prompt = ARRANGE_PROMPT.format(product_list=product_list)

    message = await anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": img_b64},
                },
                {"type": "text", "text": prompt},
            ],
        }],
    )

    raw = message.content[0].text
    # Strip markdown code fences if present
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    try:
        placements = json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError(f"Claude could not parse shelf layout. Raw response: {raw[:200]}")

    draw = ImageDraw.Draw(img, "RGBA")
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
        small_font = font
    except Exception:
        font = ImageFont.load_default()
        small_font = font

    for p in placements:
        try:
            x, y, w, h = int(p["x"]), int(p["y"]), int(p["w"]), int(p["h"])
        except (KeyError, ValueError, TypeError):
            continue
        tier = p.get("tier", "secondary").lower()
        hex_color = TIER_COLORS.get(tier, TIER_COLORS["secondary"])
        r, g, b = _hex_to_rgb(hex_color)

        # Semi-transparent fill
        draw.rectangle([x, y, x + w, y + h], fill=(r, g, b, 80), outline=(r, g, b, 255), width=2)

        # Label background
        label = p.get("name", p.get("sku", ""))[:30]
        bbox = draw.textbbox((x + 4, y + 4), label, font=small_font)
        draw.rectangle([bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2], fill=(r, g, b, 200))
        draw.text((x + 4, y + 4), label, fill="white", font=small_font)

    out = BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()
