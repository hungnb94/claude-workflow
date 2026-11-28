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

    USER_ONLY_SKILLS = {"distill-expertise", "grounded-answer", "learning-coach"}

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
        self.assertEqual(fw_agents, ["fw-3-evidence", "fw-3-implement", "fw-4-review"])
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
        self.assertIn("`STANDARDS`", review_step)
        self.assertIn("`STANDARDS`", reviewer.split("<inputs>", 1)[1].split("</inputs>", 1)[0])
        self.assertIn("`Vi phạm chuẩn`", reviewer.split("<output>", 1)[1])

        self.assertIn("`01-requirements.md`", steps[2].split("1. Chọn", 1)[0])
        self.assertIn("#4 (Extensibility) và #7 (Maintainability) đều ≥ 4", steps[2])
        templates = read("skills", "solution-brainstorm", "templates.md")
        criteria = templates.split("## Criteria", 1)[1].split("## Option card", 1)[0]
        self.assertRegex(criteria, r"(?m)^4\. Extensibility")
        self.assertRegex(criteria, r"(?m)^7\. Maintainability")
        self.assertIn("Chạy vòng 2 chỉ khi vòng 1 có Blocker hoặc Major", review_step)
        self.assertIn("Không có vòng 3", review_step)
        self.assertIn("Tối đa 5 câu mỗi vòng", steps[0])
        self.assertIn("Mỗi câu có 3-4 lựa chọn đặt ở các điểm khác nhau trên một trục", steps[0])
        self.assertIn("(a) gọn nhất ..., (b) theo chuẩn đã đọc ..., (c) bền nhất ...", steps[0])
        self.assertIn("không về cách code: việc đó của B2", steps[0])
        self.assertNotIn("Các lựa chọn: (a) ..., (b) ...\n", steps[0])
        self.assertIn("Không push, không tạo PR", body)
        self.assertIn("Session chính không tự sửa code", body)

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

    def test_standards_lookup_is_single_source(self):
        """Verify both callers detect standards through the shared lookup and every pointer resolves to a skill."""

        def read(*parts):
            return (ROOT_DIR.joinpath(*parts)).read_text(encoding="utf-8")

        lookup = read("skills", "solution-brainstorm", "standards-lookup.md")
        for token in ("`platforms.md`", "**Detect**", "**Standards**", "Glob", "`không có`", "absolute paths", "Secondary:"):
            self.assertIn(token, lookup)
        missing_skill = lookup.split("Glob", 1)[1].split("\n3. ", 1)[0]
        self.assertIn("`không có`", missing_skill)
        self.assertNotIn("primary section itself", missing_skill)
        self.assertIn("standards-lookup.md", vi.SHARED_REFERENCE_FILES)
        self.assertIn("standards-lookup.md", read("README.md"))

        workflow = read("skills", "feature-workflow", "SKILL.md")
        b1 = workflow.split("## B1.", 1)[1].split("## B2.", 1)[0]
        b3 = workflow.split("## B3.", 1)[1].split("## B4.", 1)[0]
        self.assertIn("../solution-brainstorm/standards-lookup.md", b1)
        self.assertIn("`platforms.md`", b1)
        self.assertIn("`Chuẩn áp dụng`", b1)
        self.assertIn("`Chuẩn áp dụng`", b3)
        brainstorm = read("skills", "solution-brainstorm", "SKILL.md")
        self.assertIn("standards-lookup.md", brainstorm)
        step1 = brainstorm.split("### Step 1.", 1)[1].split("### Step 2.", 1)[0]
        self.assertIn("absolute paths of its standards in your Context notes", step1)
        self.assertIn("the platform standards in the brief", read("skills", "solution-brainstorm", "lenses.md"))
        for caller in (workflow, brainstorm):
            self.assertNotIn("A section matches when", caller)

        platforms = read("skills", "solution-brainstorm", "platforms.md")
        pointers = re.findall(r"(?m)^- \*\*Standards\*\*: (.*)$", platforms)
        self.assertGreaterEqual(len(pointers), 3)
        for pointer in pointers:
            with self.subTest(pointer=pointer):
                match = re.match(r"skill `([a-z-]+)`", pointer)
                self.assertIsNotNone(match, "Standards line must name a skill as skill `<name>`")
                self.assertTrue((ROOT_DIR / "skills" / match.group(1) / "SKILL.md").is_file())

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
        judge_agents = int(re.search(r"^- Judge agents: (\d+)$", counts, flags=re.MULTILINE).group(1))
        orderings = int(re.search(r"^- Judge orderings: (\d+)$", counts, flags=re.MULTILINE).group(1))
        self.assertGreaterEqual(generators, 2)
        self.assertEqual(generators * per_generator, options)
        self.assertGreaterEqual(judge_agents, 1)
        self.assertGreaterEqual(orderings, 2)
        self.assertLessEqual(generators + judge_agents, 3)
        self.assertNotIn("Judge passes", templates)
        for token in (
            "**Generators**",
            "**Options per generator**",
            "**Judge agents**",
            "**Judge orderings**",
            "`sb-1-generator`",
            "`sb-2-judge`",
        ):
            self.assertIn(token, skill)
        self.assertNotIn("without subagents", skill)
        self.assertIn('never `subagent_type: "fork"`', skill)

        description = vi.parse_frontmatter(skill)["description"]
        for text in (description, readme):
            self.assertIn(f"lists {options} options", text)
            self.assertIn(f"narrows them to {kept}", text)
            self.assertIn(f"details the top {detailed}", text)
        self.assertIn(f"keeps at least {per_level} options", readme)
        self.assertIn(f"`⭐ top 1` to `⭐ top {detailed}`", readme)

        scores = templates.split("### 4.", 1)[1].split("### 5.", 1)[0]
        header = next(line for line in scores.splitlines() if line.startswith("| Criterion"))
        self.assertEqual(header.strip("|").count("|"), kept)

        body = skill.split("---", 2)[2]
        self.assertNotRegex(body, r"\b\d+ options\b")
        self.assertNotRegex(body, r"best \d+\b")

    def test_solution_brainstorm_output_shows_options_before_scores(self):
        """Verify each kept option is shown with its total before the per-criterion scores, top ones marked."""
        templates = (ROOT_DIR / "skills" / "solution-brainstorm" / "templates.md").read_text(encoding="utf-8")
        counts = templates.split("## Counts", 1)[1].split("## Criteria", 1)[0]
        output = templates.split("## Output", 1)[1]
        kept_part = output.split("### 4.", 1)[1].split("### 5.", 1)[0]
        detail_part = output.split("### 5.", 1)[1].split("### 6.", 1)[0]
        recommendation = output.split("### 6.", 1)[1]

        self.assertIn("`⭐ top 1`", counts)
        self.assertIn("lower investment goes first, then the earlier label", counts)
        self.assertIn("takes the last top place", counts)
        for part in (kept_part, detail_part):
            self.assertNotIn("highest averaged judge Total", part)

        short_table = kept_part.index("| Label | Option (main pattern) | Investment | How it works | When to choose | Total |")
        self.assertLess(short_table, kept_part.index("summary `Scores by criterion`"))
        self.assertLess(short_table, kept_part.index("| Criterion"))

        self.assertIn("in label order", detail_part)
        self.assertNotIn("| Label |", detail_part)
        blocks = re.findall(r"```markdown\n(.*?)```", detail_part, flags=re.DOTALL)
        self.assertEqual(len(blocks), 2)
        full_block, short_block = blocks
        for block in blocks:
            self.assertRegex(block.splitlines()[0], r"^#### Option <label>.*\(<Total>/35\)$")
        self.assertIn("⭐ top", full_block.splitlines()[0])
        for field in ("Layers/files", "Skeleton"):
            self.assertIn(field, full_block)
            self.assertNotIn(field, short_block)

        self.assertIn("**Recommendation:** Option <X> (<Total>/35)", recommendation)

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
        self.assertNotIn("`ORDERS`", judge)
        self.assertIn("`CARDS`: one block per reading order", judge)
        self.assertIn("written in that block's order", judge)
        self.assertIn("Finish the table of a block before you read the next block", judge)
        self.assertIn("one column per card in that block's order", judge)
        self.assertIn("second order reverses the first; any later order is a new shuffle", judge)
        self.assertIn("without looking back at an earlier table", judge)
        skill = (ROOT_DIR / "skills" / "solution-brainstorm" / "SKILL.md").read_text(encoding="utf-8")
        diverge_step = skill.split("### Step 4.", 1)[1].split("### Step 5.", 1)[0]
        self.assertIn("so none sees another's output", diverge_step)
        judge_step = skill.split("### Step 5.", 1)[1].split("### Step 6.", 1)[0]
        self.assertIn("in a shuffled order", judge_step)
        for token in (
            "without its Knowledge line",
            "`nợ SRP`",
            "`Lý do scope rộng hơn`",
            "Breaks convention",
            "`CARDS`: one block per reading order",
            "every card written out in full in that order",
            "second order reverses the first; any later order is a new shuffle",
            "every ordering of every judge",
            "fewer tables than the blocks in its `CARDS`",
            "score each ordering that has no table yourself",
        ):
            self.assertIn(token, judge_step)
        self.assertNotIn("`ORDERS`", judge_step)
        self.assertNotIn("identical tables", judge_step)
        self.assertIn("or every judge fails", judge_step)
        self.assertIn("only when that line names web sources", generator)
        self.assertIn("not the writing", judge)
        for heading in ("## Option card", "## Judge rubric"):
            self.assertIn(heading, templates)
            self.assertIn(f"`{heading}`", generator + judge)

    def test_feature_workflow_done_needs_fresh_evidence(self):
        """Verify B3 and the final report point to one section that demands a fresh run before saying done."""
        skill = (ROOT_DIR / "skills" / "feature-workflow" / "SKILL.md").read_text(encoding="utf-8")
        body = skill.split("---", 2)[2]
        self.assertEqual(body.count("\n## Bằng chứng xong\n"), 1)
        section = body.split("\n## Bằng chứng xong\n", 1)[1].split("\n## ", 1)[0]
        for token in ("`Lệnh build và test`", "`không có lệnh kiểm`", "exit code", "`HEAD`", "should pass", "Lint", "reviewer"):
            with self.subTest(token=token):
                self.assertIn(token, section)

        b1 = body.split("## B1.", 1)[1].split("## B2.", 1)[0]
        self.assertIn("`Lệnh build và test`", b1)
        b3 = body.split("## B3.", 1)[1].split("## B4.", 1)[0]
        self.assertIn("`Lệnh build và test`", b3.split("\n\n1. ", 1)[0])
        report = body.split("## Báo cáo cuối", 1)[1]
        for part in (b3, report):
            self.assertIn("`Bằng chứng xong`", part)
        self.assertIn("kể cả khi B4 không sửa gì", report)

    def test_feature_workflow_evidence_runs_in_fresh_agent(self):
        """Verify the done check is delegated to a fresh fw-3-evidence and AC statuses gate B3, B4, and the final report."""

        def read(*parts):
            return (ROOT_DIR.joinpath(*parts)).read_text(encoding="utf-8")

        body = read("skills", "feature-workflow", "SKILL.md").split("---", 2)[2]
        section = body.split("\n## Bằng chứng xong\n", 1)[1].split("\n## ", 1)[0]
        self.assertNotIn("Chạy lại mọi lệnh", section)
        for token in (
            "`fw-3-evidence` mới",
            "`workflow:fw-3-evidence`",
            'không dùng `subagent_type: "fork"`',
            "`EVIDENCE_DIR` = `DIR/evidence/`",
            "Session chính không tự chạy lệnh kiểm, chỉ chép bảng agent trả",
            "`đạt`, `không đạt`, `chờ người ký`, `chưa kiểm: <lý do>`",
            "thì ghi `chưa kiểm: không có file bằng\n  chứng`",
            "`RUN_DIR` agent trả",
            "nằm trong `RUN_DIR` của lần chạy này (kiểm bằng `ls`)",
            "Có lệnh đỏ hoặc AC `không đạt`: không báo xong",
            "`chưa kiểm` và `chờ người ký` không chặn, chỉ đổi lời báo cuối",
            "chạy lại một lần bằng agent mới",
        ):
            with self.subTest(token=token):
                self.assertIn(token, section)

        agent = read("agents", "fw-3-evidence.md")
        inputs = agent.split("<inputs>", 1)[1].split("</inputs>", 1)[0]
        declared = set(re.findall(r"^- `([A-Z_]+)`:", inputs, flags=re.MULTILINE))
        self.assertEqual(declared, {"REQUIREMENTS", "BASE", "CHECKS", "EVIDENCE_DIR"})
        for name in declared:
            with self.subTest(input=name):
                self.assertIn(f"`{name}`", section)
        output = agent.split("<output>", 1)[1]
        self.assertIn("đường dẫn tuyệt đối tới\n   `RUN_DIR`", output)
        self.assertNotIn("`EVIDENCE_DIR/<HEAD>/`", agent)
        self.assertIn("`mkdir -p EVIDENCE_DIR`, rồi\n   `mkdir RUN_DIR` không `-p`", agent)
        self.assertIn("không tính bảng AC ở mục 3: bảng luôn đủ mọi AC", output)
        self.assertIn("chỉ chạy lại bằng agent mới khi working tree đã sạch", section)
        resume = body.split("\n## Làm tiếp\n", 1)[1].split("\n## ", 1)[0]
        self.assertIn("Lần chạy `Bằng chứng xong` bị ngắt", resume)
        self.assertIn("bỏ qua thư mục dở đó, không xoá, vì chỉ `RUN_DIR` của lần chạy mới được tính", resume)
        self.assertIn("bằng một `fw-3-evidence` mới", resume)
        for status in ("`đạt`", "`không đạt`", "`chờ người ký`", "`chưa kiểm: <lý do>`"):
            with self.subTest(status=status):
                self.assertIn(status, output)
                self.assertIn(status, section)

        b3 = body.split("## B3.", 1)[1].split("## B4.", 1)[0]
        self.assertIn("B3 không chạy\n   `Bằng chứng xong`", b3.split("\n7. ", 1)[1].split("**Ra:**", 1)[0])
        self.assertNotIn("Bằng chứng theo AC", b3)
        b4 = body.split("## B4.", 1)[1].split("\n## ", 1)[0]
        self.assertIn("Vòng này không chạy `Bằng chứng xong`", b4.split("\n3. ", 1)[1].split("\n4. ", 1)[0])
        report = body.split("## Báo cáo cuối", 1)[1]
        for token in ("bảng trạng thái AC", "Còn AC `chưa kiểm` hoặc `chờ người ký`", '"chờ kiểm N AC"', "lý do, không báo xong"):
            with self.subTest(token=token):
                self.assertIn(token, report)

    def test_feature_workflow_ac_status_stays_out_of_requirements(self):
        """Verify AC statuses go only to the running step's file and the final report, never to 01-requirements.md."""
        body = (ROOT_DIR / "skills" / "feature-workflow" / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[2]
        section = body.split("\n## Bằng chứng xong\n", 1)[1].split("\n## ", 1)[0]
        rule = (
            "Trạng thái AC chỉ ghi vào `## Bằng chứng cuối` và báo cáo cuối, không ghi vào `01-requirements.md`;\n"
            "  file đó không đổi sau B1."
        )
        self.assertIn(rule, section)
        sentences = re.split(r"(?<=[.:;])\s", body.replace("\n", " "))
        for sentence in sentences:
            if "01-requirements.md" in sentence and re.search(r"(?i)trạng thái AC", sentence):
                with self.subTest(sentence=sentence):
                    self.assertIn("không ghi vào `01-requirements.md`", sentence)

    def test_readme_names_evidence_agent_in_each_feature_workflow_part(self):
        """Verify README names fw-3-evidence in the overview, diagram, One Writer principle, agent table, and tree."""
        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
        overview = readme.split("\n## Overview\n", 1)[1].split("\n## ", 1)[0]
        feature = next(line for line in overview.splitlines() if line.startswith("1. **Feature Workflow**"))
        architecture = readme.split("\n### Four-Step Feature Workflow\n", 1)[1].split("\n### ", 1)[0]
        diagram = architecture.split("```text\n", 1)[1].split("```", 1)[0]
        principles = readme.split("\n### Architectural Principles\n", 1)[1].split("\n## ", 1)[0]
        writer = next(line for line in principles.splitlines() if line.startswith("4. **One Writer at a Time**"))
        agents = readme.split("\n### Feature Workflow Subagents\n", 1)[1].split("\n### ", 1)[0]
        tree = readme.split("\n## Project Structure\n", 1)[1].split("\n## ", 1)[0]
        parts = {
            "overview": (feature, "`fw-3-evidence`"),
            "diagram": (diagram, "[fw-3-evidence]"),
            "principle": (writer, "`fw-3-evidence` writes only evidence files into `.workflows/<slug>/evidence/`"),
            "agent table": (agents, "\n| `fw-3-evidence` |"),
            "tree": (tree, "fw-3-evidence.md"),
        }
        for name, (part, token) in parts.items():
            with self.subTest(part=name):
                self.assertIn(token, part)

    def test_feature_workflow_b1_gates_each_ac_on_a_check(self):
        """Verify B1 writes every AC as a full table row with a measurable check before the user confirms."""
        skill = (ROOT_DIR / "skills" / "feature-workflow" / "SKILL.md").read_text(encoding="utf-8")
        body = skill.split("---", 2)[2]
        b1 = body.split("## B1.", 1)[1].split("## B2.", 1)[0]
        self.assertNotIn("acceptance criteria kiểm được", b1)

        intake, out = b1.split("**Ra:**", 1)
        for word in ('"giống"', '"đúng"', '"đẹp"', '"không bị đè"', "viết lại"):
            with self.subTest(word=word):
                self.assertIn(word, intake)
        self.assertLess(intake.index("viết lại"), intake.index("trình bản tóm tắt yêu cầu"))

        header = "| # | AC | Phép kiểm | Môi trường | Bằng chứng | Người chấm |"
        self.assertIn("\n```markdown\n" + header + "\n|---|---|---|---|---|---|\n", out)
        self.assertEqual(out.count(header), 1)
        for token in ("`lệnh`", "`script so với mốc`", "`người kiểm theo kịch bản`", "`máy`", "`verify`", "`người ký`"):
            with self.subTest(token=token):
                self.assertIn(token, out)
        self.assertIn("còn ô trống thì chưa ghi `Trạng thái: xong` và chưa sang B2", out)

    def test_feature_workflow_keeps_state_in_files(self):
        """Verify the workflow resumes from its files and writes progress to them as it happens."""
        skill = (ROOT_DIR / "skills" / "feature-workflow" / "SKILL.md").read_text(encoding="utf-8")
        body = skill.split("---", 2)[2]
        init = body.split("## Khởi tạo", 1)[1].split("\n## ", 1)[0]
        self.assertIn("làm tiếp (theo mục\n  `Làm tiếp`)", init)
        self.assertIn("`STORY` trùng tên một thư mục trong `.workflows/`", init)
        self.assertNotIn("Không làm tiếp giữa chừng", body)

        self.assertEqual(body.count("\n## Làm tiếp\n"), 1)
        resume = body.split("\n## Làm tiếp\n", 1)[1].split("\n## ", 1)[0]
        for token in ("`Trạng thái: xong`", "git merge-base --is-ancestor", "nhánh ghi trong file đó", "stash hoặc bỏ, không commit", "chạy vòng 2 của B4", "`Báo cáo cuối`"):
            with self.subTest(token=token):
                self.assertIn(token, resume)
        resume_b3 = resume.split("Đang ở B3:", 1)[1].split("Đang ở B4:", 1)[0]
        for token in ("`Bảng bước`", "`Việc phát sinh`", "git log --oneline BASE..HEAD", "`hỏng`", "bước 7 của B3"):
            with self.subTest(token=token):
                self.assertIn(token, resume_b3)
        resume_b4 = resume.split("Đang ở B4:", 1)[1]
        for token in ("`04-review-<n>.md`", "git log --oneline BASE..HEAD", "không sửa một phát hiện hai lần"):
            with self.subTest(token=token):
                self.assertIn(token, resume_b4)
        self.assertIn("`hỏng`", resume_b4)
        self.assertLess(resume.index("stash hoặc bỏ"), resume.index("git merge-base --is-ancestor"))
        self.assertIn("bước 2 của mục `Làm tiếp`", init)

        b3 = body.split("## B3.", 1)[1].split("## B4.", 1)[0]
        for token in ("## Bảng bước", "| # | Mục tiêu | File dự kiến | Lô | Trạng thái |", "## Việc phát sinh", "`xong <commit>`", "`hỏng <lý do>`"):
            with self.subTest(token=token):
                self.assertIn(token, b3)
        self.assertIn("`Việc phát sinh`", b3.split("**Ra:**", 1)[1])
        b4 = body.split("## B4.", 1)[1].split("\n## ", 1)[0]
        self.assertIn("ngay khi reviewer trả về", b4)
        self.assertIn("ghi ngay vào `04-review-<n>.md`", b4)
        self.assertIn("`Việc phát sinh`", body.split("## Báo cáo cuối", 1)[1])

    def test_feature_workflow_codes_in_fresh_subagents(self):
        """Verify each code step runs in a fresh, sequential implementer that cannot delegate or touch workflow files."""

        def read(*parts):
            return (ROOT_DIR.joinpath(*parts)).read_text(encoding="utf-8")

        body = read("skills", "feature-workflow", "SKILL.md").split("---", 2)[2]
        rules = body.split("## Luật chuyển bước", 1)[1].split("\n## ", 1)[0]
        self.assertIn("`Explore`", rules)
        self.assertIn("dòng tóm tắt và các dòng\n  lỗi", rules)

        b3 = body.split("## B3.", 1)[1].split("## B4.", 1)[0]
        spawn = b3.split("\n5. ", 1)[1].split("\n6. ", 1)[0]
        for token in ("`fw-3-implement`", "Mỗi lô một agent", "Lô sau chỉ bắt đầu khi lô trước trả về", "không chạy hai\n   agent cùng lúc", '`subagent_type: "fork"`'):
            with self.subTest(token=token):
                self.assertIn(token, spawn)
        implementer = read("agents", "fw-3-implement.md")
        inputs = implementer.split("<inputs>", 1)[1].split("</inputs>", 1)[0]
        passed = set(re.findall(r"^   - `([A-Z_]+)`:", spawn, flags=re.MULTILINE))
        declared = set(re.findall(r"^- `([A-Z_]+)`:", inputs, flags=re.MULTILINE))
        self.assertEqual(passed, declared)
        self.assertIn("`hỏng <lý do>`", b3.split("\n6. ", 1)[1])
        final_check = b3.split("\n7. ", 1)[1].split("**Ra:**", 1)[0]
        for token in ("git diff BASE..HEAD", "nới lỏng", "B3 không chạy\n   `Bằng chứng xong`", "sau 2 lần vẫn chưa ổn", "Commit trộn", "Không tự\n   sửa code"):
            with self.subTest(token=token):
                self.assertIn(token, final_check)
        b4 = body.split("## B4.", 1)[1].split("\n## ", 1)[0]
        self.assertIn("`fw-3-implement` mới", b4)
        self.assertIn("kiểm diff\n   của các commit sửa", b4)
        self.assertNotIn("như bước 7 của B3", b4)
        self.assertIn("`hỏng <lý do>`", b4)
        self.assertIn("không thêm dòng vào `Bảng bước`", b4)
        self.assertIn("`CHECKS`: các lệnh trong `Lệnh build và test`, hoặc `không có`", spawn)

        frontmatter = vi.parse_frontmatter(implementer)
        self.assertEqual(frontmatter["tools"], ["Read", "Edit", "Write", "Bash", "Grep", "Glob"])
        constraints = implementer.split("<constraints>", 1)[1].split("</constraints>", 1)[0]
        for token in ("`.workflows/`", "Không spawn\nsubagent", "push"):
            with self.subTest(token=token):
                self.assertIn(token, constraints)
        steps = implementer.split("<steps>", 1)[1].split("</steps>", 1)[0]
        for token in ("Sửa 2 lần vẫn đỏ", "`git add -- <file>`", "không `--no-verify`", "nới lỏng", "`không có lệnh kiểm`"):
            with self.subTest(token=token):
                self.assertIn(token, steps)
        output = implementer.split("<output>", 1)[1]
        for token in ("`Kết quả: xong` khi mọi mục `xong`", "exit code", "`Việc phát sinh`"):
            with self.subTest(token=token):
                self.assertIn(token, output)

    def test_feature_workflow_b3_splits_rows_into_batches(self):
        """Verify B3 gives all step rows to one implementer by default, splits into at most 3 sequential batches, and records each row as returned."""
        body = (ROOT_DIR / "skills" / "feature-workflow" / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[2]
        self.assertNotIn("Mỗi dòng một agent", body)
        b3 = body.split("## B3.", 1)[1].split("## B4.", 1)[0]
        table = b3.split("\n4. ", 1)[1].split("\n5. ", 1)[0]
        for token in ("Số lô: <n> - <lý do>", "| # | Mục tiêu | File dự kiến | Lô | Trạng thái |", "| 1 | <một thay đổi, một commit> | <file> | 1 | chưa |", "dòng `Số lô`"):
            with self.subTest(token=token):
                self.assertIn(token, table)
        spawn = b3.split("\n5. ", 1)[1].split("\n6. ", 1)[0]
        for token in ("Mặc định\n   1 lô cho mọi dòng", "một agent vừa nhanh vừa chính xác", "Chia 2-3 lô khi việc nhiều", "các\n   phần không chung file", "một agent không đọc hết context cho mọi dòng", "Tối đa 3 lô", "Mỗi lô một agent", "Lô sau chỉ bắt đầu khi lô trước trả về", "`STEP`: các dòng `chưa` của lô", "commit dòng đó"):
            with self.subTest(token=token):
                self.assertIn(token, spawn)
        record = b3.split("\n6. ", 1)[1].split("\n7. ", 1)[0]
        for token in ("theo đúng dòng agent trả", "`<#> xong <hash>` ghi\n   `xong <commit>`", "`<#> hỏng <lý do>` ghi `hỏng <lý do>`", "`<#> chưa` giữ `chưa`", "Có dòng `hỏng` hoặc agent trả `lỗi`: dừng, không chạy lô sau"):
            with self.subTest(token=token):
                self.assertIn(token, record)
        final_check = b3.split("\n7. ", 1)[1].split("**Ra:**", 1)[0]
        self.assertIn("truyền như bước 5 với `STEP` là các dòng mới", final_check)
        for token in ("ghi vào một lô mới (số lô kế tiếp)", "cập nhật `Số lô`", "lô sửa này không tính vào giới\n   hạn 3 lô"):
            with self.subTest(token=token):
                self.assertIn(token, final_check)
        self.assertLess(final_check.index("lô mới"), final_check.index("`STEP` là các dòng mới"))
        self.assertIn("Ghi `Trạng thái: xong` khi mọi dòng `xong`, diff đã kiểm và `CHECKS` của\n   agent code xanh", final_check)
        out = b3.split("**Ra:**", 1)[1]
        self.assertIn("dòng `Số lô`", out)
        self.assertNotIn("bằng chứng", out)

    def test_feature_workflow_b3_counts_diff_fix_batches_from_file(self):
        """Verify B3 marks diff-fix batches in the batch line so resume can count them against the 2-fix limit."""
        body = (ROOT_DIR / "skills" / "feature-workflow" / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[2]
        b3 = body.split("## B3.", 1)[1].split("## B4.", 1)[0]
        final_check = b3.split("\n7. ", 1)[1].split("**Ra:**", 1)[0]
        for token in ("Ghi lô đó trong `Số lô` là lô sửa diff kèm lần sửa", "`lô 2: sửa diff lần 1`", "sau 2 lần vẫn chưa ổn (đếm các lô sửa diff trong `Số lô`)"):
            with self.subTest(token=token):
                self.assertIn(token, final_check)
        resume = body.split("\n## Làm tiếp\n", 1)[1].split("\n## ", 1)[0]
        resume_b3 = resume.split("Đang ở B3:", 1)[1].split("Đang ở B4:", 1)[0]
        self.assertIn("các lô sửa diff đã ghi trong `Số lô` được tính vào giới hạn 2 lần sửa của bước đó", resume_b3)

    def test_implementer_commits_each_item_of_a_list(self):
        """Verify the implementer takes a numbered item list and runs code, checks, and one commit per item in order."""
        implementer = (ROOT_DIR / "agents" / "fw-3-implement.md").read_text(encoding="utf-8")
        role = implementer.split("<role>", 1)[1].split("</role>", 1)[0]
        self.assertIn("danh sách hạng mục", role)
        self.assertIn("mỗi mục một commit", role)
        inputs = implementer.split("<inputs>", 1)[1].split("</inputs>", 1)[0]
        for token in ("danh sách hạng mục có số, mỗi mục một commit", "dòng `Bảng bước` của một lô B3", "phát hiện của một vòng B4", "AC `không đạt` của `Bằng chứng xong`", "Một việc là danh\n  sách một mục"):
            with self.subTest(token=token):
                self.assertIn(token, inputs)
        self.assertNotIn("Minor", implementer)
        steps = implementer.split("<steps>", 1)[1].split("</steps>", 1)[0]
        per_item = steps.split("\n3. ", 1)[1]
        self.assertIn("mục trước commit xong mới sang mục sau", per_item)
        checks = per_item.split("\n   3. ", 1)[1].split("\n   4. ", 1)[0]
        self.assertIn("Chạy mọi lệnh trong `CHECKS`", checks)
        commit = per_item.split("\n   4. ", 1)[1].split("\n   5. ", 1)[0]
        for token in ("một commit cho mục đó", "`git add -- <file>`", "Không stage một phần file", "`git status --porcelain` phải sạch", "`<#> xong <hash>`"):
            with self.subTest(token=token):
                self.assertIn(token, commit)
        self.assertNotIn("bắc cầu", implementer)
        self.assertNotIn("cùng file chung một commit", implementer)
        failed = per_item.split("\n   5. ", 1)[1]
        for token in ("Sửa 2 lần vẫn đỏ", "không commit", "khôi phục file của mục đó", "`<#> hỏng <lý do>`", "dòng `LOẠI`: `LOẠI: bảng bước`", "thì dừng, các mục sau ghi `<#> chưa`", "`LOẠI: phát hiện` hay `LOẠI: bằng chứng` thì làm tiếp mục sau"):
            with self.subTest(token=token):
                self.assertIn(token, failed)
        self.assertNotIn("`STEP`\n      là dòng `Bảng bước`", failed)
        for kind in ("`LOẠI: bảng bước`", "`LOẠI: phát hiện`", "`LOẠI: bằng chứng`"):
            with self.subTest(kind=kind):
                self.assertIn(kind, inputs)
        self.assertIn("Thiếu dòng `LOẠI` thì coi là thiếu input", inputs)
        self.assertIn("Thiếu input nào thì báo thiếu gì và dừng", inputs)
        skill = (ROOT_DIR / "skills" / "feature-workflow" / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[2]
        b3_spawn = skill.split("## B3.", 1)[1].split("\n5. ", 1)[1].split("\n6. ", 1)[0]
        self.assertIn("dòng đầu\n     `LOẠI: bảng bước`", b3_spawn)
        b4_fix = skill.split("## B4.", 1)[1].split("\n3. ", 1)[1].split("\n4. ", 1)[0]
        self.assertIn("dòng đầu `LOẠI: phát hiện`", b4_fix)
        evidence = skill.split("\n## Bằng chứng xong\n", 1)[1].split("\n## ", 1)[0]
        self.assertIn("dòng đầu `LOẠI: bằng chứng`", evidence)
        description = vi.parse_frontmatter(implementer)["description"]
        self.assertIn("one commit per item", description)
        self.assertNotIn("Minor", description)
        output = implementer.split("<output>", 1)[1]
        for token in ("một dòng mỗi mục", "`<#> xong <hash>`", "`<#> hỏng <lý do>`", "`<#> chưa`"):
            with self.subTest(token=token):
                self.assertIn(token, output)

    def test_implementer_reuses_commit_of_an_earlier_item(self):
        """Verify an item already fixed by an earlier item's commit reports that commit instead of an extra one."""
        implementer = (ROOT_DIR / "agents" / "fw-3-implement.md").read_text(encoding="utf-8")
        per_item = implementer.split("<steps>", 1)[1].split("</steps>", 1)[0].split("\n3. ", 1)[1]
        commit = per_item.split("\n   4. ", 1)[1].split("\n   5. ", 1)[0]
        for token in ("Commit của một mục trước đã sửa luôn mục này", "không còn gì để sửa, `CHECKS` xanh", "không commit\n      thêm", "`<#> xong <hash của commit đó>`"):
            with self.subTest(token=token):
                self.assertIn(token, commit)

    def test_implementer_evidence_items_do_not_block_each_other(self):
        """Verify an evidence item is green when its own command passes, so two red commands do not deadlock."""
        implementer = (ROOT_DIR / "agents" / "fw-3-implement.md").read_text(encoding="utf-8")
        steps = implementer.split("<steps>", 1)[1].split("</steps>", 1)[0]
        baseline = steps.split("\n2. ", 1)[1].split("\n3. ", 1)[0]
        self.assertIn("`LOẠI: bằng chứng`: chạy mọi lệnh trong `CHECKS` một lần trước khi sửa", baseline)
        run = steps.split("\n   3. ", 1)[1].split("\n   4. ", 1)[0]
        for token in ("lệnh của chính mục đó\n      xanh", "không lệnh nào xanh ở mốc nay đỏ", "Lệnh đã đỏ ở mốc và thuộc mục sau thì không chặn mục này"):
            with self.subTest(token=token):
                self.assertIn(token, run)
        commit = steps.split("\n   4. ", 1)[1].split("\n   5. ", 1)[0]
        self.assertIn("mục sau cũng không được làm nó đỏ\n      lại", commit)

    def test_evidence_agent_is_blind_and_writes_only_evidence(self):
        """Verify the evidence agent's tools, inputs, AC statuses, and that it writes only to its RUN_DIR."""
        agent = (ROOT_DIR / "agents" / "fw-3-evidence.md").read_text(encoding="utf-8")
        frontmatter = vi.parse_frontmatter(agent)
        self.assertEqual(frontmatter["name"], "fw-3-evidence")
        self.assertEqual(sorted(frontmatter["tools"]), ["Bash", "Glob", "Grep", "Read", "Write"])
        self.assertNotIn("Edit", frontmatter["tools"])
        self.assertEqual(frontmatter["model"], "inherit")
        self.assertNotIn("-review", frontmatter["name"])

        inputs = agent.split("<inputs>", 1)[1].split("</inputs>", 1)[0]
        for token in ("`REQUIREMENTS`", "`BASE`", "`CHECKS`", "`EVIDENCE_DIR`", "`DIR/evidence/`", "báo thiếu gì và dừng"):
            with self.subTest(token=token):
                self.assertIn(token, inputs)

        steps = agent.split("<steps>", 1)[1].split("</steps>", 1)[0]
        for token in ("Không đọc file nào khác trong `.workflows/`", "`git rev-parse --short HEAD`", "`RUN_DIR` = `EVIDENCE_DIR/<HEAD>-<timestamp>/`", "`mkdir RUN_DIR` không `-p`", "Mọi file của lần chạy này nằm\n   trong `RUN_DIR`", "exit code", "`không có lệnh kiểm`", "không chép kết quả cũ", "`chưa kiểm: <lý do>`", "`chờ người ký`", "phải\n   dẫn file trong `RUN_DIR`"):
            with self.subTest(token=token):
                self.assertIn(token, steps)

        constraints = agent.split("<constraints>", 1)[1].split("</constraints>", 1)[0]
        banned = "Không đọc `02-solution.md` hay `03-implementation.md`."
        self.assertIn(banned, constraints)
        for hidden in ("02-solution.md", "03-implementation.md"):
            with self.subTest(hidden=hidden):
                self.assertEqual(agent.count(hidden), 1)
        for token in ("Chỉ tạo file bằng chứng trong `RUN_DIR`", "Không sửa code", "Không commit", "không spawn subagent"):
            with self.subTest(token=token):
                self.assertIn(token, constraints)

        output = agent.split("<output>", 1)[1]
        self.assertIn("| # | Trạng thái | File bằng chứng | Ghi chú |", output)
        for status in ("`đạt`", "`không đạt`", "`chờ người ký`", "`chưa kiểm: <lý do>`"):
            with self.subTest(status=status):
                self.assertIn(status, output)

    def test_feature_workflow_evidence_runs_once_before_final_report(self):
        """Verify the evidence check runs once after B4, records into the last review file, and owns its fix-and-rerun loop."""
        body = (ROOT_DIR / "skills" / "feature-workflow" / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[2]
        section = body.split("\n## Bằng chứng xong\n", 1)[1].split("\n## ", 1)[0]
        self.assertNotIn("Trước khi\nghi `Trạng thái: xong` của `03-implementation.md`", section)
        self.assertNotIn("03-implementation.md", section)
        for token in (
            "Mục này\nchỉ chạy ở cuối, sau B4 và trước `Báo cáo cuối`",
            "một lần, cộng các lần chạy\nlại sau mỗi lần sửa của chính mục này",
            "Agent sửa trả có mục `<#> hỏng` thì vẫn chạy lại để có kết quả mới; lần sửa đó vẫn tính vào giới hạn",
            "B3 và B4 không chạy nó",
            "Ghi lần chạy vào mục `## Bằng chứng cuối` của `04-review-<n>.md` mới nhất",
            "`RUN_DIR` agent trả, và bảng trạng thái AC agent trả",
            "Quay lại code như B3: spawn một `fw-3-implement` mới",
            "truyền như bước 5 của B3 với `STEP` là các lệnh đỏ và AC `không đạt`",
            "vào mục `## Bằng chứng cuối`, rồi chạy lại mục này bằng một `fw-3-evidence` mới",
            "Sau 2 lần sửa vẫn đỏ thì dừng và báo người dùng",
        ):
            with self.subTest(token=token):
                self.assertIn(token, section)
        self.assertNotIn("chạy đúng một lần", section)
        outside = body.replace(section, "")
        self.assertNotIn("Sau 2 lần sửa vẫn đỏ", outside)
        report = body.split("## Báo cáo cuối", 1)[1]
        self.assertIn("Chạy theo mục `Bằng chứng xong`, kể cả khi B4 không sửa gì, rồi báo người dùng", report)
        for token in ("lượt Minor cuối", "như bước 7 của B3", "mở agent mới"):
            with self.subTest(token=token):
                self.assertNotIn(token, report)
        self.assertIn("mục `## Minor`", report)

    def test_feature_workflow_evidence_fix_checks_diff_before_rerun(self):
        """Verify each evidence fix records HEAD first and checks the fix diff like B3 step 7 before a fresh evidence run."""
        body = (ROOT_DIR / "skills" / "feature-workflow" / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[2]
        section = body.split("\n## Bằng chứng xong\n", 1)[1].split("\n## ", 1)[0]
        fix = next(b for b in section.split("\n- ") if b.startswith("Có lệnh đỏ hoặc AC `không đạt`"))
        for token in ("ghi `HEAD` lúc đó vào `## Bằng chứng cuối` làm mốc", "`git diff <mốc>..HEAD`", "kiểm như bước 7 của B3", "không test hay\n  assertion nào bị xoá, skip hay nới lỏng", "không file nào nằm ngoài yêu cầu", "Diff có vấn đề: ghi vào\n  `## Bằng chứng cuối`, không chạy lại, dừng và báo người dùng, không báo xong"):
            with self.subTest(token=token):
                self.assertIn(token, fix)
        self.assertLess(fix.index("làm mốc"), fix.index("Ghi lần sửa"))
        self.assertLess(fix.index("`git diff <mốc>..HEAD`"), fix.index("Diff có vấn đề"))

    def test_feature_workflow_evidence_fixes_get_one_review(self):
        """Verify commits of the evidence fix loop get one scoped fw-4-review, which stops on Blocker or Major without a new fix round."""
        body = (ROOT_DIR / "skills" / "feature-workflow" / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[2]
        section = body.split("\n## Bằng chứng xong\n", 1)[1].split("\n## ", 1)[0]
        review = next(b for b in section.split("\n- ") if b.startswith("Review lần sửa"))
        for token in ("spawn một `fw-4-review` mới", "`BASE` là mốc của lần sửa đầu tiên", "`### Review lần sửa` trong `## Bằng chứng cuối`", "Không sửa tiếp các phát hiện này", "còn Blocker hoặc Major thì không báo xong", "Không có commit sửa nào thì không spawn"):
            with self.subTest(token=token):
                self.assertIn(token, review)
        resume = body.split("\n## Làm tiếp", 1)[1].split("\n## ", 1)[0]
        self.assertIn("chưa có\n     `### Review lần sửa` thì chạy review đó", resume)
        report = body.split("\n## Báo cáo cuối\n", 1)[1]
        for token in ("các commit sửa của `Bằng chứng xong`", "kết quả `### Review lần sửa`"):
            with self.subTest(token=token):
                self.assertIn(token, report)
        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("one fresh `fw-4-review` reviews just those commits", readme)

    def test_feature_workflow_evidence_fixer_error_without_items_stops(self):
        """Verify an evidence fixer that returns an error with no item lines stops the loop like B3 step 6."""
        body = (ROOT_DIR / "skills" / "feature-workflow" / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[2]
        section = body.split("\n## Bằng chứng xong\n", 1)[1].split("\n## ", 1)[0]
        bullet = next(b for b in section.split("\n- ") if b.startswith("`fw-3-implement` của vòng sửa"))
        self.assertIn("trả `lỗi` mà không có dòng `<#>` nào: dừng và báo người dùng như bước 6\n  của B3", bullet)

    def test_feature_workflow_b4_fixes_each_round_with_one_agent(self):
        """Verify each B4 round hands every Blocker, Major, and small Minor to one implementer and has no final Minor pass."""
        skill = (ROOT_DIR / "skills" / "feature-workflow" / "SKILL.md").read_text(encoding="utf-8")
        body = skill.split("---", 2)[2]
        b4 = body.split("## B4.", 1)[1].split("\n## ", 1)[0]
        self.assertNotIn("Sửa Minor khi sửa nhỏ", body)
        self.assertNotIn("\n5. ", b4)
        self.assertNotIn("chờ lượt cuối", b4)
        self.assertNotIn("lượt Minor cuối", b4)
        fix_step = b4.split("\n3. ", 1)[1].split("\n4. ", 1)[0]
        for token in ("Mỗi vòng spawn đúng một `fw-3-implement` mới cho mọi Blocker, Major và Minor nhỏ", "không mở\n   rộng phạm vi", "truyền như bước 5 của B3", "`STEP` là danh sách các phát hiện đó", "file:line, vấn đề, gợi ý sửa", "`không sửa: <lý do>`", "mục `## Minor` của `04-review-<n>.md`", "mỗi phát hiện bằng một commit mới", "theo đúng dòng agent trả", "`<#> xong <hash>` ghi `xong <commit>`", "`<#> hỏng <lý do>` ghi `hỏng <lý do>`", "Blocker hoặc Major\n   `hỏng`: dừng và hỏi người dùng làm lại hay dừng", "Minor `hỏng` chỉ ghi, không dừng", "kiểm diff\n   của các commit sửa", "nới lỏng"):
            with self.subTest(token=token):
                self.assertIn(token, fix_step)
        self.assertIn("chỉ khi danh sách đó không rỗng (rỗng thì không spawn)", fix_step)
        round_two = b4.split("\n4. ", 1)[1].split("**Ra:**", 1)[0]
        self.assertNotIn("chép các Minor", round_two)
        out = b4.split("**Ra:**", 1)[1]
        for token in ("\n   ## Minor\n", "| # | file:line | Vấn đề | Trạng thái |", "Trạng thái Minor: `xong <commit>`, `hỏng <lý do>`, `không sửa: <lý do>`."):
            with self.subTest(token=token):
                self.assertIn(token, out)

    def test_feature_workflow_b4_keeps_reviewer_numbers(self):
        """Verify B4 passes findings with the reviewer's numbers and the Minor table keeps those numbers instead of renumbering from 1."""
        body = (ROOT_DIR / "skills" / "feature-workflow" / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[2]
        b4 = body.split("## B4.", 1)[1].split("\n## ", 1)[0]
        fix_step = b4.split("\n3. ", 1)[1].split("\n4. ", 1)[0]
        self.assertIn("kèm số `#` reviewer đặt", fix_step)
        self.assertIn("không đánh số lại", fix_step)
        out = b4.split("**Ra:**", 1)[1]
        self.assertIn("cột `#` giữ đúng số\n`#` reviewer đặt (cũng là số trong `STEP`)", out)
        self.assertIn("| <# của reviewer> | <file:line> | <vấn đề> | xong <commit> |", out)
        self.assertNotIn("| 1 | <file:line>", out)

    def test_feature_workflow_resume_matches_batches_and_single_evidence(self):
        """Verify resume records commits before handing leftover rows or findings to a new implementer, and resumes the final evidence loop."""
        skill = (ROOT_DIR / "skills" / "feature-workflow" / "SKILL.md").read_text(encoding="utf-8")
        body = skill.split("---", 2)[2]
        for gone in ("Mỗi dòng một agent", "mỗi dòng một agent", "lượt Minor cuối", "Lượt Minor cuối", "chờ lượt cuối"):
            with self.subTest(gone=gone):
                self.assertNotIn(gone, body)
        resume = body.split("\n## Làm tiếp\n", 1)[1].split("\n## ", 1)[0]
        resume_b3 = resume.split("Đang ở B3:", 1)[1].split("Đang ở B4:", 1)[0]
        for token in ("`Số lô`", "ghi `xong <commit>` vào dòng\n   tương ứng trước", "Các dòng `chưa` còn lại giao cho\n   `fw-3-implement` mới theo bước 5 của B3", "giữ lô đã ghi"):
            with self.subTest(token=token):
                self.assertIn(token, resume_b3)
        self.assertLess(resume_b3.index("tương ứng trước"), resume_b3.index("Các dòng `chưa` còn lại"))
        resume_b4 = resume.split("Đang ở B4:", 1)[1].split("\n6. ", 1)[0]
        for token in ("ghi `xong <commit>` vào phát hiện tương ứng trước", "Blocker hoặc Major ghi `hỏng` thì hỏi người dùng", "Minor `hỏng` vào \"Minor đã bỏ qua\"", "không hỏi", "Các phát hiện còn lại chưa ghi gì", "như bước 3 của B4", "giao cho một `fw-3-implement` mới"):
            with self.subTest(token=token):
                self.assertIn(token, resume_b4)
        self.assertLess(resume_b4.index("tương ứng trước"), resume_b4.index("Các phát hiện còn lại"))
        final = resume.split("\n6. ", 1)[1].split("\n7. ", 1)[0]
        for token in ("chạy `Bằng chứng xong` rồi `Báo cáo cuối`", "`## Bằng chứng cuối`", "ghi vào lần sửa tương ứng trước", "chạy lại bằng một `fw-3-evidence` mới", "giới hạn lần\n   sửa của `Bằng chứng xong`"):
            with self.subTest(token=token):
                self.assertIn(token, final)

    def test_feature_workflow_resume_covers_each_evidence_loop_state(self):
        """Verify resuming the final evidence loop handles an interrupted fixer, a failed run with no fix yet, and a green run without a report."""
        body = (ROOT_DIR / "skills" / "feature-workflow" / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[2]
        resume = body.split("\n## Làm tiếp\n", 1)[1].split("\n## ", 1)[0]
        final = resume.split("\n6. ", 1)[1].split("\n7. ", 1)[0]
        record = final.index("ghi vào lần sửa tương ứng trước")
        bullets = final.split("\n   - ")[1:]
        self.assertEqual(len(bullets), 4)
        self.assertLess(record, final.index("\n   - "))
        interrupted = next(b for b in bullets if b.startswith("Lần sửa bị ngắt"))
        for token in ("chưa `xong` hay `hỏng`", "giao cho một `fw-3-implement` mới", "vẫn là lần sửa đó", "rồi chạy lại bằng một `fw-3-evidence` mới"):
            with self.subTest(token=token):
                self.assertIn(token, interrupted)
        no_fix = next(b for b in bullets if "mà chưa có lần sửa" in b)
        for token in ("lệnh đỏ hoặc AC `không đạt`", "sửa như `Bằng chứng xong`", "nếu chưa hết giới hạn", "dừng và báo người dùng"):
            with self.subTest(token=token):
                self.assertIn(token, no_fix)
        green = next(b for b in bullets if "không có lệnh đỏ hay AC `không đạt`" in b)
        self.assertIn("sang `Báo cáo cuối`, không chạy lại", green)
        self.assertNotIn("fw-3-evidence", green)

    def test_readme_describes_batched_implementers_and_one_final_evidence_run(self):
        """Verify README describes B3 batches, one fixer per B4 round, and a single final evidence run."""
        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("fixed together by one `fw-3-implement` after the last round", readme)
        overview = readme.split("\n## Overview\n", 1)[1].split("\n## ", 1)[0]
        self.assertIn("a fresh implementer subagent per batch of steps", overview)
        feature = next(line for line in overview.splitlines() if line.startswith("1. **Feature Workflow**"))
        for token in ("the whole step table goes to one fresh `fw-3-implement` subagent", "at most 3 batches that run one after another, never in parallel", "B3 does not run the evidence check", "hands every Blocker, Major, and small Minor finding of that round to one fresh `fw-3-implement`", "there is no separate Minor pass", "Once, after step 4 and before the final report, a fresh `fw-3-evidence`", "at most 2 times"):
            with self.subTest(token=token):
                self.assertIn(token, feature)
        self.assertNotIn("Before it marks step 3 done", feature)
        diagram = readme.split("\n### Four-Step Feature Workflow\n", 1)[1].split("```text\n", 1)[1].split("```", 1)[0]
        for token in ("one per batch", "max 3 batches", "per round", "once"):
            with self.subTest(token=token):
                self.assertIn(token, diagram)
        self.assertNotIn("one per step", diagram)
        writer = next(line for line in readme.splitlines() if line.startswith("4. **One Writer at a Time**"))
        self.assertIn("one fresh agent per batch of steps, per review round, or per evidence fix", writer)
        agents = readme.split("\n### Feature Workflow Subagents\n", 1)[1].split("\n### ", 1)[0]
        self.assertIn("one status line per item", agents)
        self.assertIn("Once after B4, before the final report", agents)

    def test_readme_names_implementer_evidence_fixes_and_item_numbers(self):
        """Verify README says fw-3-implement also fixes final evidence checks, takes a LOẠI line, and keeps reviewer numbers."""
        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
        tree = readme.split("\n## Project Structure\n", 1)[1].split("\n## ", 1)[0]
        line = next(l for l in tree.splitlines() if "fw-3-implement.md" in l)
        self.assertIn("B3/B4 and final evidence fixes", line)
        agents = readme.split("\n### Feature Workflow Subagents\n", 1)[1].split("\n### ", 1)[0]
        row = next(l for l in agents.splitlines() if l.startswith("| `fw-3-implement` |"))
        for token in ("`STEP` starts with a `LOẠI` line", "B4 findings keep the reviewer's `#` numbers"):
            with self.subTest(token=token):
                self.assertIn(token, row)

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
        for key in (
            "Candidates", "Kept", "Min schools", "Votes", "Few voices", "Shortfall", "Chat summary", "File name",
            "Principle lines", "Main file", "Source material", "Excerpt", "Metaphor", "This week",
        ):
            self.assertRegex(counts, rf"(?m)^- {key}: ", key)
        for key in ("Lesson lines", "Appendix", "Examples", "Self-check questions"):
            self.assertNotRegex(counts, rf"(?m)^- {key}: ", key)
        file_name = re.search(r"(?m)^- File name: (.*)$", counts).group(1)
        self.assertIn("-sources", file_name)
        self.assertNotIn("-answers", file_name)
        kept = int(re.search(r"(?m)^- Kept: (\d+)$", counts).group(1))
        high = int(re.search(r"(?m)^- Candidates: \d+-(\d+)$", counts).group(1))
        self.assertLess(kept, high)
        self.assertNotRegex(counts, r"\d+ of 6", "vote thresholds must scale with N, not a fixed 6")
        self.assertIn("## Self-check", templates)
        report = re.split(r"(?m)^## Self-check$", templates.split("## Report", 1)[1], maxsplit=1)[0]
        for heading in ("### Main file", "### Source material rules", "### Sources file"):
            self.assertIn(heading, report)
        self.assertNotIn("### Answers file", report)
        self.assertIn("## Reading path", report)
        main_template = report.split("### Main file", 1)[1].split("### Source material rules", 1)[0]
        principle = re.split(r"(?m)^## Principle <n>\..*$", main_template, maxsplit=1)[1]
        principle = re.split(r"(?m)^## ", principle, maxsplit=1)[0]
        self.assertEqual(
            re.findall(r"(?m)^### (.+)$", principle),
            ["Statement", "Source material", "Mechanism", "Thresholds and steps", "When not to use", "Pitfalls", "Apply"],
        )
        for part in ("### Examples", "### Self-check", "## Teach-back", "## Appendix", "Confused with"):
            self.assertNotIn(part, report)
        for old_table in ("## 2. Myths", "## 4. Common mistakes"):
            self.assertNotIn(old_table, report, "myths and mistakes belong in each principle's Pitfalls")

        header = next(line for line in domains.splitlines() if line.startswith("| Domain type"))
        for column in ("Signals", "Student evidence", "Proxy when none", "Freshness limit", "Apply form", "Source material form"):
            self.assertIn(column, header)
        columns = [cell.strip() for cell in header.strip("|").split("|")]
        form_index = columns.index("Source material form")
        rows = [line for line in domains.splitlines() if line.startswith("| ") and line != header]
        self.assertEqual(len(rows), 10)
        for row in rows:
            cells = [cell.strip() for cell in row.strip("|").split("|")]
            self.assertEqual(len(cells), len(columns), row)
            self.assertTrue(cells[form_index], row)
        self.assertIn("| Fallback |", domains)

        for heading in ("## Evidence labels", "## Red flags", "## Mentor rules", "## Principle filters", "## Principle labels"):
            self.assertIn(heading, filters)
        self.assertIn("- **Inference**:", filters)

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

    def test_every_skill_frontmatter_contract(self):
        """Verify every skill's frontmatter name, description, length, and user-only flag."""
        for path in sorted((ROOT_DIR / "skills").glob("*/SKILL.md")):
            name = path.parent.name
            with self.subTest(skill=name):
                text = path.read_text(encoding="utf-8")
                frontmatter = vi.parse_frontmatter(text)
                self.assertEqual(frontmatter["name"], name)
                self.assertLessEqual(len(frontmatter["description"]), 1024)
                self.assertLess(len(text.splitlines()), 500)
                if name in self.USER_ONLY_SKILLS:
                    self.assertEqual(frontmatter.get("disable-model-invocation"), "true")
                else:
                    self.assertNotIn("disable-model-invocation", frontmatter)

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

    def test_agent_authoring_done_needs_fresh_run(self):
        """Verify rule 4 asks for a fresh run, and a subagent's report never replaces reading its diff."""
        base = ROOT_DIR / "skills" / "agent-authoring"
        skill = (base / "SKILL.md").read_text(encoding="utf-8")
        rule4 = skill.split("4. **", 1)[1].split("\n5. ", 1)[0]
        for token in ("after your last change", "exit code", "lint", "should pass"):
            with self.subTest(token=token):
                self.assertIn(token, rule4)

        rules = (base / "subagents.md").read_text(encoding="utf-8").split("## Rules", 1)[1].split("\n## ", 1)[0]
        self.assertIn("read its diff", rules)

        references = (base / "references.md").read_text(encoding="utf-8")
        self.assertIn("obra/superpowers/blob/main/skills/verification-before-completion", references)

    def test_agent_authoring_keeps_context_small_and_state_in_files(self):
        """Verify the context and state rules sit with the other agent rules and cite public sources only."""
        base = ROOT_DIR / "skills" / "agent-authoring"
        skill = (base / "SKILL.md").read_text(encoding="utf-8")
        working = skill.split("## Working with an agent on a task", 1)[1].split("\n## ", 1)[0]
        context = working.split("- **Keep context small.**", 1)[1].split("\n- **", 1)[0]
        for token in ("subagent", "60%", "fresh session"):
            with self.subTest(token=token):
                self.assertIn(token, context)
        state = working.split("- **Keep state in files, not in the chat.**", 1)[1].split("\n- **", 1)[0]
        for token in ("`git log`", "write its status back", "new item", "committing"):
            with self.subTest(token=token):
                self.assertIn(token, state)

        references = (base / "references.md").read_text(encoding="utf-8")
        principles = references.split("## Principles", 1)[1].split("\n## ", 1)[0]
        self.assertEqual(len(re.findall(r"^\| [CPL]\d+ \|", principles, flags=re.MULTILINE)), 11)
        for url in ("humanlayer/advanced-context-engineering-for-coding-agents", "ghuntley.com/ralph", "skills/subagent-driven-development", "steveyegge/beads"):
            with self.subTest(url=url):
                self.assertIn(url, references)
        self.assertNotIn("docs/research", references + skill)

    def test_skill_file_names_are_case_unique(self):
        """Verify no skill folder has two files whose names differ only by case (they collide on macOS)."""
        for folder in (ROOT_DIR / "skills").iterdir():
            if folder.is_dir():
                names = [p.name.lower() for p in folder.iterdir()]
                self.assertEqual(len(names), len(set(names)), folder.name)


if __name__ == "__main__":
    unittest.main()
