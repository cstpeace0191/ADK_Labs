# 강의노트 §11 슬라이드 119: gcloud run deploy --source . 가 이 Dockerfile 로 Cloud Build 에서 이미지를 만든다.
# 빌드 폴더는 ../deploy_gcloud_run.sh 가 준비한다 (main.py · requirements.txt · Dockerfile + weather_agent/).
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 루트가 아닌 사용자로 실행 (ADK Cloud Run 문서 예시와 같은 방식)
RUN adduser --disabled-password --gecos "" myuser
COPY --chown=myuser:myuser . .
USER myuser

# 키는 이미지에 넣지 않는다 → --set-secrets(Secret Manager) 또는 Vertex AI 서비스 계정
# Cloud Run 이 PORT 를 넣어 준다 (기본 8080)
ENV PORT=8080
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
