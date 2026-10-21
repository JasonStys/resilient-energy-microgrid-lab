# Model, units and honest interpretation

## Time and state

All input powers are **hourly average W**, integrated over exactly one hour to Wh. An input `solar_w=1000` means 1000 Wh supplied in that slot, not a measured peak, forecast or continuous waveform. Index `h` denotes `[h,h+1)`; end stored energy is at `h+1`. UI converts Wh to kWh by dividing by 1000. Initial energy and terminal energy are explicit; no terminal restoration constraint is imposed.

The single ideal AC bus has renewable generation, a capped import-only feeder, critical/flexible load and one battery. No exports, generator, battery self-discharge or infrastructure network is represented. Battery state is an abstract usable energy store, not a chemistry/temperature/state-of-health estimate. The UI calls it a chemical store only to distinguish stored energy from delivered AC energy.

## Allocation order

1. Renewable generation supplies critical, then flexible demand.
2. Feeder imports cover remaining critical, then flexible demand, up to its limit. Grid is used before battery, even if energy prices might favor another choice.
3. Available battery covers remaining critical demand, then flexible demand, within combined discharge rate and stored-energy limits. Policy 0 allows flexible discharge down to zero. Policy 1 allows flexible discharge only above `capacity × reserve_pct/100`; critical service can consume this reserve. Reserve is not a forced minimum state.
4. Only if no battery energy was discharged in this slot, unused renewables charge within rate/headroom. If explicit top-up is enabled, spare feeder capacity also charges toward full, sharing the charger limit. A tripped/unavailable battery has zero charge/discharge and retains its prior state.
5. Remaining renewables are curtailed. Remaining demands are unserved, not silently dropped. No simultaneous charge/discharge is allowed, even if sub-hour cycling could have occurred in reality.

`charge_limit_w` limits AC input; `discharge_limit_w` limits delivered AC output. With efficiencies `ηc`, `ηd`:

```text
Eend = Estart + charge_input × ηc − delivered_discharge / ηd
charge_loss = charge_input × (1 − ηc)
discharge_loss = delivered_discharge × (1/ηd − 1)
```

Efficiencies are integer permille inputs (500..1000), e.g. 950/1000 and 900/1000. These imply 85.5% conversion round-trip efficiency when the same energy is fully cycled under the ideal model; they are illustrative, not measured battery performance.

## Verification

Production code allocates sources first with floats. Independent reference code allocates loads first with `fractions.Fraction` and no production dispatch helpers. Every hourly field and length must match within **1e−7 Wh absolute and 1e−12 relative** tolerance. Separately reconstructed AC-bus, battery-store and combined-system conservation equations, demand balances, continuity, nonnegativity, rate/capacity/feeder bounds, losses, reserve rules and availability are checked with 1e−7 Wh absolute tolerance. Verification happens before display/export; failure emits no partial verified report. Raw rows are rounded to 9 decimal Wh only after checks; summary energy is rounded to 6 decimals. Replay input and deterministic SHA-256 content identity travel with reports. Hashes prove content consistency, not authorship or physical accuracy.

These are independent implementations of the **same simplified assumptions**, not independent experimental validation. Correlated conceptual errors remain possible. Analytical examples and fault injection complement differential tests; no site/physical calibration was performed.

## Metrics

Critical coverage is `(critical demand − critical unserved)/critical demand ×100`, or `null` when demand is zero. It is energy coverage, **not uptime**. First shortage is the first hourly index whose critical-unserved energy exceeds tolerance. Longest shortage run counts adjacent affected slots; neither identifies sub-hour start/end time. Outage means supplied feeder limit equals zero; a constrained nonzero feeder is not counted as a full outage. Fully served critical outage slots require positive critical demand and no critical shortfall. The denominator shown in the UI counts all zero-feeder slots; zero-demand slots do not inflate the numerator.

Reserve recovery is the first connected slot **after any observed zero-feeder slot** with end energy at/above reserve and fully served critical demand. It is not necessarily recovery after the final interruption, exact switching recovery time or a requirement that all flexible demand is served. `null` means absent/not applicable. Direct renewable service excludes battery discharge because stored-energy source provenance is not tracked. There are no renewable-share, costs, emissions, cycle-life or reliability probability claims.

## Data and research

All six 48-hour profiles are invented in `model.configuration`; no external dataset is fetched. Default: 20 kWh capacity, 50% initial, 25% reserve, 5 kW charge/discharge, 95%/90% efficiency, top-up off. Daily solar averages are an explicit 24-number shape, wind repeats six invented values, load changes with hour. Presets include 20-hour feeder loss, 30-hour winter loss with reduced solar/wind, critical surge with a constrained feeder, 8 battery-trip hours during feeder loss, and zero-demand control. Exact generation rules, intervals and editable profile are source-controlled; see `examples/station.json` and code index.

Research context: [REopt curriculum](https://www.nlr.gov/reopt/curriculum/what-is-reopt) explains sizing/dispatch/outage-analysis tools; [REopt overview](https://www.nlr.gov/reopt/about/index) describes optimization capabilities. [SAM battery dispatch documentation](https://samrepo.nlr.gov/help/battery_dispatch_fom.html) describes dispatch choices in a much richer model. Those tools informed the distinction between accounting, dispatch heuristics and optimization; their algorithms/data were not copied or used as an oracle. This lab is not SAM/REopt, is not endorsed by their authors, and does not claim their capabilities.

## Out of scope

AC/DC power flow, voltage/frequency/reactive power, transmission/distribution, protection coordination, islanding/switching transients, generator dynamics, battery chemistry/temperature/aging, weather uncertainty, forecasting, optimization, tariffs, costs/emissions, real SCADA/PLC/device interfaces and safety-critical use. Do not size, operate or certify a real installation with this application.
