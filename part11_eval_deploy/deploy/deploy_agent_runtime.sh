#!/usr/bin/env bash
# 강의노트 Part 11 슬라이드 114(Agent Runtime 개념)·118(누가 책임지나)·121(배포 경로)·122(Agent Runtime 배포와 트리거): Agent Runtime(관리형) 배포 + Pub/Sub 트리거 Cloud Run 배포 예시
set -euo pipefail
: "${GOOGLE_CLOUD_PROJECT:?}"; : "${GOOGLE_CLOUD_LOCATION:?}"

case "${1:-runtime}" in
  runtime)
    # 관리형 세션·Memory Bank, 실행 최대 7일
    adk deploy agent_engine --project="$GOOGLE_CLOUD_PROJECT" \
      --region="$GOOGLE_CLOUD_LOCATION" --display_name="weather-agent" ./weather_agent
    ;;
  pubsub)
    # Cloud Scheduler(0 9 * * 1-5) → Pub/Sub push → Cloud Run /trigger/pubsub (이벤트마다 새 세션)
    # --trigger_sources 만 주고 OIDC 설정을 빼면 시작 시 ValueError
    # 주의: --trigger_oidc_* 플래그는 google-adk 2.13 이상에 있다 (실습 환경 2.6.3 에는 없음 → pip install -U google-adk)
    : "${AUDIENCE:?push 구독의 OIDC audience}"; : "${PUSH_SA:?push 서비스 계정 이메일}"
    adk deploy cloud_run --project="$GOOGLE_CLOUD_PROJECT" --region="$GOOGLE_CLOUD_LOCATION" \
      --service_name=tick-agent \
      --trigger_sources="pubsub" \
      --trigger_oidc_audience="$AUDIENCE" \
      --trigger_oidc_service_accounts="$PUSH_SA" ./weather_agent
    ;;
esac
