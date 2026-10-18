#!/usr/bin/env python3
"""
Unit tests for scripts/verify-integrity.py.
Tests all pass and fail conditions using temporary directory structures.
"""

import json
import re
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

    def test_agent_references_generic_prefix_pass(self):
        # A skill using an arbitrary prefix (not fw/gtw) must be detected without
        # hardcoding, so a new workflow's SKILL.md never silently produces
        # "No subagent references found" simply because its prefix is unknown.
        (self.repo_root / "skills" / "another-workflow").mkdir(parents=True)
        rcw_agent = (
            "---\n"
            "name: rcw-1-spec\n"
            "description: Senior Business Analyst - Survey refactor scope\n"
            "tools:\n"
            "  - Read\n"
            "  - Write\n"
            "model: sonnet\n"
            "---\n"
            "Content here\n"
        )
        (self.repo_root / "agents" / "rcw-1-spec.md").write_text(rcw_agent, encoding="utf-8")
        skill_content = (
            "---\n"
            "name: another-workflow\n"
            "description: Sample\n"
            "---\n"
            "| Bước | Agent |\n"
            "| 1 | `rcw-1-spec` |\n"
        )
        (self.repo_root / "skills" / "another-workflow" / "SKILL.md").write_text(
            skill_content, encoding="utf-8"
        )
        self.assertTrue(vi.check_agent_references(self.repo_root))

    def test_agent_references_generic_prefix_missing(self):
        # Referencing a not-yet-created agent under an unknown prefix must FAIL
        # loudly instead of being silently skipped by a hardcoded prefix regex.
        (self.repo_root / "skills" / "another-workflow").mkdir(parents=True)
        skill_content = (
            "---\n"
            "name: another-workflow\n"
            "description: Sample\n"
            "---\n"
            "| Bước | Agent |\n"
            "| 9 | `rcw-9-ghost` |\n"
        )
        (self.repo_root / "skills" / "another-workflow" / "SKILL.md").write_text(
            skill_content, encoding="utf-8"
        )
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

        # 1b. fw-1-spec surveys extension points and variation axes
        fw1_content = (ROOT_DIR / "agents" / "fw-1-spec.md").read_text(encoding="utf-8")
        self.assertIn("extension points", fw1_content)
        self.assertIn("trục biến thiên", fw1_content)

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
        self.assertIn("### Extension Points & OCP Evaluation", fw4_content)

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

    def test_feature_workflow_slicing_guardrails(self):
        """Verify that PR slicing, budget and rule-of-three guardrails are defined consistently."""
        def read(*parts):
            return (ROOT_DIR.joinpath(*parts)).read_text(encoding="utf-8")

        skill = read("skills", "feature-workflow", "SKILL.md")
        for token in ("≤~400 dòng production", "≤~15 file", "<slug>/<n>-<tên-slice>", "slice chuẩn bị",
                      "KHÔNG push", "KHÔNG tạo PR", "git push -u origin", "05-impl-<n>.md"):
            self.assertIn(token, skill)
        self.assertNotIn("chưa commit", skill)

        self.assertIn("Hướng mở rộng sau", read("agents", "fw-1-spec.md"))

        fw4 = read("agents", "fw-4-plan.md")
        for token in ("Slice plan", "<slug>/<n>-<tên-slice>", "≥2 consumer"):
            self.assertIn(token, fw4)

        fw5 = read("agents", "fw-5-impl.md")
        self.assertIn("đúng 1 commit", fw5)
        self.assertIn("API công khai", fw5)
        self.assertNotIn("CÙNG commit đầu", fw5)

        fw6 = read("agents", "fw-6-review.md")
        self.assertIn("git diff --numstat", fw6)
        self.assertIn("Scope & Budget Audit", fw6)
        self.assertNotIn("Edit", vi.parse_frontmatter(fw6).get("tools", []))

        fw7 = read("agents", "fw-7-fix.md")
        self.assertIn("git push -u origin", fw7)
        self.assertIn("Ship notes", fw7)
        self.assertNotIn("do NOT commit", fw7)

        standards = read("skills", "android-standards-workflow", "standards.md")
        for token in ("tách slice riêng", "/refactor-code-workflow", ":core:ui"):
            self.assertIn(token, standards)
        self.assertNotIn("CÙNG commit đầu", standards)

        android_skill = read("skills", "android-standards-workflow", "SKILL.md")
        section = android_skill.split("## Bước 3", 1)[1].split("## Sau khi gọi", 1)[0]
        block = re.search(r"```text\n(.*?)```", section, re.DOTALL).group(1)
        self.assertIsNone(re.search(r"[A-Z][A-Z0-9]+-[0-9]+", block))
        self.assertIn("slice", block)

        self.assertIn("stacked", read("README.md"))

    def test_refactor_code_workflow_guardrails(self):
        """Verify refactor-code-workflow embeds the 7 safe-refactor disciplines end-to-end."""
        skill_content = (ROOT_DIR / "skills" / "refactor-code-workflow" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        fm = vi.parse_frontmatter(skill_content)
        self.assertEqual(fm.get("name"), "refactor-code-workflow")
        self.assertIn("Chỉ dùng khi", fm.get("description", ""))
        self.assertIn("Không tự kích hoạt", fm.get("description", ""))

        # Opening line, guard clauses, Two Hats rationale, no-fork rationale, output layout
        self.assertIn(
            "Tôi đang dùng skill refactor-code-workflow, gồm 7 bước.", skill_content
        )
        self.assertIn("feature-workflow", skill_content)
        self.assertIn("reproduce", skill_content)
        self.assertIn("Two Hats", skill_content)
        self.assertIn("Branch by Abstraction", skill_content)
        self.assertIn("Strangler Fig", skill_content)
        self.assertIn("fork", skill_content)
        self.assertIn("04-baseline", skill_content)
        self.assertIn("## TÓM TẮT", skill_content)
        self.assertIn("## CHI TIẾT", skill_content)

        agent_names = [
            "rcw-1-spec",
            "rcw-2-research",
            "rcw-3-plan",
            "rcw-4-protect",
            "rcw-5-refactor",
            "rcw-6-review",
            "rcw-7-fix",
        ]
        for name in agent_names:
            self.assertIn(name, skill_content)
            agent_path = ROOT_DIR / "agents" / f"{name}.md"
            self.assertTrue(agent_path.exists(), f"missing agent file {name}.md")

        agent_contents = {
            name: (ROOT_DIR / "agents" / f"{name}.md").read_text(encoding="utf-8")
            for name in agent_names
        }

        # Model routing: only rcw-3-plan uses opus, rest use sonnet
        for name in agent_names:
            fm_agent = vi.parse_frontmatter(agent_contents[name])
            expected_model = "opus" if name == "rcw-3-plan" else "sonnet"
            self.assertEqual(fm_agent.get("model"), expected_model, f"{name} model mismatch")

        # rcw-6-review must not declare Edit tool (least privilege)
        rcw6_content = agent_contents["rcw-6-review"]
        rcw6_tools = vi.parse_frontmatter(rcw6_content).get("tools", [])
        self.assertNotIn("Edit", rcw6_tools)

        # Discipline 1: characterization test / Golden Master before any fix
        rcw4_content = agent_contents["rcw-4-protect"]
        self.assertIn("characterization test", rcw4_content)
        self.assertIn("Golden Master", rcw4_content)
        self.assertIn("### Baseline Manifest", rcw4_content)
        self.assertIn("04-baseline", rcw4_content)

        # Discipline 2: seams to cut dependencies without touching code in place
        rcw3_content = agent_contents["rcw-3-plan"]
        self.assertIn("### Seams & Dependency Breaking", rcw3_content)
        self.assertIn("### Micro-step Sequence", rcw3_content)
        self.assertIn("Branch by Abstraction", rcw3_content)
        self.assertIn("Strangler Fig", rcw3_content)
        self.assertIn("Second-order", rcw3_content)

        # Discipline 3/5: smallest scoped change, micro-step with revert on red
        rcw5_content = agent_contents["rcw-5-refactor"]
        self.assertIn("micro-step", rcw5_content)
        self.assertIn("revert", rcw5_content)
        self.assertIn("04-baseline", rcw5_content)
        self.assertIn("Two Hats", rcw5_content)

        # Discipline 4: never mix bugfix/refactor/feature (Two Hats) at spec level
        rcw1_content = agent_contents["rcw-1-spec"]
        self.assertIn("Vùng thay đổi", rcw1_content)
        self.assertIn("Hành vi quan sát được", rcw1_content)
        self.assertIn("seam", rcw1_content)
        self.assertIn("Phát hiện ngoài phạm vi", rcw1_content)

        # Discipline 6/7 verified via review's Behavior Preservation Audit rubric
        self.assertIn("Behavior Preservation Audit", rcw6_content)
        self.assertIn("test loosening", rcw6_content)
        self.assertIn("Blocker", rcw6_content)
        self.assertIn("Major", rcw6_content)
        self.assertIn("diff coverage", rcw6_content)
        self.assertIn("03-plan.md", rcw6_content)
        self.assertIn("05-refactor.md", rcw6_content)

        # rcw-7-fix restores oracle instead of loosening tests to hide the fix
        rcw7_content = agent_contents["rcw-7-fix"]
        self.assertIn("Root-cause", rcw7_content)
        self.assertIn("04-baseline", rcw7_content)
        self.assertIn("restore", rcw7_content)
        self.assertIn("test loosening", rcw7_content)
        self.assertIn("refactor:", rcw7_content)

        # No external URLs in any rcw-* agent or the SKILL.md (avoid lychee flakiness)
        for name in agent_names:
            self.assertNotIn("http://", agent_contents[name])
            self.assertNotIn("https://", agent_contents[name])
        self.assertNotIn("http://", skill_content)
        self.assertNotIn("https://", skill_content)

        # README synced: overview, usage, subagents reference
        readme_content = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("/refactor-code-workflow", readme_content)
        self.assertIn("/workflow:refactor-code-workflow", readme_content)
        self.assertIn("rcw-1-spec", readme_content)
        self.assertIn("rcw-6-review", readme_content)


if __name__ == "__main__":
    unittest.main()
