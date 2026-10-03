"""Bound caller waiting without claiming that Python provider threads can be cancelled."""
from concurrent.futures import Future
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import math
import os
from pathlib import Path
from threading import BoundedSemaphore, Thread, TIMEOUT_MAX
from time import monotonic, sleep


DEFAULT_PROVIDER_TIMEOUT_SECONDS = 30.0
# Stuck adapters cannot create an unbounded number of live threads in one process.
_PROVIDER_SLOTS = BoundedSemaphore(4)


def configured_timeout_seconds(value=None):
    seconds = float(value if value is not None else os.environ.get(
        "CONFIA_RECOGNITION_TIMEOUT_SECONDS", DEFAULT_PROVIDER_TIMEOUT_SECONDS))
    if not math.isfinite(seconds) or seconds <= 0 or seconds > TIMEOUT_MAX:
        raise ValueError("provider duration must be positive and supported by the runtime")
    return seconds


@dataclass(frozen=True)
class ProviderDeadline:
    timeout_seconds: float
    expires_at_monotonic: float

    @classmethod
    def start(cls, seconds):
        return cls(seconds, monotonic() + seconds)

    def remaining_seconds(self):
        return max(0.0, self.expires_at_monotonic - monotonic())


class RequestLease:
    def __init__(self, handle, cached_run=None):
        self.handle = handle
        self.cached_run = cached_run
        self.unfinished = None

    def retain_until_done(self, future):
        self.unfinished = future

    def release(self, _future=None):
        # Only the context exit OR its completion callback invokes this method.
        try:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        finally:
            self.handle.close()

    def finish(self):
        if self.handle is None:
            return
        if self.unfinished is None:
            self.release()
        else:
            # If already done, Future invokes this immediately. A timeout does not
            # unlock an unfinished request when publication itself has failed.
            self.unfinished.add_done_callback(self.release)


@contextmanager
def recognition_request_lock(root: Path, run_id: str, completed=None):
    locks = root / ".recognition-locks"
    if locks.is_symlink():
        raise ValueError("invalid recognition lock directory")
    locks.mkdir(parents=True, exist_ok=True)
    path = locks / f"{run_id}.lock"
    # Lock files stay in place: unlinking would let callers lock different inodes.
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    handle = os.fdopen(fd, "a+b")
    try:
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                # A peer may publish FAILED on timeout before its worker exits.
                # Existing callers must be able to replay that terminal result.
                run = completed() if completed is not None else None
                if run is not None:
                    handle.close()
                    yield RequestLease(None, cached_run=run)
                    return
                sleep(0.05)
    except BaseException:
        handle.close()
        raise
    lease = RequestLease(handle)
    try:
        yield lease
    finally:
        lease.finish()


def start_provider(operation, deadline):
    future = Future()
    slots = _PROVIDER_SLOTS
    if not slots.acquire(blocking=False):
        future.set_result((None, "PROVIDER_BUSY"))
        return future

    def worker():
        try:
            try:
                outcome = operation() if deadline.remaining_seconds() > 0 else (None, "PROVIDER_TIMEOUT")
                # Enforce completion time even if the observer is descheduled and
                # sees an already-completed Future only after its wait deadline.
                if deadline.remaining_seconds() <= 0:
                    outcome = (None, "PROVIDER_TIMEOUT")
            except TimeoutError:
                outcome = (None, "PROVIDER_TIMEOUT")
            except BaseException:
                # Do not retain exception objects/tracebacks or provider error text.
                outcome = (None, "PROVIDER_FAILED")
        finally:
            slots.release()
        future.set_result(outcome)

    try:
        Thread(target=worker, name="confia-recognition-provider", daemon=True).start()
    except BaseException:
        slots.release()
        raise
    return future
