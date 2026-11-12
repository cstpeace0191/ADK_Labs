"""Part 12 관측성 실습 전체 실행 (LLM 없이). 오프라인 스크립트 4개를 실행하고 결과를 요약한다.

실행: python run_all.py          # 출력까지 모두 보기
      python run_all.py --quiet  # 요약만 보기
obs5(OTLP) · obs6(OpenInference)는 선택 패키지가 있을 때만 의미 있는 출력을 낸다 (없으면 설치 안내만 출력).
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = [["obs1_span_tree.py", "all"], ["obs2_content_capture.py", "all"], ["obs3_metrics.py", "all"],
           ["obs4_openmetrics.py", "text"], ["obs5_otlp_export.py", "--selftest"], ["obs6_openinference.py", "all"]]


def main() -> int:
    try:  # Windows 콘솔 한글 출력
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    quiet = "--quiet" in sys.argv
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    results = []
    for cmd in SCRIPTS:
        proc = subprocess.run([sys.executable, *cmd], cwd=HERE, env=env, capture_output=True, text=True,
                              encoding="utf-8")
        optional = "📦" in proc.stdout
        results.append((cmd[0], proc.returncode, optional))
        if not quiet or proc.returncode != 0:
            print(proc.stdout[-4000:], proc.stderr[-2000:] if proc.returncode else "", sep="\n")
    print("\n=== Part 12 관측성 실습 요약 ===")
    for name, code, optional in results:
        tag = "OK  " if code == 0 else "FAIL"
        print(f"  {tag} {name}" + ("  (선택 패키지 없음 → 설치 안내만 출력)" if optional else ""))
    return 0 if all(code == 0 for _, code, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
