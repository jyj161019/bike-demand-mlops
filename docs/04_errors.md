# 4. 오류 조사와 복구

클라우드에서 **실제로 겪은** 오류만 적습니다. 실패와 복구 후 성공은 모두 [logs/run_log.md](../logs/run_log.md) 에 순서대로 남아 있고, 각 줄의 출력 로그와 Actions 실행 페이지로 확인할 수 있습니다.

## 오류 1: TODO(제목)

| 항목 | 내용 |
|---|---|
| 발생 시각 | |
| 단계 / 실행 위치 | (예: Actions train #2, Render 배포) |
| 오류 메시지 | (핵심 한두 줄) |
| 영향 | |
| 원인 | |
| 원인 확인 방법 | (어떤 로그/화면으로 확인했는지) |
| 수정 내용 | (설정 변경 or 코드 변경 + 커밋) |
| 재실행 결과 | 같은 작업, 같은 입력으로 재실행 → 결과 |
| 기록 | 실패: `logs/runs/...` / Render 배포 화면, 성공: `logs/runs/...` |

## 오류 2: TODO

(위 표 복사)

---

<!--
작성 후 이 주석은 지워도 됩니다.

실제로 자주 나는 오류 예 (겪은 것만 기록):
- Actions 결과 커밋 단계에서 "Permission ... denied to github-actions[bot]" (403)
  → 저장소 Settings → Actions → General → Workflow permissions 가 Read 로 제한됨
- Render 배포 실패 "Exited with status 1" / health check 실패 → models/v1 이 아직 없는데 배포됨 (train 전에 Render 연결)
- smoke 첫 요청이 오래 걸리거나 실패 → 무료 인스턴스가 꺼져 있다가 켜지는 중

안전하게 재현해서 기록하는 방법 (공용 자원·보안 설정은 건드리지 않음):
1) 같은 버전으로 다시 학습: Actions train 에 이미 있는 v1 입력
   → run_log 에 "실패(exit 1) 이미 있는 버전" 자동 기록 → 새 버전(v2)으로 재실행 → 성공
2) 없는 모델 버전으로 배포: render.yaml 의 MODEL_DIR 를 /work/models/v999 로 바꿔 푸시
   → Render 배포가 헬스 체크(503 model_not_loaded)에서 실패, 이전 배포는 계속 동작
   → Render Events/Logs 화면 캡처 → v1 로 되돌려 푸시 → 배포 성공 → Actions smoke 재실행
3) 잘못된 주소로 검사: Actions smoke 에 서비스 주소 오타 입력 → 실패 기록 → 올바른 주소로 재실행
-->
