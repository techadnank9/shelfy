"use client";
import { useState, useEffect } from "react";
import { FileUpload } from "@/components/file-upload";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ComplianceDiagram } from "@/components/compliance-diagram";
import { DiscrepancyList } from "@/components/discrepancy-list";
import { runAudit, getPlanogram, type AuditResult, type Planogram } from "@/lib/api";
import { IngestSidebar } from "@/components/ingest-sidebar";

export default function AuditPage() {
  const [planogramId, setPlanogramId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AuditResult | null>(null);
  const [planogram, setPlanogram] = useState<Planogram | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem("shelfy_planogram_id");
    if (saved) setPlanogramId(saved);
  }, []);

  async function handleAudit() {
    if (!file || !planogramId) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setPlanogram(null);
    try {
      const [auditData, planogramData] = await Promise.all([
        runAudit(planogramId, file),
        getPlanogram(planogramId),
      ]);
      setResult(auditData.result);
      setPlanogram(planogramData.planogram);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Audit failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <IngestSidebar selectedPlanogramId={planogramId} onSelectPlanogram={setPlanogramId} />
      <div className="flex-1 overflow-y-auto">
    <div className="max-w-4xl mx-auto p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Shelf Audit</h1>
        <p className="text-gray-500 text-sm mt-1">
          Upload a shelf photo — Claude Vision analyzes it and generates a compliance diagram.
        </p>
      </div>

      <Card>
        <CardContent className="pt-6 space-y-4">
          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700">Planogram ID</label>
            <input
              className="w-full border rounded px-3 py-2 text-sm font-mono"
              value={planogramId}
              onChange={(e) => setPlanogramId(e.target.value)}
              placeholder="Paste planogram ID from the Planogram page"
            />
            {planogramId && (
              <p className="text-xs text-green-600">Planogram ID loaded</p>
            )}
          </div>
          <FileUpload
            accept={{ "image/*": [".jpg", ".jpeg", ".png", ".webp"] }}
            label="Drop shelf photo here, or click to browse"
            onFile={setFile}
            disabled={loading}
          />
          <Button
            onClick={handleAudit}
            disabled={!file || !planogramId || loading}
            className="w-full"
          >
            {loading ? "Analyzing shelf..." : "Run Audit"}
          </Button>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </CardContent>
      </Card>

      {result && planogram && (
        <>
          <div>
            <h2 className="text-lg font-semibold mb-3">Compliance Diagram</h2>
            <ComplianceDiagram
              planogram={planogram}
              discrepancies={result.discrepancies}
              complianceScore={result.compliance_score}
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                {result.discrepancies.length} discrepanc
                {result.discrepancies.length === 1 ? "y" : "ies"} found
              </CardTitle>
            </CardHeader>
            <CardContent>
              <DiscrepancyList discrepancies={result.discrepancies} />
            </CardContent>
          </Card>
        </>
      )}
    </div>
      </div>
    </div>
  );
}
