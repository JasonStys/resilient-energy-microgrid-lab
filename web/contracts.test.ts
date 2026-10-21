/** Energy UI guard and unit contracts by Jason Stys; definitions/variables: docs/CODE_INDEX.md. */
import { describe, expect, test } from "vitest";
import { kwh, numericFields, parseRun, policyName, totals, type Row } from "./contracts";
/** Create a minimal typed protocol fixture, not an alternate simulation oracle. */
function fixture() {
  const row = Object.fromEntries(numericFields.map((key) => [key, 0])) as unknown as Row;
  row.battery_available = true;
  const summary = Object.fromEntries(
    [
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
    ].map((key) => [key, 0]),
  );
  summary.hours = 1;
  const result = {
    policy: 1,
    rows: [row],
    summary,
    verification: {
      reference_verified: true,
      energy_ledgers_verified: true,
      max_residual_wh: 0,
      absolute_tolerance_wh: 1e-7,
      relative_tolerance: 1e-12,
    },
  };
  return {
    id: "a".repeat(64),
    name: "test",
    input: {
      config: { capacity_wh: 20000, initial_wh: 10000, reserve_pct: 25, policy: 1 },
      profile: [{}],
      provenance: "Synthetic fixture",
    },
    settings: {
      scenario: "feeder-outage",
      policy: 1,
      capacity: 20000,
      initial: 50,
      reserve: 25,
      precharge: 0,
    },
    selected: result,
    comparison: structuredClone({ ...result, policy: 0 }),
  };
}
describe("bounded protocol", () => {
  test("accepts valid finite evidence", () =>
    expect(parseRun(fixture()).selected.rows).toHaveLength(1));
  test.each([null, {}, { id: "x" }, []])("rejects invalid identity %s", (value) =>
    expect(() => parseRun(value)).toThrow(),
  );
  test.each(numericFields)("rejects nonfinite %s", (key) => {
    const run = fixture();
    run.selected.rows[0]![key] = NaN;
    expect(() => parseRun(run)).toThrow();
  });
  test.each([
    "state",
    "reference",
    "ledger",
    "counterfactual",
    "summary",
    "profile",
    "settings",
    "capacity",
    "availability",
    "residual",
    "length",
  ])("fails closed: %s", (kind) => {
    const run = fixture();
    if (kind === "state") run.selected.rows[0]!.end_wh = 20001;
    if (kind === "reference") run.comparison.verification.reference_verified = false;
    if (kind === "ledger") run.selected.verification.energy_ledgers_verified = false;
    if (kind === "counterfactual") run.comparison.policy = 1;
    if (kind === "summary") run.selected.summary.hours = 2;
    if (kind === "profile") run.input.profile = [];
    if (kind === "settings") run.settings.capacity = 999;
    if (kind === "capacity") run.input.config.capacity_wh = 0;
    if (kind === "availability")
      (run.selected.rows[0] as unknown as Record<string, unknown>).battery_available = 1;
    if (kind === "residual") run.selected.verification.max_residual_wh = 1;
    if (kind === "length") run.comparison.rows = [];
    expect(() => parseRun(run)).toThrow();
  });
  test("unavailable coverage remains nullable", () => {
    const run: unknown = fixture();
    (
      run as { selected: { summary: Record<string, unknown> } }
    ).selected.summary.critical_service_pct = null;
    expect(parseRun(run).selected.summary.critical_service_pct).toBeNull();
  });
});
test("formatting does not fabricate unavailable values", () => {
  expect(kwh(null)).toBe("Not applicable");
  expect(kwh(undefined)).toBe("Not applicable");
  expect(kwh(1250)).toBe("1.25");
  expect(kwh(0)).toBe("0");
  expect(policyName(1)).toContain("reserve");
  expect(policyName(0)).toBe("Serve all loads");
});
test("flow totals keep grid top-up and source split explicit", () => {
  const row = fixture().selected.rows[0]!;
  row.solar_wh = 100;
  row.wind_wh = 200;
  row.grid_critical_wh = 40;
  row.charge_grid_wh = 50;
  row.battery_flexible_wh = 60;
  row.charge_renewable_wh = 70;
  expect(totals(row)).toEqual({
    renewable: 300,
    grid: 90,
    discharge: 60,
    charge: 120,
    critical: 40,
    flexible: 60,
  });
});
