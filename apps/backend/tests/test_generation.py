import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.generation import generate_planogram
from app.models.schemas import Planogram, StoreFormat


@pytest.mark.asyncio
async def test_generate_planogram_returns_planogram():
    mock_positions = [
        {"shelf_index": 0, "column_index": 0, "sku": "LS-001",
         "facings": 2, "rationale": "Top seller, eye level"},
        {"shelf_index": 0, "column_index": 1, "sku": "LS-002",
         "facings": 2, "rationale": "Hero product, eye level"},
    ]
    mock_planogram = Planogram(
        id="pg-test",
        brand_id="b1",
        store_format=StoreFormat.SMALL,
        status="draft",
        generated_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        positions=[],
    )

    with patch("app.services.generation.run_generation_agent",
               new_callable=AsyncMock, return_value=mock_positions):
        with patch("app.services.generation.planogram_repo") as mock_repo:
            mock_repo.save = AsyncMock(return_value=mock_planogram)
            result = await generate_planogram("b1", "SMALL")

    assert isinstance(result, Planogram)
    assert result.id == "pg-test"
