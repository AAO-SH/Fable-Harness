import { test, expect } from "@playwright/test";

const requiredSections = ["why", "install", "workflows", "evidence", "community", "faq"];

test("desktop layout renders the hero and all major sections", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Fable Harness", level: 1 })).toBeVisible();
  await expect(page.locator(".hero-art img")).toBeVisible();

  for (const section of requiredSections) {
    await expect(page.locator(`#${section}`)).toBeVisible();
  }

  const overlapping = await page.evaluate(() => {
    const blocks = [...document.querySelectorAll("h1, h2, h3, p, a, button, code")].filter((element) => {
      const rect = element.getBoundingClientRect();
      const style = window.getComputedStyle(element);
      return rect.width > 0 && rect.height > 0 && style.visibility !== "hidden" && style.display !== "none";
    });
    return blocks.some((element) => {
      const rect = element.getBoundingClientRect();
      return rect.width > window.innerWidth || rect.height === 0;
    });
  });

  expect(overlapping).toBe(false);
});

test("mobile navigation opens and copy controls work", async ({ page }) => {
  await page.goto("/");
  const isMobile = page.viewportSize()?.width < 760;

  if (isMobile) {
    await page.getByRole("button", { name: "Open navigation" }).click();
    await expect(page.getByRole("navigation", { name: "Primary" })).toHaveAttribute("data-open", "true");
  } else {
    await expect(page.getByRole("navigation", { name: "Primary" })).toBeVisible();
  }

  await page.getByRole("button", { name: /Copy prompt install command/ }).click();
  await expect(page.getByRole("button", { name: /Copied prompt install command/ })).toBeVisible();
});

test("hero text and artwork keep a clean responsive composition", async ({ page }) => {
  await page.goto("/");
  const viewportWidth = page.viewportSize()?.width ?? 0;
  const title = await page.getByRole("heading", { name: "Fable Harness", level: 1 }).boundingBox();
  const art = await page.locator(".hero-art").boundingBox();

  expect(title).not.toBeNull();
  expect(art).not.toBeNull();

  if (viewportWidth >= 1060) {
    expect(title.x + title.width).toBeLessThan(art.x);
  } else {
    expect(title.y).toBeLessThan(art.y);
  }
});
