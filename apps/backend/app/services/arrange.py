import asyncio
import base64
import json
import re
from io import BytesIO

import anthropic
import httpx
from ddgs import DDGS
from PIL import Image, ImageDraw, ImageFont

from app.config import settings
from app.models.schemas import Product

anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

TIER_COLORS = {
    "hero": "#EF4444",
    "secondary": "#3B82F6",
    "new": "#22C55E",
}

ARRANGE_PROMPT = """You are a retail shelf layout assistant. Analyze this empty shelf image carefully.

Identify every visible shelf row and slot. Map each slot to pixel coordinates.
Place these products across the shelf according to brand tier rules:
- hero: eye-level rows, centre slots
- new: row ends / secondary positions
- secondary: fill remaining slots

Products (SKU | Name | Tier):
{product_list}

IMPORTANT: Every x, y, w, h value must be within the image boundaries (0 to image width/height).
Do not place any product outside the visible shelf area.

Return ONLY valid JSON — an array where each element is:
{{"sku": "...", "name": "...", "tier": "...", "x": 10, "y": 20, "w": 80, "h": 120}}

x,y = top-left corner in pixels. w,h = width/height in pixels. Fill as many slots as products allow."""


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _shrink_for_claude(img: Image.Image) -> tuple[Image.Image, bytes]:
    """Resize image so JPEG bytes stay under 3.5 MB (Claude Vision 5 MB limit)."""
    MAX_BYTES = 3_500_000
    scale = 1.0
    while True:
        if scale < 1.0:
            w = max(1, int(img.width * scale))
            h = max(1, int(img.height * scale))
            candidate = img.resize((w, h), Image.LANCZOS)
        else:
            candidate = img
        buf = BytesIO()
        candidate.save(buf, format="JPEG", quality=85)
        data = buf.getvalue()
        if len(data) <= MAX_BYTES or scale < 0.2:
            return candidate, data
        scale *= 0.75


def _search_image_url(query: str) -> str | None:
    """Synchronous DuckDuckGo image search — run in executor."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=1))
        return results[0]["image"] if results else None
    except Exception:
        return None


async def _fetch_product_image(name: str, sku: str) -> Image.Image | None:
    """Fetch a product image: search DDG then download."""
    try:
        query = f"{name} product"
        loop = asyncio.get_event_loop()
        url = await loop.run_in_executor(None, _search_image_url, query)
        if not url:
            return None
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            r = await client.get(url)
            r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except Exception:
        return None


def _draw_fallback_card(
    draw: ImageDraw.ImageDraw,
    x: int, y: int, w: int, h: int,
    name: str, tier: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    """Draw a styled product card when no image is available."""
    r, g, b = _hex_to_rgb(TIER_COLORS.get(tier, TIER_COLORS["secondary"]))
    draw.rectangle([x, y, x + w, y + h], fill=(r, g, b, 60), outline=(r, g, b, 220), width=2)
    label = name[:28]
    try:
        bb = draw.textbbox((x + 4, y + 4), label, font=font)
        draw.rectangle([bb[0]-2, bb[1]-2, bb[2]+2, bb[3]+2], fill=(r, g, b, 200))
        draw.text((x + 4, y + 4), label, fill="white", font=font)
    except Exception:
        pass


async def render_arrangement(image_bytes: bytes, products: list[Product]) -> bytes:
    if not products:
        raise ValueError("No products found for this guideline")

    try:
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
    except Exception:
        raise ValueError("Invalid image file")

    # Resize for Claude Vision; draw_img is what Claude actually sees
    draw_img, claude_bytes = _shrink_for_claude(img)
    img_b64 = base64.standard_b64encode(claude_bytes).decode()
    iw, ih = draw_img.size

    product_list = "\n".join(f"{p.sku} | {p.name} | {p.brand_tier}" for p in products)
    prompt = ARRANGE_PROMPT.format(product_list=product_list)

    message = await anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}},
                {"type": "text", "text": prompt},
            ],
        }],
    )

    raw = re.sub(r"```(?:json)?", "", message.content[0].text).strip().rstrip("`").strip()
    try:
        placements = json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError(f"Claude returned invalid JSON: {raw[:300]}")

    # Clamp all coordinates to image bounds, drop placements entirely outside
    valid = []
    for p in placements:
        try:
            x, y, w, h = int(p["x"]), int(p["y"]), int(p["w"]), int(p["h"])
        except (KeyError, ValueError, TypeError):
            continue
        x = max(0, min(x, iw - 1))
        y = max(0, min(y, ih - 1))
        w = max(1, min(w, iw - x))
        h = max(1, min(h, ih - y))
        if w < 10 or h < 10:
            continue
        valid.append({**p, "x": x, "y": y, "w": w, "h": h})

    # Build product lookup: sku → Product
    product_map = {p.sku: p for p in products}

    # Fetch product images concurrently — dedupe by SKU
    unique_skus = {p["sku"]: p.get("name", p["sku"]) for p in valid}
    results = await asyncio.gather(
        *[_fetch_product_image(name, sku) for sku, name in unique_skus.items()],
        return_exceptions=True,
    )
    fetched = {
        sku: (r if isinstance(r, Image.Image) else None)
        for sku, r in zip(unique_skus.keys(), results)
    }

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
    except Exception:
        font = ImageFont.load_default()

    # Draw on the same image Claude saw (correct coordinate space)
    canvas = draw_img.convert("RGBA")
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for p in valid:
        x, y, w, h = p["x"], p["y"], p["w"], p["h"]
        tier = p.get("tier", "secondary").lower()
        sku = p.get("sku", "")
        name = p.get("name", sku)
        prod_img = fetched.get(sku)

        if prod_img is not None:
            # Paste actual product image, scaled to fit the slot
            thumb = prod_img.resize((w, h), Image.LANCZOS)
            overlay.paste(thumb, (x, y), thumb)
            # Thin border
            r, g, b = _hex_to_rgb(TIER_COLORS.get(tier, TIER_COLORS["secondary"]))
            draw.rectangle([x, y, x + w - 1, y + h - 1], outline=(r, g, b, 220), width=2)
        else:
            _draw_fallback_card(draw, x, y, w, h, name, tier, font)

    result = Image.alpha_composite(canvas, overlay).convert("RGB")
    out = BytesIO()
    result.save(out, format="PNG")
    return out.getvalue()
