import { test } from "node:test";
import assert from "node:assert/strict";

import { fetchLatestReleaseFooter } from "../src/data/latest-release.mjs";

const jsonResponse = (body) => ({
  ok: true,
  json: async () => body,
});

test("latest release footer data comes from the GitHub latest release API", async () => {
  const requestedUrls = [];
  const fetchImpl = async (url) => {
    requestedUrls.push(String(url));

    if (String(url).endsWith("/releases/latest")) {
      return jsonResponse({
        tag_name: "v9.9.9",
        published_at: "2031-04-05T10:20:30Z",
      });
    }

    if (String(url).endsWith("/git/ref/tags/v9.9.9")) {
      return jsonResponse({
        object: {
          type: "commit",
          sha: "abcdef1234567890abcdef1234567890abcdef12",
        },
      });
    }

    throw new Error(`Unexpected URL: ${url}`);
  };

  const release = await fetchLatestReleaseFooter(fetchImpl);

  assert.deepEqual(release, {
    label: "abcdef1 • 2031",
    url: "https://github.com/aao-sh/fable-harness/releases/tag/v9.9.9",
  });
  assert.deepEqual(requestedUrls, [
    "https://api.github.com/repos/aao-sh/fable-harness/releases/latest",
    "https://api.github.com/repos/aao-sh/fable-harness/git/ref/tags/v9.9.9",
  ]);
});

test("latest release footer resolves annotated tags to the target commit", async () => {
  const fetchImpl = async (url) => {
    if (String(url).endsWith("/releases/latest")) {
      return jsonResponse({
        tag_name: "v1.2.3",
        published_at: "2032-12-31T23:59:59Z",
      });
    }

    if (String(url).endsWith("/git/ref/tags/v1.2.3")) {
      return jsonResponse({
        object: {
          type: "tag",
          sha: "tag-object-sha",
          url: "https://api.github.com/repos/aao-sh/fable-harness/git/tags/tag-object-sha",
        },
      });
    }

    if (String(url).endsWith("/git/tags/tag-object-sha")) {
      return jsonResponse({
        object: {
          type: "commit",
          sha: "1234567890abcdef1234567890abcdef12345678",
        },
      });
    }

    throw new Error(`Unexpected URL: ${url}`);
  };

  const release = await fetchLatestReleaseFooter(fetchImpl);

  assert.deepEqual(release, {
    label: "1234567 • 2032",
    url: "https://github.com/aao-sh/fable-harness/releases/tag/v1.2.3",
  });
});
