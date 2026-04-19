"use client";
import { AuditResult } from "@/lib/api";
import { Progress } from "@/components/ui/progress";

interface AuditOverlayProps {
  photoUrl: string;
  result: AuditResult;
}

export function AuditOverlay({ photoUrl, result }: AuditOverlayProps) {
  const score = Math.round(result.compliance_score);
  const scoreColor =
    score >= 80 ? "text-green-600" : score >= 60 ? "text-yellow-600" : "text-red-600";

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <span className={`text-4xl font-bold ${scoreColor}`}>{score}%</span>
        <div className="flex-1">
          <p className="text-sm text-gray-500 mb-1">Compliance Score</p>
          <Progress value={score} className="h-3" />
        </div>
      </div>
      <div className="relative rounded-lg overflow-hidden border">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={photoUrl}
          alt="Audited shelf"
          className="w-full object-cover"
          style={{ maxHeight: 480 }}
        />
        <div className="absolute top-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded">
          {result.discrepancies.length} issue{result.discrepancies.length !== 1 ? "s" : ""} found
        </div>
      </div>
    </div>
  );
}
