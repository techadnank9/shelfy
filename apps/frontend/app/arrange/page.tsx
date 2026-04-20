"use client";
import { useEffect, useState } from "react";
import { FileUpload } from "@/components/file-upload";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { arrangeShelf, listGuidelines } from "@/lib/api";

interface Guideline {
  id: string;
  brand_id: string;
  created_at: string;
  products_count: number;
  display_name: string;
}

export default function ArrangePage() {
  const [guidelines, setGuidelines] = useState<Guideline[]>([]);
  const [guidelineId, setGuidelineId] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [imageB64, setImageB64] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listGuidelines().then((gs) => {
      setGuidelines(gs);
      if (gs.length > 0) setGuidelineId(gs[0].id);
    });
  }, []);

  async function handleArrange() {
    if (!guidelineId || !file) return;
    setLoading(true);
    setError(null);
    setImageB64(null);
    try {
      const data = await arrangeShelf(guidelineId, file);
      setImageB64(data.image_b64);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg === "Failed to fetch" ? "Cannot reach server — is the backend running?" : msg);
    } finally {
      setLoading(false);
    }
  }

  const selectedGuideline = guidelines.find((g) => g.id === guidelineId);

  return (
    <div className="max-w-5xl mx-auto p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Arrange Shelf</h1>
        <p className="text-gray-500 text-sm mt-1">
          Upload an empty shelf photo. Claude will place products according to the planogram.
        </p>
      </div>

      <div className="flex gap-6">
        {/* Left panel */}
        <div className="w-72 flex-shrink-0 space-y-4">
          <Card>
            <CardContent className="pt-5 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                  Guideline
                </label>
                <select
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
                  value={guidelineId}
                  onChange={(e) => setGuidelineId(e.target.value)}
                  disabled={loading}
                >
                  {guidelines.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.display_name} — {new Date(g.created_at).toLocaleDateString()}
                    </option>
                  ))}
                </select>
                {selectedGuideline && (
                  <p className="text-xs text-gray-400 mt-1">
                    {selectedGuideline.products_count} products
                  </p>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                  Empty Shelf Photo
                </label>
                <FileUpload
                  accept={{ "image/*": [".jpg", ".jpeg", ".png", ".webp"] }}
                  label="Drop shelf image or click to browse"
                  onFile={setFile}
                  disabled={loading}
                />
              </div>

              <Button
                onClick={handleArrange}
                disabled={!guidelineId || !file || loading}
                className="w-full"
              >
                {loading ? "Claude is arranging…" : "Arrange Products →"}
              </Button>

              {error && <p className="text-sm text-red-600">{error}</p>}
            </CardContent>
          </Card>
        </div>

        {/* Right panel */}
        <div className="flex-1 space-y-3">
          <Card>
            <CardContent className="pt-5">
              {imageB64 ? (
                <img
                  src={`data:image/png;base64,${imageB64}`}
                  alt="Arranged shelf"
                  className="w-full rounded-md"
                />
              ) : (
                <div className="flex flex-col items-center justify-center min-h-64 text-gray-300 gap-2">
                  <span className="text-4xl">🖼</span>
                  <span className="text-sm">Composite image appears here</span>
                </div>
              )}
            </CardContent>
          </Card>

          {imageB64 && (
            <a
              href={`data:image/png;base64,${imageB64}`}
              download="shelf-arrangement.png"
              className="block w-full text-center border border-gray-300 rounded-md py-2 text-sm text-gray-600 hover:bg-gray-50"
            >
              ↓ Download PNG
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
