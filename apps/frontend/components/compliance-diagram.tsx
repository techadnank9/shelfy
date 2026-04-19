"use client";
import { useEffect, useRef } from "react";
import { type Planogram, type Discrepancy } from "@/lib/api";

interface Props {
  planogram: Planogram;
  discrepancies: Discrepancy[];
  complianceScore: number;
}

const SHELF_LABELS: Record<number, string> = { 0: "TOP SHELF", 1: "EYE LEVEL ★", 2: "BOTTOM SHELF" };
const SHELF_COLORS: Record<number, string> = { 0: "#f5f5ff", 1: "#fffbe8", 2: "#f0fff4" };

const STATUS_COLORS = {
  ok:       { fill: "#d1fae5", stroke: "#059669", label: "#065f46", badge: "#059669" },
  missing:  { fill: "#fee2e2", stroke: "#dc2626", label: "#7f1d1d", badge: "#dc2626" },
  wrong:    { fill: "#fef3c7", stroke: "#d97706", label: "#78350f", badge: "#d97706" },
  facings:  { fill: "#dbeafe", stroke: "#2563eb", label: "#1e3a8a", badge: "#2563eb" },
  unexpected:{ fill: "#f3e8ff", stroke: "#7c3aed", label: "#4c1d95", badge: "#7c3aed" },
};

const SKU_COLORS: Record<string, string> = {
  "LS-001": "#ffd450", "LS-002": "#b4d4ff", "LS-003": "#282850",
  "LS-004": "#b4f0c8", "LS-005": "#dcdcf0", "LS-006": "#ffb4b4",
  "LS-007": "#c8b4ff", "LS-008": "#fff0b4",
};

function parsePosition(pos?: string | null): { shelf: number; col: number } | null {
  if (!pos) return null;
  const m = pos.match(/shelf\s+(\d+).*col\s+(\d+)/i);
  if (!m) return null;
  return { shelf: parseInt(m[1]), col: parseInt(m[2]) };
}

export function ComplianceDiagram({ planogram, discrepancies, complianceScore }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    if (!ctx) return;

    const W = canvas.width;
    const H = canvas.height;
    const CW = 72, CH = 108;
    const COL_GAP = 6;
    const LEFT = 90;
    const SHELF_Y = [60, 230, 400];
    const WOOD_H = 14;

    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#1a1a22";
    ctx.fillRect(0, 0, W, H);

    // Build discrepancy map keyed by sku
    const discMap: Record<string, Discrepancy> = {};
    for (const d of discrepancies) discMap[d.sku] = d;

    // Build set of expected skus
    const expectedSkus = new Set(planogram.positions.map(p => p.sku));

    // Group positions by shelf
    const byShelf: Record<number, typeof planogram.positions> = {};
    for (const p of planogram.positions) {
      byShelf[p.shelf_index] = byShelf[p.shelf_index] || [];
      byShelf[p.shelf_index].push(p);
    }

    // Collect unexpected (detected but not in planogram)
    const unexpectedItems: { shelf: number; col: number; sku: string }[] = [];
    for (const d of discrepancies) {
      if (d.type === "UNEXPECTED" && d.detected_position) {
        const pos = parsePosition(d.detected_position);
        if (pos) unexpectedItems.push({ shelf: pos.shelf, col: pos.col, sku: d.sku });
      }
    }

    // Draw shelf rows
    for (const [siStr, sy] of Object.entries(SHELF_Y.map((y, i) => [i, y]))) {
      const si = siStr as unknown as number;
      const sy2 = SHELF_Y[si];

      ctx.fillStyle = SHELF_COLORS[si] ?? "#f8f8f8";
      ctx.fillRect(0, sy2, W, CH + WOOD_H + 4);

      // Plank
      ctx.fillStyle = "#a07848";
      ctx.fillRect(0, sy2 + CH, W, WOOD_H);
      ctx.fillStyle = "#6e4e2a";
      ctx.fillRect(0, sy2 + CH + WOOD_H, W, 3);

      // Shelf label
      const label = SHELF_LABELS[si] ?? `Shelf ${si}`;
      const lbg = si === 1 ? "#c89828" : "#404060";
      ctx.fillStyle = lbg;
      ctx.fillRect(0, sy2, 84, 18);
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 9px Arial";
      ctx.fillText(label, 4, sy2 + 13);
    }

    function drawProductCell(
      shelf: number, col: number, sku: string,
      status: keyof typeof STATUS_COLORS,
      label: string | null
    ) {
      const x = LEFT + col * (CW + COL_GAP);
      const y = SHELF_Y[shelf];
      const s = STATUS_COLORS[status];

      // Cell background
      ctx.fillStyle = s.fill;
      ctx.strokeStyle = s.stroke;
      ctx.lineWidth = 2;
      roundRect(ctx, x, y + 4, CW, CH - 4, 6);
      ctx.fill(); ctx.stroke();

      // Product color swatch (top 55%)
      ctx.fillStyle = SKU_COLORS[sku] ?? "#ddd";
      roundRect(ctx, x + 4, y + 8, CW - 8, (CH - 4) * 0.55, 4);
      ctx.fill();

      // SKU text
      ctx.fillStyle = s.label;
      ctx.font = "bold 8px Arial";
      const skuW = ctx.measureText(sku).width;
      ctx.fillText(sku, x + (CW - skuW) / 2, y + CH - 18);

      // Annotation label pill
      if (label) {
        const pw = ctx.measureText(label).width + 10;
        const px = x + (CW - pw) / 2;
        const py = y + 6;
        ctx.fillStyle = s.badge;
        roundRect(ctx, px, py, pw, 14, 4);
        ctx.fill();
        ctx.fillStyle = "#fff";
        ctx.font = "bold 7px Arial";
        ctx.fillText(label, px + 5, py + 10);
      }
    }

    // Draw planned positions
    for (const pos of planogram.positions) {
      const disc = discMap[pos.sku];
      let status: keyof typeof STATUS_COLORS = "ok";
      let lbl: string | null = null;

      if (!disc) {
        status = "ok";
      } else if (disc.type === "MISSING") {
        status = "missing"; lbl = "MISSING";
      } else if (disc.type === "WRONG_POSITION") {
        status = "wrong"; lbl = "WRONG POS";
      } else if (disc.type === "WRONG_FACINGS") {
        status = "facings"; lbl = "LOW FACINGS";
      }

      for (let f = 0; f < pos.facings; f++) {
        drawProductCell(pos.shelf_index, pos.column_index + f, pos.sku, status, f === 0 ? lbl : null);
      }
    }

    // Draw unexpected items
    for (const item of unexpectedItems) {
      drawProductCell(item.shelf, item.col, item.sku, "unexpected", "UNEXPECTED");
    }

    // Header bar
    ctx.fillStyle = "#12121a";
    ctx.fillRect(0, 0, W, 50);

    // Score badge
    const scoreColor = complianceScore >= 80 ? "#22c55e" : complianceScore >= 60 ? "#f59e0b" : "#ef4444";
    ctx.fillStyle = scoreColor;
    ctx.font = "bold 26px Arial";
    ctx.fillText(`${Math.round(complianceScore)}%`, 20, 34);

    ctx.fillStyle = "#aaaacc";
    ctx.font = "12px Arial";
    ctx.fillText("Compliance Score", 70, 22);

    ctx.fillStyle = "#6666aa";
    ctx.font = "11px Arial";
    ctx.fillText(`${discrepancies.length} issue${discrepancies.length !== 1 ? "s" : ""} found  ·  Planogram: ${planogram.store_format} store`, 70, 38);

    // Legend
    const legendItems: [keyof typeof STATUS_COLORS, string][] = [
      ["ok", "Compliant"], ["missing", "Missing"], ["wrong", "Wrong Position"],
      ["facings", "Low Facings"], ["unexpected", "Unexpected"],
    ];
    let lx = 20;
    const ly = H - 26;
    ctx.fillStyle = "#12121a";
    ctx.fillRect(0, H - 38, W, 38);
    for (const [s, txt] of legendItems) {
      const sc = STATUS_COLORS[s];
      ctx.fillStyle = sc.badge;
      ctx.fillRect(lx, ly, 12, 12);
      ctx.fillStyle = "#ccccdd";
      ctx.font = "10px Arial";
      ctx.fillText(txt, lx + 16, ly + 10);
      lx += ctx.measureText(txt).width + 36;
    }

  }, [planogram, discrepancies, complianceScore]);

  return (
    <canvas
      ref={canvasRef}
      width={980}
      height={580}
      className="w-full rounded-xl border border-gray-200 shadow"
    />
  );
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.arcTo(x + w, y, x + w, y + r, r);
  ctx.lineTo(x + w, y + h - r);
  ctx.arcTo(x + w, y + h, x + w - r, y + h, r);
  ctx.lineTo(x + r, y + h);
  ctx.arcTo(x, y + h, x, y + h - r, r);
  ctx.lineTo(x, y + r);
  ctx.arcTo(x, y, x + r, y, r);
  ctx.closePath();
}
