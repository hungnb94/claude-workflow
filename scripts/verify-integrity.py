#!/usr/bin/env python3
"""
Zero-dependency semantic and structural integrity verification script.
Validates:
1. Version synchronization between plugin.json and marketplace.json (and optional git tag).
2. Subagent references between skills and agents/.
3. Least-privilege tool isolation for review subagents (no Edit tool).
4. Token budget guardrails for subagent frontmatter descriptions (<= 40 words).

Usage:
  python3 scripts/verify-integrity.py
  python3 scripts/verify-integrity.py --check-tag v1.0.0
"""

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path


def parse_frontmatter(content: str) -> dict:
    """
    Safely extract YAML frontmatter from markdown content without external dependencies.
    Supports scalars, folded scalars (>), literal scalars (|), and string lists (- item).
    """
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    fm_text = parts[1]

    data = {}
    lines = fm_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()

            if val in (">", "|"):
                i += 1
                multi_lines = []
                while i < len(lines) and (
                    lines[i].startswith("  ")
                    or lines[i].startswith("\t")
                    or not lines[i].strip()
                ):
                    if lines[i].strip():
                        multi_lines.append(lines[i].strip())
                    i += 1
                data[key] = " ".join(multi_lines)
                continue
            elif not val:
                i += 1
                items = []
                while i < len(lines) and (
                    lines[i].startswith("  ")
                    or lines[i].startswith("\t")
                    or lines[i].strip().startswith("- ")
                ):
                    s = lines[i].strip()
                    if s.startswith("- "):
                        items.append(s[2:].strip())
                    i += 1
                data[key] = items
                continue
            else:
                data[key] = val
                i += 1
                continue
        i += 1
    return data


def find_repo_root() -> Path:
    """Locate the repository root directory."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists() or (current / ".claude-plugin").exists():
            return current
        current = current.parent
    return Path.cwd()


def check_version_sync(repo_root: Path, check_tag: str = None) -> bool:
    """
    Check that versions in plugin.json and marketplace.json match.
    Optionally check that both match an expected git tag.
    """
    print("[INFO] Running Version Synchronization Check...")
    plugin_path = repo_root / ".claude-plugin" / "plugin.json"
    marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"

    if not plugin_path.exists():
        print(f"[FAIL] Missing plugin manifest at: {plugin_path}")
        return False
    if not marketplace_path.exists():
        print(f"[FAIL] Missing marketplace manifest at: {marketplace_path}")
        return False

    try:
        with open(plugin_path, "r", encoding="utf-8") as f:
            plugin_data = json.load(f)
    except Exception as e:
        print(f"[FAIL] Error parsing {plugin_path}: {e}")
        return False

    try:
        with open(marketplace_path, "r", encoding="utf-8") as f:
            marketplace_data = json.load(f)
    except Exception as e:
        print(f"[FAIL] Error parsing {marketplace_path}: {e}")
        return False

    plugin_version = plugin_data.get("version")
    if not plugin_version:
        print("[FAIL] Missing 'version' field in plugin.json")
        return False

    plugin_name = plugin_data.get("name")
    if not plugin_name:
        print("[FAIL] Missing 'name' field in plugin.json")
        return False

    plugins_list = marketplace_data.get("plugins", [])
    if not plugins_list:
        print("[FAIL] Missing or empty 'plugins' array in marketplace.json")
        return False

    marketplace_version = None
    for entry in plugins_list:
        if entry.get("name") == plugin_name:
            marketplace_version = entry.get("version")
            break

    if marketplace_version is None:
        print(
            f"[FAIL] Plugin '{plugin_name}' declared in plugin.json not found in marketplace.json"
        )
        return False

    if plugin_version != marketplace_version:
        print(
            f"[FAIL] Version mismatch: plugin.json={plugin_version} vs marketplace.json={marketplace_version}"
        )
        return False

    print(f"[PASS] Version synchronized: {plugin_version} (plugin.json == marketplace.json)")

    if check_tag:
        expected_version = check_tag.lstrip("v")
        if plugin_version != expected_version:
            print(
                f"[FAIL] Git tag '{check_tag}' (normalized '{expected_version}') does not match manifest version '{plugin_version}'"
            )
            return False
        print(f"[PASS] Tag version '{check_tag}' matches manifest version '{plugin_version}'")

    return True


def check_agent_references(repo_root: Path) -> bool:
    """
    Check that all subagent references in skills/*/SKILL.md have a corresponding
    definition file in agents/<agent-name>.md.
    """
    print("[INFO] Running Subagent Reference Integrity Check...")
    skills_dir = repo_root / "skills"
    agents_dir = repo_root / "agents"

    if not skills_dir.exists():
        print(f"[FAIL] Skills directory not found: {skills_dir}")
        return False
    if not agents_dir.exists():
        print(f"[FAIL] Agents directory not found: {agents_dir}")
        return False

    skill_files = list(skills_dir.glob("*/SKILL.md"))
    if not skill_files:
        print("[FAIL] No skill files found in skills/*/SKILL.md")
        return False

    # Collect existing agent definitions
    existing_agents = set()
    for agent_file in agents_dir.glob("*.md"):
        existing_agents.add(agent_file.stem)

    all_valid = True
    total_refs = 0

    for skill_file in skill_files:
        skill_rel = skill_file.relative_to(repo_root)
        try:
            content = skill_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[FAIL] Could not read {skill_rel}: {e}")
            all_valid = False
            continue

        # Pattern matches fw-1-spec, gtw-5-review, etc.
        referenced_agents = sorted(
            set(re.findall(r"\b((?:fw|gtw)-[0-9]+-[a-z0-9-]+)\b", content))
        )
        if not referenced_agents:
            print(f"[WARN] No subagent references found in {skill_rel}")
            continue

        for agent_name in referenced_agents:
            total_refs += 1
            if agent_name not in existing_agents:
                print(
                    f"[FAIL] {skill_rel} references nonexistent agent '{agent_name}' (expected agents/{agent_name}.md)"
                )
                all_valid = False
            else:
                agent_path = agents_dir / f"{agent_name}.md"
                agent_content = agent_path.read_text(encoding="utf-8")
                fm = parse_frontmatter(agent_content)
                declared_name = fm.get("name")
                if declared_name != agent_name:
                    print(
                        f"[FAIL] Agent file agents/{agent_name}.md declares name '{declared_name}', expected '{agent_name}'"
                    )
                    all_valid = False

    if all_valid:
        print(
            f"[PASS] All {total_refs} subagent references across {len(skill_files)} skills are valid and exist in agents/"
        )
    return all_valid


def check_review_tool_isolation(repo_root: Path) -> bool:
    """
    Check that review subagents (e.g., fw-5-review, gtw-5-review) adhere to the
    least privilege principle and MUST NOT declare the Edit tool.
    """
    print("[INFO] Running Least Privilege Tool Isolation Audit...")
    agents_dir = repo_root / "agents"
    if not agents_dir.exists():
        print(f"[FAIL] Agents directory not found: {agents_dir}")
        return False

    review_agents = list(agents_dir.glob("*5-review*.md"))
    if not review_agents:
        print("[FAIL] No review subagent definitions found (*5-review*.md)")
        return False

    all_valid = True
    for agent_file in review_agents:
        agent_rel = agent_file.relative_to(repo_root)
        try:
            content = agent_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[FAIL] Could not read {agent_rel}: {e}")
            all_valid = False
            continue

        fm = parse_frontmatter(content)
        tools = fm.get("tools", [])

        if isinstance(tools, str):
            tools = [t.strip() for t in tools.split(",") if t.strip()]

        if "Edit" in tools:
            print(
                f"[FAIL] Security violation in {agent_rel}: review subagent must not have 'Edit' tool declared"
            )
            all_valid = False
        else:
            print(
                f"[PASS] {agent_rel}: tools properly isolated ({', '.join(tools)})"
            )

    return all_valid


def check_token_budgets(repo_root: Path, max_words: int = 40) -> bool:
    """
    Check that all subagent descriptions in YAML frontmatter do not exceed
    the token budget limit (default 40 words).
    """
    print(f"[INFO] Running Subagent Description Token Budget Check (limit: {max_words} words)...")
    agents_dir = repo_root / "agents"
    if not agents_dir.exists():
        print(f"[FAIL] Agents directory not found: {agents_dir}")
        return False

    agent_files = sorted(list(agents_dir.glob("*.md")))
    if not agent_files:
        print("[FAIL] No agent markdown files found in agents/")
        return False

    all_valid = True
    for agent_file in agent_files:
        agent_rel = agent_file.relative_to(repo_root)
        try:
            content = agent_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[FAIL] Could not read {agent_rel}: {e}")
            all_valid = False
            continue

        fm = parse_frontmatter(content)
        description = fm.get("description", "")
        if not description:
            print(f"[FAIL] {agent_rel}: missing 'description' in YAML frontmatter")
            all_valid = False
            continue

        words = description.split()
        word_count = len(words)

        if word_count > max_words:
            print(
                f"[FAIL] {agent_rel}: description exceeded token budget ({word_count} words > {max_words} words max)"
            )
            all_valid = False
        else:
            print(
                f"[PASS] {agent_rel}: {word_count}/{max_words} words"
            )

    if all_valid:
        print(
            f"[PASS] All {len(agent_files)} subagent descriptions are within token budget limits"
        )
    return all_valid


def main():
    parser = argparse.ArgumentParser(
        description="Verify semantic and structural integrity of Claude Workflow plugin."
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=None,
        help="Path to repository root (auto-detected if omitted)",
    )
    parser.add_argument(
        "--check-tag",
        type=str,
        default=None,
        help="Git tag to verify against manifest versions (e.g., v1.0.0)",
    )
    args = parser.parse_args()

    if args.repo_root:
        repo_root = Path(args.repo_root).resolve()
    else:
        repo_root = find_repo_root()

    print(f"[INFO] Target repository root: {repo_root}")

    checks = [
        ("Version Synchronization", lambda: check_version_sync(repo_root, args.check_tag)),
        ("Subagent References", lambda: check_agent_references(repo_root)),
        ("Least Privilege Tool Isolation", lambda: check_review_tool_isolation(repo_root)),
        ("Token Budget Guardrails", lambda: check_token_budgets(repo_root)),
    ]

    failed_checks = []
    for name, check_fn in checks:
        print("-" * 60)
        success = check_fn()
        if not success:
            failed_checks.append(name)

    print("=" * 60)
    if failed_checks:
        print(f"[SUMMARY] FAILED: {len(failed_checks)} check(s) failed:")
        for name in failed_checks:
            print(f"  - {name}")
        sys.exit(1)
    else:
        print("[SUMMARY] PASSED: All integrity checks passed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
