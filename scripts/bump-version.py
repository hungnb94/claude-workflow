#!/usr/bin/env python3
"""
Zero-dependency semantic version calculation and manifest synchronization script.
Inspects PR metadata (Conventional Commits title, body, labels) or manual override,
calculates the next SemVer 2.0.0 version from base tags or manifests, updates plugin.json
and marketplace.json, and exports outputs for GitHub Actions.

Usage:
  python3 scripts/bump-version.py --pr-title "feat: add new subagent" --write-manifests
  python3 scripts/bump-version.py --pr-title "fix: resolve bug" --dry-run
  python3 scripts/bump-version.py --bump-type minor --write-manifests
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


SKIP_TYPES = {"docs", "chore", "ci", "test", "style", "build"}
MINOR_TYPES = {"feat"}
PATCH_TYPES = {"fix", "perf", "refactor", "revert"}
VALID_BUMP_TYPES = {"major", "minor", "patch", "skip"}

CONVENTIONAL_COMMIT_REGEX = re.compile(
    r"^(?P<type>[a-zA-Z0-9_-]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<desc>.+)$"
)
BREAKING_CHANGE_BODY_REGEX = re.compile(r"\bBREAKING[ -]CHANGE:\s*")


def parse_semver(v_str: str):
    """
    Parse SemVer string 'X.Y.Z' into (X, Y, Z) tuple of ints.
    Returns None if the string is not valid SemVer 2.0.0.
    """
    if not v_str:
        return None
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", str(v_str).strip())
    if m:
        return tuple(map(int, m.groups()))
    return None


def parse_labels_arg(labels_raw) -> list:
    """
    Parse labels from a JSON string, comma-separated string, or list.
    Returns a list of stripped label strings, filtering out null/none values.
    """
    if not labels_raw:
        return []
    if isinstance(labels_raw, list):
        return [
            str(item).strip()
            for item in labels_raw
            if str(item).strip() and str(item).strip().lower() not in ("null", "none")
        ]
    raw = str(labels_raw).strip()
    if raw.lower() in ("null", "none", "[]", ""):
        return []
    if raw.startswith("[") and raw.endswith("]"):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [
                    str(item).strip()
                    for item in parsed
                    if str(item).strip() and str(item).strip().lower() not in ("null", "none")
                ]
        except Exception:
            pass
    return [
        item.strip()
        for item in raw.split(",")
        if item.strip() and item.strip().lower() not in ("null", "none")
    ]


def parse_conventional_commit(
    title: str = "",
    body: str = "",
    labels: list = None,
    bump_override: str = None,
) -> tuple:
    """
    Determine the SemVer bump type ('major', 'minor', 'patch', 'skip') and reason.

    Precedence rules:
    1. Explicit bump_override if provided.
    2. Skip labels ('skip-release', 'no-release').
    3. Breaking change marker ('!' in title or 'BREAKING CHANGE:' / 'BREAKING-CHANGE:' in body).
    4. Conventional Commits prefix type:
       - 'feat' -> minor
       - 'fix', 'perf', 'refactor', 'revert' -> patch
       - 'docs', 'chore', 'ci', 'test', 'style', 'build' -> skip
    """
    if bump_override:
        norm_override = bump_override.strip().lower()
        if norm_override in VALID_BUMP_TYPES:
            return norm_override, f"Explicit bump type override: '{norm_override}'"
        raise ValueError(
            f"Invalid bump type override '{bump_override}'. Expected one of: {sorted(VALID_BUMP_TYPES)}"
        )

    clean_title = (title or "").strip()
    clean_body = body or ""
    parsed_labels = parse_labels_arg(labels)

    # 1. Check for skip labels
    for label in parsed_labels:
        norm_label = label.lower()
        if norm_label in ("skip-release", "no-release"):
            return "skip", f"Release skipped via PR label '{label}'"

    if not clean_title:
        raise ValueError("PR title cannot be empty when bump override is not provided.")

    # 2. Validate Conventional Commits syntax
    match = CONVENTIONAL_COMMIT_REGEX.match(clean_title)
    if not match:
        raise ValueError(
            f"PR title '{clean_title}' does not conform to Conventional Commits format '<type>(<scope>): <description>'"
        )

    commit_type = match.group("type").lower()
    has_exclamation = bool(match.group("breaking"))

    # 3. Check for Breaking Changes (title '!' or body 'BREAKING CHANGE:')
    if has_exclamation:
        return "major", "Breaking change denoted by '!' in PR title"

    if BREAKING_CHANGE_BODY_REGEX.search(clean_body):
        return "major", "Breaking change denoted by BREAKING CHANGE footer in PR body"

    # 4. Check Commit Type
    if commit_type in SKIP_TYPES:
        return "skip", f"Commit type '{commit_type}' does not trigger a release"

    if commit_type in MINOR_TYPES:
        return "minor", f"Commit type '{commit_type}' triggers minor release"

    if commit_type in PATCH_TYPES:
        return "patch", f"Commit type '{commit_type}' triggers patch release"

    raise ValueError(
        f"Unrecognized Conventional Commits type '{commit_type}' in PR title '{clean_title}'. "
        f"Allowed types: {sorted(SKIP_TYPES | MINOR_TYPES | PATCH_TYPES)}"
    )


def get_base_version(repo_root: Path) -> str:
    """
    Resolve base version from the latest semantic git tag (v*.*.*) and/or
    .claude-plugin/plugin.json, taking the highest SemVer version as a floor
    to prevent regressions if manifests were bumped ahead of git tags.
    """
    candidates = []

    # 1. Inspect git tags
    try:
        result = subprocess.run(
            ["git", "tag", "-l"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            tags = [t.strip() for t in result.stdout.strip().splitlines() if t.strip()]
            tag_versions = []
            for tag in tags:
                m = re.match(r"^(?:[a-zA-Z0-9_-]+--)?v(\d+\.\d+\.\d+)$", tag)
                if m:
                    ver_tuple = parse_semver(m.group(1))
                    if ver_tuple:
                        tag_versions.append((ver_tuple, m.group(1)))
            if tag_versions:
                max_tag = max(tag_versions, key=lambda item: item[0])
                candidates.append(max_tag)
    except Exception:
        pass

    # 2. Inspect .claude-plugin/plugin.json
    plugin_json_path = repo_root / ".claude-plugin" / "plugin.json"
    manifest_error = None
    if plugin_json_path.exists():
        try:
            with open(plugin_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            version = data.get("version")
            if version:
                ver_tuple = parse_semver(str(version))
                if ver_tuple:
                    candidates.append((ver_tuple, str(version)))
        except Exception as e:
            manifest_error = e

    if candidates:
        best_candidate = max(candidates, key=lambda item: item[0])
        return best_candidate[1]

    if manifest_error:
        raise ValueError(
            f"Failed to read fallback version from {plugin_json_path}: {manifest_error}"
        )

    raise ValueError(
        f"Unable to determine base version: no valid git tags and no valid version in {plugin_json_path}"
    )


def calculate_next_version(base_version: str, bump_type: str) -> str:
    """
    Calculate next SemVer 2.0.0 based on bump type:
    - major: X+1.0.0
    - minor: X.Y+1.0
    - patch: X.Y.Z+1
    - skip: returns base_version
    """
    ver_tuple = parse_semver(base_version)
    if not ver_tuple:
        raise ValueError(
            f"Base version '{base_version}' is not valid SemVer 2.0.0 (expected X.Y.Z)"
        )

    major, minor, patch = ver_tuple

    if bump_type == "major":
        return f"{major + 1}.0.0"
    if bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    if bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    if bump_type == "skip":
        return base_version

    raise ValueError(
        f"Invalid bump type '{bump_type}'. Expected one of: {sorted(VALID_BUMP_TYPES)}"
    )


def update_manifests(repo_root: Path, new_version: str) -> None:
    """
    Synchronously update version in:
    1. .claude-plugin/plugin.json ("version": new_version)
    2. .claude-plugin/marketplace.json (plugins[name=claude-workflow].version = new_version)
    Preserves 2-space indentation and trailing newline.
    """
    plugin_path = repo_root / ".claude-plugin" / "plugin.json"
    marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"

    if not plugin_path.exists():
        raise FileNotFoundError(f"Missing plugin manifest at: {plugin_path}")
    if not marketplace_path.exists():
        raise FileNotFoundError(f"Missing marketplace manifest at: {marketplace_path}")

    # 1. Update plugin.json
    with open(plugin_path, "r", encoding="utf-8") as f:
        plugin_data = json.load(f)

    plugin_data["version"] = new_version

    with open(plugin_path, "w", encoding="utf-8") as f:
        json.dump(plugin_data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # 2. Update marketplace.json
    with open(marketplace_path, "r", encoding="utf-8") as f:
        marketplace_data = json.load(f)

    plugins = marketplace_data.get("plugins", [])
    if not plugins:
        raise ValueError(f"Missing or empty 'plugins' array in {marketplace_path}")

    plugin_name = plugin_data.get("name", "workflow")
    updated = False
    for item in plugins:
        if item.get("name") == plugin_name:
            item["version"] = new_version
            updated = True
            break

    if not updated and len(plugins) > 0:
        print(
            f"[WARN] Plugin '{plugin_name}' not found by name in marketplace.json; "
            f"updating first plugin entry '{plugins[0].get('name')}'",
            file=sys.stderr,
        )
        plugins[0]["version"] = new_version
        updated = True

    if not updated:
        raise ValueError(
            f"Could not find plugin entry for '{plugin_name}' in {marketplace_path}"
        )

    with open(marketplace_path, "w", encoding="utf-8") as f:
        json.dump(marketplace_data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def export_github_outputs(output_file: str, outputs: dict) -> None:
    """
    Write key-value pairs to the GitHub Actions output file.
    """
    with open(output_file, "a", encoding="utf-8") as f:
        for key, value in outputs.items():
            f.write(f"{key}={value}\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Calculate semantic version bump and synchronize manifests."
    )
    parser.add_argument(
        "--pr-title",
        type=str,
        default="",
        help="Pull Request title conforming to Conventional Commits (or PR_TITLE env var)",
    )
    parser.add_argument(
        "--pr-body",
        type=str,
        default="",
        help="Pull Request description body (or PR_BODY env var)",
    )
    parser.add_argument(
        "--labels",
        type=str,
        default="",
        help="Comma-separated or JSON list of PR labels (or PR_LABELS env var)",
    )
    parser.add_argument(
        "--bump-type",
        type=str,
        choices=["major", "minor", "patch", "skip"],
        default=None,
        help="Manual version bump override (or BUMP_TYPE_OVERRIDE env var)",
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=None,
        help="Path to repository root (defaults to current working directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate version calculation without modifying files on disk",
    )
    parser.add_argument(
        "--write-manifests",
        action="store_true",
        help="Write updated version to plugin.json and marketplace.json",
    )
    parser.add_argument(
        "--github-output",
        type=str,
        default=None,
        help="Path to file for exporting GitHub Actions outputs (falls back to GITHUB_OUTPUT env var)",
    )

    args = parser.parse_args(argv)

    # Resolve inputs with environment variables fallback
    env_bump = (
        os.environ.get("BUMP_TYPE_OVERRIDE", "").strip()
        or os.environ.get("BUMP_TYPE", "").strip()
    )
    bump_type_override = args.bump_type or (env_bump if env_bump else None)
    pr_title = (args.pr_title or os.environ.get("PR_TITLE", "")).strip()
    pr_body = args.pr_body or os.environ.get("PR_BODY", "")
    labels = args.labels or os.environ.get("PR_LABELS", "")

    if not bump_type_override and not pr_title:
        print(
            "[ERROR] Either --pr-title (or PR_TITLE env) or --bump-type (or BUMP_TYPE_OVERRIDE env) must be provided.",
            file=sys.stderr,
        )
        return 1

    repo_root = (
        Path(args.repo_root).resolve()
        if args.repo_root
        else Path.cwd().resolve()
    )

    try:
        bump_type, reason = parse_conventional_commit(
            title=pr_title,
            body=pr_body,
            labels=labels,
            bump_override=bump_type_override,
        )
    except Exception as e:
        print(f"[ERROR] Failed to parse PR metadata: {e}", file=sys.stderr)
        return 1

    print(f"[INFO] Classification: {bump_type.upper()} ({reason})")

    try:
        base_version = get_base_version(repo_root)
    except Exception as e:
        print(f"[ERROR] Failed to resolve base version: {e}", file=sys.stderr)
        return 1

    print(f"[INFO] Base Version: {base_version}")

    should_release = bump_type != "skip"
    if should_release:
        try:
            next_version = calculate_next_version(base_version, bump_type)
        except Exception as e:
            print(f"[ERROR] Failed to calculate next version: {e}", file=sys.stderr)
            return 1
        release_tag = f"v{next_version}"
        print(f"[INFO] Next Version: {next_version} (Tag: {release_tag})")
    else:
        next_version = ""
        release_tag = ""
        print(f"[INFO] Release skipped. Version remains: {base_version}")

    # Write manifests if requested
    if should_release and args.write_manifests:
        if args.dry_run:
            print(f"[DRY-RUN] Manifest update to {next_version} simulated (files unmodified)")
        else:
            try:
                update_manifests(repo_root, next_version)
                print(f"[SUCCESS] Synchronized manifests to version {next_version}")
            except Exception as e:
                print(f"[ERROR] Failed to update manifests: {e}", file=sys.stderr)
                return 1

    # Export outputs for GitHub Actions
    github_output_file = args.github_output or os.environ.get("GITHUB_OUTPUT")
    if github_output_file:
        outputs = {
            "should_release": "true" if should_release else "false",
            "bump_type": bump_type,
            "base_version": base_version,
            "next_version": next_version,
            "release_tag": release_tag,
        }
        try:
            export_github_outputs(github_output_file, outputs)
            print(f"[INFO] Exported outputs to {github_output_file}")
        except Exception as e:
            print(f"[ERROR] Failed to write GitHub outputs: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
