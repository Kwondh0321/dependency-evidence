"""Offline dependency evidence collection."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import tomllib

MANIFEST_NAMES = {
    "package-lock.json",
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "Cargo.lock",
}
PINNED_PYTHON = re.compile(r"^([A-Za-z0-9_.-]+)(?:\[[^]]+\])?==([^\s;]+)")
ANY_PYTHON = re.compile(r"^([A-Za-z0-9_.-]+)(?:\[[^]]+\])?\s*([^;]*)")
DIRECT_PYTHON = re.compile(r"^([A-Za-z0-9_.-]+)(?:\[[^]]+\])?\s*@\s*(\S+)")


def discover_manifests(root: Path) -> list[Path]:
    ignored = {".git", ".venv", "node_modules", "dist", "build"}
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and path.name in MANIFEST_NAMES
        and not any(part in ignored for part in path.relative_to(root).parts)
    )


def _entry(
    ecosystem: str,
    name: str,
    version: str | None,
    source: str,
    direct: bool,
    license_id: str | None = None,
) -> dict[str, Any]:
    findings = []
    if (
        not version
        or version in {"*", "latest"}
        or any(token in version for token in (">", "<", "^", "~"))
    ):
        findings.append("unpinned-version")
    if source.startswith(("git+", "git://", "http://", "https://")):
        findings.append("mutable-or-insecure-source")
    if license_id is None:
        findings.append("license-unknown")
    return {
        "ecosystem": ecosystem,
        "name": name,
        "version": version,
        "source": source,
        "direct": direct,
        "license": license_id,
        "findings": findings,
    }


def _npm(path: Path) -> list[dict[str, Any]]:
    parsed = json.loads(path.read_text(encoding="utf-8"))
    packages = parsed.get("packages")
    entries = []
    if isinstance(packages, dict):
        direct_names = set((packages.get("") or {}).get("dependencies", {})) | set(
            (packages.get("") or {}).get("devDependencies", {})
        )
        for package_path, value in packages.items():
            if not package_path or not isinstance(value, dict):
                continue
            name = value.get("name") or package_path.rsplit("node_modules/", 1)[-1]
            entries.append(
                _entry(
                    "npm",
                    name,
                    value.get("version"),
                    value.get("resolved", "registry"),
                    name in direct_names,
                    value.get("license"),
                )
            )
    elif isinstance(parsed.get("dependencies"), dict):
        for name, value in parsed["dependencies"].items():
            if isinstance(value, dict):
                entries.append(
                    _entry(
                        "npm",
                        name,
                        value.get("version"),
                        value.get("resolved", "registry"),
                        True,
                        value.get("license"),
                    )
                )
    return entries


def _python_requirement(
    requirement: str, source: str, direct: bool = True
) -> dict[str, Any] | None:
    line = requirement.strip()
    if not line or line.startswith(("#", "-r", "--requirement", "--index")):
        return None
    direct_reference = DIRECT_PYTHON.match(line)
    if direct_reference:
        return _entry(
            "pypi", direct_reference.group(1), None, direct_reference.group(2), direct
        )
    if line.startswith(("git+", "http://", "https://")):
        name = (
            line.rsplit("/", 1)[-1].split("@", 1)[0].removesuffix(".git")
            or "direct-url"
        )
        return _entry("pypi", name, None, line, direct)
    pinned = PINNED_PYTHON.match(line)
    if pinned:
        return _entry("pypi", pinned.group(1), pinned.group(2), source, direct)
    match = ANY_PYTHON.match(line)
    if match:
        specifier = match.group(2).strip() or None
        return _entry("pypi", match.group(1), specifier, source, direct)
    return None


def _requirements(path: Path) -> list[dict[str, Any]]:
    return [
        entry
        for line in path.read_text(encoding="utf-8").splitlines()
        if (entry := _python_requirement(line, path.name))
    ]


def _pyproject(path: Path) -> list[dict[str, Any]]:
    parsed = tomllib.loads(path.read_text(encoding="utf-8"))
    project = parsed.get("project", {})
    if not isinstance(project, dict):
        raise TypeError("pyproject.toml의 project 항목은 테이블이어야 합니다")
    dependencies = project.get("dependencies", [])
    optional = project.get("optional-dependencies", {})
    if not isinstance(dependencies, list) or not all(
        isinstance(item, str) for item in dependencies
    ):
        raise ValueError("project.dependencies는 문자열 배열이어야 합니다")
    if not isinstance(optional, dict) or not all(
        isinstance(items, list) and all(isinstance(item, str) for item in items)
        for items in optional.values()
    ):
        raise ValueError(
            "project.optional-dependencies의 각 그룹은 문자열 배열이어야 합니다"
        )
    entries = [
        entry
        for item in dependencies
        if (entry := _python_requirement(item, "pyproject.toml"))
    ]
    for group, items in optional.items():
        entries.extend(
            entry
            for item in items
            if (entry := _python_requirement(item, f"pyproject.toml:{group}", False))
        )
    return entries


def _cargo(path: Path) -> list[dict[str, Any]]:
    parsed = tomllib.loads(path.read_text(encoding="utf-8"))
    return [
        _entry(
            "cargo",
            package["name"],
            package.get("version"),
            package.get("source", "workspace"),
            False,
        )
        for package in parsed.get("package", [])
        if isinstance(package, dict) and isinstance(package.get("name"), str)
    ]


def build_report(root: Path) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"{root} is not a repository directory")
    manifests = discover_manifests(root)
    dependencies = []
    errors = []
    for path in manifests:
        try:
            if path.name == "package-lock.json":
                entries = _npm(path)
            elif path.name.startswith("requirements"):
                entries = _requirements(path)
            elif path.name == "pyproject.toml":
                entries = _pyproject(path)
            elif path.name == "Cargo.lock":
                entries = _cargo(path)
            else:
                entries = []
            for entry in entries:
                entry["manifest"] = path.relative_to(root).as_posix()
            dependencies.extend(entries)
        except (
            OSError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
            tomllib.TOMLDecodeError,
        ) as error:
            errors.append(
                {"manifest": path.relative_to(root).as_posix(), "error": str(error)}
            )

    unique = {}
    for item in dependencies:
        key = (item["ecosystem"], item["name"], item["version"], item["manifest"])
        unique[key] = item
    dependencies = sorted(
        unique.values(),
        key=lambda item: (item["ecosystem"], item["name"], item["version"] or ""),
    )
    finding_counts: dict[str, int] = {}
    for item in dependencies:
        for finding in item["findings"]:
            finding_counts[finding] = finding_counts.get(finding, 0) + 1
    return {
        "schema_version": 1,
        "repository": ".",
        "manifests": [path.relative_to(root).as_posix() for path in manifests],
        "dependencies": dependencies,
        "errors": errors,
        "summary": {
            "dependencies": len(dependencies),
            "manifests": len(manifests),
            "findings": finding_counts,
            "parse_errors": len(errors),
        },
        "limitations": "Unknown license means the local manifest did not supply evidence; it is not a claim that the package is unlicensed.",
    }
