"""JSON persistence for the local AGOS Runtime Engine."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class RuntimePersistence:
    def __init__(self, root: str | Path = "runtime/runtime_state", logs_root: str | Path = "runtime/runtime_logs") -> None:
        self.root = Path(root)
        self.logs_root = Path(logs_root)

    @property
    def state_file(self) -> Path:
        return self.root / "current_state.json"

    @property
    def ui_state_file(self) -> Path:
        return self.root / "ui_state.json"

    def load_state(self) -> dict[str, Any]:
        if not self.state_file.exists():
            return {}
        return json.loads(self.state_file.read_text(encoding="utf-8"))

    def save_state(self, state: dict[str, Any]) -> dict[str, Any]:
        self.root.mkdir(parents=True, exist_ok=True)
        payload = {**state, "updated_at": utc_now_iso()}
        text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        self.state_file.write_text(text, encoding="utf-8")
        self.ui_state_file.write_text(text, encoding="utf-8")
        return payload

    def append_event(self, event: dict[str, Any]) -> dict[str, Any]:
        self.logs_root.mkdir(parents=True, exist_ok=True)
        payload = {"timestamp": utc_now_iso(), **event}
        cycle = str(payload.get("cycle", "cycle-unknown")).replace("/", "_")
        path = self.logs_root / f"{cycle}.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        return payload

    def load_events(self, limit: int = 20) -> list[dict[str, Any]]:
        if not self.logs_root.exists():
            return []
        events: list[dict[str, Any]] = []
        for path in sorted(self.logs_root.glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    events.append(json.loads(line))
        return events[-limit:]
