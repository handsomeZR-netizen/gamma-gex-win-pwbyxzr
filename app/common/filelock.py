from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Iterator


IS_WINDOWS = os.name == "nt"

if IS_WINDOWS:
    import msvcrt
else:
    import fcntl


def lock_stream(stream: IO[str], *, exclusive: bool = True, blocking: bool = True) -> None:
    if IS_WINDOWS:
        stream.seek(0)
        if exclusive:
            mode = msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK
        else:
            mode = msvcrt.LK_RLCK if blocking else msvcrt.LK_NBRLCK
        try:
            msvcrt.locking(stream.fileno(), mode, 1)
        except OSError as exc:
            if not blocking:
                raise BlockingIOError(str(exc)) from exc
            raise
        return

    flags = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
    if not blocking:
        flags |= fcntl.LOCK_NB
    fcntl.flock(stream.fileno(), flags)


def unlock_stream(stream: IO[str]) -> None:
    if IS_WINDOWS:
        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        return
    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


@contextmanager
def locked_open(
    path: str | Path,
    mode: str,
    *,
    exclusive: bool = True,
    blocking: bool = True,
    encoding: str = "utf-8",
) -> Iterator[IO[str]]:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, mode, encoding=encoding) as handle:
        lock_stream(handle, exclusive=exclusive, blocking=blocking)
        try:
            yield handle
        finally:
            unlock_stream(handle)

