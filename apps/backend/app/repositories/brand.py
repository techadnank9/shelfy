from supabase import AsyncClient
from app.repositories.base import BrandRepository, SalesRepository
from app.models.schemas import Product, SalesData, StoreFormat


class SupabaseBrandRepository(BrandRepository):
    def __init__(self, client: AsyncClient):
        self._db = client

    async def get_guidelines(self, brand_id: str) -> dict:
        result = (
            await self._db.table("brand_guidelines")
            .select("parsed_json")
            .eq("brand_id", brand_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if not result.data:
            raise ValueError(f"No guidelines found for brand {brand_id}")
        return result.data[0]["parsed_json"]

    async def get_product_catalog(self, brand_id: str, category: str) -> list[Product]:
        result = (
            await self._db.table("products")
            .select("*")
            .eq("brand_id", brand_id)
            .eq("category", category)
            .execute()
        )
        return [Product(**row) for row in result.data]

    async def save_guideline(self, brand_id: str, file_url: str, parsed_json: dict) -> str:
        result = (
            await self._db.table("brand_guidelines")
            .insert({"brand_id": brand_id, "raw_file_url": file_url, "parsed_json": parsed_json})
            .execute()
        )
        return result.data[0]["id"]


class SupabaseSalesRepository(SalesRepository):
    def __init__(self, client: AsyncClient):
        self._db = client

    async def get_store_sales(self, brand_id: str, store_format: str) -> list[SalesData]:
        result = (
            await self._db.table("sales_data")
            .select("*")
            .eq("brand_id", brand_id)
            .eq("store_format", store_format)
            .execute()
        )
        return [SalesData(**row) for row in result.data]
