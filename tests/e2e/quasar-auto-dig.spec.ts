import { expect, test } from "@playwright/test";

const localDocument = {
  _id: "starintel:analysis:e2e-local-finding",
  dataset: "complete-corpus",
  dtype: "analysis",
  schema_version: "0.9.0",
  version: 1,
  date_added: "2026-07-27T00:00:00Z",
  date_updated: "2026-07-27T00:00:00Z",
  title: "E2E local finding",
  summary: "Created inside embedded Quasar and mirrored into Auto-Dig local storage.",
  sources: [],
  evidence: [],
  data: {
    question: "Does local embedded state persist?",
    method: "playwright",
    input_ids: [],
    finding_ids: [],
    findings: ["Local state persists after reload."],
    conclusions: [],
    recommendations: [],
    counterarguments: [],
    limitations: [],
    unresolved: [],
    confidence: 1
  },
  extensions: { auto_dig: { kind: "finding", e2e: true } }
};

function issueDestination(url: string) {
  const parsed = new URL(url);
  if (parsed.hostname === "github.com" && parsed.pathname === "/login") {
    return parsed.searchParams.get("return_to") || "";
  }
  return url;
}

test("runs a complete local Auto-Dig investigation through embedded Quasar", async ({ page }) => {
  await page.goto("/quasar/index.html?dataset=complete-corpus&run=e2e-run");
  const quasar = page.frameLocator("#quasar-frame");

  await expect(quasar.getByText("Auto-Dig graph operator")).toBeVisible();
  await quasar.getByRole("link", { name: "Add document" }).click();
  await quasar.getByRole("button", { name: "Inspect JSON" }).click();
  await quasar.getByLabel("Complete document JSON").fill(JSON.stringify(localDocument, null, 2));
  await quasar.getByRole("button", { name: "Save" }).click();
  await expect(quasar.getByRole("heading", { name: "E2E local finding" })).toBeVisible();

  await page.getByRole("button", { name: "Graph" }).click();
  await expect(quasar.getByRole("heading", { name: /Graph/i })).toBeVisible();

  await page.getByRole("button", { name: "Actors" }).click();
  await quasar.getByRole("button", { name: "Run Auto-Dig on selection" }).click();
  await expect(quasar.getByText("Auto-Dig actor completed.")).toBeVisible();

  await quasar.getByRole("link", { name: "Documents" }).click();
  await quasar.getByText("E2E local finding").click();
  await quasar.getByRole("button", { name: "Report incorrect data" }).click();
  await quasar.getByRole("textbox", { name: "Notes", exact: true }).fill("E2E correction payload review");
  await expect(quasar.getByLabel("Exact public payload")).toContainText("E2E correction payload review");
  const popupPromise = page.waitForEvent("popup");
  await quasar.getByRole("button", { name: "Open prefilled GitHub issue" }).click();
  const popup = await popupPromise;
  await expect.poll(() => issueDestination(popup.url())).toContain("github.com/lost-rob0t/starintel-gpt-auto-dig/issues/new");
  await expect.poll(() => issueDestination(popup.url())).toContain("E2E%20correction%20payload%20review");
  await popup.close();

  await page.getByRole("button", { name: "Tipline" }).click();
  await quasar.getByPlaceholder("Tip title").fill("E2E related tip");
  await quasar.getByPlaceholder("Tip contents").fill("Follow up on the persisted E2E finding.");
  await quasar.getByRole("button", { name: "Save local tip" }).click();
  await expect(quasar.getByRole("heading", { name: "E2E related tip" })).toBeVisible();
  await quasar.getByRole("button", { name: "Convert to target" }).click();
  await quasar.getByRole("button", { name: "Start Auto-Dig" }).click();
  await expect(quasar.getByRole("heading", { name: "Generated findings" })).toBeVisible();

  await page.reload();
  await expect(quasar.getByText("Auto-Dig graph operator")).toBeVisible();
  await page.getByRole("button", { name: "Documents" }).click();
  await expect(quasar.getByText("E2E local finding")).toBeVisible();
  await page.getByRole("button", { name: "Tipline" }).click();
  await expect(quasar.getByText("E2E related tip")).toBeVisible();
});
