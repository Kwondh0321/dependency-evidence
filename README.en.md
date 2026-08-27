# DependencyEvidence

[한국어](README.md) | English

DependencyEvidence creates an offline report of dependency versions, sources, directness, and local license evidence. It supports npm lock files, Python requirements and `pyproject.toml`, and Cargo lock files without querying external registries.

## Install and run

```bash
git clone https://github.com/Kwondh0321/dependency-evidence.git
cd dependency-evidence
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install .
dependency-evidence . --output dependency-evidence.json
dependency-evidence . --fail-on unpinned
```

## Findings

- `unpinned-version`: no version or a mutable version range
- `mutable-or-insecure-source`: a direct URL or Git source needs additional review
- `license-unknown`: local metadata contains no license identifier

`--fail-on` accepts `none`, `unpinned`, `unknown-license`, or `any`. Unsupported or malformed manifests are reported as parse errors and produce status 1; invalid repository paths or output failures produce status 2.

An unknown license means that local evidence is insufficient, not that a package is unlicensed. Review package contents, registry metadata, SPDX SBOMs, exceptions, and compatibility before making a compliance decision.

## Development

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

Licensed under MIT.
