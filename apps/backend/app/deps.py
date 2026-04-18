from functools import lru_cache
from supabase import AsyncClient, create_async_client
from app.config import settings


@lru_cache
def get_settings():
    return settings


async def get_supabase() -> AsyncClient:
    return await create_async_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )
