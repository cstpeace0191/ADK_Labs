"""부록 A5 타입 힌트 · Pydantic (강의노트 _20261111f 슬라이드 188–190) — LLM 없이 실행.

실행: python a5_types_pydantic.py [schema|pydantic|validate|typing|all]
  schema   : 타입 힌트 · docstring → LLM이 보는 함수 선언 (188, 본문 77)
  pydantic : BaseModel 인자의 스키마($defs · minimum)와 dict → 모델 변환 (189)
  validate : 잘못된 인자 — 기본은 dict 그대로 전달, 실험 기능을 켜면 LLM에 오류 반환 (189)
  typing   : ADK 콜백 타입(BeforeModelCallback) 읽기 (190)

pydantic · validate는 '대본대로 답하는 모델'(before_model_callback)로 Runner의 실제
도구 호출 루프를 돌린다. Gemini를 부르지 않는다.
"""
import asyncio
import json
import logging
import sys
import typing
import warnings

import _path  # noqa: F401
from _helpers import run_turn, scripted_model, section
from common.config import MODEL
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from pydantic import BaseModel, Field


# ---------------------------------------------------------------- schema (188)
def get_weather(city: str, unit: str = "celsius") -> dict:
    """도시의 현재 날씨를 조회한다.

    Args:
      city: 도시 이름
      unit: 온도 단위
    """
    return {"status": "success", "city": city, "temp": 21, "unit": unit}


def declaration(func) -> dict:
    return FunctionTool(func)._get_declaration().model_dump(exclude_none=True)  # noqa: SLF001


def demo_schema() -> None:
    section("schema: 타입 힌트가 곧 도구 스키마 (슬라이드 188)")
    print(json.dumps(declaration(get_weather), ensure_ascii=False, indent=2))
    print("  → 이름=함수 이름, 설명=docstring, 인자=타입 힌트, 기본값이 있는 unit은 required에서 빠짐")


# ---------------------------------------------------------------- pydantic (189)
class Order(BaseModel):
    item: str
    qty: int = Field(ge=1)


def place_order(order: Order) -> dict:
    """주문을 접수한다."""
    kind = type(order).__name__
    print(f"    [place_order] 받은 인자 타입: {kind}")
    if not isinstance(order, Order):  # 변환 실패 대비 (슬라이드 189의 '주의')
        return {"status": "error", "error_message": f"주문 형식 오류: {order}"}
    return {"status": "success", "qty": order.qty}


def order_agent(args: dict) -> LlmAgent:
    return LlmAgent(name="order_agent", model=MODEL, tools=[place_order],
                    before_model_callback=scripted_model([("place_order", args), "주문 처리를 마쳤습니다."]))


async def demo_pydantic() -> None:
    section("pydantic: BaseModel 인자 → 스키마 · 변환 (슬라이드 189)")
    params = declaration(place_order).get("parameters_json_schema")
    print("  스키마 $defs.Order:", json.dumps(params["$defs"]["Order"], ensure_ascii=False))
    await run_turn(order_agent({"order": {"item": "SKU-1", "qty": 2}}), "SKU-1 두 개 주문")


async def demo_validate() -> None:
    from google.adk.features import FeatureName, override_feature_enabled
    section("validate: 잘못된 인자 qty=0 (슬라이드 189)")
    logging.getLogger("google_adk").setLevel(logging.ERROR)  # 변환 실패 경고 로그는 숨긴다
    bad = {"order": {"item": "SKU-1", "qty": 0}}
    print("  ① 기본 동작: 변환 실패 → 원래 dict가 함수로 넘어간다")
    await run_turn(order_agent(bad), "SKU-1 0개 주문")
    print("  ② FUNCTION_TOOL_ARG_VALIDATION 켬 (ADK 2.14 실험 기능): 함수 대신 오류를 LLM에 돌려준다")
    print("     (환경 변수로는 ADK_ENABLE_FUNCTION_TOOL_ARG_VALIDATION=1)")
    warnings.filterwarnings("ignore", message=r"\[EXPERIMENTAL\]")
    override_feature_enabled(FeatureName.FUNCTION_TOOL_ARG_VALIDATION, True)
    try:
        await run_turn(order_agent(bad), "SKU-1 0개 주문")
    finally:
        override_feature_enabled(FeatureName.FUNCTION_TOOL_ARG_VALIDATION, False)


# ---------------------------------------------------------------- typing (190)
def demo_typing() -> None:
    from google.adk.agents import llm_agent
    section("typing: ADK 소스의 콜백 타입 읽기 (슬라이드 190)")
    import re

    def short(t) -> str:  # 'google.adk.models.llm_response.LlmResponse' → 'LlmResponse'
        return re.sub(r"(?:[a-z_]+\.)+([A-Z]\w*)", r"\1", str(t)).replace("typing.", "")

    single = llm_agent._SingleBeforeModelCallback  # noqa: SLF001
    args, ret = typing.get_args(single)
    names = ", ".join(getattr(a, "__name__", short(a)) for a in args)
    print(f"  _SingleBeforeModelCallback = Callable[[{names}], {short(ret)}]")
    print(f"  BeforeModelCallback = Union[_SingleBeforeModelCallback, list[_SingleBeforeModelCallback]]"
          f"  (실제 인자 수: {len(typing.get_args(llm_agent.BeforeModelCallback))})")
    print("  → (컨텍스트, LlmRequest)를 받아 LlmResponse나 None을 돌려주는 함수,")
    print("    sync든 async(Awaitable)든, 하나든 리스트든 된다")
    print("  (ADK 2.6.3은 첫 인자 타입이 CallbackContext, 2.14는 Context — 쓰는 법은 같다)")


DEMOS = {"schema": demo_schema, "pydantic": demo_pydantic, "validate": demo_validate, "typing": demo_typing}


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    names = list(DEMOS) if which == "all" else [which]
    for n in names:
        if n not in DEMOS:
            sys.exit(f"알 수 없는 항목: {n} (가능: {', '.join(DEMOS)}, all)")
        r = DEMOS[n]()
        if asyncio.iscoroutine(r):
            asyncio.run(r)


if __name__ == "__main__":
    main()
