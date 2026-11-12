"""부록 A1 비동기 · asyncio (강의노트 _20261111f 슬라이드 165–178) — LLM 없이 실행.

실행: python a1_async_basics.py [sync|await|suspend|bytecode|loop|order|objects|run|all]
  sync     : 동기 vs 비동기 시간 비교 (165, 168)
  await    : await에서 멈춘 동안 다른 코루틴이 돈다 (169)
  suspend  : await는 언제 멈추나 — 바로 끝나는 코루틴은 양보하지 않는다 (170)
  bytecode : `answer = await call_llm(q)`의 바이트코드 (171)
  loop     : 이벤트 루프의 _ready · _scheduled 대기열 들여다보기 (172–174)
  order    : 스케줄링 순서 실험 (175)
  objects  : 코루틴 · Task · Future · TaskGroup (176)
  run      : asyncio.run()의 규칙 — 실행 중 루프 안에서 호출 불가, 남은 Task 취소 (178)
"""
import asyncio
import dis
import sys
import time
import warnings

import _path  # noqa: F401
from _helpers import Clock, section


# ---------------------------------------------------------------- sync (165, 168)
def fetch_sync(name: str, sec: float) -> str:
    time.sleep(sec)  # 스레드가 멈춤
    return name


async def fetch(name: str, sec: float) -> str:
    await asyncio.sleep(sec)  # 루프에 양보
    return name


async def demo_sync() -> None:
    section("sync: 같은 일을 동기와 비동기로 (슬라이드 165 · 168)")
    t = time.perf_counter()
    [fetch_sync(n, 0.3) for n in "ABC"]
    print(f"  동기   : {time.perf_counter() - t:.2f}s  (0.3초 × 3 — 대기가 누적)")
    t = time.perf_counter()
    await asyncio.gather(*(fetch(n, 0.3) for n in "ABC"))
    print(f"  비동기 : {time.perf_counter() - t:.2f}s  (대기 시간이 겹침)")


# ---------------------------------------------------------------- await (169)
async def demo_await() -> None:
    section("await: 결과가 올 때까지 멈추고 루프에 양보 (슬라이드 169)")
    log = Clock()

    async def call_llm(q: str) -> str:
        await asyncio.sleep(0.3)  # LLM 응답 대기를 흉내
        return f"'{q}'에 대한 답"

    async def handle(q: str) -> str:
        log("handle: 요청 전")
        answer = await call_llm(q)  # ① 필요하면 여기서 멈춤
        log(f"handle: 응답 → {answer}")  # ③ 결과를 받아 재개
        return answer

    async def other() -> None:
        for i in range(3):
            log(f"다른 코루틴 {i + 1}")  # ② 루프가 그동안 다른 일
            await asyncio.sleep(0.1)

    await asyncio.gather(handle("서울 날씨"), other())


# ---------------------------------------------------------------- suspend (170)
async def demo_suspend() -> None:
    section("suspend: 바로 끝나는 코루틴을 await하면 멈추지 않는다 (슬라이드 170)")

    async def quick() -> str:
        return "quick"

    async def other() -> None:
        print("  other 실행")

    asyncio.create_task(other())
    print("  1:", await quick())  # 멈추지 않음 → other는 아직
    print("  2:", await quick())
    await asyncio.sleep(0)  # 여기서 처음 양보 (bare yield)
    print("  3: sleep(0) 이후")


# ---------------------------------------------------------------- bytecode (171)
def demo_bytecode() -> None:
    section(f"bytecode: answer = await call_llm(q) (슬라이드 171 · Python {sys.version_info.major}.{sys.version_info.minor})")

    async def call_llm(q):
        return q

    async def handle(q):
        answer = await call_llm(q)
        return answer

    keep = {"CALL", "GET_AWAITABLE", "LOAD_CONST", "SEND", "YIELD_VALUE", "RESUME",
            "JUMP_BACKWARD_NO_INTERRUPT", "END_SEND", "STORE_FAST"}
    for ins in dis.get_instructions(handle):
        if ins.opname in keep:
            print(f"  {ins.opname:<28} {ins.argrepr}")
    print("  → SEND/YIELD_VALUE가 하위 코루틴에 실행을 위임하고, 기다릴 일이 생기면 위로 넘긴다")
    print("    (Python 3.12는 3.11보다 END_SEND 등 명령 이름이 조금 다르다)")


# ---------------------------------------------------------------- loop (172-155)
async def demo_loop() -> None:
    section("loop: 이벤트 루프의 대기열 (슬라이드 172–174)")
    loop = asyncio.get_running_loop()
    print(f"  루프 종류: {type(loop).__name__} (Windows 기본은 IOCP 기반 Proactor)")
    ready0 = len(loop._ready)  # noqa: SLF001 — 학습용으로 내부를 들여다본다
    loop.call_soon(print, "  (call_soon 콜백 실행)")
    loop.call_later(0.05, print, "  (call_later 콜백 실행)")
    task = asyncio.create_task(asyncio.sleep(0))
    print(f"  _ready     : {ready0} → {len(loop._ready)}  (call_soon + create_task의 __step)")  # noqa: SLF001
    when = [round(h.when() - loop.time(), 3) for h in loop._scheduled]  # noqa: SLF001
    print(f"  _scheduled : {len(loop._scheduled)}개, 남은 시간 ≈ {when}초 (call_later 타이머)")  # noqa: SLF001
    await task
    await asyncio.sleep(0.1)
    print("  → 루프가 실행하는 단위는 코루틴이 아니라 콜백(Handle)이다")


# ---------------------------------------------------------------- order (175)
async def demo_order() -> None:
    section("order: 스케줄링 순서 따라가기 (슬라이드 175)")
    log = Clock()

    async def job(name: str, delay: float) -> None:
        log(f"{name} 시작")
        await asyncio.sleep(delay)
        log(f"{name} 끝")

    loop = asyncio.get_running_loop()
    loop.call_soon(log, "call_soon 콜백")
    loop.call_later(0.15, log, "call_later 콜백")
    await asyncio.gather(job("A", 0.2), job("B", 0.1), job("C", 0))
    await asyncio.sleep(0)


# ---------------------------------------------------------------- objects (176)
async def demo_objects() -> None:
    section("objects: 코루틴 · Task · Future · TaskGroup (슬라이드 176)")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        coro = fetch("X", 0)
        print(f"  fetch() 호출 결과: {type(coro).__name__} — 아직 실행 안 됨")
        del coro
        import gc
        gc.collect()
    print(f"  await하지 않고 버리면: {[str(w.message) for w in caught][:1]}")

    task = asyncio.create_task(fetch("T", 0.01))
    print(f"  Task는 Future인가? {isinstance(task, asyncio.Future)}")
    print(f"  await task → {await task!r}")

    async def ok(n):
        await asyncio.sleep(0.2)
        print(f"  ok{n} 끝 (취소되면 이 줄이 안 나온다)")

    async def boom():
        await asyncio.sleep(0.05)
        raise ValueError("boom")

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(ok(1))
            tg.create_task(boom())
    except* ValueError as eg:
        print(f"  TaskGroup: 하나가 실패 → 나머지 취소, ExceptionGroup으로 받음: {eg.exceptions}")


# ---------------------------------------------------------------- run (178)
async def _inner() -> str:
    return "inner"


async def demo_run_inside_loop() -> None:
    coro = _inner()
    try:
        asyncio.run(coro)
    except RuntimeError as e:
        coro.close()
        print(f"  루프 안에서 asyncio.run(): RuntimeError — {e}")


def demo_run() -> None:
    section("run: asyncio.run()의 규칙 (슬라이드 178)")
    asyncio.run(demo_run_inside_loop())

    async def main():
        async def background():
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                print("  남은 Task: main()이 끝나서 취소됨 (CancelledError)")
                raise
        asyncio.create_task(background())
        await asyncio.sleep(0.01)
        return "main 결과"

    print(f"  asyncio.run(main()) → {asyncio.run(main())!r}")


ASYNC = {"sync": demo_sync, "await": demo_await, "suspend": demo_suspend,
         "loop": demo_loop, "order": demo_order, "objects": demo_objects}
SYNC = {"bytecode": demo_bytecode, "run": demo_run}
ORDER = ["sync", "await", "suspend", "bytecode", "loop", "order", "objects", "run"]


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    names = ORDER if which == "all" else [which]
    for n in names:
        if n in ASYNC:
            asyncio.run(ASYNC[n]())
        elif n in SYNC:
            SYNC[n]()
        else:
            sys.exit(f"알 수 없는 항목: {n} (가능: {', '.join(ORDER)}, all)")


if __name__ == "__main__":
    main()
