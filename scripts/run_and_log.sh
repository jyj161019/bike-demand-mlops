#!/usr/bin/env bash
# 명령을 실행하고 실행 기록을 logs/run_log.md 에 한 줄 추가한다.
# 전체 출력은 logs/runs/<시각>_<단계>.log 에 저장된다.
#
# 사용법:
#   ./scripts/run_and_log.sh <단계이름> <명령...>
# 예:
#   MODEL_VERSION=v1 ./scripts/run_and_log.sh train docker run --rm ... python -m src.train --version v1
set -uo pipefail

if [ $# -lt 2 ]; then
  echo "사용법: $0 <단계이름> <명령...>" >&2
  exit 2
fi

STEP="$1"; shift
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/logs/runs"

TS="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S')"
TS_FILE="$(TZ=Asia/Seoul date '+%Y%m%d-%H%M%S')"
LOG_FILE="logs/runs/${TS_FILE}_${STEP}.log"
COMMIT="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
if [ -n "$(git -C "$ROOT" status --porcelain -- src app Dockerfile requirements.txt 2>/dev/null)" ]; then
  COMMIT="${COMMIT}-dirty"
fi
HOST="${RUN_PLACE:-$(hostname)}"   # GitHub Actions 에서는 실행 번호/주소가 들어간다
CMD="$*"

{
  echo "# step=$STEP time=$TS host=$HOST commit=$COMMIT model_version=${MODEL_VERSION:--}"
  echo "# cmd=$CMD"
  [ -n "${RUN_URL:-}" ] && echo "# run_url=$RUN_URL"
  echo
} > "$ROOT/$LOG_FILE"

START=$(date +%s)
( cd "$ROOT" && "$@" ) 2>&1 | tee -a "$ROOT/$LOG_FILE"
EXIT=${PIPESTATUS[0]}
DUR=$(( $(date +%s) - START ))

if [ "$EXIT" -eq 0 ]; then RESULT="성공"; else RESULT="실패(exit $EXIT)"; fi
echo -e "\n# result=$RESULT duration=${DUR}s" >> "$ROOT/$LOG_FILE"

RUN_LOG="$ROOT/logs/run_log.md"
if [ ! -f "$RUN_LOG" ]; then
  {
    echo "# 실행 기록"
    echo
    echo "scripts/run_and_log.sh 가 자동으로 추가합니다. 시각은 KST입니다."
    echo
    echo "| 시각 | 단계 | 결과 | 소요 | 커밋 | 모델 버전 | 실행 위치 | 명령 | 출력 로그 |"
    echo "|---|---|---|---|---|---|---|---|---|"
  } > "$RUN_LOG"
fi
# 표가 깨지지 않도록 명령의 | 를 이스케이프
SAFE_CMD="${CMD//|/\\|}"
echo "| $TS | $STEP | $RESULT | ${DUR}s | $COMMIT | ${MODEL_VERSION:--} | $HOST | \`$SAFE_CMD\` | [$LOG_FILE](../$LOG_FILE) |" >> "$RUN_LOG"

echo "[run_and_log] $STEP → $RESULT (${DUR}s), 로그: $LOG_FILE"
exit "$EXIT"
