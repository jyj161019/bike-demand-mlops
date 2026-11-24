"""두 모델 버전의 평가 결과(metrics.json)를 비교한다. 재실행 확인용.

사용 예: python -m src.compare v1 v1-rerun
같으면 exit 0, 다르면 차이를 출력하고 exit 1.
"""
import json
import sys
from pathlib import Path


def flatten(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flatten(v, key + "."))
        else:
            out[key] = v
    return out


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("사용법: python -m src.compare <버전A> <버전B>")
    a, b = sys.argv[1], sys.argv[2]
    ma = flatten(json.loads(Path(f"models/{a}/metrics.json").read_text("utf-8")))
    mb = flatten(json.loads(Path(f"models/{b}/metrics.json").read_text("utf-8")))

    diffs = 0
    print(f"{'항목':<45} {a:>12} {b:>12}")
    for key in sorted(set(ma) | set(mb)):
        va, vb = ma.get(key), mb.get(key)
        mark = "" if va == vb else "  <-- 다름"
        diffs += va != vb
        print(f"{key:<45} {str(va):>12} {str(vb):>12}{mark}")

    print()
    if diffs:
        print(f"결과: {diffs}개 항목이 다릅니다.")
        sys.exit(1)
    print("결과: 평가 결과가 모두 같습니다 (재현됨).")


if __name__ == "__main__":
    main()
