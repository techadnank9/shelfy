from datetime import datetime
from supabase import AsyncClient
from app.repositories.base import AuditRepository
from app.models.schemas import AuditResult, Discrepancy, DiscrepancyType, Severity


class SupabaseAuditRepository(AuditRepository):
    def __init__(self, client: AsyncClient):
        self._db = client

    async def save(self, planogram_id: str, photo_url: str,
                   compliance_score: float, discrepancies: list[dict]) -> AuditResult:
        audit = (
            await self._db.table("audit_results")
            .insert({
                "planogram_id": planogram_id,
                "photo_url": photo_url,
                "compliance_score": compliance_score,
            })
            .execute()
        )
        audit_id = audit.data[0]["id"]

        if discrepancies:
            disc_rows = [{"audit_id": audit_id, **d} for d in discrepancies]
            await self._db.table("discrepancies").insert(disc_rows).execute()

        return AuditResult(
            id=audit_id,
            planogram_id=planogram_id,
            photo_url=photo_url,
            compliance_score=compliance_score,
            discrepancies=[
                Discrepancy(
                    type=DiscrepancyType(d["type"]),
                    sku=d["sku"],
                    expected_position=d.get("expected_position"),
                    detected_position=d.get("detected_position"),
                    severity=Severity(d["severity"]),
                )
                for d in discrepancies
            ],
            audited_at=datetime.fromisoformat(audit.data[0]["audited_at"]),
        )

    async def get(self, audit_id: str) -> AuditResult:
        audit = (
            await self._db.table("audit_results")
            .select("*")
            .eq("id", audit_id)
            .execute()
        )
        if not audit.data:
            raise ValueError(f"Audit not found: {audit_id}")

        discs = (
            await self._db.table("discrepancies")
            .select("*")
            .eq("audit_id", audit_id)
            .execute()
        )
        row = audit.data[0]
        return AuditResult(
            id=row["id"],
            planogram_id=row["planogram_id"],
            photo_url=row["photo_url"],
            compliance_score=row["compliance_score"],
            discrepancies=[
                Discrepancy(
                    type=DiscrepancyType(d["type"]),
                    sku=d["sku"],
                    expected_position=d.get("expected_position"),
                    detected_position=d.get("detected_position"),
                    severity=Severity(d["severity"]),
                )
                for d in discs.data
            ],
            audited_at=datetime.fromisoformat(row["audited_at"]),
        )
