"""Command-line interface for DependencyEvidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import build_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="의존성의 버전·출처·라이선스 근거를 오프라인으로 수집합니다.")
    parser.add_argument("repository", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fail-on", choices=("none", "unpinned", "unknown-license", "any"), default="none")
    args = parser.parse_args(argv)
    try:
        report = build_report(args.repository)
    except (OSError, ValueError) as error:
        print(f"dependency-evidence: {error}", file=sys.stderr)
        return 2
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(f"DependencyEvidence: 의존성 {report['summary']['dependencies']}개, 검토 항목 {sum(report['summary']['findings'].values())}개")
    findings = report["summary"]["findings"]
    failed = (
        report["errors"]
        or args.fail_on == "any" and bool(findings)
        or args.fail_on == "unpinned" and bool(findings.get("unpinned-version"))
        or args.fail_on == "unknown-license" and bool(findings.get("license-unknown"))
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
