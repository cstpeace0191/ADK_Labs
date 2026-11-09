"""단위 테스트: LLM 없이 도구 함수와 에이전트 구성을 검사한다 (agents-cli 의 tests/unit 과 같은 역할).

오프라인 모드(AGENT_OFFLINE=1)로 돌려 네트워크 상태와 무관하게 통과하게 했다.
실행: python -m pytest tests/unit -q
"""
import importlib

import pytest


@pytest.fixture(scope="module")
def agent_mod():
    import os

    os.environ["AGENT_OFFLINE"] = "1"
    import app.agent as m

    return importlib.reload(m)  # OFFLINE 값을 다시 읽게 한다


def test_root_agent_configuration(agent_mod):
    names = [t.__name__ for t in agent_mod.root_agent.tools]
    assert names == ["geocode", "get_weather", "get_current_time"]
    assert agent_mod.root_agent.name == "agents_cli_workflow"  # manifest 의 root_agent_name
    assert agent_mod.app.name == "app"                          # manifest 의 app_name


def test_geocode_known_city(agent_mod):
    res = agent_mod.geocode("Seoul")
    assert res["status"] == "success"
    assert isinstance(res["latitude"], float) and isinstance(res["longitude"], float)


def test_geocode_unknown_city(agent_mod):
    assert agent_mod.geocode("없는도시123")["status"] == "error"


def test_get_weather_with_location(agent_mod):
    text = agent_mod.get_weather(location="서울")
    assert "Weather for" in text and "Temperature:" in text


def test_get_weather_needs_input(agent_mod):
    assert "알려주세요" in agent_mod.get_weather()


def test_get_current_time_with_coordinates(agent_mod):
    text = agent_mod.get_current_time(latitude=35.6762, longitude=139.6503, location="Tokyo")
    assert "current local time" in text
