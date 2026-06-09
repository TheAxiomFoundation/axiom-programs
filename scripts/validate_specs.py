#!/usr/bin/env python3
"""Validate every program spec in this repo.

Two checks:

1. **Structure** — each spec is well-formed YAML with the required shape:
   ``program`` (string), ``period``, non-empty ``outputs`` (list of
   strings), and ``scope`` as a mapping of scope name → list of paths when
   present. Deep schema validation through axiom-compose's own loader runs
   in axiom-compose's CI, which composes real specs from this repo;
   axiom-compose is a private repo, so this script stays dependency-free
   and runnable anywhere.
2. **Scope existence** — every ``scope:`` entry must resolve to a module file
   in the corresponding rulespec checkout. A dangling entry composes into a
   program the engine cannot compile (see axiom-programs#14).

Known-dangling entries are ratcheted through ``known-dangling.yaml`` at the
repo root: a dangling entry not listed there fails the build, and a listed
entry that now resolves also fails (remove it from the allowlist). Scope
prefixes mirror axiom_compose.core._scope_prefix: ``federal`` → ``us``,
``state`` → the spec's jurisdiction, anything else is itself the prefix;
prefix ``p`` resolves against ``<rulespec-root>/rulespec-<p>``.

Usage:
    validate_specs.py --rulespec-root _rulespec [--repo-root .]

A missing rulespec checkout for a referenced prefix is an error: the audit
must never silently skip a scope.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


def structural_errors(rel: str, raw: object) -> list[str]:
    """Required-shape checks shared by every spec."""
    if not isinstance(raw, dict):
        return [f"{rel}: spec root must be a mapping"]
    errors = []
    if not isinstance(raw.get("program"), str) or not raw.get("program"):
        errors.append(f"{rel}: missing or non-string `program`")
    if "period" not in raw:
        errors.append(f"{rel}: missing `period`")
    outputs = raw.get("outputs")
    if (
        not isinstance(outputs, list)
        or not outputs
        or not all(isinstance(item, str) for item in outputs)
    ):
        errors.append(f"{rel}: `outputs` must be a non-empty list of strings")
    scope = raw.get("scope")
    if scope is not None:
        if not isinstance(scope, dict):
            errors.append(f"{rel}: `scope` must be a mapping")
        else:
            for name, paths in scope.items():
                if not isinstance(paths, list) or not all(
                    isinstance(item, str) for item in paths
                ):
                    errors.append(
                        f"{rel}: scope `{name}` must be a list of path strings"
                    )
    return errors


def scope_prefix(program: str, scope_name: str) -> str:
    normalized = scope_name.strip()
    if normalized == "federal":
        return "us"
    if normalized == "state":
        return program.split("/", 1)[0]
    return normalized


def load_allowlist(repo_root: Path) -> set[tuple[str, str, str]]:
    path = repo_root / "known-dangling.yaml"
    if not path.exists():
        return set()
    payload = yaml.safe_load(path.read_text()) or {}
    entries = payload.get("entries", [])
    return {
        (entry["spec"], entry["scope"], entry["path"])
        for entry in entries
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rulespec-root",
        type=Path,
        required=True,
        help="directory containing rulespec-<prefix> checkouts",
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    rulespec_root = args.rulespec_root.resolve()

    spec_paths = sorted(
        path
        for path in repo_root.glob("*/*/*.yaml")
        if path.parts[len(repo_root.parts)] != "artifacts"
        and not path.parts[len(repo_root.parts)].startswith(("_", "."))
    )
    if not spec_paths:
        print("error: no specs found", file=sys.stderr)
        return 1

    allowlist = load_allowlist(repo_root)
    seen_allowlisted: set[tuple[str, str, str]] = set()
    errors: list[str] = []
    checked = 0

    for spec_path in spec_paths:
        rel = str(spec_path.relative_to(repo_root))
        try:
            raw = yaml.safe_load(spec_path.read_text()) or {}
        except yaml.YAMLError as exc:
            errors.append(f"{rel}: invalid YAML: {exc}")
            continue
        shape_errors = structural_errors(rel, raw)
        if shape_errors:
            errors.extend(shape_errors)
            continue

        for scope_name, paths in (raw.get("scope") or {}).items():
            prefix = scope_prefix(raw["program"], scope_name)
            repo_dir = rulespec_root / f"rulespec-{prefix}"
            if not repo_dir.exists():
                errors.append(
                    f"{rel}: no checkout for prefix {prefix!r} at {repo_dir} "
                    "(clone it in CI; the audit never skips a scope)"
                )
                continue
            for path in paths or []:
                checked += 1
                key = (rel, scope_name, path)
                resolves = (repo_dir / f"{path}.yaml").exists()
                if not resolves and key not in allowlist:
                    errors.append(
                        f"{rel}: scope entry {scope_name}: {path} does not "
                        f"resolve in {repo_dir.name}"
                    )
                if resolves and key in allowlist:
                    errors.append(
                        f"{rel}: {scope_name}: {path} now resolves — remove "
                        "it from known-dangling.yaml"
                    )
                if key in allowlist:
                    seen_allowlisted.add(key)

    for stale in sorted(allowlist - seen_allowlisted):
        errors.append(
            "known-dangling.yaml entry matches no spec scope entry "
            f"(stale): {stale}"
        )

    print(
        f"validated {len(spec_paths)} specs, {checked} scope entries, "
        f"{len(allowlist)} allowlisted"
    )
    if errors:
        print(f"\n{len(errors)} problem(s):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print("all specs parse and all scope entries resolve or are allowlisted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
