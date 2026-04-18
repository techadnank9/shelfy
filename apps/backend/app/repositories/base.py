from abc import ABC, abstractmethod
from app.models.schemas import Product, Planogram, AuditResult, SalesData


class BrandRepository(ABC):
    @abstractmethod
    async def get_guidelines(self, brand_id: str) -> dict: ...

    @abstractmethod
    async def get_product_catalog(self, brand_id: str, category: str) -> list[Product]: ...

    @abstractmethod
    async def save_guideline(self, brand_id: str, file_url: str, parsed_json: dict) -> str: ...


class SalesRepository(ABC):
    @abstractmethod
    async def get_store_sales(self, brand_id: str, store_format: str) -> list[SalesData]: ...


class PlanogramRepository(ABC):
    @abstractmethod
    async def save(self, brand_id: str, store_format: str, positions: list[dict]) -> Planogram: ...

    @abstractmethod
    async def get(self, planogram_id: str) -> Planogram: ...


class AuditRepository(ABC):
    @abstractmethod
    async def save(self, planogram_id: str, photo_url: str,
                   compliance_score: float, discrepancies: list[dict]) -> AuditResult: ...

    @abstractmethod
    async def get(self, audit_id: str) -> AuditResult: ...
