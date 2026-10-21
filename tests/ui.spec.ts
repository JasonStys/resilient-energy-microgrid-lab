/** Real three-engine energy workflow and accessibility tests by Jason Stys. Index: docs/CODE_INDEX.md. */
import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFile } from "node:fs/promises";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#status")).toContainText("Verified");
});

test("real model, two policies, visible chart, author and help", async ({ page }) => {
  await expect(page.locator("#comparison tr")).toHaveCount(2);
  await expect(page.locator("#identity")).toHaveText(/^[a-f0-9]{64}$/);
  await expect(page.locator("#coverage")).not.toHaveText("100.00%");
  await expect(page.locator("#verification")).toContainText("Both policy traces");
  const pixels = await page.locator("#storage-chart").evaluate((node) => {
    const canvas = node as HTMLCanvasElement,
      values = canvas.getContext("2d")!.getImageData(0, 0, 1000, 300).data;
    let count = 0;
    for (let i = 3; i < values.length; i += 4) if (values[i]) count++;
    return count;
  });
  expect(pixels).toBeGreaterThan(10000);
  await expect(page.getByRole("link", { name: "User guide" })).toHaveAttribute(
    "href",
    /docs\/USER_GUIDE.md/,
  );
  await expect(page.locator("footer")).toContainText("Jason Stys");
});

test("controls invalidate old evidence then use identical starting profile", async ({ page }) => {
  const before = await page.locator("#identity").textContent();
  await page.locator("#capacity").selectOption("40000");
  await expect(page.locator("#evidence")).toBeHidden();
  await page.getByRole("button", { name: "Compare policies" }).click();
  await expect(page.locator("#status")).toContainText("Verified");
  await expect(page.locator("#identity")).not.toHaveText(before!);
  await expect(page.locator("#downloads a")).toHaveCount(4);
  expect(await page.locator("#downloads a").first().getAttribute("href")).toContain(
    "capacity=40000",
  );
});

test("actual JSON CSV HTML and input downloads", async ({ page }) => {
  for (const format of ["JSON", "CSV", "HTML", "INPUT"]) {
    const waiting = page.waitForEvent("download");
    await page
      .locator("#downloads")
      .getByRole("link", { name: format + " ↓", exact: true })
      .click();
    const download = await waiting,
      path = await download.path();
    expect(path).not.toBeNull();
    const body = await readFile(path!, "utf8");
    if (format === "JSON") {
      const run = JSON.parse(body);
      expect(run.selected.rows).toHaveLength(48);
      expect(run.comparison.verification.reference_verified).toBe(true);
      expect(run.id).toBe(await page.locator("#identity").textContent());
    }
    if (format === "CSV") {
      expect(body.trim().split("\n")).toHaveLength(97);
      expect(body).toContain("policy,");
    }
    if (format === "HTML") {
      expect(body).toContain("Resilient Energy Microgrid Lab");
      expect(body).not.toContain("<script");
    }
    if (format === "INPUT") expect(JSON.parse(body).config.capacity_wh).toBe(20000);
  }
});

test("zero-demand has no invented coverage or shortage", async ({ page }) => {
  await page.locator("#scenario").selectOption("zero-demand");
  await page.locator("#run").click();
  await expect(page.locator("#coverage")).toHaveText("Not applicable");
  await expect(page.locator("#critical-unserved")).toHaveText("0");
  await expect(page.locator("#service-detail")).toContainText("none in this supplied profile");
});

test("battery trip inspection reflects unavailable no-flow hour", async ({ page }) => {
  await page.locator("#scenario").selectOption("battery-trip");
  await page.locator("#run").click();
  await expect(page.locator("#status")).toContainText("Verified");
  await page.locator("#hour").fill("22");
  await expect(page.locator("#interval-state")).toContainText(
    "battery unavailable / no charge or discharge",
  );
  await expect(page.locator("#flow-battery")).toHaveText("0 · 0");
});

test("failed and malformed responses hide all prior evidence", async ({ page }) => {
  await page.route("**/api/run?**", (route) => route.fulfill({ status: 500, body: "failure" }));
  await page.locator("#run").click();
  await expect(page.locator("#status")).toContainText("No verified evidence");
  await expect(page.locator("#evidence")).toBeHidden();
  await page.route("**/api/run?**", (route) =>
    route.fulfill({ contentType: "application/json", body: '{"selected":{}}' }),
  );
  await page.locator("#run").click();
  await expect(page.locator("#status")).toContainText("No verified evidence");
  await expect(page.locator("#evidence")).toBeHidden();
});

test("slow old request cannot resurrect stale evidence", async ({ page }) => {
  let release!: () => void;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  let entered!: () => void;
  const started = new Promise<void>((resolve) => {
    entered = resolve;
  });
  await page.route("**/api/run?**", async (route) => {
    const response = await route.fetch();
    entered();
    await held;
    await route.fulfill({ response });
  });
  await page.locator("#run").click();
  await started;
  await page.locator("#initial").selectOption("75");
  release();
  await expect(page.locator("#status")).toContainText("Controls changed");
  await expect(page.locator("#evidence")).toBeHidden();
});

test("provenance is text, never executable markup", async ({ page, request }) => {
  const response = await request.get("/api/run"),
    run = await response.json();
  run.input.provenance = '<img src=x onerror="window.injection=true">';
  await page.route("**/api/run?**", (route) => route.fulfill({ json: run }));
  await page.locator("#run").click();
  await expect(page.locator("#provenance")).toHaveText(run.input.provenance);
  await expect(page.locator("#provenance img")).toHaveCount(0);
});

test("keyboard mobile and accessible comparison region", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator("#scenario").focus();
  await page.keyboard.press("Tab");
  await expect(page.locator("#policy")).toBeFocused();
  await page.getByRole("region", { name: "Scrollable policy comparison" }).focus();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
});

test("finite server surface and loopback security", async ({ request }) => {
  expect((await request.get("/api/run?policy=9")).status()).toBe(400);
  expect(
    (await request.get("/api/run", { headers: { Origin: "https://outside.invalid" } })).status(),
  ).toBe(403);
  expect((await request.post("/api/run")).status()).toBe(405);
  expect((await request.get("/.env")).status()).toBe(404);
});
