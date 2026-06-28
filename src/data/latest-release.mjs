const githubOwner = "aao-sh";
const githubRepo = "fable-harness";
const githubApiRepoUrl = `https://api.github.com/repos/${githubOwner}/${githubRepo}`;
const githubRepoUrl = `https://github.com/${githubOwner}/${githubRepo}`;

let latestReleaseFooterPromise;

const buildHeaders = () => {
  const headers = {
    Accept: "application/vnd.github+json",
    "User-Agent": "fable-harness-webpage",
  };

  if (process.env.GITHUB_TOKEN) {
    headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  }

  return headers;
};

const readJson = async (fetchImpl, url) => {
  const response = await fetchImpl(url, { headers: buildHeaders() });

  if (!response.ok) {
    throw new Error(`GitHub release lookup failed: ${response.status} ${response.statusText ?? ""}`.trim());
  }

  return response.json();
};

const releaseYear = (publishedAt) => {
  const date = new Date(publishedAt);

  if (Number.isNaN(date.getTime())) {
    throw new Error(`GitHub release has an invalid published_at value: ${publishedAt}`);
  }

  return String(date.getUTCFullYear());
};

const releaseTagUrl = (tagName) => `${githubRepoUrl}/releases/tag/${encodeURIComponent(tagName)}`;

export const fetchLatestReleaseFooter = async (fetchImpl = globalThis.fetch) => {
  if (typeof fetchImpl !== "function") {
    throw new Error("A fetch implementation is required to resolve the latest release.");
  }

  const release = await readJson(fetchImpl, `${githubApiRepoUrl}/releases/latest`);
  const tagName = release.tag_name;

  if (!tagName) {
    throw new Error("GitHub latest release response did not include tag_name.");
  }

  const ref = await readJson(fetchImpl, `${githubApiRepoUrl}/git/ref/tags/${encodeURIComponent(tagName)}`);
  let commitSha = ref.object?.sha;

  if (ref.object?.type === "tag") {
    const tagObject = await readJson(fetchImpl, ref.object.url);
    commitSha = tagObject.object?.sha;
  }

  if (!commitSha) {
    throw new Error(`GitHub tag ${tagName} did not resolve to a commit SHA.`);
  }

  return {
    label: `${commitSha.slice(0, 7)} • ${releaseYear(release.published_at)}`,
    url: releaseTagUrl(tagName),
  };
};

export const getLatestReleaseFooter = () => {
  latestReleaseFooterPromise ??= fetchLatestReleaseFooter();
  return latestReleaseFooterPromise;
};
