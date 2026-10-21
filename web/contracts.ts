/** Bounded energy-evidence guards by Jason Stys. Functions/fields: docs/CODE_INDEX.md. */
export const numericFields = [
  "hour",
  "solar_wh",
  "wind_wh",
  "grid_limit_wh",
  "critical_demand_wh",
  "flexible_demand_wh",
  "start_wh",
  "end_wh",
  "renewable_critical_wh",
  "renewable_flexible_wh",
  "grid_critical_wh",
  "grid_flexible_wh",
  "battery_critical_wh",
  "battery_flexible_wh",
  "charge_renewable_wh",
  "charge_grid_wh",
  "curtailed_wh",
  "critical_unserved_wh",
  "flexible_unserved_wh",
  "charge_loss_wh",
  "discharge_loss_wh",
  "bus_residual_wh",
  "storage_residual_wh",
  "system_residual_wh",
] as const;
export type Row = Record<(typeof numericFields)[number], number> & { battery_available: boolean };
export interface Result {
  policy: number;
  rows: Row[];
  summary: Record<string, number | null>;
  verification: {
    reference_verified: boolean;
    energy_ledgers_verified: boolean;
    max_residual_wh: number;
    absolute_tolerance_wh: number;
    relative_tolerance: number;
  };
}
export interface Run {
  id: string;
  name: string;
  settings: {
    scenario: string;
    policy: number;
    capacity: number;
    reserve: number;
    initial: number;
    precharge: number;
  };
  input: {
    config: { capacity_wh: number; initial_wh: number; reserve_pct: number; policy: number };
    profile: unknown[];
    provenance: string;
  };
  selected: Result;
  comparison: Result;
}
/** Reject unsafe shapes/nonfinite values before calculations, charts, tables or download links. */
export function parseRun(value: unknown): Run {
  const r = value as Run | null;
  if (
    !r ||
    typeof r !== "object" ||
    !/^[a-f0-9]{64}$/.test(r.id ?? "") ||
    !/^[a-z0-9][a-z0-9-]{0,47}$/.test(r.name ?? "") ||
    !r.input ||
    !Array.isArray(r.input.profile) ||
    r.input.profile.length < 1 ||
    r.input.profile.length > 168 ||
    typeof r.input.provenance !== "string" ||
    r.input.provenance.length > 240
  )
    throw new Error("Invalid evidence identity");
  const c = r.input.config,
    s = r.settings;
  if (
    !c ||
    !Number.isInteger(c.capacity_wh) ||
    c.capacity_wh < 1 ||
    c.capacity_wh > 100000 ||
    !Number.isInteger(c.initial_wh) ||
    c.initial_wh < 0 ||
    c.initial_wh > c.capacity_wh ||
    !Number.isInteger(c.reserve_pct) ||
    c.reserve_pct < 0 ||
    c.reserve_pct > 100 ||
    ![0, 1].includes(c.policy) ||
    !s ||
    typeof s.scenario !== "string" ||
    ![0, 1].includes(s.policy) ||
    ![10000, 20000, 40000].includes(s.capacity) ||
    ![0, 25, 50].includes(s.reserve) ||
    ![25, 50, 75].includes(s.initial) ||
    ![0, 1].includes(s.precharge)
  )
    throw new Error("Invalid input envelope");
  for (const result of [r.selected, r.comparison]) {
    if (
      !result ||
      ![0, 1].includes(result.policy) ||
      !Array.isArray(result.rows) ||
      result.rows.length !== r.input.profile.length ||
      !result.summary ||
      result.verification?.reference_verified !== true ||
      result.verification.energy_ledgers_verified !== true ||
      !Number.isFinite(result.verification.max_residual_wh) ||
      result.verification.max_residual_wh < 0 ||
      result.verification.max_residual_wh > 1e-7
    )
      throw new Error("Unverified result");
    if (
      result.rows.some(
        (row, index) =>
          !row ||
          row.hour !== index ||
          typeof row.battery_available !== "boolean" ||
          numericFields.some((key) => !Number.isFinite(row[key]) || Math.abs(row[key]) > 1e9) ||
          row.end_wh < -1e-7 ||
          row.end_wh > c.capacity_wh + 1e-7,
      )
    )
      throw new Error("Invalid hourly row");
    const keys = [
      "hours",
      "critical_demand_wh",
      "critical_unserved_wh",
      "flexible_unserved_wh",
      "critical_service_pct",
      "first_critical_shortfall_hour",
      "critical_shortfall_hours",
      "longest_critical_shortfall_run_hours",
      "outage_hours",
      "fully_served_critical_outage_hours",
      "reserve_recovery_hour",
      "generation_wh",
      "grid_import_wh",
      "curtailed_wh",
      "loss_wh",
      "end_wh",
      "min_wh",
      "direct_renewable_service_wh",
    ];
    const nullable = [
      "critical_service_pct",
      "first_critical_shortfall_hour",
      "reserve_recovery_hour",
    ];
    if (
      keys.some(
        (key) =>
          result.summary[key] === undefined ||
          (result.summary[key] === null && !nullable.includes(key)),
      ) ||
      Object.values(result.summary).some(
        (x) => x !== null && (!Number.isFinite(x) || x < -1e-7 || x > 1e9),
      ) ||
      result.summary.hours !== result.rows.length
    )
      throw new Error("Invalid summary accounting");
  }
  if (r.selected.policy !== c.policy || r.comparison.policy !== 1 - c.policy)
    throw new Error("Mismatched counterfactual policy");
  return r;
}
/** Display Wh as kWh; null means unavailable, never a fabricated zero or perfect score. */
export function kwh(value: number | null | undefined): string {
  return value === null || value === undefined
    ? "Not applicable"
    : (value / 1000).toLocaleString("en-US", { maximumFractionDigits: 3 });
}
/** Aggregate actual source splits without guessing renewable provenance of stored/grid energy. */
export function totals(row: Row) {
  return {
    renewable: row.solar_wh + row.wind_wh,
    grid: row.grid_critical_wh + row.grid_flexible_wh + row.charge_grid_wh,
    discharge: row.battery_critical_wh + row.battery_flexible_wh,
    charge: row.charge_renewable_wh + row.charge_grid_wh,
    critical: row.renewable_critical_wh + row.grid_critical_wh + row.battery_critical_wh,
    flexible: row.renewable_flexible_wh + row.grid_flexible_wh + row.battery_flexible_wh,
  };
}
/** Human-readable policy label; neither heuristic is described as globally optimal. */
export function policyName(policy: number): string {
  return policy === 1 ? "Protect critical reserve" : "Serve all loads";
}
