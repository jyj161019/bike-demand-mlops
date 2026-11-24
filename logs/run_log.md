# 실행 기록

scripts/run_and_log.sh 가 자동으로 추가합니다. 시각은 KST입니다.

| 시각 | 단계 | 결과 | 소요 | 커밋 | 모델 버전 | 실행 위치 | 명령 | 출력 로그 |
|---|---|---|---|---|---|---|---|---|
| 2026-11-24 19:09:40 | train | 성공 | 3s | f18db3a | v1 | GitHub Actions train #2 | `python -m src.train --data data/raw/SeoulBikeData.csv --version v1` | [logs/runs/20261124-190940_train.log](../logs/runs/20261124-190940_train.log) |
| 2026-11-24 19:26:18 | smoke | 성공 | 6s | 46e632b | v1 | GitHub Actions smoke #1 | `./scripts/smoke_test.sh https://bike-demand-api-uv3r.onrender.com` | [logs/runs/20261124-192618_smoke.log](../logs/runs/20261124-192618_smoke.log) |
