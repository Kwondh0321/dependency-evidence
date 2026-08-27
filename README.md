# DependencyEvidence

한국어 | [English](README.en.md) | [변경 기록 / Changelog](CHANGELOG.md)

DependencyEvidence는 외부 레지스트리에 접속하지 않고 의존성 버전·출처·직접성·라이선스 근거를 정리합니다. npm 잠금 파일, Python requirements와 `pyproject.toml`, Cargo 잠금 파일을 지원합니다.

## 설치 및 사용

```bash
git clone https://github.com/Kwondh0321/dependency-evidence.git
cd dependency-evidence
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install .
dependency-evidence . --output dependency-evidence.json
dependency-evidence . --fail-on unpinned
```

## 발견 항목

- `unpinned-version`: 여러 버전을 허용하거나 버전이 없음
- `mutable-or-insecure-source`: 직접 URL 또는 Git 출처에 추가 검토가 필요함
- `license-unknown`: 로컬 메타데이터에 라이선스 식별자가 없음

라이선스 미확인은 “라이선스가 없다”는 결론이 아니라 로컬 근거가 부족하다는 뜻입니다. 규정 준수 판단 전에는 패키지 내용, 레지스트리 정보, SPDX SBOM, 예외와 라이선스 호환성을 별도로 검토하세요.

## 개발

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

## 라이선스

MIT
