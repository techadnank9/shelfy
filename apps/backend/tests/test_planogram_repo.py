import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from app.repositories.planogram import SupabasePlanogramRepository
from app.models.schemas import Planogram, StoreFormat


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    tm = MagicMock()
    tm.select = MagicMock(return_value=tm)
    tm.insert = MagicMock(return_value=tm)
    tm.eq = MagicMock(return_value=tm)
    tm.execute = AsyncMock()
    client.table = MagicMock(return_value=tm)
    return client, tm


@pytest.mark.asyncio
async def test_save_planogram_returns_planogram(mock_supabase):
    client, tm = mock_supabase
    now = datetime.now(timezone.utc).isoformat()
    tm.execute.side_effect = [
        MagicMock(data=[{"id": "pg-1", "brand_id": "b1",
                         "store_format": "SMALL", "status": "draft",
                         "generated_at": now}]),
        MagicMock(data=[]),  # positions insert
    ]
    repo = SupabasePlanogramRepository(client)
    planogram = await repo.save("b1", "SMALL", [
        {"shelf_index": 0, "column_index": 0, "sku": "LS-001", "facings": 2, "rationale": "top seller"}
    ])
    assert planogram.id == "pg-1"
    assert planogram.store_format == StoreFormat.SMALL


@pytest.mark.asyncio
async def test_get_planogram_raises_when_missing(mock_supabase):
    client, tm = mock_supabase
    tm.execute.return_value = MagicMock(data=[])
    repo = SupabasePlanogramRepository(client)
    with pytest.raises(ValueError, match="Planogram not found"):
        await repo.get("nonexistent-id")
