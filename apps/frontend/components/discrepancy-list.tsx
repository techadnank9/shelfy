import { Discrepancy } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

const SEVERITY_COLOR: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  HIGH: "destructive",
  MEDIUM: "secondary",
  LOW: "outline",
};

const TYPE_LABEL: Record<string, string> = {
  MISSING: "Missing",
  WRONG_POSITION: "Wrong Position",
  WRONG_FACINGS: "Wrong Facings",
  UNEXPECTED: "Unexpected",
};

interface DiscrepancyListProps {
  discrepancies: Discrepancy[];
}

export function DiscrepancyList({ discrepancies }: DiscrepancyListProps) {
  const sorted = [...discrepancies].sort((a, b) => {
    const order = { HIGH: 0, MEDIUM: 1, LOW: 2 };
    return order[a.severity] - order[b.severity];
  });

  if (sorted.length === 0) {
    return (
      <p className="text-sm text-green-600 font-medium">
        No discrepancies — shelf is fully compliant.
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {sorted.map((d, i) => (
        <li key={i} className="flex items-start gap-3 p-3 bg-white border rounded-lg">
          <Badge variant={SEVERITY_COLOR[d.severity]}>{d.severity}</Badge>
          <div className="flex-1 text-sm">
            <span className="font-medium">{TYPE_LABEL[d.type]}</span>
            {" — "}
            <span className="font-mono">{d.sku}</span>
            {d.expected_position && (
              <div className="text-xs text-gray-500 mt-0.5">
                Expected: {d.expected_position}
                {d.detected_position ? ` · Found: ${d.detected_position}` : ""}
              </div>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}
