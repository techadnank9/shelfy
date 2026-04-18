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
                "severity": Severity.HIGH,
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
