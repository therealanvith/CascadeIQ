"use client";

import type { Vessel } from "@/lib/types";

function Card({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="dp-card rounded-2xl px-5 py-4">
      <div className="text-xs uppercase tracking-wider text-white/60">{label}</div>
      <div className="mt-2 text-2xl font-semibold text-white">{value}</div>
      {sub ? <div className="mt-1 text-sm text-white/60">{sub}</div> : null}
    </div>
  );
}

export function SummaryCards({ vessels }: { vessels: Vessel[] }) {
  const total = vessels.length;
  const atRisk = vessels.filter((v) => v.risk.risk_level !== "low").length;
  const avgHours =
    total === 0
      ? 0
      : vessels.reduce((acc, v) => acc + (v.risk.estimated_delay_hours || 0), 0) / total;

  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
      <Card label="Vessels monitored" value={`${total}`} sub="AIS + ops signals" />
      <Card label="At risk today" value={`${atRisk}`} sub="Medium + high risk" />
      <Card label="Avg predicted delay" value={`${avgHours.toFixed(1)}h`} sub="Across monitored fleet" />
      <Card
        label="Cascade affected (est.)"
        value={`${Math.round(atRisk * 5)}`}
        sub="Downstream shipments"
      />
    </div>
  );
}

