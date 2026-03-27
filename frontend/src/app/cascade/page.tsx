"use client";

import { useEffect, useMemo, useState } from "react";

import { fetchGraph, fetchVessels, runCascade } from "@/lib/api";
import type { CascadeResponse, GraphResponse, Vessel } from "@/lib/types";
import { CascadeGraph } from "@/components/CascadeGraph";
import { ActionPanel } from "@/components/ActionPanel";

export default function CascadePage() {
  const [vessels, setVessels] = useState<Vessel[]>([]);
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [cascade, setCascade] = useState<CascadeResponse | null>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const vesselFromUrl = useMemo(() => {
    if (typeof window === "undefined") return null;
    return new URLSearchParams(window.location.search).get("vessel_id");
  }, []);

  const [selectedVesselId, setSelectedVesselId] = useState<string>("vessel:endeavour");
  const selected = useMemo(
    () => vessels.find((v) => v.vessel_id === selectedVesselId) || null,
    [vessels, selectedVesselId],
  );

  const [delayHours, setDelayHours] = useState<number>(14);

  useEffect(() => {
    fetchVessels()
      .then((v) => setVessels(v))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
    fetchGraph()
      .then((g) => setGraph(g))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  useEffect(() => {
    if (vesselFromUrl) setSelectedVesselId(vesselFromUrl);
  }, [vesselFromUrl]);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStep((s) => {
        if (!cascade) return 0;
        const max = cascade.steps.length;
        if (max === 0) return 0;
        return Math.min(max, s + 1);
      });
    }, 550);
    return () => clearInterval(timer);
  }, [cascade]);

  async function onRun() {
    console.log("Running cascade with:", selectedVesselId, delayHours);
    setError(null);
    setLoading(true);
    setActiveStep(0);
    try {
      const res = await runCascade({ vessel_id: selectedVesselId, delay_hours: delayHours });
      setCascade(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  const affected = useMemo(() => cascade?.affected ?? [], [cascade]);
  const affectedSorted = useMemo(
    () => [...affected].sort((a, b) => (b.delay_hours || 0) - (a.delay_hours || 0)),
    [affected],
  );

  return (
    <main className="mx-auto w-full max-w-6xl px-5 py-8">
      <div className="flex flex-col gap-2">
        <div className="text-xs uppercase tracking-[0.24em] text-[color:var(--dp-muted)]">Simulation</div>
        <h1 className="text-3xl font-semibold tracking-tight text-white">Cascade simulator</h1>
        <p className="max-w-3xl text-sm leading-6 text-white/65">
          Run a BFS propagation from the delayed vessel across the downstream network. Buffers reduce impact; breached
          SLAs are flagged.
        </p>
      </div>

      {error ? (
        <div className="mt-6 rounded-2xl border border-red-500/30 bg-red-500/10 px-5 py-4 text-sm text-red-200">
          {error}
        </div>
      ) : null}

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="dp-card rounded-2xl px-5 py-4 lg:col-span-1">
          <div className="text-sm font-semibold text-white">Inputs</div>
          <div className="mt-1 text-xs text-white/60">Pick a vessel and a delay, then simulate.</div>

          <div className="mt-4">
            <label className="text-xs uppercase tracking-wider text-white/50">Vessel</label>
            <select
              className="mt-2 w-full rounded-xl border border-white/10 bg-[#050912] px-3 py-2 text-sm text-white outline-none"
              value={selectedVesselId}
              onChange={(e) => setSelectedVesselId(e.target.value)}
            >
              {vessels.map((v) => (
                <option key={v.vessel_id} value={v.vessel_id}>
                  {v.name} ({v.origin}→{v.destination})
                </option>
              ))}
            </select>
          </div>

          <div className="mt-4">
            <label className="text-xs uppercase tracking-wider text-white/50">Delay hours</label>
            <input
              type="number"
              min={0}
              step={0.5}
              className="mt-2 w-full rounded-xl border border-white/10 bg-[#050912] px-3 py-2 text-sm text-white outline-none"
              value={delayHours}
              onChange={(e) => setDelayHours(Number(e.target.value))}
            />
            <div className="mt-2 text-xs text-white/60">
              Demo: MV Endeavour with <span className="text-white/85">14h</span>
            </div>
          </div>

          {selected ? (
            <div className="mt-4 rounded-xl border border-white/10 bg-white/5 px-4 py-3">
              <div className="text-xs uppercase tracking-wider text-white/50">Prediction snapshot</div>
              <div className="mt-2 text-sm text-white">
                {(selected.risk.delay_probability * 100).toFixed(0)}% • {selected.risk.estimated_delay_hours.toFixed(1)}h
              </div>
              <div className="mt-1 text-xs text-white/60">
                features: speed {selected.features.speed_deviation.toFixed(1)}%, weather{" "}
                {selected.features.weather_severity.toFixed(1)}, congestion {selected.features.port_congestion.toFixed(1)}
              </div>
            </div>
          ) : null}

          <button
            onClick={onRun}
            disabled={loading}
            className="mt-5 w-full rounded-xl border border-white/10 bg-[rgba(216,176,76,0.14)] px-4 py-2 text-sm font-semibold text-white hover:bg-[rgba(216,176,76,0.20)] disabled:opacity-60"
          >
            {loading ? "Simulating…" : "Simulate cascade"}
          </button>

          <div className="mt-6">
            <div className="text-xs uppercase tracking-wider text-white/50">Affected nodes</div>
            <div className="mt-2 flex flex-col gap-2">
              {affectedSorted.length === 0 ? (
                <div className="text-sm text-white/60">No simulation results yet.</div>
              ) : (
                affectedSorted.slice(0, 8).map((a) => (
                  <div key={a.node_id} className="rounded-xl border border-white/10 bg-white/5 px-4 py-3">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-medium text-white">{a.name}</div>
                      <div className="text-xs text-white/60">+{a.delay_hours.toFixed(1)}h</div>
                    </div>
                    <div className="mt-1 text-xs text-white/60">
                      {a.node_type} • severity {a.severity}
                      {a.sla_breached ? " • SLA breached" : ""}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 flex flex-col gap-4">
          <CascadeGraph graph={graph} cascade={cascade} activeStep={activeStep} />
          <ActionPanel affected={affected} />
        </div>
      </div>
    </main>
  );
}

