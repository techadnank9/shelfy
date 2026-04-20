"use client";
import { useState } from "react";
import { FileUpload } from "@/components/file-upload";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ingestPlanogram, type Product } from "@/lib/api";

const DEMO_BRAND_ID = "11111111-1111-1111-1111-111111111111";

export default function IngestPage() {
  const [file, setFile] = useState<File | null>(null);
  const [brandName, setBrandName] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    guideline_id: string;
    products_parsed: number;
    parsed_products: Product[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const data = await ingestPlanogram(DEMO_BRAND_ID, file, brandName || undefined);
      setResult(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Ingest Planogram</h1>
        <p className="text-gray-500 text-sm mt-1">
          Upload your brand planogram PDF. We&apos;ll extract products and placement rules.
        </p>
      </div>

      <Card>
        <CardContent className="pt-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Brand Name</label>
            <input
              type="text"
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
              placeholder="e.g. Jo Malone, Lumiskin"
              value={brandName}
              onChange={(e) => setBrandName(e.target.value)}
              disabled={loading}
            />
          </div>
          <FileUpload
            accept={{ "application/pdf": [".pdf"], "image/*": [".png", ".jpg", ".jpeg"] }}
            label="Drop your planogram PDF or image here, or click to browse"
            onFile={setFile}
            disabled={loading}
          />
          <Button onClick={handleSubmit} disabled={!file || loading} className="w-full">
            {loading ? "Parsing planogram..." : "Upload & Parse"}
          </Button>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Parsed {result.products_parsed} products
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b">
                    <th className="pb-2 pr-4">SKU</th>
                    <th className="pb-2 pr-4">Name</th>
                    <th className="pb-2 pr-4">Tier</th>
                    <th className="pb-2">Category</th>
                  </tr>
                </thead>
                <tbody>
                  {result.parsed_products.map((p, i) => (
                    <tr key={`${p.sku}-${i}`} className="border-b last:border-0">
                      <td className="py-2 pr-4 font-mono">{p.sku}</td>
                      <td className="py-2 pr-4">{p.name}</td>
                      <td className="py-2 pr-4">{p.brand_tier}</td>
                      <td className="py-2">{p.category}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
