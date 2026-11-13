#!/usr/bin/env python3
"""
Zero-dependency semantic version calculation, manifest synchronization, and PR version check.

Developers bump the version inside their pull request. This script:
- suggests a bump from PR metadata (Conventional Commits title, body, labels),
- writes the next version (computed from the latest release tag) into plugin.json
  and marketplace.json,
- checks in CI that the version in a PR is a valid bump over the latest release tag.

Usage:
  python3 scripts/bump-version.py --pr-title "feat: add new subagent"            # suggest only
  python3 scripts/bump-version.py --pr-title "feat: add new subagent" --write-manifests
  python3 scripts/bump-version.py --bump-type minor --write-manifests
  python3 scripts/bump-version.py --check --pr-title "fix: resolve bug" --report-file report.md
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


def get_latest_tag_version(repo_root: Path):
    """
    Return the highest SemVer version among release tags (v*.*.*, optionally
    prefixed like 'workflow--v1.2.3'), or None when there is no such tag.
    """
    try:
        result = subprocess.run(
            ["git", "tag", "-l"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None

    tag_versions = []
    for tag in result.stdout.splitlines():
        m = re.match(r"^(?:[a-zA-Z0-9_-]+--)?v(\d+\.\d+\.\d+)$", tag.strip())
        if m:
            ver_tuple = parse_semver(m.group(1))
            if ver_tuple:
                tag_versions.append((ver_tuple, m.group(1)))
    if not tag_versions:
        return None
    return max(tag_versions, key=lambda item: item[0])[1]


def get_base_version(repo_root: Path) -> str:
    """
    Resolve the base version a PR bumps from: the latest release tag.
    Falls back to .claude-plugin/plugin.json only when the repository has no release tag.

    The manifest is not used as a floor: inside a PR it already holds the bumped
    version, and bumping from it again would skip a version.
    """
    tag_version = get_latest_tag_version(repo_root)
    if tag_version:
        return tag_version

    plugin_json_path = repo_root / ".claude-plugin" / "plugin.json"
    if not plugin_json_path.exists():
        raise ValueError(
            f"Unable to determine base version: no valid git tags and no {plugin_json_path}"
        )
    try:
        with open(plugin_json_path, "r", encoding="utf-8") as f:
            version = json.load(f).get("version")
    except Exception as e:
        raise ValueError(
            f"Failed to read fallback version from {plugin_json_path}: {e}"
        )
    if not parse_semver(str(version or "")):
        raise ValueError(
            f"Unable to determine base version: no valid git tags and no valid version in {plugin_json_path}"
        )
    return str(version)


def read_manifest_versions(manifest_root: Path) -> tuple:
    """
    Return (plugin_version, marketplace_version) read from manifest_root/.claude-plugin.
    marketplace_version is taken from the plugins entry whose name matches plugin.json.
    """
    plugin_path = manifest_root / ".claude-plugin" / "plugin.json"
    marketplace_path = manifest_root / ".claude-plugin" / "marketplace.json"
    with open(plugin_path, "r", encoding="utf-8") as f:
        plugin_data = json.load(f)
    with open(marketplace_path, "r", encoding="utf-8") as f:
        marketplace_data = json.load(f)

    plugin_name = plugin_data.get("name")
    marketplace_version = None
    for item in marketplace_data.get("plugins", []):
        if item.get("name") == plugin_name:
            marketplace_version = item.get("version")
            break
    return plugin_data.get("version"), marketplace_version


def classify_actual_bump(base_version: str, version: str):
    """
    Classify how `version` relates to `base_version`:
    'none' (equal), 'major' / 'minor' / 'patch' (exactly one valid SemVer step),
    'lower' (older than base), or 'invalid' (not SemVer, or skips versions).
    """
    base = parse_semver(base_version)
    ver = parse_semver(version)
    if not base or not ver:
        return "invalid"
    if ver == base:
        return "none"
    if ver < base:
        return "lower"
    for bump in ("major", "minor", "patch"):
        if calculate_next_version(base_version, bump) == version:
            return bump
    return "invalid"


def check_pr_version(
    base_version: str,
    plugin_version: str,
    marketplace_version: str,
    suggested_bump: str,
    suggestion_reason: str,
) -> dict:
    """
    Validate the version a developer set in a PR against the latest release tag.

    Hard failures:
    - plugin.json and marketplace.json disagree, or the version is not SemVer;
    - the version is lower than, or skips past, the next valid version;
    - the PR metadata asks for a release but the version was not bumped;
    - the PR metadata marks a breaking change but the bump is not major.
    A bump that differs from the suggestion in any other way is only a warning,
    because the developer knows the scope of the change.

    Returns a dict with keys: ok, should_release, actual_bump, errors, warnings.
    """
    errors = []
    warnings = []
    actual_bump = None

    if plugin_version != marketplace_version:
        errors.append(
            f"Version mismatch: plugin.json={plugin_version} vs marketplace.json={marketplace_version}."
        )
    elif not parse_semver(str(plugin_version or "")):
        errors.append(f"Version '{plugin_version}' is not valid SemVer (expected X.Y.Z).")
    else:
        actual_bump = classify_actual_bump(base_version, plugin_version)
        if actual_bump == "lower":
            errors.append(
                f"Version {plugin_version} is lower than the latest release v{base_version}."
            )
        elif actual_bump == "invalid":
            valid_next = ", ".join(
                calculate_next_version(base_version, b) for b in ("patch", "minor", "major")
            )
            errors.append(
                f"Version {plugin_version} is not a single step from v{base_version}. "
                f"Valid next versions: {valid_next}."
            )
        elif actual_bump == "none":
            if suggested_bump != "skip":
                errors.append(
                    f"Version was not bumped from v{base_version}, but this PR needs a "
                    f"{suggested_bump} release ({suggestion_reason}). Bump the version, "
                    f"or add the 'skip-release' label if this PR must not be released."
                )
        elif suggested_bump == "major" and actual_bump != "major":
            errors.append(
                f"This PR is a breaking change ({suggestion_reason}) but the bump is "
                f"{actual_bump}. Bump major to {calculate_next_version(base_version, 'major')}."
            )
        elif suggested_bump not in ("skip", actual_bump):
            warnings.append(
                f"Bump is {actual_bump} but PR metadata suggests {suggested_bump} "
                f"({suggestion_reason}). Keep it if the scope really is {actual_bump}."
            )

    return {
        "ok": not errors,
        "should_release": not errors and actual_bump in ("major", "minor", "patch"),
        "actual_bump": actual_bump,
        "errors": errors,
        "warnings": warnings,
    }


def format_check_report(
    base_version: str,
    version: str,
    suggested_bump: str,
    suggestion_reason: str,
    result: dict,
) -> str:
    """Render the PR version check as Markdown for a sticky PR comment."""
    status = "Passed" if result["ok"] else "Failed"
    lines = [
        f"### Version check: {status}",
        "",
        f"- Latest release: `v{base_version}`",
        f"- Version in this PR: `{version}`",
    ]
    if suggested_bump == "skip":
        lines.append(f"- Suggested bump: none ({suggestion_reason})")
    else:
        suggested_version = calculate_next_version(base_version, suggested_bump)
        lines.append(
            f"- Suggested bump: **{suggested_bump}** to `{suggested_version}` ({suggestion_reason})"
        )
    if result["ok"]:
        lines.append(
            f"- On merge: release `v{version}`" if result["should_release"]
            else "- On merge: no release"
        )
    for error in result["errors"]:
        lines.append(f"- :x: {error}")
    for warning in result["warnings"]:
        lines.append(f"- :warning: {warning}")
    lines += [
        "",
        "Set the version from the latest release tag (run on your branch, then commit):",
        "",
        "```bash",
        "git fetch --tags",
        "python3 scripts/bump-version.py --bump-type <patch|minor|major> --write-manifests",
        "```",
    ]
    return "\n".join(lines) + "\n"


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


def run_check(
    repo_root: Path,
    manifest_root: Path,
    pr_title: str,
    pr_body: str,
    labels,
    report_file: str = None,
    github_output_file: str = None,
) -> int:
    """Run the PR version gate. Returns 0 when the version is acceptable, 1 otherwise."""
    def fail(message: str) -> int:
        print(f"[ERROR] {message}", file=sys.stderr)
        if report_file:
            Path(report_file).write_text(
                f"### Version check: Failed\n\n- :x: {message}\n", encoding="utf-8"
            )
        return 1

    try:
        base_version = get_base_version(repo_root)
        plugin_version, marketplace_version = read_manifest_versions(manifest_root)
    except Exception as e:
        return fail(f"Failed to read versions: {e}")

    try:
        suggested_bump, reason = parse_conventional_commit(
            title=pr_title, body=pr_body, labels=labels
        )
    except Exception as e:
        return fail(f"Failed to parse PR metadata: {e}")

    result = check_pr_version(
        base_version, plugin_version, marketplace_version, suggested_bump, reason
    )
    report = format_check_report(
        base_version, plugin_version, suggested_bump, reason, result
    )
    print(report)

    if report_file:
        Path(report_file).write_text(report, encoding="utf-8")

    if github_output_file:
        export_github_outputs(github_output_file, {
            "check_passed": "true" if result["ok"] else "false",
            "should_release": "true" if result["should_release"] else "false",
            "base_version": base_version,
            "pr_version": plugin_version,
            "suggested_bump": suggested_bump,
        })

    return 0 if result["ok"] else 1


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
        "--check",
        action="store_true",
        help="Validate the version already set in the manifests against the latest release tag (PR gate)",
    )
    parser.add_argument(
        "--manifest-root",
        type=str,
        default=None,
        help="Directory holding the .claude-plugin manifests to check (defaults to --repo-root)",
    )
    parser.add_argument(
        "--report-file",
        type=str,
        default=None,
        help="Write the --check result as Markdown to this file",
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

    repo_root = (
        Path(args.repo_root).resolve()
        if args.repo_root
        else Path.cwd().resolve()
    )

    if args.check:
        manifest_root = (
            Path(args.manifest_root).resolve() if args.manifest_root else repo_root
        )
        return run_check(
            repo_root=repo_root,
            manifest_root=manifest_root,
            pr_title=pr_title,
            pr_body=pr_body,
            labels=labels,
            report_file=args.report_file,
            github_output_file=args.github_output or os.environ.get("GITHUB_OUTPUT"),
        )

    if not bump_type_override and not pr_title:
        print(
            "[ERROR] Either --pr-title (or PR_TITLE env) or --bump-type (or BUMP_TYPE_OVERRIDE env) must be provided.",
            file=sys.stderr,
        )
        return 1

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
    elif should_release:
        print(
            f"[INFO] To apply: python3 scripts/bump-version.py --bump-type {bump_type} --write-manifests"
        )

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
