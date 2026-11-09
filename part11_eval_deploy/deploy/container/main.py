"""강의노트 Part 11 슬라이드 113(Cloud Run 개념)·117~118(서버와 상태)·120 'gcloud run deploy': main.py + requirements.txt + Dockerfile.

이 파일이 '서버'다: get_fast_api_app() 이 adk api_server 와 같은 ADK HTTP API(/list-apps, 세션, /run_sse)를 만든다.
agents_dir = 이 파일이 있는 폴더 → 같은 폴더의 weather_agent/ 를 서빙한다.

빌드 폴더 준비 + 배포:  bash deploy/deploy_gcloud_run.sh         (part11_eval_deploy 폴더에서, DRY_RUN=1 이면 명령만 출력)
로컬 확인 (키 불필요):  python -m pytest tests/test_container_app.py -q
로컬 실행:              빌드 폴더(deploy/.build_gcloud)에서 python main.py → http://localhost:8080/docs
"""
import os

import uvicorn
from google.adk.cli.fast_api import get_fast_api_app

AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))  # 이 폴더 안의 weather_agent/ 를 서빙

app = get_fast_api_app(
    agents_dir=AGENTS_DIR,
    # 운영: postgresql+asyncpg://... (Cloud SQL) 또는 agentengine://<id> / 로컬: sqlite
    # 주의: 기본값 sqlite 파일은 '컨테이너 안'에 생긴다 → Cloud Run 인스턴스마다 따로 있고 교체되면 사라진다.
    #       Cloud Run 에서는 반드시 SESSION_SERVICE_URI 를 바깥 DB 로 지정한다 (슬라이드 117~118, run_server_state.py).
    session_service_uri=os.getenv("SESSION_SERVICE_URI", "sqlite+aiosqlite:///./sessions.db"),
    allow_origins=["*"],
    web=os.getenv("SERVE_WEB_UI", "false").lower() == "true",  # 데모만 true
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
