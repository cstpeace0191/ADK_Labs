# memory_agent — MemoryService 기반 장기 기억 회상 에이전트

단일 세션 범위를 넘어 과거 여러 대화 세션에서 나눈 주요 사실을 벡터/의미 기반으로 저장하고 필요할 때 회상하는 **Memory Service** 실습 에이전트입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent`
- **핵심 컴포넌트**:
  - `InMemoryMemoryService`: 에이전트 대화에서 추출된 기억(Memory)을 관리하는 인메모리 저장소
  - `load_memory`: Runner가 사용자 질의와 관련된 과거 기억을 검색하여 에이전트 컨텍스트에 사전 주입
- **실습 시나리오**:
  1. 세션 1: "나 땅콩 알레르기 있어" (메모리 서비스에 저장)
  2. 세션 2: "내 알레르기 기억해? 저녁 메뉴 추천해줘" (새 세션이지만 과거 기억을 자동 검색하여 땅콩 없는 메뉴 추천)

---

## 2. 실행 방법

`part07_context` 폴더에서 실행합니다:

```bash
cd part07_context
uv run run_memory.py
```


