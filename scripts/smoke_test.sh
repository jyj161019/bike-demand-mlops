#!/usr/bin/env bash
# 배포된 서비스에 정상 입력과 잘못된 입력을 보내고, 기대한 상태 코드가 오는지 확인한다.
# 사용법: ./scripts/smoke_test.sh <API주소>
#   예: ./scripts/smoke_test.sh https://bike-demand-api.onrender.com
set -uo pipefail
cd "$(dirname "$0")/.."

BASE="${1:-http://localhost:8000}"
BASE="${BASE%/}"
PASS=0; FAIL=0

# Render 무료 서비스는 15분간 요청이 없으면 꺼지고, 다음 요청 때 다시 켜지는 데 최대 1분 정도 걸린다.
# 그래서 /health 가 응답할 때까지 최대 120초 기다린 뒤 검사한다.
echo "== 서비스 응답 대기: $BASE/health"
START=$(date +%s)
CODE=000
while [ $(( $(date +%s) - START )) -lt 120 ]; do
  CODE="$(curl -s -o /dev/null -m 30 -w '%{http_code}' "$BASE/health")"
  [ "$CODE" = "200" ] || [ "$CODE" = "503" ] && break
  sleep 5
done
echo "응답 코드 $CODE, 대기 $(( $(date +%s) - START ))초"
if [ "$CODE" != "200" ]; then
  echo "[FAIL] 서비스가 정상 상태가 아닙니다."
  curl -s -m 30 "$BASE/health"; echo
  exit 1
fi

echo "== $BASE/health";  curl -s -m 30 "$BASE/health"; echo
echo "== $BASE/model";   curl -s -m 30 "$BASE/model";  echo
echo

check() {  # check <이름> <기대코드> <json파일>
  local name="$1" expect="$2" file="$3"
  local out code body
  out="$(curl -s -m 30 -w '\n%{http_code}' -X POST "$BASE/predict" \
          -H 'Content-Type: application/json' --data @"$file")"
  code="$(echo "$out" | tail -n1)"
  body="$(echo "$out" | sed '$d')"
  if [ "$code" = "$expect" ]; then
    echo "[PASS] $name  (기대 $expect, 실제 $code)  입력=$(tr -d '\n' < "$file")  응답=$body"; PASS=$((PASS+1))
  else
    echo "[FAIL] $name  (기대 $expect, 실제 $code)  입력=$(tr -d '\n' < "$file")  응답=$body"; FAIL=$((FAIL+1))
  fi
}

for f in tests/requests/ok_*.json;  do check "$(basename "$f")" 200 "$f"; done
for f in tests/requests/bad_*.json; do check "$(basename "$f")" 422 "$f"; done

echo
echo "합계: PASS $PASS / FAIL $FAIL"
[ "$FAIL" -eq 0 ]
