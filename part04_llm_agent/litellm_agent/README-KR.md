# litellm_agent — 다중 모델 공급자 연동 에이전트

LiteLLM 라이브러리를 통해 Gemini뿐만 아니라 Anthropic Claude 등 이종 LLM 공급자의 모델을 유연하게 교체하여 사용할 수 있도록 구현한 에이전트입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent`
- **동작 방식**:
  - `ANTHROPIC_API_KEY` 환경 변수가 존재하면 `LiteLlm` 어댑터를 통해 `claude-sonnet-5-5` 모델로 연결합니다.
  - 별도 키가 없으면 기본 `ADK_MODEL`(Gemini)로 안전하게 fallback 처리됩니다.
  ```python
  if os.getenv("ANTHROPIC_API_KEY"):
      from google.adk.models.lite_llm import LiteLlm
      model = LiteLlm(model=os.getenv("LITELLM_MODEL", "anthropic/claude-sonnet-5-5"))
  else:
      model = os.getenv("ADK_MODEL", "gemini-flash-latest")
  ```

---

## 2. 실행 방법

`part04_llm_agent` 폴더에서 실행합니다:

```bash
cd part04_llm_agent
uv run run_with_runner.py litellm
```


