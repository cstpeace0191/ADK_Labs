"""강의노트 Part 11 슬라이드 116: pytest 에서 AgentEvaluator 로 CI 품질 게이트 (Gemini 키 필요).

실행 (part11_eval_deploy 폴더):  pytest -q tests
"""
import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
load_dotenv(HERE.parent / ".env")

from google.adk.evaluation.agent_evaluator import AgentEvaluator  # noqa: E402

_key = os.getenv("GOOGLE_API_KEY", "")
needs_llm = pytest.mark.skipif(
    not ((_key and not _key.startswith("<")) or os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").upper() == "TRUE"),
    reason="Gemini 인증 정보가 없음")


@needs_llm
@pytest.mark.asyncio
async def test_weather_evalset():
    await AgentEvaluator.evaluate(
        agent_module="weather_agent",
        eval_dataset_file_path_or_dir=str(HERE / "weather_agent" / "weather.evalset.json"),
        num_runs=1,
    )


def test_tool_unit():
    """LLM 없이 도구 자체를 단위 테스트한다."""
    from weather_agent.agent import get_weather
    assert get_weather("서울")["status"] == "success"
    assert get_weather("제주")["status"] == "error"
