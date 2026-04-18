import pytest
from unittest.mock import AsyncMock, MagicMock
from app.repositories.brand import SupabaseBrandRepository
from app.models.schemas import Product


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    table_mock = MagicMock()
    table_mock.select = MagicMock(return_value=table_mock)
    table_mock.insert = MagicMock(return_value=table_mock)
    table_mock.eq = MagicMock(return_value=table_mock)
    table_mock.order = MagicMock(return_value=table_mock)
    table_mock.limit = MagicMock(return_value=table_mock)
    table_mock.execute = AsyncMock()
    client.table = MagicMock(return_value=table_mock)
    return client, table_mock


@pytest.mark.asyncio
async def test_get_product_catalog_returns_products(mock_supabase):
    client, table_mock = mock_supabase
    table_mock.execute.return_value = MagicMock(data=[
        {"id": "p1", "brand_id": "b1", "sku": "LS-001",
         "name": "Vitamin C Serum", "category": "skincare", "brand_tier": "hero"},
    ])
    repo = SupabaseBrandRepository(client)
    products = await repo.get_product_catalog("b1", "skincare")
    assert len(products) == 1
    assert products[0].sku == "LS-001"
    assert isinstance(products[0], Product)


@pytest.mark.asyncio
async def test_get_guidelines_raises_when_missing(mock_supabase):
    client, table_mock = mock_supabase
    table_mock.execute.return_value = MagicMock(data=[])
    repo = SupabaseBrandRepository(client)
    with pytest.raises(ValueError, match="No guidelines"):
        await repo.get_guidelines("b1")
