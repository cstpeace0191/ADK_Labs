"""부록 A 실습 전체 실행 (LLM 없이). 각 스크립트를 'all'로 실행하고 성공 여부를 요약한다.

실행: python run_all.py          # 출력까지 모두 보기
      python run_all.py --quiet  # 요약만 보기
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = ["a1_async_basics.py", "a2_concurrency.py", "a3_generators.py", "a4_context_managers.py",
           "a5_types_pydantic.py", "a6_extend_adk.py", "a7_runner.py"]


def main() -> int:
    quiet = "--quiet" in sys.argv
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    results = []
    for name in SCRIPTS:
        proc = subprocess.run([sys.executable, name, "all"], cwd=HERE, env=env,
                              capture_output=quiet, text=True, encoding="utf-8")
        results.append((name, proc.returncode))
        if quiet and proc.returncode != 0:
            print(proc.stdout[-2000:], proc.stderr[-2000:], sep="\n")
    print("\n=== 부록 A 실습 요약 ===")
    for name, code in results:
        print(f"  {'OK  ' if code == 0 else 'FAIL'} {name}")
    return 0 if all(code == 0 for _, code in results) else 1


if __name__ == "__main__":
    sys.exit(main())
