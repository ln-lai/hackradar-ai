import { test, expect } from "@playwright/test";

test("default matches, transparent details and local preparation brief", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "The Agent Foundry", exact: true })).toBeVisible();
  await expect(page.locator(".event-card")).toHaveCount(4);
  await page.getByRole("button", { name: "View match" }).first().click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByText("This is a fictional demonstration.", { exact: false })).toBeVisible();
  await expect(dialog.getByRole("heading", { name: "Why this match?" })).toBeVisible();
  await dialog.getByRole("button", { name: "Generate local brief" }).click();
  await expect(dialog.getByText("LOCAL TEMPLATE", { exact: true })).toBeVisible();
  await expect(dialog.getByText("Application starter", { exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
});

test("saving persists after reload and appears in saved view", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Save The Agent Foundry", exact: true }).click();
  await page.reload();
  await page.getByRole("button", { name: /^Saved/ }).click();
  await expect(page.locator(".event-card")).toHaveCount(1);
  await page.getByRole("button", { name: "Unsave The Agent Foundry", exact: true }).click();
  await expect(page.getByRole("heading", { name: "A little room for possibility." })).toBeVisible();
});

test("filters, online toggle, search and sorting affect actual results", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Include online events").check();
  await page.getByRole("button", { name: "Update my radar" }).click();
  await expect(page.getByRole("heading", { name: "Global Agents Sprint", exact: true })).toBeVisible();
  await page.getByLabel("Sort events").selectOption("date");
  await expect(page.locator(".event-card h3").first()).toHaveText("Global Agents Sprint");
  await page.getByRole("searchbox", { name: "Search events" }).fill("zero to one");
  await expect(page.locator(".event-card")).toHaveCount(1);
  await expect(page.locator(".event-card h3")).toHaveText("Zero to One: AI Build Weekend");
});

test("hide examples yields honest empty state", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Show example events").uncheck();
  await page.getByRole("button", { name: "Update my radar" }).click();
  await expect(page.locator(".provenance.example")).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Nothing on this frequency. Yet." })).toBeVisible();
});

test("import rejects an unsupported URL with useful feedback", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Add an event" }).click();
  await page.getByLabel("Event URL").fill("https://localhost/private");
  await page.getByRole("button", { name: "Import & deduplicate" }).click();
  await expect(page.getByRole("dialog").getByRole("alert")).toContainText("Use an HTTPS event page on Luma");
});

test("same-origin API works and cross-origin requests are rejected", async ({ request, baseURL }) => {
  const allowed = await request.post("/api/search", { data: {}, headers: { Origin: baseURL! } });
  expect(allowed.status()).toBe(200);
  const blocked = await request.post("/api/search", { data: {}, headers: { Origin: "https://untrusted.example" } });
  expect(blocked.status()).toBe(403);
});

test("JSON import persists once and is labeled unverified", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Where are you building?").fill("Bristol");
  await page.getByRole("button", { name: "Update my radar" }).click();
  await page.getByRole("button", { name: "Add an event" }).click();
  await page.getByRole("button", { name: "JSON import", exact: true }).click();
  const start = new Date(Date.now() + 3 * 86400000).toISOString();
  await page.getByLabel("Event JSON").fill(JSON.stringify({ events: [{
    title: "Integration fixture — fictional agents hackathon",
    description: "Fictional integration fixture for AI agents, FDE and startups.",
    start_at: start, city: "Bristol", url: "https://example.com/e2e-fixture", tags: ["AI Agents", "FDE", "Startups"],
  }] }));
  await page.getByRole("button", { name: "Import & deduplicate" }).click();
  await expect(page.getByRole("dialog").getByRole("status")).toContainText("1 event added");
  await page.getByRole("button", { name: "Import & deduplicate" }).click();
  await expect(page.getByRole("dialog").getByRole("status")).toContainText("0 events added · 1 duplicate merged");
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.reload();
  await expect(page.locator(".event-card")).toHaveCount(1);
  await expect(page.locator(".event-card")).toContainText("User import · unverified");
});

test("mobile layout, filters and dialogs fit the viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "The Agent Foundry", exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.getByRole("button", { name: "Filters", exact: true }).click();
  await expect(page.getByLabel("Where are you building?")).toBeVisible();
  await page.getByLabel("Your time window").selectOption("7");
  await page.getByRole("button", { name: "Update my radar" }).click();
  await expect(page.locator(".event-card")).toHaveCount(1);
  await page.getByRole("button", { name: "View match" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  expect(await page.getByRole("dialog").evaluate(el => el.scrollWidth <= el.clientWidth)).toBeTruthy();
});
