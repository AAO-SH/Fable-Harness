import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PackagePublishWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.workflow = (ROOT / ".github" / "workflows" / "publish-package.yml").read_text(
            encoding="utf-8"
        )

    def test_package_defaults_to_github_packages_for_existing_consumers(self):
        self.assertEqual(self.package["name"], "@aao-sh/fable-harness")
        self.assertEqual(self.package["publishConfig"]["registry"], "https://npm.pkg.github.com")
        self.assertEqual(self.package["publishConfig"]["access"], "public")

    def test_workflow_publishes_to_github_packages_and_npmjs_separately(self):
        self.assertIn("publish-github-packages:", self.workflow)
        self.assertIn("registry-url: https://npm.pkg.github.com", self.workflow)
        self.assertIn("NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}", self.workflow)

        self.assertIn("publish-npmjs:", self.workflow)
        self.assertIn("registry-url: https://registry.npmjs.org", self.workflow)
        self.assertIn("NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}", self.workflow)
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
