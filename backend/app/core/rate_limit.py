"""
Защита входа от подбора пароля: не больше N неудачных попыток на логин за окно.

Логины предсказуемы (транслит ФИО), поэтому считаем по логину, а не по IP:
в учебном классе десятки человек выходят в интернет с одного IP, и лимит
по IP блокировал бы весь класс. Хранится в памяти процесса — при нескольких
воркерах uvicorn лимит действует на каждый воркер отдельно, этого достаточно,
чтобы перебор стал бессмысленным.
"""
import time
from collections import defaultdict, deque

MAX_FAILURES = 10
WINDOW_SECONDS = 15 * 60

_failures: dict[str, deque] = defaultdict(deque)


def _key(login: str) -> str:
    return login.strip().lower()


def _prune(q: deque, now: float) -> None:
    while q and now - q[0] > WINDOW_SECONDS:
        q.popleft()


def is_blocked(login: str) -> bool:
    q = _failures.get(_key(login))
    if not q:
        return False
    _prune(q, time.monotonic())
    return len(q) >= MAX_FAILURES


def register_failure(login: str) -> None:
    now = time.monotonic()
    q = _failures[_key(login)]
    _prune(q, now)
    q.append(now)
    # Не даём словарю расти бесконечно от случайных логинов.
    if len(_failures) > 50_000:
        for k in [k for k, v in _failures.items() if not v or now - v[-1] > WINDOW_SECONDS]:
            _failures.pop(k, None)


def reset(login: str) -> None:
    _failures.pop(_key(login), None)
