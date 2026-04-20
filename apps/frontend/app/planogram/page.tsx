"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ShelfGrid } from "@/components/shelf-grid";
import { generatePlanogram, type Planogram } from "@/lib/api";

const DEMO_BRAND_ID = "11111111-1111-1111-1111-111111111111";
const STORE_FORMATS = ["SMALL", "MEDIUM", "LARGE"] as const;

export default function PlanogramPage() {
  const [format, setFormat] = useState<"SMALL" | "MEDIUM" | "LARGE">("SMALL");
  const [loading, setLoading] = useState(false);
  const [planogram, setPlanogram] = useState<Planogram | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const data = await generatePlanogram(DEMO_BRAND_ID, format);
      setPlanogram(data.planogram);
      localStorage.setItem("shelfy_planogram_id", data.planogram.id);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-5xl mx-auto p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Generate Planogram</h1>
        <p className="text-gray-500 text-sm mt-1">
          AI generates a store-adapted shelf layout based on brand rules and sales data.
        </p>
      </div>

      <Card>
        <CardContent className="pt-6 flex gap-4 items-end">
          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700">Store Format</label>
            <div className="flex gap-2">
              {STORE_FORMATS.map((f) => (
                <Button
                  key={f}
                  variant={format === f ? "default" : "outline"}
                  size="sm"
                  onClick={() => setFormat(f)}
                >
                  {f}
                </Button>
              ))}
            </div>
          </div>
          <Button onClick={handleGenerate} disabled={loading}>
            {loading ? "Generating..." : "Generate Planogram"}
          </Button>
        </CardContent>
      </Card>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {planogram && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center justify-between">
              <span>{format.charAt(0) + format.slice(1).toLowerCase()} store — {planogram.positions.length} positions</span>
              <span className="text-xs text-gray-400">{new Date(planogram.generated_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ShelfGrid positions={planogram.positions} />
            <div className="mt-6 space-y-2">
              <h3 className="text-sm font-medium text-gray-700">Placement Rationale</h3>
              {planogram.positions.map((pos, i) => (
                <div key={i} className="text-xs text-gray-600 flex gap-2">
                  <span className="font-mono text-gray-400">
                    [{pos.shelf_index},{pos.column_index}]
                  </span>
                  <span className="font-mono font-medium">{pos.sku}</span>
                  <span>{pos.rationale}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
