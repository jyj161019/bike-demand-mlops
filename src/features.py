"""데이터 로딩과 특성 생성.

학습(train.py)과 서비스(app/main.py)가 같은 코드로 특성을 만들도록 한 곳에 모아 둔다.
학습과 서비스의 전처리가 달라지는 것을 막기 위함이다.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

# 원본 CSV의 14개 열 순서 (UCI Seoul Bike Sharing Demand)
# 열 이름에 °C 같은 특수문자가 있어 인코딩에 따라 이름이 깨지므로 위치로 매핑한다.
RAW_COLUMNS = [
    "date",
    "rented_count",          # 정답 (시간당 대여 대수)
    "hour",
    "temperature",           # °C
    "humidity",              # %
    "wind_speed",            # m/s
    "visibility",            # 10m 단위 (사용 안 함)
    "dew_point",             # °C (사용 안 함)
    "solar_radiation",       # MJ/m2 (사용 안 함)
    "rainfall",              # mm
    "snowfall",              # cm
    "season",                # 월에서 계산 가능하므로 사용 안 함
    "holiday",               # "Holiday" / "No Holiday"
    "functioning_day",       # "Yes" / "No" (운영하지 않은 날)
]

TARGET = "rented_count"

# 서비스 입력으로 받는 값 + 날짜에서 계산하는 값
# 시정, 이슬점, 일사량은 사용자가 예측 시점에 알기 어려워 입력에서 제외했다.
FEATURES = [
    "hour",
    "temperature",
    "humidity",
    "wind_speed",
    "rainfall",
    "snowfall",
    "is_holiday",
    "month",
    "weekday",
    "is_weekend",
]


def load_raw(path: str) -> pd.DataFrame:
    """원본 CSV를 읽고 열 이름과 형식을 정리한다."""
    last_error: Exception | None = None
    for enc in ("utf-8", "cp949", "latin-1"):
        try:
            df = pd.read_csv(path, encoding=enc)
            break
        except UnicodeDecodeError as e:
            last_error = e
    else:
        raise ValueError(f"CSV 인코딩을 읽을 수 없습니다: {path}") from last_error

    if df.shape[1] != len(RAW_COLUMNS):
        raise ValueError(
            f"열 개수가 다릅니다. 기대 {len(RAW_COLUMNS)}개, 실제 {df.shape[1]}개: {list(df.columns)}"
        )
    df.columns = RAW_COLUMNS
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")
    df["is_holiday"] = (df["holiday"].str.strip() == "Holiday").astype(int)
    return df


def add_date_features(df: pd.DataFrame) -> pd.DataFrame:
    """date 열에서 월, 요일, 주말 여부를 만든다."""
    out = df.copy()
    d = pd.to_datetime(out["date"])
    out["month"] = d.dt.month
    out["weekday"] = d.dt.weekday          # 월=0 ... 일=6
    out["is_weekend"] = (out["weekday"] >= 5).astype(int)
    return out


def build_single_row(
    day: date,
    hour: int,
    temperature: float,
    humidity: float,
    wind_speed: float,
    rainfall: float,
    snowfall: float,
    is_holiday: bool,
) -> pd.DataFrame:
    """서비스 요청 1건을 모델 입력 형식(1행 DataFrame)으로 만든다."""
    row = pd.DataFrame(
        [
            {
                "date": pd.Timestamp(day),
                "hour": hour,
                "temperature": temperature,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "rainfall": rainfall,
                "snowfall": snowfall,
                "is_holiday": int(is_holiday),
            }
        ]
    )
    return add_date_features(row)[FEATURES]
