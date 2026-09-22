"""Background writer for request logs.

Logging must not sit on the request path, so the middleware hands a plain dict
to an in-memory queue and returns. A single task drains the queue, batches the
rows, and inserts them from a worker thread — one commit per batch instead of
one per request.

Back pressure is explicit: if the queue is full the log is dropped and counted,
because dropping a log line is better than slowing down the API it describes.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy import func, insert, update

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import APIKey, RequestLog

logger = logging.getLogger("api.logs")

QUEUE_MAX = 10_000


class RequestLogWriter:
    def __init__(self) -> None:
        # The queue is created in start(), not here: an asyncio.Queue binds to
        # the running loop the first time it is used, and this object outlives
        # any single loop (reloads, tests, an app embedded in another runner).
        self._queue: asyncio.Queue[dict[str, Any]] | None = None
        self._task: asyncio.Task[None] | None = None
        self.dropped = 0
        self.written = 0

    # -- lifecycle ---------------------------------------------------------
    async def start(self) -> None:
        if self._task is not None:
            return
        self._queue = asyncio.Queue(maxsize=QUEUE_MAX)
        self._task = asyncio.create_task(self._run(), name="request-log-writer")

    async def stop(self) -> None:
        """Drain what is queued before the process goes away."""
        if self._task is None or self._queue is None:
            return
        await self._queue.join()
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
        self._queue = None

    # -- producer ----------------------------------------------------------
    def submit(self, entry: dict[str, Any]) -> None:
        """Never blocks and never raises: called from the request path."""
        if self._queue is None:  # writer not running (e.g. during shutdown)
            self.dropped += 1
            return
        try:
            self._queue.put_nowait(entry)
        except asyncio.QueueFull:
            self.dropped += 1
            if self.dropped % 100 == 1:
                logger.warning("Request log queue full; dropped %s entries", self.dropped)

    # -- consumer ----------------------------------------------------------
    async def _run(self) -> None:
        assert self._queue is not None
        while True:
            batch = [await self._queue.get()]
            # Take whatever else is already waiting, up to the batch size.
            deadline = asyncio.get_running_loop().time() + settings.log_flush_interval_seconds
            while len(batch) < settings.log_batch_size:
                timeout = deadline - asyncio.get_running_loop().time()
                if timeout <= 0:
                    break
                try:
                    batch.append(await asyncio.wait_for(self._queue.get(), timeout))
                except (TimeoutError, asyncio.TimeoutError):
                    break

            try:
                await asyncio.to_thread(self._write, batch)
                self.written += len(batch)
            except Exception:  # noqa: BLE001 - a failed batch must not kill the writer
                logger.exception("Failed to write %s request logs", len(batch))
            finally:
                for _ in batch:
                    self._queue.task_done()

    @staticmethod
    def _write(rows: list[dict[str, Any]]) -> None:
        with SessionLocal() as db:
            db.execute(insert(RequestLog), rows)
            # last_used_at is refreshed from the same batch, so a busy key
            # costs one UPDATE per flush instead of one per request.
            touched = {row["api_key_id"] for row in rows if row.get("api_key_id")}
            if touched:
                db.execute(
                    update(APIKey)
                    .where(APIKey.id.in_(touched))
                    .values(last_used_at=func.now())
                )
            db.commit()

    # -- test support ------------------------------------------------------
    async def flush(self) -> None:
        """Wait until everything queued has been written."""
        if self._queue is not None:
            await self._queue.join()


writer = RequestLogWriter()
