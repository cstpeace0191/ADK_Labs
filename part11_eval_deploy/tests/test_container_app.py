"""강의노트 Part 11 슬라이드 125: gcloud run deploy 로 올릴 컨테이너 서버(main.py)를 배포 전에 로컬에서 검증한다 (🟢 키 불필요).

deploy_gcloud_run.sh 와 같은 빌드 폴더(main.py + weather_agent/)를 임시로 만들고,
main.py 의 FastAPI 앱을 TestClient 로 띄워 ADK HTTP API 가 살아 있는지 본다. LLM 은 부르지 않는다.

실행 (part11_eval_deploy 폴더):  python -m pytest tests/test_container_app.py -q
"""
import importlib.util
import shutil
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PART10 = Path(__file__).resolve().parents[1]
CONTAINER = PART10 / "deploy" / "container"


@pytest.fixture()
def built_app(tmp_path, monkeypatch):
    build = tmp_path / "build"
    build.mkdir()
    for name in ("main.py", "Dockerfile", "requirements.txt"):
        shutil.copy(CONTAINER / name, build / name)
    shutil.copytree(PART10 / "weather_agent", build / "weather_agent",
                    ignore=shutil.ignore_patterns("__pycache__", ".adk"))
    # 운영이면 Cloud SQL 등 바깥 DB. 테스트는 임시 폴더의 sqlite 파일.
    monkeypatch.setenv("SESSION_SERVICE_URI", f"sqlite+aiosqlite:///{(tmp_path / 'sessions.db').as_posix()}")
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy-key-not-used")
    monkeypatch.chdir(build)
    monkeypatch.syspath_prepend(str(build))
    spec = importlib.util.spec_from_file_location("container_main", build / "main.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    yield build, module.app
    for k in [k for k in sys.modules if k == "weather_agent" or k.startswith("weather_agent.")]:
        del sys.modules[k]


def test_dockerfile_runs_main_app():
    text = (CONTAINER / "Dockerfile").read_text(encoding="utf-8")
    assert "uvicorn main:app" in text and "${PORT}" in text   # Cloud Run 이 주는 PORT 로 main.py 의 app 을 띄운다
    code = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    assert not any("GOOGLE_API_KEY" in ln for ln in code)   # 키를 이미지에 굽지 않는다 (--set-secrets 로 주입)


def test_server_lists_agent_and_creates_session(built_app):
    _, app = built_app
    with TestClient(app) as client:
        r = client.get("/list-apps")
        assert r.status_code == 200
        assert "weather_agent" in r.json()

        # ADK 2.6.3: 본문이 곧 초기 State (dict)
        r = client.post("/apps/weather_agent/users/u1/sessions/s1", json={"city": "서울"})
        assert r.status_code == 200
        assert r.json()["id"] == "s1"

        r = client.get("/apps/weather_agent/users/u1/sessions/s1")
        assert r.status_code == 200
        assert r.json()["state"]["city"] == "서울"   # SESSION_SERVICE_URI 의 DB 에 저장됐다
