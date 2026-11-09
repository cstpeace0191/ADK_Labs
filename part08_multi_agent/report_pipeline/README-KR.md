# report_pipeline — 파이프라인 컨테이너 기반 보고서 작성 시스템

ADK 1.x의 워크플로우 컨테이너 에이전트(`SequentialAgent`, `ParallelAgent`, `LoopAgent`)를 활용하여 다단계 보고서 작성 파이프라인을 구축한 실습입니다.

---

## 1. 동작 구조

- **엔트리포인트**: `agent.py`의 `root_agent`
- **파이프라인 흐름**:
  1. **`ParallelAgent` (자료 조사)**: 기술 동향 분석가와 시장 조사 분석가가 병렬로 정보 수집
  2. **`drafter` (초안 작성)**: 수집된 자료를 취합하여 첫 번째 보고서 초안 생성
  3. **`LoopAgent` (품질 검토 루프)**:
     - 검토자(`reviewer`)가 초안을 평가하고 합격 기준(Pass)에 도달할 때까지 수정 피드백 반복

---

## 2. 실행 방법

`part08_multi_agent` 폴더에서 실행합니다:

```bash
cd part08_multi_agent
uv run run_multi_agent.py pipeline
```


