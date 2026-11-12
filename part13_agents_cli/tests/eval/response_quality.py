"""로컬 LLM-as-judge: eval_config.yaml 의 custom_response_quality.

instance 에는 prompt / response / reference / agent_data(전체 트레이스)가 들어온다.
구조화 출력(response_schema)으로 {"score", "explanation"} JSON 을 강제해 파싱 실패를 막는다.
"""
import os
import threading
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

# agents-cli 는 이 파일을 자기 프로세스 안에서 실행한다 → 실습 루트 .env(키, ADK_MODEL)를 직접 읽는다
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

_local = threading.local()
JUDGE_MODEL = os.getenv("JUDGE_MODEL", os.getenv("ADK_MODEL", "gemini-3.8-flash"))


class _Verdict(BaseModel):
    score: int  # 1~5
    explanation: str


def _client() -> genai.Client:
    """채점은 여러 스레드에서 돌므로 스레드마다 클라이언트를 하나씩 만든다."""
    if getattr(_local, "client", None) is None:
        _local.client = genai.Client()
    return _local.client


def evaluate(instance):
    reference = instance.get("reference")
    rubric = "에이전트의 최종 응답을 정확성·관련성·명확성 기준으로 1~5점(5가 최고)으로 채점하라."
    if reference:
        rubric += " 아래 기대 답과 사실이 어긋나면 감점하라."
    prompt = (f"너는 AI 비서 응답을 채점하는 QA 평가자다. {rubric}\n"
              f"사용자 질문: {instance.get('prompt', '')}\n"
              f"최종 응답: {instance.get('response', '')}\n")
    if reference:
        prompt += f"기대 답: {reference}\n"
    prompt += f"전체 트레이스: {instance.get('agent_data', '')}\n"

    resp = _client().models.generate_content(
        model=JUDGE_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,  # 채점은 결정적으로
            response_mime_type="application/json",
            response_schema=_Verdict,
        ),
    )
    verdict = resp.parsed
    if verdict is None:
        return {"score": 0, "explanation": resp.text or ""}
    return {"score": max(1, min(5, verdict.score)), "explanation": verdict.explanation}
