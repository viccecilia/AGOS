"""Human Review Gate for local Runtime actions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


class HumanReviewRuntime:
    def __init__(self, root: str | Path = "runtime/runtime_state") -> None:
        self.path = Path(root) / "human_review_queue.json"

    def request_review(self, item: dict[str, Any]) -> dict[str, Any]:
        queue = self._load()
        payload = {
            "review_id": item.get("review_id") or f"review_{len(queue) + 1:04d}",
            "workspace": item.get("workspace", "jag_app_growth"),
            "cycle": item.get("cycle", "CYCLE-001"),
            "stage": item.get("stage", "Human Review"),
            "target_type": item.get("target_type", "strategy"),
            "content": item.get("content", {}),
            "status": "needs_human_review",
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        }
        queue.append(payload)
        self._save(queue)
        return payload

    def approve(self, review_id: str) -> dict[str, Any]:
        return self._decision(review_id, "approved")

    def reject(self, review_id: str, reason: str = "") -> dict[str, Any]:
        item = self._decision(review_id, "rejected")
        item["reason"] = reason
        self._replace(item)
        return item

    def modify(self, review_id: str, modified_content: dict[str, Any]) -> dict[str, Any]:
        item = self._decision(review_id, "modified")
        item["modified_content"] = modified_content
        self._replace(item)
        return item

    def pending(self) -> list[dict[str, Any]]:
        return [item for item in self._load() if item["status"] == "needs_human_review"]

    def list(self) -> list[dict[str, Any]]:
        return self._load()

    def _decision(self, review_id: str, status: str) -> dict[str, Any]:
        queue = self._load()
        for item in queue:
            if item["review_id"] == review_id:
                item["status"] = status
                item["updated_at"] = utc_now_iso()
                self._save(queue)
                return item
        raise KeyError(review_id)

    def _replace(self, updated: dict[str, Any]) -> None:
        queue = self._load()
        self._save([updated if item["review_id"] == updated["review_id"] else item for item in queue])

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, queue: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(queue, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
