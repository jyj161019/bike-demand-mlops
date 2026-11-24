# 5. 권한, 비용, 자원 정리

## 권한

| 주체 | 권한 | 범위 |
|---|---|---|
| GitHub Actions 워크플로 | `contents: write` (GITHUB_TOKEN) | 이 저장소에 결과 커밋만. 실행마다 자동 발급·만료되는 토큰이라 저장소에 비밀값 없음 |
| Render GitHub 앱 | 저장소 읽기 | 설치할 때 "Only select repositories" 로 `bike-demand-mlops` 만 허용 |
| Render 서비스 | 공개 HTTPS 주소 | 누구나 /predict 호출 가능. 개인정보를 받거나 저장하지 않음 |
| 로컬 PC 푸시 | GitHub 계정 `jyj161019` | 같은 PC에 저장된 다른 계정과 섞이지 않도록 저장소 주소에 계정을 지정 (`https://jyj161019@github.com/...`) |

- 비밀번호, API 키, 토큰을 코드·로그·커밋에 넣지 않았습니다. 이 서비스는 비밀값이 필요 없습니다.
- `.pem`, `.env`, 자격 증명 파일은 `.gitignore` 로 커밋을 막았습니다.

## 비용

| 자원 | 요금 | 제한 |
|---|---|---|
| GitHub Actions | 공개 저장소 표준 러너 무료 | 실행 1회 약 15~35초 |
| Render 웹 서비스 | Free 인스턴스, 카드 등록 없음 | 월 750 인스턴스 시간, 15분 동안 요청이 없으면 꺼짐(다시 켜질 때 약 50초 이상), 파일 시스템은 재시작 시 초기화 |

카드를 등록하지 않았으므로 요금이 청구될 수 없습니다.

실제 사용 (2026-11-24):

| 항목 | 사용량 |
|---|---|
| Actions 실행 | train 4회, smoke 2회 (모두 1분 미만) |
| Render 배포 | 3회 (최초 배포, v1-rerun 커밋 자동 배포, 캐시 삭제 후 수동 재배포) |
| 비용 | 0원 |

## 정리

| 자원 | 처리 | 이유 |
|---|---|---|
| Render 서비스 `bike-demand-api` | 채점 기간까지 유지 → 채점 후 Settings → Delete Web Service | 채점자가 주소로 직접 확인할 수 있도록. 무료이고 요청이 없으면 자동으로 꺼져 자원을 쓰지 않음 |
| Render Blueprint `bike-demand` | 서비스와 함께 삭제 | |
| Render GitHub 앱 권한 | 서비스 삭제 후 GitHub Settings → Applications → Installed GitHub Apps 에서 제거 | |
| GitHub 저장소 | 유지 | 제출물 |
| Actions 실행 기록 | 유지 (GitHub 기본 보관 기간 후 자동 삭제) | 필요한 기록은 `logs/` 에 커밋되어 있음 |
| 테스트용 모델 버전 `v1-rerun` | 저장소에 유지 | 재실행 증거. 서비스에는 사용하지 않음 (`render.yaml` 은 v1) |
