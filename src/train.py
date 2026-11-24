"""학습 + 평가 스크립트.

사용 예:
    python -m src.train --data data/raw/SeoulBikeData.csv --version v1

결과 (models/<version>/):
    model.joblib          학습된 모델
    metadata.json         모델 버전, 데이터 해시, Git 커밋, 라이브러리 버전, 설정
    metrics.json          기준 방법 / 모델 평가 수치
    evaluation.md         평가 표 (README나 보고서에 그대로 인용 가능)
    test_predictions.csv  평가 자료 전체의 실제값과 예측값
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.features import FEATURES, TARGET, add_date_features, load_raw

RANDOM_STATE = 42
MODEL_PARAMS = {
    "loss": "poisson",       # 대여 대수는 0 이상의 개수라 poisson 손실 사용
    "max_iter": 300,
    "learning_rate": 0.05,
    "random_state": RANDOM_STATE,
}


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--", "src", "app", "requirements.txt", "Dockerfile"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return out + ("-dirty" if dirty else "")
    except Exception:
        return "unknown"


def metrics(y_true, y_pred) -> dict:
    return {
        "MAE": round(float(mean_absolute_error(y_true, y_pred)), 2),
        "RMSE": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 2),
        "R2": round(float(r2_score(y_true, y_pred)), 4),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="data/raw/SeoulBikeData.csv")
    p.add_argument("--out-dir", default="models")
    p.add_argument("--version", default=None, help="모델 버전 이름 (기본: 날짜-시각)")
    p.add_argument("--test-start", default="2018-09-01", help="이 날짜부터 평가 자료로 사용")
    args = p.parse_args()

    version = args.version or datetime.now().strftime("v%Y%m%d-%H%M")
    out = Path(args.out_dir) / version
    if out.exists():
        raise SystemExit(f"이미 있는 버전입니다: {out}  (--version 을 바꿔 주세요)")

    # 1) 데이터 로딩과 점검 --------------------------------------------------
    df = load_raw(args.data)
    data_check = {
        "rows_raw": int(len(df)),
        "missing_values": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated(subset=["date", "hour"]).sum()),
        "rows_non_functioning_day": int((df["functioning_day"].str.strip() == "No").sum()),
        "date_min": str(df["date"].min().date()),
        "date_max": str(df["date"].max().date()),
    }
    # 운영하지 않은 날은 정답이 항상 0이라 수요가 아니므로 제외
    df = df[df["functioning_day"].str.strip() == "Yes"].copy()
    df = df.dropna(subset=FEATURES[:6] + [TARGET])
    df = add_date_features(df)
    data_check["rows_used"] = int(len(df))

    # 2) 시간 기준 분리 (미래 데이터가 학습에 섞이지 않도록) ---------------------
    test_start = pd.Timestamp(args.test_start)
    train = df[df["date"] < test_start]
    test = df[df["date"] >= test_start]
    split = {
        "method": "time-based",
        "train_period": f"{train['date'].min().date()} ~ {train['date'].max().date()}",
        "test_period": f"{test['date'].min().date()} ~ {test['date'].max().date()}",
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
    }

    X_train, y_train = train[FEATURES], train[TARGET]
    X_test, y_test = test[FEATURES], test[TARGET]

    # 3) 기준 방법: 학습 기간의 (시간대, 주말 여부)별 평균 ---------------------
    baseline_table = train.groupby(["hour", "is_weekend"])[TARGET].mean()
    base_pred = (
        test.set_index(["hour", "is_weekend"]).index.map(baseline_table).to_numpy(dtype=float)
    )

    # 4) 모델 학습 ------------------------------------------------------------
    model = HistGradientBoostingRegressor(**MODEL_PARAMS)
    model.fit(X_train, y_train)
    model_pred = np.clip(model.predict(X_test), 0, None)

    # 5) 평가 -----------------------------------------------------------------
    result = test[["date", "hour", "temperature", "rainfall", "is_holiday", TARGET]].copy()
    result["pred_baseline"] = base_pred.round(1)
    result["pred_model"] = model_pred.round(1)
    result["abs_err_model"] = (result["pred_model"] - result[TARGET]).abs()

    overall = {
        "baseline": metrics(y_test, base_pred),
        "model": metrics(y_test, model_pred),
    }

    def group_mae(mask: pd.Series) -> dict:
        sub = result[mask]
        if len(sub) == 0:
            return {"rows": 0}
        return {
            "rows": int(len(sub)),
            "baseline_MAE": round(float((sub["pred_baseline"] - sub[TARGET]).abs().mean()), 2),
            "model_MAE": round(float(sub["abs_err_model"].mean()), 2),
        }

    groups = {
        "비 안 옴 (rainfall=0)": group_mae(result["rainfall"] == 0),
        "비 옴 (rainfall>0)": group_mae(result["rainfall"] > 0),
        "출퇴근 (7-9시, 17-19시)": group_mae(result["hour"].isin([7, 8, 9, 17, 18, 19])),
        "심야 (0-5시)": group_mae(result["hour"].between(0, 5)),
        "공휴일": group_mae(result["is_holiday"] == 1),
    }
    worst = result.sort_values("abs_err_model", ascending=False).head(10)

    # 6) 저장 -----------------------------------------------------------------
    out.mkdir(parents=True)
    joblib.dump(model, out / "model.joblib")
    result.to_csv(out / "test_predictions.csv", index=False, encoding="utf-8-sig")

    metadata = {
        "model_version": version,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "data_file": args.data,
        "data_sha256": sha256_of(args.data),
        "features": FEATURES,
        "target": TARGET,
        "target_unit": "대/시간",
        "model": "HistGradientBoostingRegressor",
        "model_params": MODEL_PARAMS,
        "split": split,
        "data_check": data_check,
        "python": platform.python_version(),
        "scikit_learn": sklearn.__version__,
        "pandas": pd.__version__,
    }
    (out / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), "utf-8")
    (out / "metrics.json").write_text(
        json.dumps({"overall": overall, "groups": groups}, ensure_ascii=False, indent=2), "utf-8"
    )

    lines = [
        f"# 평가 결과 ({version})",
        "",
        f"- 평가 자료: {split['test_period']}, {split['test_rows']}건 (시간 단위)",
        f"- 학습 자료: {split['train_period']}, {split['train_rows']}건",
        "- 단위: MAE·RMSE는 대/시간, R2는 단위 없음",
        "",
        "## 전체",
        "",
        "| 방법 | MAE | RMSE | R2 |",
        "|---|---|---|---|",
    ]
    for name, m in [("기준(시간대×주말 평균)", overall["baseline"]), ("모델", overall["model"])]:
        lines.append(f"| {name} | {m['MAE']} | {m['RMSE']} | {m['R2']} |")
    lines += ["", "## 조건별 MAE", "", "| 조건 | 건수 | 기준 MAE | 모델 MAE |", "|---|---|---|---|"]
    for name, g in groups.items():
        if g["rows"]:
            lines.append(f"| {name} | {g['rows']} | {g['baseline_MAE']} | {g['model_MAE']} |")
    lines += [
        "",
        "## 오차가 가장 큰 10건",
        "",
        "| 날짜 | 시 | 기온 | 강수 | 실제 | 모델 예측 | 오차 |",
        "|---|---|---|---|---|---|---|",
    ]
    for _, r in worst.iterrows():
        lines.append(
            f"| {r['date'].date()} | {r['hour']} | {r['temperature']} | {r['rainfall']} "
            f"| {r[TARGET]} | {r['pred_model']} | {r['abs_err_model']:.0f} |"
        )
    (out / "evaluation.md").write_text("\n".join(lines) + "\n", "utf-8")

    print(json.dumps({"model_version": version, "out_dir": str(out), **overall}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
