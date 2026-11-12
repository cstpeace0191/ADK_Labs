"""부록 A2 동시성 제어 (강의노트 _20261111f 슬라이드 179–181) — LLM 없이 실행.

실행: python a2_concurrency.py [lock|semaphore|event|gather|taskgroup|timeout|contextvars|all]
  lock        : await를 사이에 둔 '읽기 → 수정 → 쓰기'의 경쟁 상태와 asyncio.Lock (179)
  semaphore   : 동시에 최대 N개 — LLM 요청 한도 지키기 (179)
  event       : ADK 이벤트 큐의 '저장될 때까지 기다리기' 핸드셰이크 재현 (179)
  gather      : ADK 병렬 도구 호출 패턴 — 실패 시 남은 Task를 직접 cancel (180)
  taskgroup   : TaskGroup은 자동 취소 + ExceptionGroup, except* (180)
  timeout     : asyncio.timeout()과 TimeoutError (181)
  contextvars : Task마다 따로 보이는 값 (181)
"""
import asyncio
import contextvars
import sys

import _path  # noqa: F401
from _helpers import Clock, section


# ---------------------------------------------------------------- lock (179)
async def demo_lock() -> None:
    section("lock: 협력적 멀티태스킹에도 락이 필요한 경우 (슬라이드 179)")

    async def add(shared: dict, lock: asyncio.Lock | None) -> None:
        async def body():
            value = shared["count"]  # 읽기
            await asyncio.sleep(0)  # await 사이에 다른 코루틴이 끼어든다
            shared["count"] = value + 1  # 쓰기
        if lock:
            async with lock:
                await body()
        else:
            await body()

    for lock in (None, asyncio.Lock()):
        shared = {"count": 0}
        await asyncio.gather(*(add(shared, lock) for _ in range(100)))
        label = "Lock 사용" if lock else "Lock 없음"
        print(f"  {label}: 100번 더했는데 count = {shared['count']}")


# ---------------------------------------------------------------- semaphore (179)
async def demo_semaphore() -> None:
    section("semaphore: 동시에 최대 3개만 (슬라이드 179)")
    sem = asyncio.Semaphore(3)
    running, peak = 0, 0

    async def ask(i: int) -> str:
        nonlocal running, peak
        async with sem:
            running += 1
            peak = max(peak, running)
            await asyncio.sleep(0.05)  # LLM 호출을 흉내
            running -= 1
            return f"답{i}"

    answers = await asyncio.gather(*(ask(i) for i in range(10)))
    print(f"  요청 10개 처리 → {len(answers)}개 응답, 동시에 실행된 최대 개수 = {peak}")


# ---------------------------------------------------------------- event (179)
async def demo_event() -> None:
    section("event: '세션에 저장될 때까지 기다린다' 핸드셰이크 (슬라이드 179 · ADK InvocationContext)")
    log = Clock()
    queue: asyncio.Queue = asyncio.Queue()
    session: list[str] = []

    async def agent() -> None:  # 생산자: 이벤트를 넣고 저장될 때까지 기다린다
        for name in ("function_call", "function_response", "최종 응답"):
            done = asyncio.Event()
            await queue.put((name, done))
            log(f"agent : {name} 넣음 → 저장 대기")
            await done.wait()
            log(f"agent : {name} 저장 확인 → 다음 진행")
        await queue.put((None, None))

    async def runner() -> None:  # 소비자: 꺼내서 저장하고 신호를 준다
        while True:
            name, done = await queue.get()
            if name is None:
                break
            await asyncio.sleep(0.05)  # append_event(DB 쓰기)를 흉내
            session.append(name)
            log(f"runner: {name} 세션에 저장 · yield")
            done.set()

    await asyncio.gather(agent(), runner())
    print(f"  세션: {session}")


# ---------------------------------------------------------------- gather (180)
async def run_tool(name: str, delay: float, fail: bool = False) -> str:
    try:
        await asyncio.sleep(delay)
        if fail:
            raise RuntimeError(f"{name} 실패")
        return f"{name} 결과"
    except asyncio.CancelledError:
        print(f"  {name}: 취소됨")
        raise


async def demo_gather() -> None:
    section("gather: ADK 병렬 도구 호출 패턴 (슬라이드 180 · flows/llm_flows/functions.py 요약)")
    function_calls = [("search", 0.3, False), ("weather", 0.05, True), ("calendar", 0.3, False)]
    tasks = [asyncio.create_task(run_tool(*fc)) for fc in function_calls]
    try:
        print("  결과:", await asyncio.gather(*tasks))
    except Exception as e:
        still = sum(1 for t in tasks if not t.done())
        print(f"  gather가 첫 예외를 던짐: {e!r} — 나머지는 아직 실행 중: {still}개")
        for t in tasks:
            if not t.done():
                t.cancel()  # 남은 도구 취소
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f"  정리 후 모두 끝남: {all(t.done() for t in tasks)}")


# ---------------------------------------------------------------- taskgroup (180)
async def demo_taskgroup() -> None:
    section("taskgroup: 자동 취소 + ExceptionGroup (슬라이드 180 · ADK ParallelAgent)")
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(run_tool("researcher", 0.3))
            tg.create_task(run_tool("writer", 0.05, fail=True))
            tg.create_task(run_tool("reviewer", 0.05, fail=True))
    except* RuntimeError as eg:
        print(f"  except* RuntimeError: {[str(e) for e in eg.exceptions]}")


# ---------------------------------------------------------------- timeout (181)
async def demo_timeout() -> None:
    section("timeout: asyncio.timeout() (슬라이드 181)")

    async def call_llm(sec: float) -> str:
        await asyncio.sleep(sec)
        return "응답"

    for sec in (0.05, 0.5):
        try:
            async with asyncio.timeout(0.2):
                r = await call_llm(sec)
            print(f"  {sec}s 걸리는 호출 → {r}")
        except TimeoutError:
            print(f"  {sec}s 걸리는 호출 → TimeoutError (블록 바깥에서 잡음) → {{'status': 'timeout'}}")


# ---------------------------------------------------------------- contextvars (181)
request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


def log_line(msg: str) -> None:  # 인자로 받지 않아도 현재 Task의 값을 본다
    print(f"  [rid={request_id.get()}] {msg}")


async def handle(rid: str) -> None:
    request_id.set(rid)
    await asyncio.sleep(0.01)
    log_line("모델 호출")
    await asyncio.sleep(0.01)
    log_line("도구 호출")


async def demo_contextvars() -> None:
    section("contextvars: Task마다 따로 보이는 값 (슬라이드 181)")
    await asyncio.gather(handle("req-A"), handle("req-B"))
    log_line("main Task의 값은 그대로")


DEMOS = {"lock": demo_lock, "semaphore": demo_semaphore, "event": demo_event, "gather": demo_gather,
         "taskgroup": demo_taskgroup, "timeout": demo_timeout, "contextvars": demo_contextvars}


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    names = list(DEMOS) if which == "all" else [which]
    for n in names:
        if n not in DEMOS:
            sys.exit(f"알 수 없는 항목: {n} (가능: {', '.join(DEMOS)}, all)")
        asyncio.run(DEMOS[n]())


if __name__ == "__main__":
    main()
