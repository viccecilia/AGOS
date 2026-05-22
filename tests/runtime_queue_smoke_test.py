from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.runtime_queue import RuntimeQueue


def main() -> None:
    root = Path("runtime/test_runtime_queue")
    if root.exists():
        shutil.rmtree(root)

    queue = RuntimeQueue(root)
    item = queue.enqueue({"queue_id": "q1", "type": "待分析", "payload": {"question": "Tokyo transport anxiety"}})
    assert item["status"] == "pending"

    dequeued = queue.dequeue("待分析")
    assert dequeued is not None
    assert dequeued["queue_id"] == "q1"
    assert dequeued["status"] == "in_progress"

    failed = queue.failed("q1", "analysis model unavailable")
    assert failed["status"] == "failed"

    retry = queue.retry("q1")
    assert retry["status"] == "pending"
    assert retry["attempts"] == 1

    review = queue.waiting_review("q1")
    assert review["status"] == "waiting_review"

    shutil.rmtree(root)
    print("runtime queue smoke test passed")


if __name__ == "__main__":
    main()
