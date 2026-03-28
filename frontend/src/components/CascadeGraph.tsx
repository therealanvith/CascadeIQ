"use client";

import type { CascadeResponse, GraphResponse } from "@/lib/types";

type NodeVisual = {
  id: string;
  label: string;
  type: string;
  x: number;
  y: number;
};

function nodeColor(affected?: { severity: string }) {
  if (!affected) return { fill: "rgba(58, 140, 255, 0.18)", stroke: "rgba(58, 140, 255, 0.45)" };
  if (affected.severity === "critical" || affected.severity === "high")
    return { fill: "rgba(255, 77, 77, 0.22)", stroke: "rgba(255, 77, 77, 0.55)" };
  if (affected.severity === "medium")
    return { fill: "rgba(246, 196, 84, 0.20)", stroke: "rgba(246, 196, 84, 0.50)" };
  return { fill: "rgba(69, 212, 131, 0.18)", stroke: "rgba(69, 212, 131, 0.45)" };
}

function shortType(t: string) {
  return t.replace("Warehouse", "WH").replace("Delivery", "LM");
}

export function CascadeGraph({
  graph,
  cascade,
  activeStep,
}: {
  graph: GraphResponse | null;
  cascade: CascadeResponse | null;
  activeStep: number;
}) {
  if (!graph) {
    return (
      <div className="dp-card rounded-2xl px-5 py-6 text-sm text-white/60">
        Loading supply chain graph…
      </div>
    );
  }

  type AffectedNode = NonNullable<CascadeResponse["affected"]>[number];
  const affectedById = new Map<string, AffectedNode>();
  (cascade?.affected || []).forEach((a) => affectedById.set(a.node_id, a));
  const stepSet = new Set<string>();
  (cascade?.steps || []).slice(0, Math.max(0, activeStep)).forEach((s) => stepSet.add(s.node_id));

  const layers: Record<string, string[]> = {
    Vessel: [],
    Port: [],
    Warehouse: [],
    Truck: [],
    Delivery: [],
  };
  for (const n of graph.nodes) {
    if (layers[n.node_type]) layers[n.node_type].push(n.id);
  }

  const layerKeys = Object.keys(layers);
  const maxPerLayer = Math.max(...layerKeys.map((k) => layers[k].length), 1);

  const nodeW = 160;
  const nodeH = 44;
  const colGap = 15;
  const rowGap = 30;
  const paddingX = 20;
  const paddingY = 40;

  const colWidth = nodeW + colGap;
  const width = paddingX * 2 + layerKeys.length * colWidth;
  const height = paddingY * 2 + maxPerLayer * (nodeH + rowGap);

  const visuals: NodeVisual[] = [];
  layerKeys.forEach((k, i) => {
    const ids = layers[k];
    ids.forEach((id, j) => {
      const x = paddingX + i * colWidth + nodeW / 2;
      const y = paddingY + j * (nodeH + rowGap) + nodeH / 2;
      const meta = graph.nodes.find((nn) => nn.id === id);
      visuals.push({
        id,
        label: meta?.name || id,
        type: meta?.node_type || k,
        x,
        y,
      });
    });
  });

  const byId = new Map(visuals.map((v) => [v.id, v]));

  return (
    <div className="dp-card rounded-2xl overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4">
        <div>
          <div className="text-sm font-semibold text-white">Cascade graph</div>
          <div className="text-xs text-white/60">
            Unaffected nodes are blue; affected nodes are highlighted with delay.
          </div>
        </div>
        <div className="text-xs text-white/60">
          Step: <span className="text-white/85">{activeStep}</span>
        </div>
      </div>
      <div className="px-3 pb-4 overflow-x-auto">
        <svg width={width} height={height} style={{ minWidth: width }}>
          {graph.edges.map((e, idx) => {
            const s = byId.get(e.source);
            const t = byId.get(e.target);
            if (!s || !t) return null;
            const isActive = cascade
              ? stepSet.has(e.target) || stepSet.has(e.source)
              : false;
            return (
              <line
                key={`${e.source}-${e.target}-${idx}`}
                x1={s.x + nodeW / 2}
                y1={s.y}
                x2={t.x - nodeW / 2}
                y2={t.y}
                stroke={
                  isActive
                    ? "rgba(216, 176, 76, 0.65)"
                    : "rgba(255,255,255,0.12)"
                }
                strokeWidth={2}
              />
            );
          })}

          {visuals.map((n) => {
            const aff = affectedById.get(n.id);
            const colors = nodeColor(aff);
            const isRevealed = cascade ? stepSet.has(n.id) : true;
            return (
              <g key={n.id} opacity={isRevealed ? 1 : 0.35}>
                <rect
                  x={n.x - nodeW / 2}
                  y={n.y - nodeH / 2}
                  width={nodeW}
                  height={nodeH}
                  rx={12}
                  fill={colors.fill}
                  stroke={colors.stroke}
                  strokeWidth={1.5}
                />
                <text
                  x={n.x}
                  y={n.y - 5}
                  textAnchor="middle"
                  fill="white"
                  fontSize="12"
                  fontWeight={700}
                >
                  {n.label}
                </text>
                <text
                  x={n.x}
                  y={n.y + 12}
                  textAnchor="middle"
                  fill="rgba(255,255,255,0.70)"
                  fontSize="11"
                >
                  {shortType(n.type)}
                  {aff ? ` • +${aff.delay_hours.toFixed(1)}h` : ""}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}