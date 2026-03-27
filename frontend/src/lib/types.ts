export type RiskLevel = "low" | "medium" | "high";

export type Vessel = {
  vessel_id: string;
  name: string;
  route: string;
  origin: string;
  destination: string;
  status: string;
  position: { lat: number; lon: number };
  route_polyline: { lat: number; lon: number }[];
  risk: {
    delay_probability: number;
    estimated_delay_hours: number;
    risk_level: RiskLevel;
  };
  features: {
    speed_deviation: number;
    weather_severity: number;
    port_congestion: number;
    distance_remaining: number;
    month: number;
  };
};

export type PredictRequest = Vessel["features"];

export type PredictResponse = {
  delay_probability: number;
  estimated_delay_hours: number;
};

export type GraphNode = {
  id: string;
  node_type: string;
  name: string;
  sla_hours: number;
};

export type GraphEdge = {
  source: string;
  target: string;
  buffer_hours: number;
  expected_arrival_time: string;
};

export type GraphResponse = {
  nodes: GraphNode[];
  edges: GraphEdge[];
};

export type CascadeRequest = {
  vessel_id: string;
  delay_hours: number;
};

export type CascadeAffected = {
  node_id: string;
  node_type: string;
  name: string;
  delay_hours: number;
  severity: "low" | "medium" | "high" | "critical";
  sla_breached: boolean;
  sla_hours: number;
  path: string[];
};

export type CascadeResponse = {
  vessel_id: string;
  input_delay_hours: number;
  affected: CascadeAffected[];
  steps: { node_id: string; delay_hours: number; severity: string; path: string[] }[];
};

