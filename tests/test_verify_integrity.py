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
            "  - Grep\n"
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

    def test_review_tool_isolation_fail_with_write(self):
        bad_review = (
            "---\n"
            "name: fw-5-review\n"
            "description: Senior Quality Auditor\n"
            "tools:\n"
            "  - Read\n"
            "  - Write\n"
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

        gate = text.split("## Kiểm tra SRP", 1)[1].split("## Kiểm tra phạm vi owner", 1)[0]
        for token in ("YAGNI", "trách nhiệm MỚI", "Extract Method/Class", "nợ SRP", "Đề xuất refactor tiếp"):
            self.assertIn(token, gate)

        owner_gate = text.split("## Kiểm tra phạm vi owner", 1)[1].split("## Thang chi phí", 1)[0]
        for token in ("từ hẹp tới rộng", "caller truyền vào", "không phải hòa", "Lý do scope rộng hơn", "dừng đúng lúc"):
            self.assertIn(token, owner_gate)
        self.assertIn("cùng phạm vi owner", text.split("## Quy ước chung", 1)[1])

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

    def test_feature_workflow_four_steps(self):
        """Verify the four steps, their artifact gates, and the blind read-only reviewer."""

        def read(*parts):
            return (ROOT_DIR.joinpath(*parts)).read_text(encoding="utf-8")

        skill = read("skills", "feature-workflow", "SKILL.md")
        body = skill.split("---", 2)[2]
        headings = re.findall(r"^## (B\d)\. ", body, flags=re.MULTILINE)
        self.assertEqual(headings, ["B1", "B2", "B3", "B4"])

        artifacts = ["01-requirements.md", "02-solution.md", "03-implementation.md", "04-review-<n>.md"]
        steps = re.split(r"^## B\d\. .*$", body, flags=re.MULTILINE)[1:]
        for step, artifact in zip(steps, artifacts):
            with self.subTest(artifact=artifact):
                self.assertIn(f"**Ra:** `{artifact}`", step)
        for step, previous in zip(steps[1:], artifacts):
            with self.subTest(gate=previous):
                self.assertIn(f"**Vào:** `{previous}`", step)
        self.assertIn("`Trạng thái: xong`", body)
        self.assertIn("`CALLER: feature-workflow`", body)
        self.assertIn("comment-policy.md", body)

        description = vi.parse_frontmatter(skill)["description"]
        self.assertNotRegex(description, r"B\d")
        self.assertLess(len(description), 1024)

        fw_agents = sorted(f.stem for f in (ROOT_DIR / "agents").glob("fw-*.md"))
        self.assertEqual(fw_agents, ["fw-4-review"])
        self.assertIn("`fw-4-review`", body)
        reviewer = read("agents", "fw-4-review.md")
        tools = vi.parse_frontmatter(reviewer)["tools"]
        self.assertNotIn("Edit", tools)
        self.assertNotIn("Write", tools)
        self.assertIn("Không đọc file nào khác trong `.workflows/`", reviewer)
        review_step = steps[3]
        for hidden in ("`02-solution.md`", "`03-implementation.md`"):
            self.assertIn(hidden, review_step)
        self.assertIn('không dùng `subagent_type: "fork"`', review_step)

        self.assertIn("`01-requirements.md`", steps[2].split("1. Chọn", 1)[0])
        self.assertIn("#4 (Extensibility) và #7 (Maintainability) đều ≥ 4", steps[2])
        templates = read("skills", "solution-brainstorm", "templates.md")
        criteria = templates.split("## Criteria", 1)[1].split("## Option card", 1)[0]
        self.assertRegex(criteria, r"(?m)^4\. Extensibility")
        self.assertRegex(criteria, r"(?m)^7\. Maintainability")
        self.assertIn("Chạy vòng 2 chỉ khi vòng 1 có Blocker hoặc Major", review_step)
        self.assertIn("Không có vòng 3", review_step)
        self.assertIn("Tối đa 5 câu mỗi vòng", steps[0])
        self.assertIn("Không push, không tạo PR", body)
        self.assertIn("Không giao việc viết code cho\nsubagent", body)
        self.assertNotIn("làm tiếp từ bước", body)

    def test_standards_skills_guardrails(self):
        """Verify each platform standards skill is model-invocable, routes to its reference files, and replaced the old wrappers."""
        platforms = (ROOT_DIR / "skills" / "solution-brainstorm" / "platforms.md").read_text(encoding="utf-8")
        for name, heading in (("android-standards", "## Android"), ("kmp-standards", "## Kotlin Multiplatform")):
            with self.subTest(skill=name):
                base = ROOT_DIR / "skills" / name
                skill = (base / "SKILL.md").read_text(encoding="utf-8")
                frontmatter = vi.parse_frontmatter(skill)
                self.assertEqual(frontmatter["name"], name)
                self.assertNotIn("disable-model-invocation", frontmatter)
                description = frontmatter["description"]
                self.assertLessEqual(len(description), 1024)
                self.assertIn("Use when", description)
                self.assertIn("Do not use", description)
                self.assertLess(len(skill.splitlines()), 500)
                self.assertIn("## Luật bắt buộc", skill)

                router = skill.split("## Đọc thêm khi cần", 1)[1].split("\n## ", 1)[0]
                linked = set(re.findall(r"\| `([a-z-]+\.md)` \|", router))
                references = {p.name for p in base.glob("*.md") if p.name != "SKILL.md"}
                self.assertEqual(linked, references)
                for reference in references:
                    self.assertIn(f"Read by `{name}`", (base / reference).read_text(encoding="utf-8"))

                section = platforms.split(f"{heading}\n", 1)[1].split("\n## ", 1)[0]
                self.assertIn(f"`{name}`", section)

        self.assertIn("migration.md", (ROOT_DIR / "skills" / "android-standards" / "SKILL.md").read_text(encoding="utf-8"))
        scanned = [ROOT_DIR / "README.md", *ROOT_DIR.glob(".claude-plugin/*.json"), *ROOT_DIR.glob("skills/*/*.md"), *ROOT_DIR.glob("agents/*.md")]
        for path in scanned:
            with self.subTest(stale_reference=path.name):
                self.assertNotIn("standards-workflow", path.read_text(encoding="utf-8"))

    def test_cost_ladder_guardrails(self):
        """Verify the cheapest-first cost ladder in the shared legacy catalog."""

        def read(*parts):
            return (ROOT_DIR.joinpath(*parts)).read_text(encoding="utf-8")

        catalog = read("skills", "solution-brainstorm", "legacy-techniques.md")
        ladder = catalog.split("## Thang chi phí", 1)[1].split("## Quy ước chung", 1)[0]
        positions = []
        for token in ("Sprout/Wrap", "dependency-breaking Feathers", "Branch by Abstraction", "Strangler Fig"):
            self.assertIn(token, ladder)
            positions.append(ladder.index(token))
        self.assertEqual(positions, sorted(positions))
        self.assertIn("Mikado", ladder)
        self.assertIn("### Mikado graph", catalog)

        # Two Hats: solution-brainstorm filters techniques by hat for pure refactors
        self.assertIn("- Mũ: feature", catalog)
        self.assertIn("- Mũ: chung", catalog)
        brainstorm = read("skills", "solution-brainstorm", "SKILL.md")
        for token in ("`Mũ: feature`", "`Mũ: chung`", "Two Hats", "Lý do bậc rẻ hơn không đủ"):
            self.assertIn(token, brainstorm)

        self.assertIn("cost ladder", read("README.md"))

    def test_solution_brainstorm_legacy_guardrails(self):
        """Verify brainstorm reads the legacy catalog without changing its fixed structure."""
        base = ROOT_DIR / "skills" / "solution-brainstorm"
        skill = (base / "SKILL.md").read_text(encoding="utf-8")
        templates = (base / "templates.md").read_text(encoding="utf-8")
        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")

        self.assertIn("legacy-techniques.md", skill)
        self.assertIn("Read-only", skill)
        self.assertIn("**Options** in its Counts", skill)
        self.assertIn("**Kept** in its Counts", skill)
        self.assertIn("Add up each option's scores into the Total row", skill)
        self.assertNotIn("Do not add", skill)
        self.assertIn("Lý do bậc rẻ hơn không đủ", skill)
        self.assertIn("`## Kiểm tra SRP`", skill)
        self.assertIn("`## Kiểm tra phạm vi owner`", skill)
        self.assertIn("/issue-writing", templates)

        self.assertIn("Legacy technique & tests", templates)
        self.assertIn("Always one row per option", templates)
        self.assertIn("**Total (/35)**", templates)
        self.assertIn("does not have the highest Total", templates)
        criteria = re.findall(r"^(\d+)\. ", templates.split("## Output", 1)[0], flags=re.MULTILINE)
        self.assertEqual(criteria, ["1", "2", "3", "4", "5", "6", "7"])

        self.assertIn("legacy-techniques.md", readme)
        self.assertIn("cost ladder", readme)
        self.assertIn("total out of 35", readme)
        self.assertIn("owner scope check", readme)
        self.assertIn("owner scope dependency", templates)

    def test_solution_brainstorm_caller_mode(self):
        """Verify a calling workflow can skip the clarify step and the final question."""
        skill = (ROOT_DIR / "skills" / "solution-brainstorm" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`CALLER: feature-workflow`", skill.split("### Step 1.", 1)[0])
        self.assertIn("a caller is set (Step 0)", skill.split("### Step 3.", 1)[1].split("### Step 4.", 1)[0])
        self.assertIn("a caller is set (Step 0)", skill.split("### Step 6.", 1)[1])
        caller = skill.split("### Step 0.", 1)[1].split("### Step 1.", 1)[0]
        for token in ("Read the requirements file", "**Assumptions**", "`BRIEF`"):
            self.assertIn(token, caller)
        templates = (ROOT_DIR / "skills" / "solution-brainstorm" / "templates.md").read_text(encoding="utf-8")
        self.assertIn("Leave out the closing question when a caller is set", templates)
        self.assertIn("or a caller is set", templates.split("### 2. Assumptions", 1)[1].split("### 3.", 1)[0])

    def test_solution_brainstorm_counts_are_single_source(self):
        """Verify option counts live only in templates.md and the summaries quote them."""
        base = ROOT_DIR / "skills" / "solution-brainstorm"
        skill = (base / "SKILL.md").read_text(encoding="utf-8")
        templates = (base / "templates.md").read_text(encoding="utf-8")
        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")

        counts = templates.split("## Counts", 1)[1].split("## Criteria", 1)[0]
        options = int(re.search(r"^- Options: (\d+)$", counts, flags=re.MULTILINE).group(1))
        kept = int(re.search(r"^- Kept: (\d+)$", counts, flags=re.MULTILINE).group(1))
        detailed = int(re.search(r"^- Detailed: (\d+)$", counts, flags=re.MULTILINE).group(1))
        per_level = int(re.search(r"^- Min per level: (\d+)$", counts, flags=re.MULTILINE).group(1))
        self.assertLess(kept, options)
        self.assertLess(detailed, kept)
        self.assertLessEqual(per_level * 3, kept)
        generators = int(re.search(r"^- Generators: (\d+)$", counts, flags=re.MULTILINE).group(1))
        per_generator = int(re.search(r"^- Options per generator: (\d+)$", counts, flags=re.MULTILINE).group(1))
        passes = int(re.search(r"^- Judge passes: (\d+)$", counts, flags=re.MULTILINE).group(1))
        self.assertGreaterEqual(generators, 2)
        self.assertEqual(generators * per_generator, options)
        self.assertGreaterEqual(passes, 2)
        for token in ("**Generators**", "**Options per generator**", "**Judge passes**", "`sb-1-generator`", "`sb-2-judge`"):
            self.assertIn(token, skill)
        self.assertNotIn("without subagents", skill)
        self.assertIn('never `subagent_type: "fork"`', skill)

        description = vi.parse_frontmatter(skill)["description"]
        for text in (description, readme):
            self.assertIn(f"lists {options} options", text)
            self.assertIn(f"narrows them to {kept}", text)
            self.assertIn(f"details the top {detailed}", text)
        self.assertIn(f"keeps at least {per_level} options", readme)

        scores = templates.split("### 4. Scores", 1)[1].split("### 5.", 1)[0]
        header = next(line for line in scores.splitlines() if line.startswith("| Criterion"))
        self.assertEqual(header.strip("|").count("|"), kept)

        body = skill.split("---", 2)[2]
        self.assertNotRegex(body, r"\b\d+ options\b")
        self.assertNotRegex(body, r"best \d+\b")

    def test_lens_catalog_guardrails(self):
        """Verify every knowledge lens keeps its schema and conventions is always picked."""
        text = (ROOT_DIR / "skills" / "solution-brainstorm" / "lenses.md").read_text(encoding="utf-8")
        parts = re.split(r"^## (.+)$", text, flags=re.MULTILINE)
        lenses = {parts[i].strip(): parts[i + 1] for i in range(1, len(parts) - 1, 2)}

        self.assertEqual(list(lenses), ["conventions", "legacy", "research", "industry"])
        for name, body in lenses.items():
            with self.subTest(lens=name):
                for field in ("**Knowledge**:", "**Ask**:", "**Pick**:"):
                    self.assertIn(f"- {field}", body)
        self.assertIn("- **Pick**: always.", lenses["conventions"])
        self.assertIn("**Generators**", text)

    def test_brainstorm_subagents_are_read_only_and_blind(self):
        """Verify brainstorm generators and judge cannot write files and the judge uses another model."""
        agents = ROOT_DIR / "agents"
        generator = (agents / "sb-1-generator.md").read_text(encoding="utf-8")
        judge = (agents / "sb-2-judge.md").read_text(encoding="utf-8")
        templates = (ROOT_DIR / "skills" / "solution-brainstorm" / "templates.md").read_text(encoding="utf-8")

        for text in (generator, judge):
            tools = vi.parse_frontmatter(text).get("tools")
            self.assertNotIn("Write", tools)
            self.assertNotIn("Edit", tools)
            self.assertIn("Do not spawn subagents", text)
        self.assertNotIn("WebSearch", vi.parse_frontmatter(judge).get("tools"))
        self.assertNotEqual(vi.parse_frontmatter(generator)["model"], vi.parse_frontmatter(judge)["model"])

        self.assertIn("LENS_CATALOG", generator)
        self.assertIn("Do not score, rank, or recommend", generator)
        self.assertIn("Ignore the position of a card", judge)
        skill = (ROOT_DIR / "skills" / "solution-brainstorm" / "SKILL.md").read_text(encoding="utf-8")
        judge_step = skill.split("### Step 5.", 1)[1].split("### Step 6.", 1)[0]
        for token in ("without its Knowledge line", "`nợ SRP`", "`Lý do scope rộng hơn`", "Breaks convention"):
            self.assertIn(token, judge_step)
        self.assertIn("only when that line names web sources", generator)
        self.assertIn("not the writing", judge)
        for heading in ("## Option card", "## Judge rubric"):
            self.assertIn(heading, templates)
            self.assertIn(f"`{heading}`", generator + judge)

    def test_comment_policy_is_single_source(self):
        """Verify every code-writing step reads the shared comment policy instead of copying it."""

        def read(*parts):
            return (ROOT_DIR.joinpath(*parts)).read_text(encoding="utf-8")

        policy = read("skills", "solution-brainstorm", "comment-policy.md")
        for heading in ("## Mặc định", "## Được giữ (chỉ WHY)", "## Không viết", "## Phạm vi", "## Mức độ khi review"):
            self.assertIn(heading, policy)

        self.assertIn("comment-policy.md", read("skills", "solution-brainstorm", "SKILL.md"))
        self.assertIn("comment-policy.md", read("skills", "solution-brainstorm", "templates.md"))
        self.assertIn("COMMENT_POLICY", read("skills", "feature-workflow", "SKILL.md"))
        reviewer = read("agents", "fw-4-review.md")
        self.assertIn("COMMENT_POLICY", reviewer)
        self.assertNotIn("nhãn/banner", reviewer)
        self.assertIn("comment-policy.md", vi.SHARED_REFERENCE_FILES)
        self.assertIn("comment-policy.md", read("README.md"))

    def test_distill_expertise_tables_are_single_source(self):
        """Verify counts, domains, and filters live in their sidecar files and the skill only points to them."""
        base = ROOT_DIR / "skills" / "distill-expertise"
        skill = (base / "SKILL.md").read_text(encoding="utf-8")
        templates = (base / "templates.md").read_text(encoding="utf-8")
        domains = (base / "evidence-domains.md").read_text(encoding="utf-8")
        filters = (base / "knowledge-filters.md").read_text(encoding="utf-8")

        frontmatter = vi.parse_frontmatter(skill)
        self.assertEqual(frontmatter["name"], "distill-expertise")
        self.assertEqual(frontmatter["disable-model-invocation"], "true")

        counts = templates.split("## Counts", 1)[1].split("## Report", 1)[0]
        for key in ("Candidates", "Kept", "Min schools", "Votes", "Few voices", "Shortfall", "Chat summary", "File name"):
            self.assertRegex(counts, rf"(?m)^- {key}: ", key)
        kept = int(re.search(r"(?m)^- Kept: (\d+)$", counts).group(1))
        high = int(re.search(r"(?m)^- Candidates: \d+-(\d+)$", counts).group(1))
        self.assertLess(kept, high)
        self.assertNotRegex(counts, r"\d+ of 6", "vote thresholds must scale with N, not a fixed 6")
        self.assertIn("## Self-check", templates)

        header = next(line for line in domains.splitlines() if line.startswith("| Domain type"))
        for column in ("Signals", "Student evidence", "Proxy when none", "Freshness limit", "Apply form"):
            self.assertIn(column, header)
        self.assertIn("| Fallback |", domains)

        for heading in ("## Evidence labels", "## Red flags", "## Mentor rules", "## Principle filters", "## Principle labels"):
            self.assertIn(heading, filters)

        body = skill.split("---", 2)[2]
        for name in ("templates.md", "evidence-domains.md", "knowledge-filters.md"):
            self.assertIn(name, body)
        self.assertNotRegex(body, r"\b\d+ (candidates|teachers|of \d+)\b")
        for name in ("evidence-domains.md", "knowledge-filters.md"):
            self.assertIn(name, vi.SHARED_REFERENCE_FILES)

        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
        low = int(re.search(r"(?m)^- Candidates: (\d+)-\d+$", counts).group(1))
        min_schools = int(re.search(r"(?m)^- Min schools: (\d+)$", counts).group(1))
        self.assertIn(f"searches the web for {low}-{high} candidates", readme)
        self.assertIn(f"keeps {kept} teachers from at least {min_schools} schools", readme)

    def test_agent_authoring_router_guardrails(self):
        """Verify agent-authoring routes to every reference file directly and stays model-invocable."""
        base = ROOT_DIR / "skills" / "agent-authoring"
        skill = (base / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = vi.parse_frontmatter(skill)
        self.assertEqual(frontmatter["name"], "agent-authoring")
        self.assertNotIn("disable-model-invocation", frontmatter)
        description = frontmatter["description"]
        self.assertLessEqual(len(description), 1024)
        self.assertIn("Use when", description)
        self.assertIn("Do not use", description)
        self.assertLess(len(skill.splitlines()), 500)

        router = skill.split("## Read only what you need", 1)[1].split("\n## ", 1)[0]
        linked = set(re.findall(r"\| `([a-z-]+\.md)` \|", router))
        references = {p.name for p in base.glob("*.md") if p.name != "SKILL.md"}
        self.assertEqual(linked, references)
        for name in references:
            with self.subTest(reference=name):
                text = (base / name).read_text(encoding="utf-8")
                self.assertIn("Read by `agent-authoring`", text)
                if len(text.splitlines()) > 100:
                    self.assertIn("## Contents", text)

        platforms = (ROOT_DIR / "skills" / "solution-brainstorm" / "platforms.md").read_text(encoding="utf-8")
        section = platforms.split("## Claude Code agent artifacts", 1)[1].split("\n## ", 1)[0]
        for field in ("- **Detect**:", "- **Standards**:", "- **Outdated signals**:"):
            self.assertIn(field, section)
        self.assertIn("`agent-authoring`", section)

    def test_skill_file_names_are_case_unique(self):
        """Verify no skill folder has two files whose names differ only by case (they collide on macOS)."""
        for folder in (ROOT_DIR / "skills").iterdir():
            if folder.is_dir():
                names = [p.name.lower() for p in folder.iterdir()]
                self.assertEqual(len(names), len(set(names)), folder.name)


if __name__ == "__main__":
    unittest.main()
