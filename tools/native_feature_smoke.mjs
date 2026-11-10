/**
 * Frozen feeder-loss replay acceptance by Jason Stys.
 * Function: runNativeJourney callback; variables: original/stressed profiles and exact downloaded input.
 * Synthetic hourly accounting is not electrical control or outage-survival assurance.
 * Symbol locations: docs/CODE_INDEX.md.
 */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { expect } from "@playwright/test";
import { runNativeJourney } from "./native_browser.mjs";

await runNativeJourney(async ({ page, request }) => {
  await page.goto("/");
  await expect(page.locator("#status")).toContainText("Verified");
  await expect(page.locator("#feeder-loss")).toContainText(
    "Independent reference/energy checks: passed",
  );
  const response = await request.get("/api/run");
  assert.equal(response.status(), 200);
  const report = await response.json();
  assert.equal(report.input.profile.length, 48);
  assert.deepEqual(report.feeder_loss.input.config, report.input.config);
  for (let index = 0; index < report.input.profile.length; index += 1) {
    assert.deepEqual(report.feeder_loss.input.profile[index], {
      ...report.input.profile[index],
      grid_limit_w: 0,
    });
  }
  for (const policy of [report.feeder_loss.selected, report.feeder_loss.comparison]) {
    assert.equal(policy.verification.reference_verified, true);
    assert.equal(policy.verification.energy_ledgers_verified, true);
    assert.equal(policy.summary.grid_import_wh, 0);
  }
  assert.ok(
    Math.abs(
      report.feeder_loss.critical_unserved_delta_wh -
        (report.feeder_loss.selected.summary.critical_unserved_wh -
          report.selected.summary.critical_unserved_wh),
    ) < 1e-8,
  );
  const identity = await page.locator("#identity").textContent();
  const pending = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Download feeder-loss replay input", exact: true })
    .click();
  const downloaded = await pending;
  assert.deepEqual(
    JSON.parse(await readFile(await downloaded.path(), "utf8")),
    report.feeder_loss.input,
  );
  await expect(page.locator("#identity")).toHaveText(identity);
  await expect(page.locator("#showing")).toContainText("feeder-outage");
});
