# Compare complete feeder loss

The stress panel evaluates both existing dispatch policies after replacing **every hourly feeder limit with zero**. It preserves initial battery energy, capacity/rate/efficiency limits, reserves, precharge policy, loads, renewable output and battery availability. This is a declared hypothetical outage over the full supplied profile, separate from the original hourly replay.

Both stressed traces must pass the exact-rational reference and independent energy audits before publication. The panel reports critical/flexible unserved energy, ending storage and selected-policy differences from the original profile. Differences may depend on storage/precharge interactions; neither policy is universally optimal. No-demand service remains undefined. Full JSON/HTML/history contain stressed rows, verification, and the exact derived input. Download the derived input to replay it with the strict CLI; original input is never modified.

These are fictional hourly adequacy calculations, not electrical power-flow/protection/transient analysis, forecasts, guarantees of outage survival or instructions to control real infrastructure. The feature adds no live device connection.
