# agents-cli 가 생성하는 Dockerfile 과 같은 구조.
# agents-cli deploy 는 이 파일로 **클라우드에서** 이미지를 빌드한다(로컬 Docker 불필요).
#   agent_runtime : 소스 번들 → Agent Runtime 관리형 빌더
#   cloud_run     : gcloud run deploy --source . → Cloud Build → Artifact Registry
FROM python:3.12-slim

# uv: 의존성 설치·실행 도구
COPY --from=ghcr.io/astral-sh/uv:0.8.13 /uv /uvx /bin/

WORKDIR /code
COPY ./pyproject.toml ./README.md ./uv.lock* ./
COPY ./app ./app

RUN uv sync --frozen || uv sync

ARG AGENT_VERSION=0.0.0
ENV AGENT_VERSION=${AGENT_VERSION}

EXPOSE 8080
CMD ["uv", "run", "uvicorn", "app.fast_api_app:app", "--host", "0.0.0.0", "--port", "8080"]
