const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export interface Product {
  id: string;
  brand_id: string;
  sku: string;
  name: string;
  category: string;
  brand_tier: string;
}

export interface PlanogramPosition {
  shelf_index: number;
  column_index: number;
  sku: string;
  facings: number;
  rationale?: string;
}

export interface Planogram {
  id: string;
  brand_id: string;
  store_format: "SMALL" | "MEDIUM" | "LARGE";
  status: string;
  generated_at: string;
  positions: PlanogramPosition[];
}

export interface Discrepancy {
  type: "MISSING" | "WRONG_POSITION" | "WRONG_FACINGS" | "UNEXPECTED";
  sku: string;
  expected_position?: string;
  detected_position?: string;
  severity: "HIGH" | "MEDIUM" | "LOW";
}

export interface AuditResult {
  id: string;
  planogram_id: string;
  photo_url: string;
  compliance_score: number;
  discrepancies: Discrepancy[];
  audited_at: string;
}

export async function ingestPlanogram(
  brandId: string,
  file: File
): Promise<{ guideline_id: string; brand_id: string; products_parsed: number; parsed_products: Product[] }> {
  const form = new FormData();
  form.append("brand_id", brandId);
  form.append("file", file);
  const res = await fetch(`${BACKEND}/ingest/planogram`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function generatePlanogram(
  brandId: string,
  storeFormat: "SMALL" | "MEDIUM" | "LARGE"
): Promise<{ planogram: Planogram }> {
  const res = await fetch(`${BACKEND}/planogram/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ brand_id: brandId, store_format: storeFormat }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getPlanogram(planogramId: string): Promise<{ planogram: Planogram }> {
  const res = await fetch(`${BACKEND}/planogram/${planogramId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listPlanograms(): Promise<{
  id: string; brand_id: string; store_format: string; status: string; generated_at: string; display_name: string;
}[]> {
  const res = await fetch(`${BACKEND}/planogram/`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listGuidelines(): Promise<{
  id: string; brand_id: string; raw_file_url: string; created_at: string; products_count: number; display_name: string;
}[]> {
  const res = await fetch(`${BACKEND}/ingest/guidelines`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function runAudit(
  planogramId: string,
  file: File
): Promise<{ result: AuditResult }> {
  const form = new FormData();
  form.append("planogram_id", planogramId);
  form.append("file", file);
  const res = await fetch(`${BACKEND}/audit/`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listGuidelineProducts(guidelineId: string): Promise<{ products: Product[] }> {
  const res = await fetch(`${BACKEND}/ingest/guidelines/${guidelineId}/products`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function arrangeShelf(guidelineId: string, file: File): Promise<{ image_b64: string }> {
  const form = new FormData();
  form.append("guideline_id", guidelineId);
  form.append("file", file);
  const res = await fetch(`${BACKEND}/arrange/`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
