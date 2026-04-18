import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.audit import run_shelf_audit
from app.models.schemas import AuditResult, StoreFormat, Planogram, PlanogramPosition


@pytest.fixture
def sample_planogram():
    from datetime import datetime, timezone
    return Planogram(
        id="pg-1",
        brand_id="b1",
        store_format=StoreFormat.SMALL,
        status="draft",
        generated_at=datetime.now(timezone.utc),
        positions=[
            PlanogramPosition(shelf_index=1, column_index=0, sku="LS-001", facings=2,
                              rationale="hero"),
            PlanogramPosition(shelf_index=1, column_index=1, sku="LS-002", facings=2,
                              rationale="hero"),
        ],
    )


@pytest.mark.asyncio
async def test_run_shelf_audit_returns_result(sample_planogram):
    mock_vision_response = MagicMock()
    mock_vision_response.content = [MagicMock(text='''{
        "detected_products": [
            {"sku": "LS-001", "shelf_index": 1, "column_index": 0, "facings": 2, "confidence": 0.92},
            {"sku": "LS-003", "shelf_index": 1, "column_index": 1, "facings": 1, "confidence": 0.85}
        ]
    }''')]

    mock_audit_result = MagicMock(spec=AuditResult)
    mock_audit_result.compliance_score = 50.0

    with patch("app.services.audit.anthropic_client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_vision_response)
        with patch("app.services.audit.audit_repo") as mock_repo:
            mock_repo.save = AsyncMock(return_value=mock_audit_result)
            result = await run_shelf_audit("pg-1", "https://example.com/shelf.jpg",
                                           sample_planogram)

    assert result.compliance_score == 50.0
