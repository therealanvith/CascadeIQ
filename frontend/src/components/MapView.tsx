"use client";

import { MapContainer, Marker, Popup, Polyline, TileLayer } from "react-leaflet";
import L from "leaflet";
import { useMemo } from "react";

import type { Vessel } from "@/lib/types";

// Fix default marker icon paths for bundlers.
const DefaultIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

function riskColor(risk: Vessel["risk"]["risk_level"]) {
  if (risk === "high") return "#ff4d4d";
  if (risk === "medium") return "#f6c454";
  return "#45d483";
}

export function MapView({ vessels }: { vessels: Vessel[] }) {
  const center = useMemo<[number, number]>(() => [17.2, 74.2], []);
  return (
    <div className="dp-card overflow-hidden rounded-2xl border border-white/10">
      <div className="flex items-center justify-between px-5 py-4">
        <div>
          <div className="text-sm font-semibold text-white">Live vessel view</div>
          <div className="text-xs text-white/60">Click a vessel to see prediction inputs + outputs</div>
        </div>
        <div className="flex items-center gap-2 text-xs text-white/60">
          <span className="inline-flex items-center gap-1">
            <span className="h-2 w-2 rounded-full" style={{ background: "#45d483" }} /> Low
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="h-2 w-2 rounded-full" style={{ background: "#f6c454" }} /> Medium
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="h-2 w-2 rounded-full" style={{ background: "#ff4d4d" }} /> High
          </span>
        </div>
      </div>
      <div className="h-[420px]">
        <MapContainer center={center} zoom={3} style={{ height: "100%", width: "100%" }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {vessels.map((v) => (
            <Marker
              key={v.vessel_id}
              position={[v.position.lat, v.position.lon]}
              icon={DefaultIcon}
            >
              <Popup>
                <div style={{ minWidth: 220 }}>
                  <div style={{ fontWeight: 700, marginBottom: 4 }}>{v.name}</div>
                  <div style={{ fontSize: 12, opacity: 0.8 }}>
                    {v.origin} → {v.destination}
                  </div>
                  <div style={{ marginTop: 8, fontSize: 12 }}>
                    <div>
                      Risk:{" "}
                      <span style={{ color: riskColor(v.risk.risk_level), fontWeight: 700 }}>
                        {v.risk.risk_level.toUpperCase()}
                      </span>
                    </div>
                    <div>Delay probability: {(v.risk.delay_probability * 100).toFixed(0)}%</div>
                    <div>Est. delay: {v.risk.estimated_delay_hours.toFixed(1)}h</div>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
          {vessels.map((v) => (
            <Polyline
              key={`${v.vessel_id}-route`}
              positions={v.route_polyline.map((p) => [p.lat, p.lon])}
              pathOptions={{ color: riskColor(v.risk.risk_level), weight: 3, opacity: 0.6 }}
            />
          ))}
        </MapContainer>
      </div>
    </div>
  );
}

