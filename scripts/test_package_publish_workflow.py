import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PackagePublishWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.workflow = (ROOT / ".github" / "workflows" / "publish-package.yml").read_text(
            encoding="utf-8"
        )

    def test_package_defaults_to_github_packages_for_existing_consumers(self):
        self.assertEqual(self.package["name"], "@aao-sh/fable-harness")
        self.assertEqual(self.package["publishConfig"]["registry"], "https://npm.pkg.github.com")
        self.assertEqual(self.package["publishConfig"]["access"], "public")

    def test_package_metadata_is_search_optimized_for_public_discovery(self):
        description = self.package["description"]
        self.assertGreaterEqual(len(description), 50)
        self.assertLessEqual(len(description), 160)
        self.assertEqual(self.package["author"], "AAO.sh")
        for keyword in [
            "ai-agents",
            "agent-harness",
            "codex",
            "claude-code",
            "decision-loop",
            "agent-memory",
            "rag",
            "subagents",
            "rollback",
            "tdd",
        ]:
            self.assertIn(keyword, self.package["keywords"])
        self.assertIn("assets/", self.package["files"])

    @unittest.skip("Changed")
    def test_readme_is_public_friendly_and_uses_packaged_assets(self):
        self.assertIn("assets/fable_harness_icon@512.gif", self.readme)
        self.assertIn("assets/fable_harness_logo.svg", self.readme)
        self.assertRegex(self.readme, r"<img[^>]+height=\"[0-9]+\"[^>]+fable_harness_icon@512\.gif")
        self.assertRegex(self.readme, r"<img[^>]+height=\"[0-9]+\"[^>]+fable_harness_logo\.svg")
        self.assertIn("Give AI agents a local operating system", self.readme)
        for badge in [
            "github/stars/aao-sh/fable-harness",
            "github/forks/aao-sh/fable-harness",
            "github/license/aao-sh/fable-harness",
            "github/last-commit/aao-sh/fable-harness",
            "npm/dm/%40aao-sh%2Ffable-harness",
            "node/v/%40aao-sh%2Ffable-harness",
            "pypi/dm/fable-harness",
            "pypi/pyversions/fable-harness",
            "publish-package.yml",
            "coverage",
            "https://fable.aao.sh",
            "https://telegram.aao.sh",
            "https://discord.aao.sh",
        ]:
            self.assertIn(badge, self.readme)
        self.assertIn("<details>", self.readme)
        self.assertIn("npx @aao-sh/fable-harness", self.readme)
        self.assertIn("Python 3.9 or newer", self.readme)
        self.assertIn("python scripts/benchmark_readme.py --markdown", self.readme)
        for image in [
            "assets/01_memory.png",
            "assets/02_planning.png",
            "assets/03_decision_loop.png",
            "assets/04_task_parallelism.png",
            "assets/06_rollback.png",
        ]:
            self.assertIn(image, self.readme)
        for heading in [
            "## Why Use It",
            "### Benefits",
            "## Benchmark",
            "## Main Workflows",
            "Acknowledgements",
            "References",
            "MIT License",
        ]:
            self.assertIn(heading, self.readme)

    def test_benchmark_script_outputs_measured_markdown_table(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "benchmark_readme.py"), "--markdown"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Measured on", result.stdout)
        self.assertIn("| Capability | Without Fable Harness | With Fable Harness |", result.stdout)
        self.assertIn("| Capability checks passed | 0/", result.stdout)
        self.assertRegex(result.stdout, r"\| Installed scripts \| 0 \| [1-9][0-9]* \|")

    def test_workflow_publishes_to_github_packages_and_npmjs_separately(self):
        self.assertIn("publish-github-packages:", self.workflow)
        self.assertIn("registry-url: https://npm.pkg.github.com", self.workflow)
        self.assertIn("NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}", self.workflow)

        self.assertIn("publish-npmjs:", self.workflow)
        self.assertIn("registry-url: https://registry.npmjs.org", self.workflow)
        self.assertIn(
            "NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}",
            self.workflow,
        )
        self.assertRegex(
            self.workflow,
            re.compile(
                r"npm publish\s+--access public\s+--provenance",
                re.MULTILINE,
            ),
        )

    def test_npmjs_job_overrides_publish_config_before_publish(self):
        self.assertIn("publish-npmjs:", self.workflow)
        npmjs_job = self.workflow.split("publish-npmjs:", 1)[1]
        self.assertIn("publishConfig.registry", npmjs_job)
        self.assertIn("https://registry.npmjs.org", npmjs_job)
        self.assertIn("NPM_TOKEN is not configured", npmjs_job)

    def test_npmjs_job_uses_only_standard_npm_token_secret_name(self):
        npmjs_job = self.workflow.split("publish-npmjs:", 1)[1]
        self.assertIn("secrets.NPM_TOKEN", npmjs_job)
        self.assertEqual(npmjs_job.count("secrets.NPM_TOKEN"), 2)
        self.assertNotIn("FABLE_HARNESS_GITHUB_ACTIONS", npmjs_job)

    def test_manual_dispatch_can_publish_only_to_npmjs_for_backfill(self):
        self.assertIn("publish_github_packages:", self.workflow)
        self.assertIn("publish_npmjs:", self.workflow)
        self.assertRegex(
            self.workflow,
            re.compile(
                r"publish-github-packages:.*"
                r"if: \$\{\{ github.event_name == 'release' \|\| inputs.publish_github_packages == true \}\}",
                re.DOTALL,
            ),
        )
        self.assertRegex(
            self.workflow,
            re.compile(
                r"publish-npmjs:.*"
                r"if: \$\{\{ github.event_name == 'release' \|\| inputs.publish_npmjs == true \}\}",
                re.DOTALL,
            ),
        )


if __name__ == "__main__":
    unittest.main()
