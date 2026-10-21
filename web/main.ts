/** FIELDGRID energy instrument by Jason Stys; functions, state and DOM: docs/CODE_INDEX.md. */
import "./style.css";
import { kwh, parseRun, policyName, totals, type Run, type Result } from "./contracts";
document.querySelector<HTMLDivElement>("#app")!.innerHTML = /* HTML */ ` <a
    class="skip"
    href="#workspace"
    >Skip to energy experiment</a
  >
  <header>
    <a class="brand" href="#workspace"
      ><span class="brand-mark">▥</span>FIELDGRID <small>RESILIENT ENERGY MICROGRID LAB</small></a
    >
    <nav aria-label="Project">
      <a href="#method">Method & limits</a
      ><a href="https://github.com/JasonStys/resilient-energy-microgrid-lab">Source ↗</a
      ><a href="https://github.com/JasonStys">Jason Stys ↗</a>
    </nav>
  </header>
  <main id="workspace">
    <section class="intro">
      <div>
        <p class="eyebrow">RESEARCH STATION / 48 SYNTHETIC HOURS</p>
        <h1>Keep the essentials<br /><em>in the equation.</em></h1>
        <p class="lede">
          Renewables fluctuate. Feeders fail. Compare battery policies—and account for every
          watt-hour before calling a system resilient.
        </p>
      </div>
      <aside>
        <span class="pill">OFFLINE · NO INFRASTRUCTURE CONTROL</span>
        <p>
          Python dispatch.<br />Exact-rational reference.<br />Three independent energy ledgers.
        </p>
      </aside>
    </section>
    <form id="controls" aria-label="Energy experiment controls">
      <label class="case"
        >Scenario<select id="scenario">
          <option value="feeder-outage">Station / feeder outage</option>
          <option value="clear-day">Clear weather / connected</option>
          <option value="winter-drought">Low renewables / long outage</option>
          <option value="load-surge">Critical load surge</option>
          <option value="battery-trip">Battery unavailable</option>
          <option value="zero-demand">No demand / curtailment</option>
        </select></label
      ><label
        >Dispatch policy<select id="policy">
          <option value="1">Protect critical reserve</option>
          <option value="0">Serve all loads</option>
        </select></label
      ><label
        >Battery capacity<select id="capacity">
          <option value="20000">20 kWh</option>
          <option value="10000">10 kWh</option>
          <option value="40000">40 kWh</option>
        </select></label
      ><label
        >Initial energy<select id="initial">
          <option value="50">50%</option>
          <option value="25">25%</option>
          <option value="75">75%</option>
        </select></label
      ><label
        >Flexible-load reserve<select id="reserve">
          <option value="25">25%</option>
          <option value="0">0%</option>
          <option value="50">50%</option>
        </select></label
      ><label
        >Feeder battery top-up<select id="precharge">
          <option value="0">Off</option>
          <option value="1">On / fill battery</option>
        </select></label
      ><button id="run" type="submit">Compare policies ↗</button>
    </form>
    <p id="status" role="status" aria-live="polite">Checking the energy ledgers…</p>
    <div id="evidence" hidden>
      <div class="metrics">
        <div>
          <span>CRITICAL LOAD SERVED</span><strong id="coverage"></strong
          ><small>hourly energy coverage / not uptime</small>
        </div>
        <div>
          <span>CRITICAL ENERGY UNSERVED</span><strong id="critical-unserved"></strong
          ><small>kWh over the complete profile</small>
        </div>
        <div>
          <span>FEEDER ENERGY IMPORTED</span><strong id="imported"></strong
          ><small>kWh / includes selected top-up</small>
        </div>
        <div>
          <span>BATTERY ENERGY AT END</span><strong id="terminal"></strong
          ><small>kWh remaining / chemical store</small>
        </div>
      </div>
      <section class="panel">
        <div class="section-head">
          <div>
            <p class="eyebrow">01 / SAME PROFILE · TWO POLICIES</p>
            <h2>What you preserve today<br />changes what remains tomorrow.</h2>
          </div>
          <p class="muted" id="showing"></p>
        </div>
        <canvas
          id="storage-chart"
          width="1000"
          height="300"
          role="img"
          aria-label="Selected and counterfactual stored battery energy versus elapsed hours; shaded slots indicate unavailable feeder; exact hourly values are in inspector and CSV"
        ></canvas>
        <div class="legend">
          <span><i class="line"></i>Selected policy</span
          ><span><i class="alternate"></i>Other policy</span
          ><span><i class="outage"></i>No feeder</span
          ><span>Dashed horizontal: flexible-load reserve · kWh / elapsed hour</span>
        </div>
        <p class="notice">
          Critical loads may use the reserve. Only flexible battery service is restricted by it.
          Neither policy is an optimal schedule or a real-grid safety determination.
        </p>
        <div
          class="table-wrap"
          tabindex="0"
          role="region"
          aria-label="Scrollable policy comparison"
        >
          <table>
            <caption>
              Both policies start with identical battery energy and supplied hourly profile.
            </caption>
            <thead>
              <tr>
                <th>Policy</th>
                <th>Critical coverage</th>
                <th>Critical unserved / kWh</th>
                <th>Flexible unserved / kWh</th>
                <th>Feeder import / kWh</th>
                <th>End stored / kWh</th>
              </tr>
            </thead>
            <tbody id="comparison"></tbody>
          </table>
        </div>
      </section>
      <section class="panel">
        <div class="section-head">
          <div>
            <p class="eyebrow">02 / FOLLOW THE WATT-HOURS</p>
            <h2>One interval.<br />A complete energy ledger.</h2>
          </div>
          <p class="muted">
            One-hour average inputs.<br />No voltage, frequency or switching model.
          </p>
        </div>
        <label class="scrub"
          >Inspect profile hour <output id="hour-label">0–1 h</output
          ><input id="hour" type="range" min="0" max="47" value="0"
        /></label>
        <p id="interval-state" class="notice"></p>
        <div class="flow" aria-label="Selected hour energy flows">
          <div class="node">
            <span>SOLAR + WIND</span><strong id="flow-renewable"></strong
            ><small>kWh generated</small>
          </div>
          <div class="node bus">
            <span>HOURLY AC BUS</span><strong id="flow-served"></strong
            ><small>kWh supplied to loads</small>
          </div>
          <div class="node critical">
            <span>CRITICAL LOAD</span><strong id="flow-critical"></strong
            ><small>kWh served / demand</small>
          </div>
          <div class="node">
            <span>FEEDER</span><strong id="flow-grid"></strong
            ><small>kWh imported / available limit</small>
          </div>
          <div class="node">
            <span>BATTERY</span><strong id="flow-battery"></strong
            ><small>kWh delivered · charge input</small>
          </div>
          <div class="node flexible">
            <span>FLEXIBLE LOAD</span><strong id="flow-flexible"></strong
            ><small>kWh served / demand</small>
          </div>
        </div>
        <div id="interval-detail" class="inspection" aria-live="polite"></div>
        <p class="muted">
          Storage conversion losses are reported separately. Curtailed renewable energy is not
          silently counted as delivered power. Stored energy has no tracked renewable/grid
          provenance.
        </p>
      </section>
      <section class="panel">
        <p class="eyebrow">03 / SERVICE GAPS ARE EVIDENCE</p>
        <h2>See the shortage.<br />Keep its limits visible.</h2>
        <canvas
          id="shortfall-chart"
          width="1000"
          height="200"
          role="img"
          aria-label="Critical and flexible unserved hourly energy; exact values are available in exported rows"
        ></canvas>
        <div class="legend">
          <span><i class="critical-key"></i>Critical unserved</span
          ><span><i class="flexible-key"></i>Flexible unserved</span
          ><span>kWh per hourly slot / not sub-hour outage timing</span>
        </div>
        <p id="service-detail" class="notice"></p>
      </section>
      <section class="export">
        <div>
          <p class="eyebrow">04 / REPRODUCIBLE, NOT BLACK-BOX</p>
          <h2>Take the assumptions<br />with the result.</h2>
          <p>
            Complete inputs, both policy traces, conversion losses, reference checks and content
            identity. SQLite history is explicit through the CLI, not a hidden browser write.
          </p>
          <div id="downloads" class="downloads"></div>
        </div>
        <div>
          <span class="eyebrow">REPORT SHA-256</span><code id="identity"></code>
          <p id="verification" class="muted"></p>
          <p id="provenance" class="muted"></p>
        </div>
      </section>
    </div>
    <section id="method" class="method">
      <p class="eyebrow">METHOD / ENERGY ADEQUACY IS NOT ELECTRICAL SAFETY</p>
      <h2>A full battery is a state.<br /><em>Resilience needs context.</em></h2>
      <div class="method-grid">
        <article>
          <h3>01 · Respect energy limits</h3>
          <p>
            Finite capacity, charge/discharge rates and separate efficiencies constrain every hourly
            allocation. The battery cannot charge and discharge simultaneously or operate while
            unavailable.
          </p>
        </article>
        <article>
          <h3>02 · Compare fairly</h3>
          <p>
            Both heuristics receive the same profile and initial store. Serving flexible loads now
            can reduce later reserves; feeder top-up can increase imports. No universal winning
            policy is claimed.
          </p>
        </article>
        <article>
          <h3>03 · Verify, then interpret</h3>
          <p>
            Source-first floating dispatch must agree with an independent load-first rational model.
            Bus, storage and combined ledgers must close. This does not validate real batteries,
            wiring or protection.
          </p>
        </article>
      </div>
      <p>
        <a
          href="https://github.com/JasonStys/resilient-energy-microgrid-lab/blob/main/docs/USER_GUIDE.md"
          >User guide ↗</a
        >
        ·
        <a href="https://github.com/JasonStys/resilient-energy-microgrid-lab/issues"
          >Help / report an issue ↗</a
        >
      </p>
    </section>
  </main>
  <footer>
    <span>Designed and engineered by <a href="https://github.com/JasonStys">Jason Stys</a></span
    ><span>SYNTHETIC CIVILIAN ENERGY EDUCATION · NO ENDORSEMENT</span>
  </footer>`;
/** Resolve uniquely owned fixed-template elements; no report text is interpreted as HTML. */
function element<T extends HTMLElement>(id: string): T {
  return document.getElementById(id) as T;
}
let current: Run | null = null,
  requestVersion = 0;
const status = element("status"),
  evidence = element("evidence"),
  form = element<HTMLFormElement>("controls"),
  button = element<HTMLButtonElement>("run");
/** Return finite control query; export links are later built from the accepted run, not mutable controls. */
function query() {
  return new URLSearchParams(
    ["scenario", "policy", "capacity", "reserve", "initial", "precharge"].map((key) => [
      key,
      element<HTMLSelectElement>(key).value,
    ]),
  );
}
/** Draw both actual energy traces on the same fixed capacity axis and annotate islanded slots. */
function drawStorage(): void {
  if (!current) return;
  const r = current,
    canvas = element<HTMLCanvasElement>("storage-chart"),
    ctx = canvas.getContext("2d")!,
    hours = r.selected.rows.length,
    capacity = r.input.config.capacity_wh;
  const x = (h: number) => 65 + (h / hours) * 915,
    y = (wh: number) => 260 - (wh / capacity) * 235;
  ctx.clearRect(0, 0, 1000, 300);
  ctx.font = "13px monospace";
  ctx.fillStyle = "#ede6ce";
  for (const row of r.selected.rows)
    if (row.grid_limit_wh === 0) ctx.fillRect(x(row.hour), 20, 915 / hours, 240);
  ctx.strokeStyle = "#c5cec4";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 2; i++) {
    const value = (capacity * i) / 2;
    ctx.beginPath();
    ctx.moveTo(65, y(value));
    ctx.lineTo(980, y(value));
    ctx.stroke();
    ctx.fillStyle = "#465449";
    ctx.fillText(kwh(value), 2, y(value) - 4);
  }
  ctx.strokeStyle = "#697369";
  ctx.setLineDash([3, 5]);
  ctx.beginPath();
  ctx.moveTo(65, y((capacity * r.input.config.reserve_pct) / 100));
  ctx.lineTo(980, y((capacity * r.input.config.reserve_pct) / 100));
  ctx.stroke();
  for (const [result, color, dash] of [
    [r.comparison, "#a15d31", [6, 4]],
    [r.selected, "#215a41", []],
  ] as const) {
    ctx.strokeStyle = color;
    ctx.setLineDash([...dash]);
    ctx.lineWidth = 2.8;
    ctx.beginPath();
    ctx.moveTo(x(0), y(r.input.config.initial_wh));
    for (const row of result.rows) ctx.lineTo(x(row.hour + 1), y(row.end_wh));
    ctx.stroke();
  }
  ctx.setLineDash([]);
  ctx.fillStyle = "#465449";
  for (let i = 0; i <= 4; i++) {
    const h = (hours * i) / 4;
    ctx.fillText(`${h} h`, Math.min(946, x(h) - 10), 287);
  }
  const hour = Number(element<HTMLInputElement>("hour").value);
  ctx.strokeStyle = "#1b2b22";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(x(hour + 0.5), 20);
  ctx.lineTo(x(hour + 0.5), 260);
  ctx.stroke();
}
/** Render actual critical/flexible shortage bars; no demand or shortage creates no invented event. */
function drawShortfall(): void {
  if (!current) return;
  const rows = current.selected.rows,
    ctx = element<HTMLCanvasElement>("shortfall-chart").getContext("2d")!,
    maximum = Math.max(
      1000,
      ...rows.map((row) => row.critical_unserved_wh + row.flexible_unserved_wh),
    );
  ctx.clearRect(0, 0, 1000, 200);
  const width = 915 / rows.length;
  ctx.font = "13px monospace";
  ctx.fillStyle = "#465449";
  ctx.fillText(kwh(maximum), 2, 20);
  ctx.fillText("0", 2, 169);
  ctx.strokeStyle = "#c5cec4";
  ctx.beginPath();
  ctx.moveTo(65, 170);
  ctx.lineTo(980, 170);
  ctx.stroke();
  for (const row of rows) {
    const critical = (row.critical_unserved_wh / maximum) * 145,
      flexible = (row.flexible_unserved_wh / maximum) * 145;
    ctx.fillStyle = "#a54837";
    ctx.fillRect(65 + row.hour * width, 170 - critical, width * 0.85, critical);
    ctx.fillStyle = "#bd8b2e";
    ctx.fillRect(65 + row.hour * width, 170 - critical - flexible, width * 0.85, flexible);
  }
  for (let i = 0; i <= 4; i++)
    ctx.fillText(`${(rows.length * i) / 4} h`, Math.min(946, 55 + (915 * i) / 4), 193);
}
/** Inspect the accepted hourly interval and explicit flow splits; no real sensor values are shown. */
function inspect(): void {
  if (!current) return;
  const hour = Number(element<HTMLInputElement>("hour").value),
    row = current.selected.rows[hour]!,
    t = totals(row);
  element("hour-label").textContent = `${hour}–${hour + 1} h`;
  element("interval-state").textContent =
    `${row.grid_limit_wh === 0 ? "Feeder unavailable" : "Feeder available within supplied limit"} · battery ${row.battery_available ? "available" : "unavailable / no charge or discharge"}. ${policyName(current.selected.policy)}.`;
  for (const [id, text] of [
    ["flow-renewable", kwh(t.renewable)],
    ["flow-served", kwh(t.critical + t.flexible)],
    ["flow-critical", `${kwh(t.critical)} / ${kwh(row.critical_demand_wh)}`],
    ["flow-flexible", `${kwh(t.flexible)} / ${kwh(row.flexible_demand_wh)}`],
    ["flow-grid", `${kwh(t.grid)} / ${kwh(row.grid_limit_wh)}`],
    ["flow-battery", `${kwh(t.discharge)} · ${kwh(t.charge)}`],
  ])
    element(id!).textContent = text!;
  element("interval-detail").textContent =
    `Stored ${kwh(row.start_wh)} → ${kwh(row.end_wh)} kWh · curtailed ${kwh(row.curtailed_wh)} kWh · charge loss ${kwh(row.charge_loss_wh)} kWh · discharge loss ${kwh(row.discharge_loss_wh)} kWh · critical unserved ${kwh(row.critical_unserved_wh)} kWh · flexible unserved ${kwh(row.flexible_unserved_wh)} kWh.`;
  drawStorage();
}
/** Convert unavailable service metrics to a label, never a fabricated zero or 100 percent. */
function coverage(result: Result) {
  const value = result.summary.critical_service_pct;
  return value === null ? "Not applicable" : `${value!.toFixed(2)}%`;
}
/** Render finite verified reports with text nodes and explicit same-origin download intent. */
function render(run: Run): void {
  current = run;
  evidence.hidden = false;
  const selected = run.selected.summary;
  element("coverage").textContent = coverage(run.selected);
  element("critical-unserved").textContent = kwh(selected.critical_unserved_wh);
  element("imported").textContent = kwh(selected.grid_import_wh);
  element("terminal").textContent = kwh(selected.end_wh);
  element("showing").textContent =
    `Showing ${run.name} · ${run.selected.rows.length} hourly intervals · selected: ${policyName(run.selected.policy)}.`;
  element("comparison").replaceChildren(
    ...[run.selected, run.comparison].map((result) => {
      const tr = document.createElement("tr");
      for (const text of [
        policyName(result.policy) + (result === run.selected ? " / selected" : ""),
        coverage(result),
        kwh(result.summary.critical_unserved_wh),
        kwh(result.summary.flexible_unserved_wh),
        kwh(result.summary.grid_import_wh),
        kwh(result.summary.end_wh),
      ]) {
        const td = document.createElement("td");
        td.textContent = text;
        tr.append(td);
      }
      return tr;
    }),
  );
  element<HTMLInputElement>("hour").max = String(run.selected.rows.length - 1);
  element<HTMLInputElement>("hour").value = "0";
  const first = selected.first_critical_shortfall_hour,
    recovery = selected.reserve_recovery_hour;
  element("service-detail").textContent =
    `First critical shortage: ${first === null ? "none in this supplied profile" : `hour ${first}`}. Longest run of critical-shortfall slots: ${selected.longest_critical_shortfall_run_hours} h. Fully served critical-demand slots with no feeder: ${selected.fully_served_critical_outage_hours} / ${selected.outage_hours} outage slots. Reserve recovery on a later connected slot: ${recovery === null ? "not observed / not applicable" : `hour ${recovery}`}. These are hourly slot metrics, not precise blackout timing.`;
  element("identity").textContent = run.id;
  element("provenance").textContent = run.input.provenance;
  element("verification").textContent =
    `Both policy traces passed rational reference and bus/storage/system ledger checks at 1e−7 Wh absolute tolerance. Largest reconstructed residual: ${Math.max(run.selected.verification.max_residual_wh, run.comparison.verification.max_residual_wh).toExponential(2)} Wh.`;
  element("downloads").replaceChildren(
    ...["json", "csv", "html", "input"].map((kind) => {
      const a = document.createElement("a"),
        params = new URLSearchParams(
          Object.entries(run.settings).map(([key, value]) => [key, String(value)]),
        );
      params.set("format", kind);
      a.href = "/api/report?" + params;
      a.download = "";
      a.textContent = kind.toUpperCase() + " ↓";
      return a;
    }),
  );
  inspect();
  drawShortfall();
}
/** Gate every response by request generation; failures and control changes hide stale evidence. */
async function run(): Promise<void> {
  const version = ++requestVersion;
  current = null;
  evidence.hidden = true;
  button.disabled = true;
  status.textContent = "Comparing both policies with exact rational arithmetic and energy ledgers…";
  try {
    const response = await fetch("/api/run?" + query(), { signal: AbortSignal.timeout(15000) });
    if (!response.ok) throw new Error("Request failed");
    const data = await response.json();
    if (version !== requestVersion) return;
    render(parseRun(data));
    status.textContent =
      "Verified · both policies agree with the rational reference; all three energy ledgers close.";
  } catch {
    if (version !== requestVersion) return;
    current = null;
    evidence.hidden = true;
    status.textContent =
      "No verified evidence available. Check local inputs and retry. Previous results are hidden.";
  } finally {
    if (version === requestVersion) button.disabled = false;
  }
}
form.addEventListener("submit", (event) => {
  event.preventDefault();
  void run();
});
form.addEventListener("change", () => {
  requestVersion++;
  current = null;
  evidence.hidden = true;
  button.disabled = false;
  status.textContent = "Controls changed. Compare policies to create new verified evidence.";
});
element("hour").addEventListener("input", inspect);
void run();
