# 따릉이 시간당 대여량 예측 API (클라우드 MLOps 실습)

날씨와 날짜를 입력하면 그 시간의 서울 공공자전거 대여 대수(대/시간)를 예측하는 API입니다.
공개 데이터로 모델을 직접 학습했습니다. 학습과 검사는 **GitHub Actions**(클라우드 러너)에서 하고, 서비스는 **Render**(클라우드 웹 서비스, Docker)에서 실행합니다.

| 문서 | 내용 |
|---|---|
| [docs/01_data_model.md](docs/01_data_model.md) | 서비스 목적, 데이터 출처·처리 기준·분리, 모델 |
| [docs/02_cloud.md](docs/02_cloud.md) | 클라우드 구성과 선택 이유, 설정, 입력→결과 확인 |
| [docs/03_evaluation.md](docs/03_evaluation.md) | 평가 기준·결과·해석, 서비스 동작 검사, 한계 |
| [docs/04_errors.md](docs/04_errors.md) | 클라우드 오류 재현, 원인, 수정, 재실행 |
| [docs/05_cost_cleanup.md](docs/05_cost_cleanup.md) | 권한, 비용, 자원 정리 |
| [logs/run_log.md](logs/run_log.md) | 단계별 실행 기록 (자동 생성) |

서비스 주소: https://bike-demand-api-uv3r.onrender.com (API 문서: [/docs](https://bike-demand-api-uv3r.onrender.com/docs))

> 무료 인스턴스라 15분간 요청이 없으면 꺼집니다. 첫 요청은 50초 이상 걸릴 수 있습니다.

## 저장소 구성

```
src/features.py              데이터 로딩, 특성 생성 (학습과 서비스가 함께 사용)
src/train.py                 학습 + 기준 방법 비교 평가 + 모델/메타데이터 저장
src/compare.py               두 버전의 평가 결과 비교 (재실행 확인)
app/main.py                  FastAPI 서비스 (/health, /model, /predict), 입력 검사, 요청 기록
Dockerfile                   서비스 이미지 (python 3.11, 라이브러리 버전 고정)
render.yaml                  Render 서비스 설정 (서비스할 모델 버전, 헬스 체크, 자동 배포 범위)
requirements.txt             라이브러리 버전
.github/workflows/train.yml  클라우드 학습 → 모델·기록 커밋
.github/workflows/smoke.yml  배포된 서비스 검사 → 기록 커밋
scripts/run_and_log.sh       명령 실행 + logs/run_log.md 기록
scripts/smoke_test.sh        정상/잘못된 입력 검사
tests/requests/              검사용 입력 (ok_* 정상 4개, bad_* 잘못된 입력 7개)
data/raw/                    원본 데이터 (CC BY 4.0)
models/<버전>/               모델, 메타데이터, 평가 결과
logs/                        실행 기록
```

## 실행 환경

| 구분 | 환경 |
|---|---|
| 학습·검사 | GitHub Actions `ubuntu-latest`, python 3.11, requirements.txt |
| 서비스 | Render 웹 서비스 free 인스턴스, singapore 리전, Docker `python:3.11-slim` |
| 라이브러리 | pandas 2.2.3, numpy 2.1.3, scikit-learn 1.5.2, fastapi 0.115.6, uvicorn 0.32.1, pydantic 2.10.3 |
| 필요한 계정 | GitHub, Render (GitHub로 가입, 카드 등록 없음) |

## 실행 절차

처음부터 다시 실행할 때도 이 순서를 따릅니다. 모든 단계는 브라우저에서 할 수 있고, 결과는 `logs/run_log.md` 에 자동으로 커밋됩니다.

### 1. 저장소 만들기

GitHub에서 **Public** 저장소를 만들고 이 폴더를 올립니다. (`data/raw/SeoulBikeData.csv` 포함)

```bash
git init && git add . && git commit -m "초기 구성"
git branch -M main
git remote add origin https://github.com/<계정>/bike-demand-mlops.git
git push -u origin main
```

> Actions가 결과를 main에 커밋하므로, 로컬에서 수정하기 전에는 항상 `git pull` 을 먼저 합니다.

### 2. 클라우드 학습

저장소 → **Actions** → **train** → **Run workflow** → version `v1` → 실행

- 끝나면 실행 페이지 Summary에 평가 표가 나오고, `models/v1/` 과 `logs/` 가 자동으로 커밋됩니다.

### 3. 서비스 배포

1. https://render.com → **GitHub로 가입** (Render 앱 권한은 이 저장소만 허용)
2. **New → Blueprint** → 이 저장소 선택 → `render.yaml` 내용 확인 → **Apply**
3. 배포가 끝나면 나오는 주소(`https://bike-demand-api-xxxx.onrender.com`)를 위 "서비스 주소" 에 적습니다.
4. 브라우저에서 `<주소>/docs` → `POST /predict` → Try it out → Execute

### 4. 서비스 검사

Actions → **smoke** → Run workflow → url 에 서비스 주소 입력 → 실행

### 5. 새 환경에서 재실행 확인

Actions 러너는 실행할 때마다 새로 만들어지는 머신이라, 같은 코드를 처음부터 다시 실행하는 것과 같습니다.

1. Actions → train → version `v1-rerun`, compare_with `v1` → 실행 → `compare` 단계에서 평가 결과가 같은지 확인
2. Render → 서비스 → **Manual Deploy → Clear build cache & deploy** (캐시 없이 새로 빌드)
3. Actions → smoke → url 입력, step `rerun-smoke` → 실행

**재실행 결과 (2026-11-24):** 새 러너에서 다시 학습한 `v1-rerun`(train #4)의 평가 결과가 v1과 완전히 같았고, 빌드 캐시를 지운 재배포 후 smoke #2도 PASS 11 / FAIL 0, 같은 입력에 같은 예측값이 나왔습니다. 자세한 내용은 [docs/03_evaluation.md](docs/03_evaluation.md#재실행-확인)에 있습니다.

### 6. 서비스할 모델 버전 바꾸기

`render.yaml` 의 `MODEL_DIR` 을 `/work/models/<새 버전>` 으로 바꿔 커밋·푸시하면 자동으로 다시 배포됩니다.
새 모델을 못 읽으면 헬스 체크가 실패해 배포가 중단되고, 이전 버전이 계속 서비스됩니다.

### 7. 로컬 실행 (선택)

```bash
pip install -r requirements.txt
python -m src.train --version local-test
MODEL_DIR=models/local-test LOG_DIR=logs/app uvicorn app.main:app --port 8000
./scripts/smoke_test.sh http://localhost:8000
```

### 8. 자원 정리

[docs/05_cost_cleanup.md](docs/05_cost_cleanup.md) 참고.

## API

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | /health | 200 정상 / 503 모델 로드 실패 (원인 포함) |
| GET | /model | 모델 버전, Git 커밋, 데이터 해시, 입력 특성 |
| POST | /predict | 예측. 범위를 벗어난 입력은 422 와 필드별 이유 반환 |
| GET | /docs | API 문서와 직접 요청 화면 |

| 입력 | 형식 | 범위 |
|---|---|---|
| date | YYYY-MM-DD | 필수 |
| hour | 정수 | 0~23, 필수 |
| temperature | °C | -30~45, 필수 |
| humidity | % | 0~100, 필수 |
| wind_speed | m/s | 0~20, 필수 |
| rainfall | mm | 0~100, 기본 0 |
| snowfall | cm | 0~50, 기본 0 |
| is_holiday | true/false | 기본 false |

요청 예:

```json
{"date": "2018-10-05", "hour": 18, "temperature": 17.5, "humidity": 55,
 "wind_speed": 1.8, "rainfall": 0, "snowfall": 0, "is_holiday": false}
```

## 참고 자료와 직접 구현 범위

- 데이터: UCI Seoul Bike Sharing Demand (CC BY 4.0) — [data/raw/README.md](data/raw/README.md)
- 문서: scikit-learn `HistGradientBoostingRegressor`, FastAPI, Pydantic, GitHub Actions, Render Blueprint
- 직접 구현: 이 저장소의 코드·워크플로·스크립트 전체 (데이터 처리, 기준 방법, 학습·평가, API, 검사, 실행 기록)
- AI 도구 사용: Claude(Anthropic)를 코드·문서 초안 작성과 오류 원인 확인에 참고했습니다. 클라우드 설정, 실행, 결과 확인, 오류 재현·수정, 기록은 직접 수행했습니다.
