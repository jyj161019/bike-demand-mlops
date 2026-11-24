"""따릉이 시간당 대여량 예측 API (FastAPI).

환경 변수:
    MODEL_DIR  모델 폴더 (model.joblib, metadata.json 이 있는 곳). 기본 /models/current
    LOG_DIR    예측 요청 기록 폴더. 기본 /logs
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
import datetime as dt
from datetime import datetime, timezone
from pathlib import Path

import joblib
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.features import build_single_row

MODEL_DIR = Path(os.getenv("MODEL_DIR", "/models/current"))
LOG_DIR = Path(os.getenv("LOG_DIR", "/logs"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("bike-api")

app = FastAPI(title="Bike Demand API", version="1.0")

state: dict = {"model": None, "metadata": None, "load_error": None}


def load_model() -> None:
    """서버 시작 시 모델을 읽는다. 실패해도 서버는 뜨고 /health 에서 원인을 알려준다."""
    try:
        state["model"] = joblib.load(MODEL_DIR / "model.joblib")
        state["metadata"] = json.loads((MODEL_DIR / "metadata.json").read_text("utf-8"))
        state["load_error"] = None
        log.info("model loaded: %s from %s", state["metadata"]["model_version"], MODEL_DIR)
    except Exception as e:  # 경로 오류, 파일 없음, 버전 불일치 등
        state["model"] = None
        state["load_error"] = f"{type(e).__name__}: {e}"
        log.error("model load failed (MODEL_DIR=%s): %s", MODEL_DIR, state["load_error"])


load_model()


class PredictRequest(BaseModel):
    """입력 범위는 학습 데이터 범위를 조금 넓힌 값이다. 벗어나면 422로 거절한다."""

    date: dt.date = Field(..., description="예측할 날짜 (YYYY-MM-DD)")
    hour: int = Field(..., ge=0, le=23, description="시 (0~23)")
    temperature: float = Field(..., ge=-30, le=45, description="기온 °C")
    humidity: float = Field(..., ge=0, le=100, description="습도 %")
    wind_speed: float = Field(..., ge=0, le=20, description="풍속 m/s")
    rainfall: float = Field(0, ge=0, le=100, description="강수량 mm")
    snowfall: float = Field(0, ge=0, le=50, description="적설 cm")
    is_holiday: bool = Field(False, description="공휴일 여부")

    model_config = {
        "extra": "forbid",  # 모르는 필드가 오면 거절 (오타 방지)
        "json_schema_extra": {
            "example": {
                "date": "2018-10-05",
                "hour": 18,
                "temperature": 17.5,
                "humidity": 55,
                "wind_speed": 1.8,
                "rainfall": 0,
                "snowfall": 0,
                "is_holiday": False,
            }
        },
    }


def write_log(record: dict) -> None:
    log.info(json.dumps(record, ensure_ascii=False))
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_DIR / "predictions.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as e:
        log.warning("log file write failed: %s", e)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(x) for x in e["loc"][1:]), "message": e["msg"]} for e in exc.errors()
    ]
    write_log(
        {
            "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "path": request.url.path,
            "status": 422,
            "errors": errors,
        }
    )
    return JSONResponse(status_code=422, content={"error": "잘못된 입력", "details": errors})


@app.get("/health")
def health():
    if state["model"] is None:
        return JSONResponse(
            status_code=503,
            content={"status": "model_not_loaded", "model_dir": str(MODEL_DIR), "error": state["load_error"]},
        )
    return {"status": "ok", "model_version": state["metadata"]["model_version"]}


@app.get("/model")
def model_info():
    if state["metadata"] is None:
        raise HTTPException(status_code=503, detail=state["load_error"])
    m = state["metadata"]
    return {k: m[k] for k in ("model_version", "git_commit", "data_sha256", "features", "target_unit", "scikit_learn")}


@app.post("/predict")
def predict(req: PredictRequest):
    if state["model"] is None:
        raise HTTPException(status_code=503, detail=f"모델이 로드되지 않았습니다: {state['load_error']}")

    start = time.perf_counter()
    fields = req.model_dump()
    fields["day"] = fields.pop("date")
    X = build_single_row(**fields)
    pred = max(0.0, float(state["model"].predict(X)[0]))
    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

    response = {
        "request_id": uuid.uuid4().hex[:12],
        "predicted_rented_count": round(pred),
        "unit": "대/시간",
        "model_version": state["metadata"]["model_version"],
    }
    write_log(
        {
            "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "path": "/predict",
            "status": 200,
            "input": req.model_dump(mode="json"),
            **response,
            "elapsed_ms": elapsed_ms,
        }
    )
    return response
