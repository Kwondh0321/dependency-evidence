# 변경 기록 / Changelog

이 프로젝트는 [Keep a Changelog](https://keepachangelog.com/)의 구조와 [Semantic Versioning](https://semver.org/) 원칙을 따릅니다.

## [Unreleased]

### 한국어

- PEP 508 `name @ URL` 직접 참조를 정확히 파싱하고 HTTPS 직접 참조도 검토 대상으로 표시합니다.
- 존재하지 않는 저장소와 잘못된 `pyproject.toml` 자료형을 명확히 거부합니다.
- 보고서의 루트 경로를 이식 가능하게 만들고 심볼릭 링크 매니페스트를 건너뜁니다.
- 출력 오류와 누락 입력이 성공으로 처리되지 않도록 종료 동작을 강화했습니다.

### English

- Correctly parses PEP 508 `name @ URL` references and flags HTTPS direct references for review.
- Rejects missing repositories and malformed `pyproject.toml` field types explicitly.
- Keeps report roots portable and skips symlinked manifests.
- Ensures output errors and missing inputs cannot be reported as success.

### 검증 / Validation

- 5 regression tests, Ruff checks, clean wheel build and install, installed scan example, missing-directory failure, and GitHub Actions.

[Unreleased]: https://github.com/Kwondh0321/dependency-evidence/compare/v0.1.0...HEAD
