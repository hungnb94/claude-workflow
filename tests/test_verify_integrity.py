#!/usr/bin/env python3
"""
Unit tests for scripts/verify-integrity.py.
Tests all pass and fail conditions using temporary directory structures.
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to sys.path
import sys
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import importlib.util
spec = importlib.util.spec_from_file_location("verify_integrity", ROOT_DIR / "scripts" / "verify-integrity.py")
vi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vi)


class TestVerifyIntegrity(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_root = Path(self.test_dir)

        # Setup minimal valid repo structure
        (self.repo_root / ".claude-plugin").mkdir(parents=True)
        (self.repo_root / "skills" / "sample-workflow").mkdir(parents=True)
        (self.repo_root / "agents").mkdir(parents=True)

        plugin_json = {
            "name": "workflow",
            "version": "1.0.0"
        }
        (self.repo_root / ".claude-plugin" / "plugin.json").write_text(
            json.dumps(plugin_json), encoding="utf-8"
        )

        marketplace_json = {
            "name": "claude-workflow",
            "plugins": [
                {
                    "name": "workflow",
                    "version": "1.0.0"
                }
            ]
        }
        (self.repo_root / ".claude-plugin" / "marketplace.json").write_text(
            json.dumps(marketplace_json), encoding="utf-8"
        )

        agent_content = (
            "---\n"
            "name: fw-1-spec\n"
            "description: Senior Business Analyst - Survey scope\n"
            "tools:\n"
            "  - Read\n"
            "  - Grep\n"
            "model: sonnet\n"
            "---\n"
            "Content here\n"
        )
        (self.repo_root / "agents" / "fw-1-spec.md").write_text(
            agent_content, encoding="utf-8"
        )

        review_content = (
            "---\n"
            "name: fw-5-review\n"
            "description: Senior Quality Auditor - Objective review\n"
            "tools:\n"
            "  - Read\n"
            "  - Write\n"
            "model: sonnet\n"
            "---\n"
            "Review content\n"
        )
        (self.repo_root / "agents" / "fw-5-review.md").write_text(
            review_content, encoding="utf-8"
        )

        skill_content = (
            "---\n"
            "name: sample-workflow\n"
            "description: Sample\n"
            "---\n"
            "| Bước | Agent |\n"
            "| 1 | `fw-1-spec` |\n"
            "| 5 | `fw-5-review` |\n"
        )
        (self.repo_root / "skills" / "sample-workflow" / "SKILL.md").write_text(
            skill_content, encoding="utf-8"
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_version_sync_pass(self):
        self.assertTrue(vi.check_version_sync(self.repo_root))
        self.assertTrue(vi.check_version_sync(self.repo_root, check_tag="v1.0.0"))
        self.assertTrue(vi.check_version_sync(self.repo_root, check_tag="1.0.0"))
        self.assertTrue(vi.check_version_sync(self.repo_root, check_tag="workflow--v1.0.0"))
        self.assertTrue(vi.check_version_sync(self.repo_root, check_tag="workflow--1.0.0"))

    def test_version_sync_mismatch(self):
        # Alter marketplace.json version
        mp = json.loads((self.repo_root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        mp["plugins"][0]["version"] = "1.0.1"
        (self.repo_root / ".claude-plugin" / "marketplace.json").write_text(json.dumps(mp), encoding="utf-8")
        self.assertFalse(vi.check_version_sync(self.repo_root))

    def test_version_sync_tag_mismatch(self):
        self.assertFalse(vi.check_version_sync(self.repo_root, check_tag="v2.0.0"))
        self.assertFalse(vi.check_version_sync(self.repo_root, check_tag="workflow--v2.0.0"))

    def test_version_sync_tag_prefix_mismatch(self):
        self.assertFalse(vi.check_version_sync(self.repo_root, check_tag="other-plugin--v1.0.0"))

    def test_version_sync_plugin_name_mismatch(self):
        # Alter marketplace.json plugin name so it doesn't match plugin.json
        mp = json.loads((self.repo_root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        mp["plugins"][0]["name"] = "other-plugin"
        (self.repo_root / ".claude-plugin" / "marketplace.json").write_text(json.dumps(mp), encoding="utf-8")
        self.assertFalse(vi.check_version_sync(self.repo_root))

    def test_version_sync_missing_plugin_name(self):
        # Remove name from plugin.json
        pj = json.loads((self.repo_root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        del pj["name"]
        (self.repo_root / ".claude-plugin" / "plugin.json").write_text(json.dumps(pj), encoding="utf-8")
        self.assertFalse(vi.check_version_sync(self.repo_root))

    def test_agent_references_pass(self):
        self.assertTrue(vi.check_agent_references(self.repo_root))

    def test_agent_references_missing_agent(self):
        # Reference an agent that doesn't exist
        skill_file = self.repo_root / "skills" / "sample-workflow" / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8") + "\n| 2 | `fw-2-research` |\n"
        skill_file.write_text(content, encoding="utf-8")
        self.assertFalse(vi.check_agent_references(self.repo_root))

    def test_agent_references_name_mismatch(self):
        # Frontmatter name doesn't match filename
        bad_agent = (
            "---\n"
            "name: different-name\n"
            "description: Test\n"
            "tools:\n"
            "  - Read\n"
            "---\n"
        )
        (self.repo_root / "agents" / "fw-1-spec.md").write_text(bad_agent, encoding="utf-8")
        self.assertFalse(vi.check_agent_references(self.repo_root))

    def test_review_tool_isolation_pass(self):
        self.assertTrue(vi.check_review_tool_isolation(self.repo_root))

    def test_review_tool_isolation_fail_with_edit(self):
        # Add Edit to review agent
        bad_review = (
            "---\n"
            "name: fw-5-review\n"
            "description: Senior Quality Auditor\n"
            "tools:\n"
            "  - Read\n"
            "  - Edit\n"
            "---\n"
        )
        (self.repo_root / "agents" / "fw-5-review.md").write_text(bad_review, encoding="utf-8")
        self.assertFalse(vi.check_review_tool_isolation(self.repo_root))

    def test_token_budgets_pass(self):
        self.assertTrue(vi.check_token_budgets(self.repo_root, max_words=40))

    def test_token_budgets_fail_too_long(self):
        long_desc = "word " * 45
        bloated_agent = (
            "---\n"
            "name: fw-1-spec\n"
            f"description: {long_desc}\n"
            "tools:\n"
            "  - Read\n"
            "---\n"
        )
        (self.repo_root / "agents" / "fw-1-spec.md").write_text(bloated_agent, encoding="utf-8")
        self.assertFalse(vi.check_token_budgets(self.repo_root, max_words=40))

    def test_token_budgets_folded_scalar(self):
        folded_agent = (
            "---\n"
            "name: gtw-1-spec\n"
            "description: >\n"
            "  Line one of description.\n"
            "  Line two of description.\n"
            "tools:\n"
            "  - Read\n"
            "---\n"
        )
        (self.repo_root / "agents" / "gtw-1-spec.md").write_text(folded_agent, encoding="utf-8")
        self.assertTrue(vi.check_token_budgets(self.repo_root, max_words=40))

    def test_real_codebase(self):
        # Validate that the actual real codebase passes all checks
        self.assertTrue(vi.check_version_sync(ROOT_DIR))
        self.assertTrue(vi.check_agent_references(ROOT_DIR))
        self.assertTrue(vi.check_review_tool_isolation(ROOT_DIR))
        self.assertTrue(vi.check_token_budgets(ROOT_DIR, max_words=40))

    def test_feature_workflow_ocp_guardrails(self):
        """Verify that OCP and extensibility guardrails are properly defined across all agents and docs."""
        # 1. AC 1: SKILL.md and README.md define OCP and extensibility principles
        skill_content = (ROOT_DIR / "skills" / "feature-workflow" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Open/Closed Principle (OCP)", skill_content)
        self.assertIn("data-driven dispatch", skill_content)

        readme_content = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("Open/Closed Principle & Extensibility", readme_content)

        # 2. AC 2: fw-2-research instructs researching OCP patterns & anti-patterns
        fw2_content = (ROOT_DIR / "agents" / "fw-2-research.md").read_text(encoding="utf-8")
        self.assertIn("Open/Closed Principle (OCP)", fw2_content)
        self.assertIn("anti-pattern", fw2_content)

        # 3. AC 3: fw-3-role-model requires OCP reference implementations & contrasting anti-patterns
        fw3_content = (ROOT_DIR / "agents" / "fw-3-role-model.md").read_text(encoding="utf-8")
        self.assertIn("Open/Closed Principle", fw3_content)
        self.assertIn("anti-pattern", fw3_content)

        # 4. AC 4: fw-4-plan instructs identifying extension points & OCP evaluation
        fw4_content = (ROOT_DIR / "agents" / "fw-4-plan.md").read_text(encoding="utf-8")
        self.assertIn("extension points", fw4_content)
        self.assertIn("Open/Closed", fw4_content)

        # 5. AC 5: fw-5-impl forbids patching conditionals & prioritizes data-driven lookups
        fw5_content = (ROOT_DIR / "agents" / "fw-5-impl.md").read_text(encoding="utf-8")
        self.assertIn("Open/Closed Principle (OCP)", fw5_content)
        self.assertIn("hướng dữ liệu", fw5_content)

        # 6. AC 6: fw-6-review includes Extensibility Audit rubric with Blocker/Major
        fw6_content = (ROOT_DIR / "agents" / "fw-6-review.md").read_text(encoding="utf-8")
        self.assertIn("Extensibility Audit", fw6_content)
        self.assertIn("Blocker", fw6_content)
        self.assertIn("Major", fw6_content)

        # 7. AC 7: fw-7-fix enforces root-cause remediation without branching hotfixes
        fw7_content = (ROOT_DIR / "agents" / "fw-7-fix.md").read_text(encoding="utf-8")
        self.assertIn("Root-cause Remediation", fw7_content)
        self.assertIn("hotfixing", fw7_content)

        # 8. AC 9: fw-6-review strictly adheres to least privilege (no Edit tool)
        fw6_tools = vi.parse_frontmatter(fw6_content).get("tools", [])
        self.assertNotIn("Edit", fw6_tools)


if __name__ == "__main__":
    unittest.main()
