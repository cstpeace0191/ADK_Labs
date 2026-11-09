#!/usr/bin/env bash
# 강의노트 Part 11 슬라이드 120: gcloud run deploy — 내 컨테이너(main.py + Dockerfile)로 Cloud Run 에 배포
#                 슬라이드 121: gcloud run deploy 는 Cloud Run 전용 (Agent Runtime 은 deploy_agent_runtime.sh / deploy_agent_runtime_sdk.py)
# part11_eval_deploy 폴더에서 실행한다.
#
#   export GOOGLE_CLOUD_PROJECT=<project-id>
#   export GOOGLE_CLOUD_LOCATION=asia-northeast3
#   export SESSION_SERVICE_URI="postgresql+asyncpg://user:pass@host:5432/adk"   # 바깥 DB (없으면 컨테이너 안 sqlite → 유실)
#   # 모델 인증: 둘 중 하나
#   export API_KEY_SECRET=gemini-api-key        # AI Studio 키를 Secret Manager 에 둔 이름 (--set-secrets)
#   export USE_VERTEXAI=TRUE                    # 또는 Vertex AI: 키 없이 서비스 계정 권한으로 호출
#   DRY_RUN=1 bash deploy/deploy_gcloud_run.sh  # 빌드 폴더와 명령만 확인 (gcloud 호출 안 함)
#
# 빌드 폴더(deploy/.build_gcloud/) = container/{main.py,Dockerfile,requirements.txt} + weather_agent/
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PART10="$(dirname "$HERE")"
BUILD="$HERE/.build_gcloud"
SERVICE="${SERVICE_NAME:-weather-agent}"

# ① 빌드 폴더 준비
rm -rf "$BUILD"
mkdir -p "$BUILD"
cp "$HERE/container/main.py" "$HERE/container/Dockerfile" "$HERE/container/requirements.txt" "$BUILD/"
cp "$HERE/container/.dockerignore" "$BUILD/" 2>/dev/null || true
cp -r "$PART10/weather_agent" "$BUILD/weather_agent"
rm -rf "$BUILD/weather_agent/__pycache__" "$BUILD/weather_agent/.adk"
echo "빌드 폴더: $BUILD"
(cd "$BUILD" && find . -type f | sort | sed 's/^/  /')

# ② 배포 명령 조립
PROJECT="${GOOGLE_CLOUD_PROJECT:-<project-id>}"
REGION="${GOOGLE_CLOUD_LOCATION:-<region>}"
ENV_VARS="GOOGLE_CLOUD_PROJECT=$PROJECT,GOOGLE_CLOUD_LOCATION=$REGION"
if [[ "${USE_VERTEXAI:-FALSE}" == "TRUE" ]]; then
  ENV_VARS+=",GOOGLE_GENAI_USE_VERTEXAI=TRUE"
else
  ENV_VARS+=",GOOGLE_GENAI_USE_VERTEXAI=FALSE"
fi
if [[ -n "${SESSION_SERVICE_URI:-}" ]]; then
  ENV_VARS+=",SESSION_SERVICE_URI=$SESSION_SERVICE_URI"
else
  echo "⚠ SESSION_SERVICE_URI 미지정: 컨테이너 안 sqlite → 인스턴스가 바뀌면 대화 유실 (run_server_state.py 참고)" >&2
fi

CMD=(gcloud run deploy "$SERVICE" --source .
     --region="$REGION" --project="$PROJECT"
     --no-allow-unauthenticated
     --set-env-vars="$ENV_VARS")
if [[ "${USE_VERTEXAI:-FALSE}" != "TRUE" ]]; then
  CMD+=(--set-secrets="GOOGLE_API_KEY=${API_KEY_SECRET:-gemini-api-key}:latest")
fi

echo "실행할 명령 (빌드 폴더에서):"
echo "  ${CMD[*]}"

if [[ "${DRY_RUN:-0}" == "1" ]]; then
  echo "DRY_RUN=1 → 배포하지 않음"
  exit 0
fi
: "${GOOGLE_CLOUD_PROJECT:?GOOGLE_CLOUD_PROJECT 필요}"
: "${GOOGLE_CLOUD_LOCATION:?GOOGLE_CLOUD_LOCATION 필요}"

# ③ 배포: --source . → Cloud Build 가 Dockerfile 로 이미지 빌드 → Artifact Registry → 새 리비전
(cd "$BUILD" && "${CMD[@]}")

# ④ 호출 확인 (비공개 서비스 → ID 토큰)
URL=$(gcloud run services describe "$SERVICE" --region="$REGION" --project="$PROJECT" --format='value(status.url)')
TOKEN=$(gcloud auth print-identity-token)
echo "서비스 URL: $URL"
curl -s -H "Authorization: Bearer $TOKEN" "$URL/list-apps"; echo
