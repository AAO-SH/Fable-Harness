import { test, expect } from "@playwright/test";
import AxeBuilder from "axe-core";

test("landing page has no critical accessibility violations", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Fable Harness", level: 1 })).toBeVisible();

  const results = await page.evaluate(async (axeSource) => {
    const script = document.createElement("script");
    script.textContent = axeSource;
    document.head.appendChild(script);
    return await window.axe.run(document, {
      runOnly: {
        type: "tag",
        values: ["wcag2a", "wcag2aa", "wcag21aa"],
      },
    });
  }, AxeBuilder.source);

  const serious = results.violations.filter((violation) =>
    ["critical", "serious"].includes(violation.impact)
  );

  expect(serious).toEqual([]);
});
