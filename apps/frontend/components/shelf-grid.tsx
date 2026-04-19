import { PlanogramPosition } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

interface ShelfGridProps {
  positions: PlanogramPosition[];
  shelves?: number;
  columns?: number;
}

const TIER_COLORS: Record<string, string> = {
  hero: "bg-blue-100 border-blue-300 text-blue-800",
  secondary: "bg-gray-100 border-gray-300 text-gray-700",
  new: "bg-green-100 border-green-300 text-green-800",
};

export function ShelfGrid({ positions, shelves = 3, columns = 6 }: ShelfGridProps) {
  const grid: Record<string, PlanogramPosition> = {};
  for (const pos of positions) {
    grid[`${pos.shelf_index}-${pos.column_index}`] = pos;
  }

  const shelfLabels = ["Top", "Eye Level", "Bottom"];

  return (
    <div className="space-y-2">
      {Array.from({ length: shelves }, (_, si) => (
        <div key={si} className="flex items-center gap-2">
          <span className="text-xs text-gray-400 w-16 text-right">
            {shelfLabels[si] ?? `Shelf ${si}`}
          </span>
          <div className="flex gap-1 flex-1 bg-gray-200 p-1 rounded">
            {Array.from({ length: columns }, (_, ci) => {
              const pos = grid[`${si}-${ci}`];
              const tierColor = pos
                ? (TIER_COLORS[pos.sku.toLowerCase().includes("ls-001") || pos.sku.toLowerCase().includes("ls-002") ? "hero" : "secondary"] ?? TIER_COLORS.secondary)
                : "";
              return (
                <div
                  key={ci}
                  className={`flex-1 min-h-[80px] border rounded p-1 text-xs flex flex-col justify-between
                    ${pos ? tierColor : "bg-white border-gray-200"}`}
                >
                  {pos ? (
                    <>
                      <div className="font-mono font-bold">{pos.sku}</div>
                      <div className="text-gray-500 text-[10px] line-clamp-2">{pos.rationale}</div>
                      <div className="text-[10px]">×{pos.facings}</div>
                    </>
                  ) : (
                    <div className="text-gray-300 text-center mt-4">—</div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
