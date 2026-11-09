#!/usr/bin/env python3
"""
Unit tests for scripts/verify-integrity.py.
Tests all pass and fail conditions using temporary directory structures.
"""

import contextlib
import io
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
        # A skill using an arbitrary prefix (not fw) must be detected without
        # hardcoding, so a new workflow's SKILL.md never silently produces
        # "No subagent references found" simply because its prefix is unknown.
        (self.repo_root / "skills" / "another-workflow").mkdir(parents=True)
        zzz_agent = (
            "---\n"
            "name: zzz-1-spec\n"
            "description: Senior Business Analyst - Survey refactor scope\n"
            "tools:\n"
            "  - Read\n"
            "  - Write\n"
            "model: sonnet\n"
            "---\n"
            "Content here\n"
        )
        (self.repo_root / "agents" / "zzz-1-spec.md").write_text(zzz_agent, encoding="utf-8")
        skill_content = (
            "---\n"
            "name: another-workflow\n"
            "description: Sample\n"
            "---\n"
            "| Bước | Agent |\n"
            "| 1 | `zzz-1-spec` |\n"
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
            "| 9 | `zzz-9-ghost` |\n"
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
            "name: zzz-1-spec\n"
            "description: >\n"
            "  Line one of description.\n"
            "  Line two of description.\n"
            "tools:\n"
            "  - Read\n"
            "---\n"
        )
        (self.repo_root / "agents" / "zzz-1-spec.md").write_text(folded_agent, encoding="utf-8")
        self.assertTrue(vi.check_token_budgets(self.repo_root, max_words=40))

    def test_real_codebase(self):
        # Validate that the actual real codebase passes all checks
        self.assertTrue(vi.check_version_sync(ROOT_DIR))
        self.assertTrue(vi.check_agent_references(ROOT_DIR))
        self.assertTrue(vi.check_review_tool_isolation(ROOT_DIR))
        self.assertTrue(vi.check_token_budgets(ROOT_DIR, max_words=40))
        self.assertTrue(vi.check_hooks(ROOT_DIR))
        self.assertTrue(vi.check_catalog_references(ROOT_DIR))

    def _write_hooks(self, config, script_mode=0o755, script=True):
        (self.repo_root / "hooks").mkdir(exist_ok=True)
        (self.repo_root / "hooks" / "hooks.json").write_text(
            config if isinstance(config, str) else json.dumps(config), encoding="utf-8"
        )
        if script:
            path = self.repo_root / "hooks" / "run.sh"
            path.write_text("#!/bin/sh\n", encoding="utf-8")
            path.chmod(script_mode)

    @staticmethod
    def _hooks_config(command='"${CLAUDE_PLUGIN_ROOT}/hooks/run.sh" stop'):
        return {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": command}]}]}}

    def test_hooks_absent_pass(self):
        self.assertTrue(vi.check_hooks(self.repo_root))

    def test_hooks_pass(self):
        self._write_hooks(self._hooks_config())
        self.assertTrue(vi.check_hooks(self.repo_root))

    def test_hooks_invalid_json(self):
        self._write_hooks("{not json", script=False)
        self.assertFalse(vi.check_hooks(self.repo_root))

    def test_hooks_missing_top_level_key(self):
        self._write_hooks({"Stop": []}, script=False)
        self.assertFalse(vi.check_hooks(self.repo_root))

    def test_hooks_script_missing(self):
        self._write_hooks(self._hooks_config(), script=False)
        self.assertFalse(vi.check_hooks(self.repo_root))

    def test_hooks_script_not_executable(self):
        self._write_hooks(self._hooks_config(), script_mode=0o644)
        self.assertFalse(vi.check_hooks(self.repo_root))

    def test_hooks_command_without_plugin_root(self):
        self._write_hooks(self._hooks_config("/usr/bin/true"))
        self.assertFalse(vi.check_hooks(self.repo_root))

    def _write(self, rel, content):
        path = self.repo_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_catalog_references_pass_with_catalog(self):
        self._write("skills/solution-brainstorm/legacy-techniques.md", "# catalog\n")
        self._write("agents/fw-4-plan.md", "Read legacy-techniques.md\n")
        self.assertTrue(vi.check_catalog_references(self.repo_root))

    def test_catalog_references_fail_when_catalog_missing(self):
        self._write("agents/fw-4-plan.md", "Read legacy-techniques.md\n")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            ok = vi.check_catalog_references(self.repo_root)
        self.assertFalse(ok)
        self.assertIn("[FAIL]", out.getvalue())
        self.assertIn("fw-4-plan.md", out.getvalue())

    def test_catalog_references_pass_without_referrer(self):
        self.assertTrue(vi.check_catalog_references(self.repo_root))

    def test_legacy_catalog_guardrails(self):
        """Verify the legacy techniques catalog keeps its data schema."""
        text = (ROOT_DIR / "skills" / "solution-brainstorm" / "legacy-techniques.md").read_text(encoding="utf-8")
        techniques_part = text.split("## Kỹ thuật", 1)[1]
        parts = re.split(r"^### (.+)$", techniques_part, flags=re.MULTILINE)
        entries = {parts[i].split("(")[0].strip(): parts[i + 1] for i in range(1, len(parts) - 1, 2)}

        required_techniques = (
            "Sprout Method",
            "Sprout Class",
            "Wrap Method",
            "Wrap Class",
            "Parameterize Constructor",
            "Extract Interface",
            "Extract and Override Call",
            "Branch by Abstraction",
            "Strangler Fig",
            "Mikado Method",
        )
        required_fields = ("Bậc:", "Mũ:", "Khi dùng:", "Khi leo bậc:", "Các bước:", "Test bắt buộc:", "Nợ còn lại:")
        for name in required_techniques:
            with self.subTest(technique=name):
                self.assertIn(name, entries)
                for field in required_fields:
                    self.assertIn(f"- {field}", entries[name])

        for token in (
            "Mikado",
            "characterization test",
            "happy",
            "edge",
            "error",
            "Lý do bậc rẻ hơn không đủ",
            "≥2 consumer",
            "Mũ: feature",
            "Mũ: chung",
        ):
            self.assertIn(token, text)
        self.assertNotIn("http://", text)
        self.assertNotIn("https://", text)

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
        self.assertNotIn("Mỗi slice đúng 1 commit", skill)
        self.assertIn("Commit theo task", skill)

        self.assertIn("Hướng mở rộng sau", read("agents", "fw-1-spec.md"))

        fw4 = read("agents", "fw-4-plan.md")
        for token in ("Slice plan", "<slug>/<n>-<tên-slice>", "≥2 consumer", "Task plan", "PR title"):
            self.assertIn(token, fw4)
        for kind in ("`refactor`", "`add`", "`change`", "`switch`", "`remove`"):
            self.assertIn(kind, fw4)

        fw5 = read("agents", "fw-5-impl.md")
        self.assertNotIn("đúng 1 commit", fw5)
        self.assertIn("Vòng task", fw5)
        self.assertIn("Task Ledger", fw5)
        self.assertIn("API công khai", fw5)
        self.assertNotIn("CÙNG commit đầu", fw5)

        fw6 = read("agents", "fw-6-review.md")
        self.assertIn("git diff --numstat", fw6)
        self.assertIn("Scope & Budget Audit", fw6)
        self.assertIn("Commit Granularity Audit", fw6)
        self.assertIn("[TASKS]", fw6)
        self.assertNotIn("Số commit phải là 1", fw6)
        self.assertNotIn("Edit", vi.parse_frontmatter(fw6).get("tools", []))

        fw7 = read("agents", "fw-7-fix.md")
        self.assertIn("git push -u origin", fw7)
        self.assertIn("Ship notes", fw7)
        self.assertNotIn("do NOT commit", fw7)
        self.assertIn("Không viết lại commit đã có", fw7)
        self.assertNotIn("git rebase -i", fw7)
        self.assertNotIn("git rev-list --count <base>..HEAD` = 1", fw7)

        standards = read("skills", "android-standards-workflow", "standards.md")
        for token in ("tách slice riêng", "/feature-workflow", ":core:ui"):
            self.assertIn(token, standards)
        self.assertNotIn("CÙNG commit đầu", standards)

        android_skill = read("skills", "android-standards-workflow", "SKILL.md")
        section = android_skill.split("## Bước 3", 1)[1].split("## Sau khi gọi", 1)[0]
        block = re.search(r"```text\n(.*?)```", section, re.DOTALL).group(1)
        self.assertIsNone(re.search(r"[A-Z][A-Z0-9]+-[0-9]+", block))
        self.assertIn("slice", block)

        self.assertIn("stacked", read("README.md"))

    def test_cost_ladder_guardrails(self):
        """Verify the cheapest-first cost ladder in feature-workflow."""

        def read(*parts):
            return (ROOT_DIR.joinpath(*parts)).read_text(encoding="utf-8")

        def section(text, start, end):
            return text.split(start, 1)[1].split(end, 1)[0]

        def assert_ordered(text, tokens):
            positions = []
            for token in tokens:
                self.assertIn(token, text)
                positions.append(text.index(token))
            self.assertEqual(positions, sorted(positions))

        reason = "Lý do bậc rẻ hơn không đủ"
        fw4 = read("agents", "fw-4-plan.md")
        ladder = section(fw4, "## 2b. Thang chi phí cho legacy chưa test", "## 3.")
        assert_ordered(
            ladder,
            [
                "| 1. Sprout/Wrap",
                "| 2. dependency-breaking Feathers",
                "| 3. Branch by Abstraction",
                "| 4. Strangler Fig",
            ],
        )
        for token in (
            "Sprout Method",
            "Sprout Class",
            "Wrap Method",
            "Wrap Class",
            "characterization test",
            "≥2 consumer",
        ):
            self.assertIn(token, ladder)
        self.assertIn(reason, section(fw4, "<constraints>", "</constraints>"))
        self.assertIn(reason, fw4.split("<output>", 1)[1])

        fw_skill = read("skills", "feature-workflow", "SKILL.md")
        self.assertIn("Sprout/Wrap", fw_skill)
        self.assertIn("fw-4-plan", fw_skill)
        self.assertIn("legacy chưa test", read("agents", "fw-1-spec.md"))
        self.assertIn("Sprout/Wrap", read("agents", "fw-2-research.md"))
        fw5 = read("agents", "fw-5-impl.md")
        self.assertIn("Sprout", fw5)
        self.assertIn("điểm gọi", fw5)
        fw6 = read("agents", "fw-6-review.md")
        self.assertIn("bậc thấp nhất đủ dùng", fw6)
        self.assertIn("điểm gọi", fw6)
        self.assertNotIn("Edit", vi.parse_frontmatter(fw6).get("tools"))

        catalog = read("skills", "solution-brainstorm", "legacy-techniques.md")
        mikado_heading = "### Mikado graph"
        self.assertIn(mikado_heading, catalog)
        self.assertIn(mikado_heading, fw4)
        fw4_ladder = section(fw4, "## 2b. Thang chi phí cho legacy chưa test", "## 3.")
        self.assertIn("legacy-techniques.md", fw4_ladder)
        self.assertIn("Mikado", fw4_ladder)
        for name in ("fw-5-impl", "fw-6-review"):
            self.assertIn("Mikado", read("agents", f"{name}.md"))
        self.assertIn("LEGACY_CATALOG", fw_skill)

        for text in (fw4, fw_skill):
            self.assertNotIn("http://", text)
            self.assertNotIn("https://", text)

        self.assertIn("cost ladder", read("README.md"))

    def test_solution_brainstorm_legacy_guardrails(self):
        """Verify brainstorm reads the legacy catalog without changing its fixed structure."""
        base = ROOT_DIR / "skills" / "solution-brainstorm"
        skill = (base / "SKILL.md").read_text(encoding="utf-8")
        templates = (base / "templates.md").read_text(encoding="utf-8")
        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")

        self.assertIn("legacy-techniques.md", skill)
        self.assertIn("Read-only", skill)
        self.assertIn("exactly 12", skill)
        self.assertIn("Add up each option's scores into the Total row", skill)
        self.assertNotIn("Do not add", skill)
        self.assertIn("Lý do bậc rẻ hơn không đủ", skill)

        self.assertIn("Legacy technique & tests", templates)
        self.assertIn("Always 12 rows", templates)
        self.assertIn("**Total (/30)**", templates)
        self.assertIn("does not have the highest Total", templates)
        criteria = re.findall(r"^(\d+)\. ", templates.split("## Output", 1)[0], flags=re.MULTILINE)
        self.assertEqual(criteria, ["1", "2", "3", "4", "5", "6"])

        self.assertIn("legacy-techniques.md", readme)
        self.assertIn("cost ladder", readme)
        self.assertIn("lists 12 options", readme)
        self.assertIn("total out of 30", readme)


if __name__ == "__main__":
    unittest.main()
