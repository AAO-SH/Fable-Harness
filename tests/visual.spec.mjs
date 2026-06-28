import { test, expect } from "@playwright/test";

test.setTimeout(60_000);

const requiredSections = ["why", "install", "workflows", "community"];

const parseRgb = (value) => {
  const numbers = value.match(/[\d.]+/g)?.map(Number) ?? [];
  return numbers.slice(0, 3);
};

const contrastRatio = ([r1, g1, b1], [r2, g2, b2]) => {
  const luminance = ([r, g, b]) => {
    const [rs, gs, bs] = [r, g, b].map((channel) => {
      const value = channel / 255;
      return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  };

  const a = luminance([r1, g1, b1]);
  const b = luminance([r2, g2, b2]);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
};

const gotoLanding = async (page, { webgl = false } = {}) => {
  await page.addInitScript((enableWebgl) => {
    Object.defineProperty(window.navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async () => undefined,
      },
    });

    if (enableWebgl) {
      window.localStorage.removeItem("fable-disable-webgl");
    } else {
      window.localStorage.setItem("fable-disable-webgl", "1");
    }
  }, webgl);
  await page.goto("/", { waitUntil: "domcontentloaded" });
};

const collectAstroAuditPerformanceIssues = async (page) =>
  page.evaluate(async () => {
    const externalUrlRegex = /^(?:[a-z+]+:)?\/\//i;
    const absoluteTop = (element) => {
      let currentElement = element;
      let elementYPosition = 0;

      while (currentElement) {
        elementYPosition += currentElement.offsetTop || 0;
        currentElement = currentElement.offsetParent;
      }

      return elementYPosition;
    };
    const issues = [];

    for (const img of [...document.querySelectorAll("img:not([data-image-component])")]) {
      const src = img.getAttribute("src");
      if (!src || src.startsWith("data:")) {
        continue;
      }

      if (!externalUrlRegex.test(src)) {
        const size = await fetch(src)
          .then((response) => response.blob())
          .then((blob) => blob.size)
          .catch(() => 0);

        if (size < 20480) {
          continue;
        }

        issues.push({ code: "perf-use-image-component", src, size });
      } else {
        issues.push({ code: "perf-use-image-component", src, size: null });
      }
    }

    for (const element of [
      ...document.querySelectorAll('img:not([loading]), img[loading="eager"], iframe:not([loading]), iframe[loading="eager"]'),
    ]) {
      const top = absoluteTop(element);
      if (top < window.innerHeight) {
        continue;
      }
      if (element.src?.startsWith("data:")) {
        continue;
      }
      issues.push({
        code: "perf-use-loading-lazy",
        src: element.getAttribute("src"),
        loading: element.getAttribute("loading"),
        top,
        innerHeight: window.innerHeight,
      });
    }

    for (const element of [...document.querySelectorAll('img[loading="lazy"], iframe[loading="lazy"]')]) {
      const top = absoluteTop(element);
      if (top > window.innerHeight) {
        continue;
      }
      if (element.src?.startsWith("data:")) {
        continue;
      }
      issues.push({
        code: "perf-use-loading-eager",
        src: element.getAttribute("src"),
        loading: element.getAttribute("loading"),
        top,
        innerHeight: window.innerHeight,
      });
    }

    return issues;
  });

test("workshop atmosphere animates smoke and sparks behind the blueprint grid", async ({ page }) => {
  await gotoLanding(page);

  const atmosphere = await page.evaluate(() => {
    const body = window.getComputedStyle(document.body);
    const smoke = window.getComputedStyle(document.body, "::before");
    const sparks = window.getComputedStyle(document.body, "::after");

    return {
      bodyBackground: body.backgroundImage,
      smokeAnimation: smoke.animationName,
      smokePointerEvents: smoke.pointerEvents,
      smokeZIndex: smoke.zIndex,
      sparksAnimation: sparks.animationName,
      sparksPointerEvents: sparks.pointerEvents,
      sparksZIndex: sparks.zIndex,
    };
  });

  expect(atmosphere.bodyBackground).toContain("linear-gradient");
  expect(atmosphere.bodyBackground).not.toContain("var(--paper)");
  expect(atmosphere.smokeAnimation).toContain("workshop-smoke-drift");
  expect(atmosphere.sparksAnimation).toContain("workshop-spark-rise");
  expect(atmosphere.smokePointerEvents).toBe("none");
  expect(atmosphere.sparksPointerEvents).toBe("none");
  expect(Number.parseInt(atmosphere.smokeZIndex, 10)).toBeLessThan(
    Number.parseInt(atmosphere.sparksZIndex, 10)
  );

  await page.emulateMedia({ reducedMotion: "reduce" });
  const reducedMotionAtmosphere = await page.evaluate(() => ({
    smokeAnimation: window.getComputedStyle(document.body, "::before").animationName,
    sparksAnimation: window.getComputedStyle(document.body, "::after").animationName,
  }));

  expect(reducedMotionAtmosphere.smokeAnimation).toBe("none");
  expect(reducedMotionAtmosphere.sparksAnimation).toBe("none");
});

test("desktop layout renders the hero and all major sections", async ({ page }) => {
  await gotoLanding(page);
  await expect(page.getByRole("heading", { name: "Fable Harness", level: 1 })).toBeVisible();
  await expect(page.locator(".trace-engine-animation")).toBeVisible();

  for (const section of requiredSections) {
    await expect(page.locator(`#${section}`)).toBeVisible();
  }

  const evidenceSection = page.locator("#evidence");
  await expect(evidenceSection).toBeAttached();
  await expect(evidenceSection).toHaveAttribute("hidden", "");
  await expect(evidenceSection).not.toBeVisible();
  await expect(page.locator("#evidence-title")).toBeAttached();
  await expect(page.locator("#evidence .evidence-loop")).toBeAttached();
  const faqSection = page.locator("#faq");
  await expect(faqSection).toBeAttached();
  await expect(faqSection).toHaveAttribute("hidden", "");
  await expect(faqSection).not.toBeVisible();
  await expect(page.locator("#faq-title")).toHaveText("Adoption questions.");
  await expect(page.locator("#faq .faq-list")).toBeAttached();
  await expect(page.locator("#faq .faq-list")).not.toBeVisible();
  await expect(page.locator("#community .eyebrow")).toHaveText("Community");
  await expect(page.locator("#community-title")).toHaveText("Join the community and help build open source together.");
  const communityCardBackground = await page.locator("#community .community-card").evaluate((element) => {
    const style = window.getComputedStyle(element);
    return {
      backgroundImage: style.backgroundImage,
      backgroundPosition: style.backgroundPosition,
      backgroundSize: style.backgroundSize,
    };
  });
  expect(communityCardBackground.backgroundImage).toContain("community-agent-assembly");
  expect(communityCardBackground.backgroundImage).toContain("linear-gradient");
  expect(communityCardBackground.backgroundSize).toContain("cover");
  const pluginPanel = page.locator("#community .plugin-panel");
  await expect(pluginPanel).toBeAttached();
  await expect(pluginPanel).toHaveAttribute("hidden", "");
  await expect(pluginPanel).not.toBeVisible();
  await expect(page.locator("#community .community-links a")).toHaveCount(4);
  await expect(page.locator('#community .community-links a[href="https://aao.sh"]')).toContainText("Organization");
  await expect(page.locator('#community .community-links a[href="https://github.com/aao-sh"]')).toContainText("GitHub");
  await expect(page.locator("#community .community-links")).not.toContainText("MIT License");
  await expect(page.locator("#community .community-link-icon")).toHaveCount(4);
  const communityLinkLabels = await page
    .locator("#community .community-links a")
    .evaluateAll((links) => links.map((link) => link.textContent?.trim()));
  expect(communityLinkLabels).toEqual(["Discord", "Telegram", "GitHub", "Organization"]);
  const communityIconColor = await page
    .locator("#community .community-link-icon")
    .first()
    .evaluate((element) => window.getComputedStyle(element).color);
  expect(communityIconColor).toBe("rgb(247, 249, 252)");
  const communityLinkLayout = await page.locator("#community .community-links").evaluate((element) => {
    const style = window.getComputedStyle(element);
    return style.gridTemplateColumns.split(" ").length;
  });
  expect(communityLinkLayout).toBe(1);
  const iconScale = await page.locator("#community .community-links a").first().evaluate((link) => {
    const icon = link.querySelector(".community-link-icon");
    const linkFontSize = Number.parseFloat(window.getComputedStyle(link).fontSize);
    const iconWidth = icon?.getBoundingClientRect().width ?? 0;
    return iconWidth / linkFontSize;
  });
  expect(iconScale).toBeGreaterThanOrEqual(1.49);
  expect(iconScale).toBeLessThanOrEqual(1.51);
  const communityLinkAlignment = await page.locator("#community .community-links a").first().evaluate((link) => {
    const linkStyle = window.getComputedStyle(link);
    const icon = link.querySelector(".community-link-icon");
    const label = link.querySelector("span");
    return {
      alignItems: linkStyle.alignItems,
      display: linkStyle.display,
      gridTemplateColumns: linkStyle.gridTemplateColumns,
      justifyContent: linkStyle.justifyContent,
      linkFontSize: Number.parseFloat(linkStyle.fontSize),
      iconJustifySelf: icon ? window.getComputedStyle(icon).justifySelf : "",
      labelJustifySelf: label ? window.getComputedStyle(label).justifySelf : "",
    };
  });
  expect(communityLinkAlignment.display).toBe("grid");
  const communityLinkColumns = communityLinkAlignment.gridTemplateColumns.split(" ").map(Number.parseFloat);
  expect(communityLinkColumns).toHaveLength(2);
  expect(communityLinkColumns[1]).toBeCloseTo(communityLinkAlignment.linkFontSize * 6.25, 0);
  expect(communityLinkAlignment.justifyContent).toBe("center");
  expect(communityLinkAlignment.alignItems).toBe("center");
  expect(communityLinkAlignment.iconJustifySelf).toBe("end");
  expect(communityLinkAlignment.labelJustifySelf).toBe("center");
  const firstCommunityLink = page.locator("#community .community-links a").first();
  await firstCommunityLink.scrollIntoViewIfNeeded();
  await page.mouse.move(1, 1);
  const communityLinkBeforeHover = await firstCommunityLink.evaluate((link) => {
    const style = window.getComputedStyle(link);
    return {
      backgroundColor: style.backgroundColor,
      borderColor: style.borderColor,
      boxShadow: style.boxShadow,
      transform: style.transform,
    };
  });
  await firstCommunityLink.hover({ force: true });
  await page.waitForTimeout(300);
  const communityLinkAfterHover = await firstCommunityLink.evaluate((link) => {
    const style = window.getComputedStyle(link);
    return {
      backgroundColor: style.backgroundColor,
      borderColor: style.borderColor,
      boxShadow: style.boxShadow,
      transform: style.transform,
    };
  });
  expect(communityLinkAfterHover.backgroundColor).not.toBe(communityLinkBeforeHover.backgroundColor);
  expect(communityLinkAfterHover.borderColor).not.toBe(communityLinkBeforeHover.borderColor);
  expect(communityLinkAfterHover.boxShadow).not.toBe("none");
  expect(communityLinkAfterHover.transform).not.toBe(communityLinkBeforeHover.transform);
  const communityIconCenters = await page.locator("#community .community-link-icon").evaluateAll((icons) =>
    icons.map((icon) => {
      const rect = icon.getBoundingClientRect();
      return rect.left + rect.width / 2;
    })
  );
  expect(Math.max(...communityIconCenters) - Math.min(...communityIconCenters)).toBeLessThanOrEqual(0.5);
  const communityButtonSpacing = await page.locator("#community .community-links a").evaluateAll((links) =>
    links.map((link) => {
      const label = link.querySelector("span");
      const linkRect = link.getBoundingClientRect();
      const labelRect = label.getBoundingClientRect();
      const fontSize = Number.parseFloat(window.getComputedStyle(link).fontSize);
      return {
        linkWidth: linkRect.width,
        maxExpectedWidth: fontSize * 15,
        rightSpace: linkRect.right - labelRect.right,
      };
    })
  );
  expect(Math.max(...communityButtonSpacing.map((metric) => metric.linkWidth))).toBeLessThanOrEqual(
    Math.max(...communityButtonSpacing.map((metric) => metric.maxExpectedWidth))
  );
  expect(Math.max(...communityButtonSpacing.map((metric) => metric.rightSpace))).toBeLessThanOrEqual(90);
  await expect(page.locator(".site-footer").getByRole("link", { name: "AAO.sh Community" })).toHaveAttribute(
    "href",
    "https://github.com/aao-sh/fable-harness/graphs/contributors"
  );
  await expect(page.locator(".site-footer").getByRole("link", { name: "MIT License" })).toHaveAttribute(
    "href",
    "https://github.com/aao-sh/fable-harness/blob/main/LICENSE"
  );
  await expect(page.locator(".site-footer").getByRole("link", { name: "AAO.sh", exact: true })).toHaveAttribute(
    "href",
    "https://aao.sh"
  );
  const latestReleaseLink = page.locator('.site-footer a[href^="https://github.com/aao-sh/fable-harness/releases/tag/"]');
  await expect(latestReleaseLink).toHaveText(/^[0-9a-f]{7} • \d{4}$/);
  await expect(latestReleaseLink).toHaveAttribute("href", /^https:\/\/github\.com\/aao-sh\/fable-harness\/releases\/tag\/.+/);
  const footerLinkWeights = await page.locator(".site-footer a").evaluateAll((links) =>
    links.map((link) => window.getComputedStyle(link).fontWeight)
  );
  expect(footerLinkWeights.every((weight) => Number.parseInt(weight, 10) >= 700)).toBe(true);
  const githubHrefs = await page.locator('a[href*="github.com/"]').evaluateAll((links) =>
    links.map((link) => link.href)
  );
  expect(githubHrefs.every((href) => !href.includes("github.com/AAO-SH"))).toBe(true);

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

test("Astro Audit performance rules report no image loading issues", async ({ page }) => {
  await gotoLanding(page);
  await page.waitForLoadState("networkidle");
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));

  expect(await collectAstroAuditPerformanceIssues(page)).toEqual([]);
});

test("mobile navigation opens and copy controls work", async ({ page }) => {
  await gotoLanding(page);
  const usesCompactNav = page.viewportSize()?.width < 900;

  if (usesCompactNav) {
    await page.getByRole("button", { name: "Open navigation" }).click();
    await expect(page.getByRole("navigation", { name: "Primary" })).toHaveAttribute("data-open", "true");
  } else {
    await expect(page.getByRole("navigation", { name: "Primary" })).toBeVisible();
  }

  await expect(page.getByRole("navigation", { name: "Primary" }).getByRole("link", { name: "Install" })).toHaveCount(0);
  await expect(page.getByRole("navigation", { name: "Primary" }).getByRole("link", { name: "Workflows" })).toHaveCount(0);
  await expect(page.getByRole("navigation", { name: "Primary" }).getByRole("link", { name: "Evidence" })).toHaveCount(0);
  await expect(page.getByRole("navigation", { name: "Primary" }).getByRole("link", { name: "FAQ" })).toHaveCount(0);
  await page.getByRole("button", { name: /Copy install command/ }).click();
  await expect(page.getByRole("button", { name: /Copied install command/ })).toBeVisible();
});

test("theme defaults dark, toggles light, and hover states stay legible", async ({ page }) => {
  await gotoLanding(page);
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.getByRole("button", { name: /Switch to light mode/ })).toBeVisible();
  await expect(page.locator("[data-theme-toggle]")).not.toContainText(/Light|Dark/);
  await expect(page.locator(".theme-toggle-icon-sun")).toBeVisible();
  await expect(page.locator(".theme-toggle-icon-moon")).toBeHidden();

  if ((page.viewportSize()?.width ?? 0) < 900) {
    await page.getByRole("button", { name: "Open navigation" }).click();
  }

  const navLink = page.getByRole("link", { name: "Why" });
  await navLink.hover();
  const hoverColors = await navLink.evaluate((element) => {
    const style = window.getComputedStyle(element);
    return { color: style.color, backgroundColor: style.backgroundColor };
  });
  expect(contrastRatio(parseRgb(hoverColors.color), parseRgb(hoverColors.backgroundColor))).toBeGreaterThanOrEqual(4.5);

  await page.getByRole("button", { name: /Switch to light mode/ }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.getByRole("button", { name: /Switch to dark mode/ })).toBeVisible();
  await expect(page.locator(".theme-toggle-icon-sun")).toBeHidden();
  await expect(page.locator(".theme-toggle-icon-moon")).toBeVisible();
});

test("light mode keeps the workshop atmosphere bright enough for secondary copy", async ({ page }) => {
  await gotoLanding(page);
  await page.getByRole("button", { name: /Switch to light mode/ }).click();

  const lightModeReadability = await page.evaluate(() => {
    const parseRgb = (value) => {
      const numbers = value.match(/[\d.]+/g)?.map(Number) ?? [];
      return numbers.slice(0, 3);
    };
    const luminance = ([r, g, b]) => {
      const channels = [r, g, b].map((channel) => {
        const value = channel / 255;
        return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
      });
      return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
    };
    const contrastRatio = (foreground, background) => {
      const foregroundLuminance = luminance(parseRgb(foreground));
      const backgroundLuminance = luminance(parseRgb(background));
      return (Math.max(foregroundLuminance, backgroundLuminance) + 0.05) /
        (Math.min(foregroundLuminance, backgroundLuminance) + 0.05);
    };
    const rootStyle = window.getComputedStyle(document.documentElement);
    const noteStyle = window.getComputedStyle(document.querySelector(".hero-command-note"));
    const bodyAtmosphere = window.getComputedStyle(document.body, "::before");

    return {
      atmosphereBackground: bodyAtmosphere.backgroundImage,
      noteContrast: contrastRatio(noteStyle.color, rootStyle.backgroundColor),
    };
  });

  expect(lightModeReadability.atmosphereBackground).toMatch(/rgba?\(234,\s*217,\s*182|rgba?\(255,\s*250,\s*238/);
  expect(lightModeReadability.atmosphereBackground).not.toMatch(/rgba?\(17,\s*12,\s*8|rgba?\(33,\s*23,\s*15/);
  expect(lightModeReadability.noteContrast).toBeGreaterThanOrEqual(5.25);
});

test("AAO header icon follows light mode and hover assets", async ({ page }) => {
  await gotoLanding(page);
  const aaoLink = page.locator(".aao-link");
  const aaoIcon = page.locator(".aao-link img");

  await page.getByRole("button", { name: /Switch to light mode/ }).click();
  await expect(aaoIcon).toHaveAttribute("src", /aao-icon-black\.svg/);

  const lightStyles = await aaoLink.evaluate((element) => {
    const style = window.getComputedStyle(element);
    return { backgroundColor: style.backgroundColor, borderColor: style.borderColor };
  });
  expect(lightStyles.backgroundColor).toBe("rgba(255, 250, 238, 0.64)");
  expect(lightStyles.borderColor).toBe("rgba(64, 43, 25, 0.22)");

  await aaoLink.hover();
  await expect(aaoIcon).toHaveAttribute("src", /aao-icon-black\.svg/);
  const hoverFilter = await aaoIcon.evaluate((element) => window.getComputedStyle(element).filter);
  expect(hoverFilter).toBe("invert(1)");
});

test("header uses the butterfly mark, AAO link, and scroll flight system", async ({ page }) => {
  await gotoLanding(page);
  await expect(page.locator(".brand-butterfly")).toBeVisible();
  await expect(page.locator(".brand .brand-butterfly svg")).toHaveCount(0);
  await expect(page.locator(".brand .brand-butterfly")).toHaveJSProperty("childElementCount", 0);
  await expect(page.getByRole("link", { name: "AAO home" })).toHaveAttribute("href", "https://aao.sh");
  await expect(page.locator("[data-flight-butterfly]")).toBeVisible();
  await expect(page.locator("[data-flight-butterfly] img.flight-butterfly-mark")).toBeVisible();
  await expect(page.locator("[data-flight-butterfly] img.flight-butterfly-mark")).toHaveAttribute(
    "src",
    /steampunk-butterfly\.webp/
  );
  const headerLayout = await page.evaluate(() => {
    const header = document.querySelector(".site-header")?.getBoundingClientRect();
    const aao = document.querySelector(".aao-link")?.getBoundingClientRect();
    const brand = document.querySelector(".brand")?.getBoundingClientRect();
    if (!header || !aao || !brand) {
      return null;
    }

    return {
      headerLeft: header.left,
      headerCenter: header.left + header.width / 2,
      aaoLeft: aao.left,
      brandCenter: brand.left + brand.width / 2,
    };
  });
  expect(headerLayout).not.toBeNull();
  expect(Math.abs(headerLayout.aaoLeft - (headerLayout.headerLeft + 12))).toBeLessThanOrEqual(2);
  expect(Math.abs(headerLayout.brandCenter - headerLayout.headerCenter)).toBeLessThanOrEqual(2);

  const initialButterflyOverlapsTitle = await page.evaluate(() => {
    const butterfly = document.querySelector("[data-flight-butterfly]")?.getBoundingClientRect();
    const title = document.querySelector("#hero-title")?.getBoundingClientRect();
    if (!butterfly || !title) {
      return true;
    }

    return !(
      butterfly.right < title.left ||
      butterfly.left > title.right ||
      butterfly.bottom < title.top ||
      butterfly.top > title.bottom
    );
  });
  expect(initialButterflyOverlapsTitle).toBe(false);

  const initialTransform = await page.locator("[data-flight-butterfly]").evaluate((element) =>
    window.getComputedStyle(element).transform
  );
  await page.evaluate(() => window.scrollTo(0, Math.min(document.documentElement.scrollHeight, window.innerHeight * 1.15)));
  await page.waitForFunction(() => window.scrollY > 120);
  await page.waitForFunction((previousTransform) => {
    const butterfly = document.querySelector("[data-flight-butterfly]");
    return butterfly ? window.getComputedStyle(butterfly).transform !== previousTransform : false;
  }, initialTransform);
  const scrolledTransform = await page.locator("[data-flight-butterfly]").evaluate((element) =>
    window.getComputedStyle(element).transform
  );

  expect(scrolledTransform).not.toBe(initialTransform);
});

test("butterfly flight waits for the fifteen-percent landing band and returns before the header", async ({ page }) => {
  test.setTimeout(60_000);
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await gotoLanding(page);
  await page.addStyleTag({ content: "html { scroll-behavior: auto !important; }" });
  await page.addStyleTag({
    content:
      "#workflows .butterfly-landing, #evidence .butterfly-landing, #community .butterfly-landing { display: none !important; }",
  });
  const landingSelector = "#why .butterfly-landing";
  const flightButterfly = page.locator("[data-flight-butterfly]");

  await expect(flightButterfly).toHaveAttribute("data-flight-target", /brand|content|why/);

  const placeLandingAtRatio = async (selector, viewportRatio) => {
    await page.evaluate(
      ({ selector: targetSelector, viewportRatio: targetRatio }) => {
        const target = document.querySelector(targetSelector);
        const rect = target?.getBoundingClientRect();
        if (!rect) {
          return;
        }
        const targetY = window.innerHeight * targetRatio;
        window.scrollTo(0, window.scrollY + rect.top - targetY);
      },
      { selector, viewportRatio }
    );
    await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  };

  await placeLandingAtRatio(landingSelector, 0.86);
  await expect(flightButterfly).toHaveAttribute("data-flight-target", "brand");

  await placeLandingAtRatio(landingSelector, 0.85);
  await expect(flightButterfly).toHaveAttribute("data-flight-target", "why");

  const headerReturnY = await page.evaluate(() => {
    const headerRect = document.querySelector(".site-header")?.getBoundingClientRect();
    return (headerRect?.bottom ?? 0) + Math.max(72, (headerRect?.height ?? 64) * 1.1);
  });
  await page.evaluate(
    ({ selector: targetSelector, targetY }) => {
      const target = document.querySelector(targetSelector);
      const rect = target?.getBoundingClientRect();
      if (!rect) {
        return;
      }
      window.scrollTo(0, window.scrollY + rect.top - targetY);
    },
    { selector: landingSelector, targetY: headerReturnY - 8 }
  );
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  await expect(flightButterfly).toHaveAttribute("data-flight-target", "brand");
});

test("hero command card is visible and exposes prompt install plus copy", async ({ page }) => {
  await gotoLanding(page);

  await expect(page.getByText("The Trace Engine", { exact: true })).toBeVisible();
  await expect(page.getByText("The Trace Engine Field Manual")).toHaveCount(0);
  await expect(page.locator(".hero-lede")).toContainText(
    "A system that teaches AI agents to organize memory context into traces and manageable notes."
  );
  await expect(page.locator(".hero-field-note")).toHaveCount(0);
  await expect(page.locator(".hero-actions")).toHaveCount(0);
  await expect(page.locator(".hero-command")).toBeVisible();
  await expect(page.getByRole("tab")).toHaveCount(0);
  await expect(page.getByRole("button", { name: /^prompt$/i })).toHaveCount(0);
  await expect(page.getByRole("button", { name: /npm|npx|yarn|pip/i })).toHaveCount(0);
  const installPromptButton = page.getByRole("button", { name: "Install by prompt" });
  await expect(installPromptButton).toBeVisible();
  await expect(installPromptButton).toHaveClass(/is-active/);
  const promptButtonStyles = await installPromptButton.evaluate((element) => {
    const style = window.getComputedStyle(element);
    return {
      backgroundColor: style.backgroundColor,
      borderColor: style.borderColor,
      color: style.color,
    };
  });
  expect(promptButtonStyles.backgroundColor).toBe("rgb(240, 196, 106)");
  expect(promptButtonStyles.borderColor).toBe("rgba(240, 196, 106, 0.85)");
  expect(contrastRatio(parseRgb(promptButtonStyles.color), parseRgb(promptButtonStyles.backgroundColor))).toBeGreaterThanOrEqual(4.5);
  await expect(page.locator("#hero-command-value")).toContainText("Install the Fable-Harness skill");
  await page.getByRole("button", { name: /Copy install command/ }).click();
  await expect(page.getByRole("button", { name: /Copied install command/ })).toBeVisible();
  await expect(page.locator(".hero-command-note")).toContainText("Requires Python 3.9 or newer");
  await expect(page.locator(".install-section")).toHaveCount(0);
});

test("hero art animates the prompt-to-archive trace engine narrative", async ({ page }) => {
  test.setTimeout(60_000);
  const shouldRenderWebgl = (page.viewportSize()?.width ?? 0) >= 1000;
  await gotoLanding(page, { webgl: shouldRenderWebgl });
  await expect(page.locator(".trace-engine-animation")).toBeVisible();
  await expect(page.locator(".trace-rig")).toBeVisible();
  await expect(page.locator(".trace-rig")).toHaveAttribute(
    "data-render-state",
    shouldRenderWebgl ? "active" : "fallback",
    { timeout: 12_000 }
  );
  await expect(page.locator(".trace-rig canvas.trace-engine-canvas")).toBeVisible();
  await expect(page.locator(".trace-rig img.trace-rig-backdrop")).toBeVisible();
  await expect(page.locator(".trace-rig svg.trace-rig-backdrop")).toHaveCount(0);
  await expect(page.locator(".rig-agent-lens")).toHaveCount(0);
  await expect(page.locator(".rig-prompt-slip")).toBeVisible();
  await expect(page.locator(".rig-prompt-slip")).toContainText("# Make a 2D platformer game...");
  await expect(page.locator(".rig-cabinet-target")).toBeVisible();
  await expect(page.locator(".rig-drawer-light")).toHaveCount(3);
  await expect(page.locator(".rig-document-slip")).toHaveCount(3);
  await expect(page.locator(".rig-document-memory")).toHaveText("agents.md");
  await expect(page.locator(".rig-rollback-dial")).toBeVisible();
  await expect(page.locator(".rig-depth-vignette")).toBeVisible();
  await expect(page.locator(".cinematic-sprite")).toHaveCount(0);
  await expect(page.locator(".archive-cabinet")).toHaveCount(0);
  await expect(page.locator(".prompt-card")).toHaveCount(0);
  await expect(page.locator(".document-stack")).toHaveCount(0);

  const canvasState = await page.locator(".trace-rig canvas.trace-engine-canvas").evaluate((canvas) => ({
    width: canvas.width,
    height: canvas.height,
    cssWidth: canvas.getBoundingClientRect().width,
    cssHeight: canvas.getBoundingClientRect().height,
    dataState: canvas.closest("[data-trace-engine-scene]")?.getAttribute("data-render-state"),
  }));
  if (shouldRenderWebgl) {
    expect(canvasState.width).toBeGreaterThan(300);
    expect(canvasState.height).toBeGreaterThan(240);
  }
  expect(canvasState.cssWidth).toBeGreaterThan(300);
  expect(canvasState.cssHeight).toBeGreaterThan(240);
  expect(canvasState.dataState).toBe(shouldRenderWebgl ? "active" : "fallback");

  const animationNames = await page.evaluate(() => ({
    canvas: window.getComputedStyle(document.querySelector(".trace-engine-canvas")).animationName,
    backdrop: window.getComputedStyle(document.querySelector(".trace-rig-backdrop")).animationName,
    prompt: window.getComputedStyle(document.querySelector(".rig-prompt-slip")).animationName,
    drawer: window.getComputedStyle(document.querySelector(".rig-drawer-plans")).animationName,
    document: window.getComputedStyle(document.querySelector(".rig-document-notes")).animationName,
    clock: window.getComputedStyle(document.querySelector(".rig-rollback-dial")).animationName,
    promptTransform: window.getComputedStyle(document.querySelector(".rig-prompt-slip")).transform,
    cabinetTransform: window.getComputedStyle(document.querySelector(".rig-cabinet-target")).transform,
  }));
  if (shouldRenderWebgl) {
    expect(animationNames.canvas).toContain("rig-camera-breathe");
  }
  expect(animationNames.backdrop).toContain("rig-camera-breathe");
  expect(animationNames.prompt).toContain("rig-paper-intake");
  expect(animationNames.drawer).toContain("rig-drawer-store");
  expect(animationNames.document).toContain("rig-document-settle");
  expect(animationNames.clock).toContain("rig-dial-rewind");
  expect(animationNames.promptTransform).not.toBe("none");
  expect(animationNames.cabinetTransform).not.toBe("none");

  await expect(page.locator(".trace-rig img.trace-rig-backdrop")).toHaveAttribute(
    "src",
    /trace-engine-painted-base/
  );
});

test("hero text and artwork keep a clean responsive composition", async ({ page }) => {
  await gotoLanding(page);
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

test("why and workflows headings stay compact enough to keep sections light", async ({ page }) => {
  await gotoLanding(page);
  const viewportWidth = page.viewportSize()?.width ?? 0;

  for (const section of ["why", "workflows"]) {
    const title = await page.locator(`#${section}-title`).boundingBox();
    const heading = await page.locator(`#${section} .section-heading`).boundingBox();

    expect(title).not.toBeNull();
    expect(heading).not.toBeNull();
    expect(title.height).toBeLessThanOrEqual(viewportWidth >= 1060 ? 150 : 120);
    expect(heading.height).toBeLessThanOrEqual(viewportWidth >= 1060 ? 290 : 310);
  }
});

test("workflow carousel loops with visible neighboring slide peeks", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await gotoLanding(page);
  await page.addStyleTag({
    content: "#workflows .workflow-track { animation-play-state: paused !important; transform: translate3d(0, 0, 0) !important; }",
  });

  const carousel = page.locator("#workflows .workflow-carousel");
  const track = page.locator("#workflows .workflow-track");

  await expect(carousel).toBeVisible();
  await expect(track).toBeVisible();
  await expect(page.locator("#workflows .workflow-slide-set")).toHaveCount(2);
  await expect(page.locator("#workflows .workflow-slide-set").nth(1)).toHaveAttribute("aria-hidden", "true");
  await expect(page.locator("#workflows .workflow-slide-set").first().locator(".workflow-plate")).toHaveCount(5);
  await expect(page.locator("#workflows .workflow-slide-set").nth(1).locator(".workflow-plate")).toHaveCount(5);

  const styles = await page.evaluate(() => {
    const carouselElement = document.querySelector("#workflows .workflow-carousel");
    const trackElement = document.querySelector("#workflows .workflow-track");
    const carouselStyle = window.getComputedStyle(carouselElement);
    const trackStyle = window.getComputedStyle(trackElement);
    return {
      overflowX: carouselStyle.overflowX,
      animationName: trackStyle.animationName,
      maskImage: carouselStyle.maskImage || carouselStyle.webkitMaskImage,
    };
  });

  expect(styles.overflowX).toBe("hidden");
  expect(styles.animationName).toContain("workflow-loop");
  expect(styles.maskImage).not.toBe("none");

  const geometry = await page.evaluate(() => {
    const viewport = document.querySelector("#workflows .workflow-carousel")?.getBoundingClientRect();
    const slides = [...document.querySelectorAll("#workflows .workflow-plate")].map((slide) =>
      slide.getBoundingClientRect()
    );

    if (!viewport) {
      return null;
    }

    return {
      hasLeftPeek: slides.some((slide) => slide.left < viewport.left && slide.right > viewport.left + 8),
      hasRightPeek: slides.some((slide) => slide.left < viewport.right - 8 && slide.right > viewport.right),
      hasCenteredSlide: slides.some((slide) => slide.left >= viewport.left + 8 && slide.right <= viewport.right - 8),
    };
  });

  expect(geometry).not.toBeNull();
  expect(geometry.hasLeftPeek).toBe(true);
  expect(geometry.hasRightPeek).toBe(true);
  expect(geometry.hasCenteredSlide).toBe(true);
});

test("workflow slides center content and open a full page image modal", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await gotoLanding(page);
  await page.addStyleTag({
    content: "#workflows .workflow-track { animation-play-state: paused !important; transform: translate3d(0, 0, 0) !important; }",
  });

  await expect(page.locator("#workflows .plate-number")).toHaveCount(0);

  const centeredSlideIndex = await page.evaluate(() => {
    const viewport = document.querySelector("#workflows .workflow-carousel")?.getBoundingClientRect();
    const slides = [...document.querySelectorAll("#workflows .workflow-slide-set:first-child .workflow-plate")].map((slide) =>
      slide.getBoundingClientRect()
    );

    if (!viewport) {
      return -1;
    }

    return slides.findIndex((slide) => slide.left >= viewport.left + 8 && slide.right <= viewport.right - 8);
  });

  expect(centeredSlideIndex).toBeGreaterThanOrEqual(0);

  const firstSlide = page
    .locator("#workflows .workflow-slide-set")
    .first()
    .locator(".workflow-plate")
    .nth(centeredSlideIndex);
  const trigger = firstSlide.locator("[data-workflow-modal-trigger]");
  const slideImage = firstSlide.locator("img");

  await expect(trigger).toBeVisible();
  await expect(slideImage).toBeVisible();

  const bodyStyles = await firstSlide.locator(".workflow-body").evaluate((element) => {
    const style = window.getComputedStyle(element);
    return {
      alignItems: style.alignItems,
      display: style.display,
      justifyContent: style.justifyContent,
      textAlign: style.textAlign,
    };
  });

  expect(bodyStyles.display).toBe("flex");
  expect(bodyStyles.alignItems).toBe("center");
  expect(bodyStyles.justifyContent).toBe("center");
  expect(bodyStyles.textAlign).toBe("center");

  const slideImageSrc = await slideImage.evaluate((image) => image.currentSrc || image.src);
  const expectedModalTitle = await trigger.getAttribute("data-workflow-title");
  await trigger.click();

  const modal = page.locator("[data-workflow-modal]");
  const modalImage = page.locator("[data-workflow-modal-image]");

  await expect(modal).toBeVisible();
  await expect(modal).toHaveJSProperty("open", true);
  await expect(page.locator("[data-workflow-modal-title]")).toContainText(expectedModalTitle);
  await expect(modalImage).toBeVisible();

  const modalImageSrc = await modalImage.evaluate((image) => image.currentSrc || image.src);
  expect(modalImageSrc).toBe(slideImageSrc);

  await page.locator("[data-workflow-modal-close]").click();
  await expect(modal).toHaveJSProperty("open", false);
});

test("visible cloned workflow slides also open the image modal during the loop", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await gotoLanding(page);
  await page.addStyleTag({
    content:
      "#workflows .workflow-track { animation-play-state: paused !important; transform: translate3d(-50%, 0, 0) !important; }",
  });
  await page.locator("#workflows").scrollIntoViewIfNeeded();
  await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));

  const clonedSlideIndex = await page.evaluate(() => {
    const viewport = document.querySelector("#workflows .workflow-carousel")?.getBoundingClientRect();
    const slides = [...document.querySelectorAll('#workflows .workflow-slide-set[aria-hidden="true"] .workflow-plate')].map(
      (slide) => slide.getBoundingClientRect()
    );

    if (!viewport) {
      return -1;
    }

    return slides.findIndex((slide) => slide.left >= viewport.left + 8 && slide.right <= viewport.right - 8);
  });

  expect(clonedSlideIndex).toBeGreaterThanOrEqual(0);

  const clonedSlide = page
    .locator('#workflows .workflow-slide-set[aria-hidden="true"] .workflow-plate')
    .nth(clonedSlideIndex);
  const clonedImage = clonedSlide.locator("img");

  await expect(clonedSlide).toBeVisible();
  await expect(clonedImage).toBeVisible();

  const slideImageSrc = await clonedImage.evaluate((image) => image.currentSrc || image.src);
  const expectedTitle = await clonedSlide.locator("h3").textContent();
  const slideBox = await clonedSlide.boundingBox();

  expect(slideBox).not.toBeNull();
  await page.mouse.click(slideBox.x + slideBox.width / 2, slideBox.y + slideBox.height / 2);

  const modal = page.locator("[data-workflow-modal]");
  const modalImage = page.locator("[data-workflow-modal-image]");

  await expect(modal).toBeVisible();
  await expect(modal).toHaveJSProperty("open", true);
  await expect(page.locator("[data-workflow-modal-title]")).toContainText(expectedTitle.trim());

  const modalImageSrc = await modalImage.evaluate((image) => image.currentSrc || image.src);
  expect(modalImageSrc).toBe(slideImageSrc);
});

test("responsive layout avoids horizontal overflow and reveals page continuation", async ({ page }) => {
  await gotoLanding(page);
  const viewport = page.viewportSize();
  const metrics = await page.evaluate(() => {
    const why = document.querySelector("#why");
    return {
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      whyTop: why?.getBoundingClientRect().top ?? Number.POSITIVE_INFINITY,
    };
  });

  expect(metrics.scrollWidth).toBeLessThanOrEqual(metrics.clientWidth + 1);

  if ((viewport?.width ?? 0) >= 768) {
    expect(metrics.whyTop).toBeLessThan(viewport?.height ?? 0);
  }
});
