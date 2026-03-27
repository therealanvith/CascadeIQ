"use client";

import type { CascadeAffected } from "@/lib/types";

function actionFor(nodeType: string, severity: CascadeAffected["severity"]) {
  const base =
    nodeType === "Port"
      ? "Pre-book berth slots, notify terminal ops, prioritize unloading."
      : nodeType === "Warehouse"
        ? "Reschedule dock appointments, allocate overflow space, re-slot labor."
        : nodeType === "Truck"
          ? "Re-route fleet, add standby drivers, adjust dispatch windows."
          : nodeType === "Delivery"
            ? "Update ETAs, offer customer slots, prioritize perishable/urgent."
            : "Coordinate stakeholders and update ETAs.";
  if (severity === "critical") return `${base} Escalate to incident response.`;
  if (severity === "high") return `${base} Trigger mitigation playbook.`;
  if (severity === "medium") return `${base} Monitor and pre-alert partners.`;
  return `${base} Low impact; watch for drift.`;
}

function impactEstimates(nodeType: string, delayHours: number) {
  // Very simple demo multipliers (tunable).
  const co2PerHour = nodeType === "Truck" ? 0.22 : nodeType === "Delivery" ? 0.12 : 0.06;
  const costPerHour = nodeType === "Port" ? 420 : nodeType === "Warehouse" ? 260 : nodeType === "Truck" ? 180 : 90;
  return {
    co2Tons: delayHours * co2PerHour,
    costUsd: delayHours * costPerHour,
  };
}

export function ActionPanel({ affected }: { affected: CascadeAffected[] }) {
  const totalCo2 = affected.reduce((acc, a) => acc + impactEstimates(a.node_type, a.delay_hours).co2Tons, 0);
  const totalCost = affected.reduce((acc, a) => acc + impactEstimates(a.node_type, a.delay_hours).costUsd, 0);
  const breached = affected.filter((a) => a.sla_breached);

  return (
    <div className="dp-card rounded-2xl px-5 py-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-white">Action panel</div>
          <div className="mt-1 text-xs text-white/60">Recommendations + cost/carbon impact from cascaded delay</div>
        </div>
        <div className="text-right">
          <div className="text-xs text-white/60">Impact estimate</div>
          <div className="mt-1 text-sm font-semibold text-white">${Math.round(totalCost).toLocaleString()}</div>
          <div className="text-xs text-white/60">{totalCo2.toFixed(2)} tons CO₂</div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-3">
          <div className="text-xs uppercase tracking-wider text-white/50">SLA breaches</div>
          <div className="mt-2 text-2xl font-semibold text-white">{breached.length}</div>
          <div className="mt-1 text-xs text-white/60">Nodes with breached thresholds</div>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-3">
          <div className="text-xs uppercase tracking-wider text-white/50">Affected nodes</div>
          <div className="mt-2 text-2xl font-semibold text-white">{affected.length}</div>
          <div className="mt-1 text-xs text-white/60">Downstream impact footprint</div>
        </div>
      </div>

      <div className="mt-4">
        <div className="text-xs uppercase tracking-wider text-white/50">Recommendations</div>
        <div className="mt-2 flex flex-col gap-2">
          {affected.length === 0 ? (
            <div className="text-sm text-white/60">Run a simulation to see recommendations.</div>
          ) : (
            affected
              .slice()
              .sort((a, b) => (b.delay_hours || 0) - (a.delay_hours || 0))
              .slice(0, 6)
              .map((a) => {
                const imp = impactEstimates(a.node_type, a.delay_hours);
                return (
                  <div key={a.node_id} className="rounded-xl border border-white/10 bg-white/5 px-4 py-3">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-medium text-white">{a.name}</div>
                      <div className="text-xs text-white/60">
                        +{a.delay_hours.toFixed(1)}h • ${Math.round(imp.costUsd)} • {imp.co2Tons.toFixed(2)}t CO₂
                      </div>
                    </div>
                    <div className="mt-1 text-xs text-white/60">{actionFor(a.node_type, a.severity)}</div>
                  </div>
                );
              })
          )}
        </div>
      </div>
    </div>
  );
}

