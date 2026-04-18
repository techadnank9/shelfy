from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class StoreFormat(str, Enum):
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"


class DiscrepancyType(str, Enum):
    MISSING = "MISSING"
    WRONG_POSITION = "WRONG_POSITION"
    WRONG_FACINGS = "WRONG_FACINGS"
    UNEXPECTED = "UNEXPECTED"


class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Product(BaseModel):
    id: str
    brand_id: str
    sku: str
    name: str
    category: str
    brand_tier: str  # hero | secondary | new


class SalesData(BaseModel):
    sku: str
    brand_id: str
    store_format: StoreFormat
    units_sold: int
    period: str = "Q4-2024"


class PlanogramPosition(BaseModel):
    shelf_index: int
    column_index: int
    sku: str
    facings: int
    rationale: Optional[str] = None


class Planogram(BaseModel):
    id: str
    brand_id: str
    store_format: StoreFormat
    status: str
    generated_at: datetime
    positions: list[PlanogramPosition] = []


class Discrepancy(BaseModel):
    type: DiscrepancyType
    sku: str
    expected_position: Optional[str] = None
    detected_position: Optional[str] = None
    severity: Severity


class AuditResult(BaseModel):
    id: str
    planogram_id: str
    photo_url: str
    compliance_score: float
    discrepancies: list[Discrepancy] = []
    audited_at: datetime


# ── Request / Response ────────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    guideline_id: str
    brand_id: str
    products_parsed: int
    parsed_products: list[dict]


class GenerateRequest(BaseModel):
    brand_id: str
    store_format: StoreFormat


class GenerateResponse(BaseModel):
    planogram: Planogram


class AuditResponse(BaseModel):
    result: AuditResult
