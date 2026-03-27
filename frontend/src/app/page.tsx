"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";

import { fetchVessels } from "@/lib/api";
import type { Vessel } from "@/lib/types";
import { SummaryCards } from "@/components/SummaryCards";

const MapView = dynamic(() => import("@/components/MapView").then((m) => m.MapView), {
  ssr: false,
});

export default function DashboardPage() {
  const [vessels, setVessels] = useState<Vessel[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchVessels()
      .then((v) => setVessels(v))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  const atRisk = useMemo(
    () => vessels.filter((v) => v.risk.risk_level !== "low"),
    [vessels],
  );

  return (
    <main className="mx-auto w-full max-w-6xl px-5 py-8">
      <div className="flex flex-col gap-2">
        <div className="text-xs uppercase tracking-[0.24em] text-[color:var(--dp-muted)]">
          Vessel Delay Cascade Predictor
        </div>
        <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <h1 className="text-3xl font-semibold tracking-tight text-white">
            Operational awareness for downstream resilience
          </h1>
          <a
            href="/cascade"
            className="inline-flex items-center justify-center rounded-xl border border-white/10 bg-[rgba(216,176,76,0.12)] px-4 py-2 text-sm font-medium text-white hover:bg-[rgba(216,176,76,0.18)]"
          >
            Run a cascade simulation →
          </a>
        </div>
        <p className="max-w-3xl text-sm leading-6 text-white/65">
          Select a vessel, view predicted delay risk, and simulate how delays cascade from{" "}
          <span className="text-white/85">port → warehouse → trucks → last mile delivery</span>, including SLA
          breaches and recommended actions.
        </p>
      </div>

      <div className="mt-6">
        <SummaryCards vessels={vessels} />
      </div>

      {error ? (
        <div className="mt-6 rounded-2xl border border-red-500/30 bg-red-500/10 px-5 py-4 text-sm text-red-200">
          Failed to load backend data. {error}
          <div className="mt-2 text-xs text-red-200/70">
            Set <code className="rounded bg-black/30 px-1 py-0.5">NEXT_PUBLIC_API_BASE_URL</code> to your backend
            URL.
          </div>
        </div>
      ) : null}

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <MapView vessels={vessels} />
        </div>
        <div className="dp-card rounded-2xl px-5 py-4">
          <div className="text-sm font-semibold text-white">Today’s at-risk shipments</div>
          <div className="mt-1 text-xs text-white/60">Focus on high propagation potential routes</div>
          <div className="mt-4 flex flex-col gap-3">
            {atRisk.length === 0 ? (
              <div className="text-sm text-white/60">No vessels flagged as medium/high risk.</div>
            ) : (
              atRisk.map((v) => (
                <a
                  key={v.vessel_id}
                  href={`/cascade?vessel_id=${encodeURIComponent(v.vessel_id)}`}
                  className="group rounded-xl border border-white/10 bg-white/5 px-4 py-3 hover:bg-white/7"
                >
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium text-white">{v.name}</div>
                    <div className="text-xs text-white/65 group-hover:text-white/80">
                      {(v.risk.delay_probability * 100).toFixed(0)}% risk
                    </div>
                  </div>
                  <div className="mt-1 text-xs text-white/55">
                    {v.origin} → {v.destination} • est. {v.risk.estimated_delay_hours.toFixed(1)}h
                  </div>
                </a>
              ))
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
