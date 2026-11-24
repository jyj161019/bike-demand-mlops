# 서비스 이미지 (Render에서 빌드·실행)
# 학습(GitHub Actions)과 같은 python 3.11, 같은 requirements.txt 를 써서
# 학습 환경과 서비스 환경의 라이브러리 버전이 달라 모델을 못 읽는 문제를 막는다.
FROM python:3.11-slim

WORKDIR /work
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    MODEL_DIR=/work/models/v1 \
    LOG_DIR=/tmp/logs

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY app ./app
COPY models ./models

EXPOSE 8000
# Render는 PORT 환경 변수로 포트를 알려준다. 로컬 실행 시에는 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
