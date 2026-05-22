"""Local JSON-backed Runtime Queue."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


QUEUE_STATUSES = {"pending", "in_progress", "failed", "waiting_review", "done"}


class RuntimeQueue:
    def __init__(self, root: str | Path = "runtime/runtime_state") -> None:
        self.path = Path(root) / "runtime_queue.json"

    def enqueue(self, item: dict[str, Any]) -> dict[str, Any]:
        queue = self._load()
        payload = {
            "queue_id": item.get("queue_id") or f"queue_{len(queue) + 1:04d}",
            "type": item.get("type", "analysis"),
            "status": item.get("status", "pending"),
            "attempts": int(item.get("attempts", 0)),
            "payload": item.get("payload", {}),
            "created_at": item.get("created_at", utc_now_iso()),
            "updated_at": utc_now_iso(),
        }
        if payload["status"] not in QUEUE_STATUSES:
            raise ValueError(f"Invalid queue status: {payload['status']}")
        queue.append(payload)
        self._save(queue)
        return payload

    def dequeue(self, queue_type: str | None = None) -> dict[str, Any] | None:
        queue = self._load()
        for item in queue:
            if item["status"] != "pending":
                continue
            if queue_type and item["type"] != queue_type:
                continue
            item["status"] = "in_progress"
            item["updated_at"] = utc_now_iso()
            self._save(queue)
            return item
        return None

    def retry(self, queue_id: str) -> dict[str, Any]:
        return self._update(queue_id, "pending", increment_attempt=True)

    def failed(self, queue_id: str, error: str) -> dict[str, Any]:
        item = self._update(queue_id, "failed")
        item["error"] = error
        self._replace(item)
        return item

    def waiting_review(self, queue_id: str) -> dict[str, Any]:
        return self._update(queue_id, "waiting_review")

    def done(self, queue_id: str) -> dict[str, Any]:
        return self._update(queue_id, "done")

    def list(self, status: str | None = None) -> list[dict[str, Any]]:
        queue = self._load()
        if status:
            return [item for item in queue if item["status"] == status]
        return queue

    def _update(self, queue_id: str, status: str, increment_attempt: bool = False) -> dict[str, Any]:
        if status not in QUEUE_STATUSES:
            raise ValueError(f"Invalid queue status: {status}")
        queue = self._load()
        for item in queue:
            if item["queue_id"] == queue_id:
                item["status"] = status
                item["updated_at"] = utc_now_iso()
                if increment_attempt:
                    item["attempts"] += 1
                self._save(queue)
                return item
        raise KeyError(queue_id)

    def _replace(self, updated: dict[str, Any]) -> None:
        queue = self._load()
        self._save([updated if item["queue_id"] == updated["queue_id"] else item for item in queue])

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, queue: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(queue, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
