# 5. 권한, 비용, 자원 정리

## 권한

| 주체 | 권한 | 범위 |
|---|---|---|
| GitHub Actions 워크플로 | `contents: write` (GITHUB_TOKEN) | 이 저장소에 결과 커밋만. 실행마다 자동 발급·만료되는 토큰이라 저장소에 비밀값 없음 |
| Render GitHub 앱 | 저장소 읽기 | 설치할 때 "Only select repositories" 로 이 저장소만 허용 |
| Render 서비스 | 공개 HTTPS 주소 | 누구나 /predict 호출 가능 (개인정보를 받거나 저장하지 않음) |

- 비밀번호, API 키, 토큰을 코드·로그·커밋에 넣지 않았습니다. 이 서비스는 비밀값이 필요 없습니다.
- `.pem`, `.env`, 자격 증명 파일은 `.gitignore` 로 커밋을 막았습니다.

## 비용

| 자원 | 요금 | 제한 |
|---|---|---|
| GitHub Actions | 공개 저장소 표준 러너 무료 | 실행 1회 약 1~2분 |
| Render 웹 서비스 | free 인스턴스, 카드 등록 없음 | 월 750 인스턴스 시간, 15분 동안 요청이 없으면 꺼짐(다시 켜질 때 최대 약 1분), 파일 시스템은 재시작 시 초기화 |

카드를 등록하지 않았으므로 요금이 청구될 수 없습니다.
실제 사용량: TODO (Render 대시보드 → Billing/Usage 의 인스턴스 시간, 빌드 분)

## 정리

| 자원 | 처리 | 이유 |
|---|---|---|
| Render 서비스 | TODO: 채점 기간까지 유지 → TODO(날짜)에 Settings → Delete Web Service | 채점자가 주소로 확인할 수 있도록. 무료라 유지 비용 없음 |
| Render GitHub 앱 권한 | 서비스 삭제 후 GitHub Settings → Applications 에서 제거 | |
| GitHub 저장소 | 유지 (제출물) | |
| Actions 실행 기록 | 유지 (GitHub 기본 보관 기간 후 자동 삭제) | 필요한 기록은 logs/ 에 커밋되어 있음 |

정리 후 확인: TODO (Render 대시보드에 서비스가 없는 화면 / 남긴 자원과 이유)
