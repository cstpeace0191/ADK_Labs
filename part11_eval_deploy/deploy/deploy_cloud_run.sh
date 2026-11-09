#!/usr/bin/env bash
# 강의노트 Part 11 슬라이드 113(Cloud Run 개념)·117~118(서버와 상태)·119(Cloud Run 배포) — part11_eval_deploy 폴더에서 실행
#
# Cloud Run 은 '서버'만 돌린다. '상태'(세션·기억·파일)는 내가 바깥 저장소에 연결해야 한다.
# URI 를 하나도 주지 않으면 Cloud Run 을 감지(K_SERVICE)해 메모리 세션을 쓴다 → 인스턴스 교체·0개 축소 때 대화 유실.
# 확인: python run_server_state.py  (키 없이 실행)
#
#   export GOOGLE_CLOUD_PROJECT=<project-id>
#   export GOOGLE_CLOUD_LOCATION=asia-northeast3
#   # 상태 저장소 (권장: 최소 SESSION_URI)
#   export SESSION_URI="postgresql+asyncpg://user:pass@host:5432/adk"   # Cloud SQL 등 (비동기 드라이버 형식)
#   #   또는 혼합 구성: export SESSION_URI="agentengine://<agent-runtime-id>"  # 서버는 Cloud Run, 세션만 Agent Runtime 관리형
#   export ARTIFACT_URI="gs://<bucket>"                                  # 파일·이미지 (선택)
#   export MEMORY_URI="agentengine://<agent-runtime-id>"                 # 장기 기억 = Memory Bank (선택)
#   WITH_UI=1 bash deploy/deploy_cloud_run.sh                            # 개발 UI 포함(데모용)
set -euo pipefail
: "${GOOGLE_CLOUD_PROJECT:?GOOGLE_CLOUD_PROJECT 필요}"
: "${GOOGLE_CLOUD_LOCATION:?GOOGLE_CLOUD_LOCATION 필요}"

# 이전 이름(SESSION_DB_URI)도 받는다
SESSION_URI="${SESSION_URI:-${SESSION_DB_URI:-}}"

ARGS=(--project="$GOOGLE_CLOUD_PROJECT" --region="$GOOGLE_CLOUD_LOCATION" --service_name=weather-agent)
if [[ -n "$SESSION_URI" ]]; then
  ARGS+=(--session_service_uri="$SESSION_URI")
else
  echo "⚠ SESSION_URI 미지정: 메모리 세션으로 배포된다 (인스턴스가 바뀌면 대화 유실)" >&2
fi
if [[ -n "${ARTIFACT_URI:-}" ]]; then ARGS+=(--artifact_service_uri="$ARTIFACT_URI"); fi
if [[ -n "${MEMORY_URI:-}" ]]; then ARGS+=(--memory_service_uri="$MEMORY_URI"); fi
if [[ "${WITH_UI:-0}" == "1" ]]; then ARGS+=(--with_ui); fi   # 데모용, 운영은 끄기

adk deploy cloud_run "${ARGS[@]}" ./weather_agent
