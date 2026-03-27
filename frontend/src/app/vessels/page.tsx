"use client";

import { useEffect, useMemo, useState } from "react";

import { fetchVessels } from "@/lib/api";
import type { Vessel } from "@/lib/types";

function Pill({ level }: { level: Vessel["risk"]["risk_level"] }) {
  const style =
    level === "high"
      ? "bg-red-500/15 text-red-200 border-red-400/20"
      : level === "medium"
        ? "bg-amber-500/15 text-amber-200 border-amber-400/20"
        : "bg-emerald-500/15 text-emerald-200 border-emerald-400/20";
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs ${style}`}>
      {level.toUpperCase()}
    </span>
  );
}

export default function VesselsPage() {
  const [vessels, setVessels] = useState<Vessel[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchVessels()
      .then((v) => setVessels(v))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  const sorted = useMemo(() => {
    return [...vessels].sort((a, b) => b.risk.delay_probability - a.risk.delay_probability);
  }, [vessels]);

  return (
    <main className="mx-auto w-full max-w-6xl px-5 py-8">
      <div className="flex items-end justify-between">
        <div>
          <div className="text-xs uppercase tracking-[0.24em] text-[color:var(--dp-muted)]">Fleet view</div>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">Vessels</h1>
          <p className="mt-2 max-w-2xl text-sm text-white/65">
            Ranked by predicted delay probability. Use the cascade simulator to see downstream impact.
          </p>
        </div>
        <a
          href="/cascade"
          className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-white/85 hover:bg-white/8"
        >
          Open simulator
        </a>
      </div>

      {error ? (
        <div className="mt-6 rounded-2xl border border-red-500/30 bg-red-500/10 px-5 py-4 text-sm text-red-200">
          Failed to load vessels. {error}
        </div>
      ) : null}

      <div className="mt-6 dp-card overflow-hidden rounded-2xl">
        <div className="grid grid-cols-12 gap-3 border-b border-white/10 px-5 py-3 text-xs uppercase tracking-wider text-white/50">
          <div className="col-span-4">Vessel</div>
          <div className="col-span-4">Route</div>
          <div className="col-span-2">Risk</div>
          <div className="col-span-2 text-right">Est. delay</div>
        </div>
        <div className="divide-y divide-white/5">
          {sorted.map((v) => (
            <div key={v.vessel_id} className="grid grid-cols-12 gap-3 px-5 py-4">
              <div className="col-span-4">
                <div className="text-sm font-medium text-white">{v.name}</div>
                <div className="mt-1 text-xs text-white/55">{v.status.replaceAll("_", " ")}</div>
              </div>
              <div className="col-span-4">
                <div className="text-sm text-white/85">
                  {v.origin} → {v.destination}
                </div>
                <div className="mt-1 text-xs text-white/55">{v.route}</div>
              </div>
              <div className="col-span-2 flex items-center gap-2">
                <Pill level={v.risk.risk_level} />
                <div className="text-xs text-white/60">{(v.risk.delay_probability * 100).toFixed(0)}%</div>
              </div>
              <div className="col-span-2 text-right">
                <div className="text-sm font-medium text-white">{v.risk.estimated_delay_hours.toFixed(1)}h</div>
                <a
                  href={`/cascade?vessel_id=${encodeURIComponent(v.vessel_id)}`}
                  className="mt-1 inline-block text-xs text-[color:var(--dp-gold)] hover:underline"
                >
                  Simulate cascade →
                </a>
              </div>
            </div>
          ))}
          {sorted.length === 0 ? (
            <div className="px-5 py-6 text-sm text-white/60">Loading…</div>
          ) : null}
        </div>
      </div>
    </main>
  );
}

