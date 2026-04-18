from datetime import datetime, timezone
from supabase import AsyncClient
from app.repositories.base import PlanogramRepository
from app.models.schemas import Planogram, PlanogramPosition, StoreFormat


class SupabasePlanogramRepository(PlanogramRepository):
    def __init__(self, client: AsyncClient):
        self._db = client

    async def save(self, brand_id: str, store_format: str, positions: list[dict]) -> Planogram:
        pg_result = (
            await self._db.table("planograms")
            .insert({"brand_id": brand_id, "store_format": store_format, "status": "draft"})
            .execute()
        )
        row = pg_result.data[0]
        planogram_id = row["id"]

        if positions:
            pos_rows = [{"planogram_id": planogram_id, **p} for p in positions]
            await self._db.table("planogram_positions").insert(pos_rows).execute()

        return Planogram(
            id=planogram_id,
            brand_id=brand_id,
            store_format=StoreFormat(store_format),
            status=row["status"],
            generated_at=datetime.fromisoformat(row["generated_at"]),
            positions=[PlanogramPosition(**p) for p in positions],
        )

    async def get(self, planogram_id: str) -> Planogram:
        pg = (
            await self._db.table("planograms")
            .select("*")
            .eq("id", planogram_id)
            .execute()
        )
        if not pg.data:
            raise ValueError(f"Planogram not found: {planogram_id}")

        pos = (
            await self._db.table("planogram_positions")
            .select("*")
            .eq("planogram_id", planogram_id)
            .execute()
        )
        row = pg.data[0]
        return Planogram(
            id=row["id"],
            brand_id=row["brand_id"],
            store_format=StoreFormat(row["store_format"]),
            status=row["status"],
            generated_at=datetime.fromisoformat(row["generated_at"]),
            positions=[PlanogramPosition(**p) for p in pos.data],
        )
