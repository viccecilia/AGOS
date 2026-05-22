from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from urllib import request


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.runtime_api_server import SERVER_HOST, SERVER_PORT


BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"


def get_json(path: str) -> dict:
    with request.urlopen(f"{BASE_URL}{path}", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(path: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload or {}).encode("utf-8")
    req = request.Request(
        f"{BASE_URL}{path}",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_server(proc: subprocess.Popen) -> None:
    deadline = time.time() + 15
    last_error: Exception | None = None
    while time.time() < deadline:
        if proc.poll() is not None:
            stdout, stderr = proc.communicate(timeout=1)
            raise RuntimeError(
                "runtime_api_server exited early\n"
                f"stdout={stdout.decode('utf-8', errors='replace')}\n"
                f"stderr={stderr.decode('utf-8', errors='replace')}"
            )
        try:
            get_json("/api/runtime/status")
            return
        except Exception as exc:  # pragma: no cover - only used while waiting.
            last_error = exc
            time.sleep(0.25)
    raise TimeoutError(f"runtime_api_server did not start: {last_error}")


def main() -> None:
    assert SERVER_HOST == "127.0.0.1", "Runtime API must bind to 127.0.0.1 only"

    proc = subprocess.Popen(
        [sys.executable, "services/runtime_api_server.py"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        wait_for_server(proc)

        status = get_json("/api/runtime/status")
        assert status["ok"] is True
        assert status["workspace"]
        assert status["current_stage"]
        assert isinstance(status["runtime_feed"], list)
        assert "no_social_platform_api" in status["safety_boundary"]

        started = post_json("/api/runtime/start")
        assert started["ok"] is True
        assert started["status"] == "running"
        assert started["message"] == "JAG-LAB runtime training cycle started"

        ui_state_path = PROJECT_ROOT / "runtime" / "runtime_state" / "ui_state.json"
        assert ui_state_path.exists(), "ui_state.json must be updated after start"
        ui_state = json.loads(ui_state_path.read_text(encoding="utf-8"))
        assert (ui_state.get("systemControl") or {}).get("currentWorkspace") == "JAG-LAB"
        assert ui_state.get("warRoomFeed"), "Runtime Feed must update after start"
        assert ui_state.get("opportunityRanking"), "Opportunity Ranking must update after start"

        corrected = post_json(
            "/api/runtime/correction",
            {
                "workspace": "JAG-LAB",
                "target_type": "opportunity",
                "target_id": "OPP-001",
                "decision": "reject",
                "reason": "This is normal chatter, not a high-value travel pain point.",
            },
        )
        assert corrected["ok"] is True
        assert corrected["correction"]["target_id"] == "OPP-001"
        assert corrected["ui_state"].get("mislearningAlerts"), "Correction must update mislearning alerts"

        review_queue_path = PROJECT_ROOT / "runtime" / "runtime_state" / "human_review_queue.json"
        review_queue = json.loads(review_queue_path.read_text(encoding="utf-8"))
        review_id = review_queue[-1]["review_id"]
        reviewed = post_json(
            "/api/runtime/review",
            {
                "review_id": review_id,
                "decision": "modify",
                "modified_text": "Keep the reply useful and non-promotional.",
            },
        )
        assert reviewed["ok"] is True
        assert reviewed["review"]["status"] == "modified"

        stopped = post_json("/api/runtime/stop")
        assert stopped["ok"] is True
        assert stopped["status"] == "stopped"
        ui_state = json.loads(ui_state_path.read_text(encoding="utf-8"))
        assert ui_state.get("runtimeStatus") == "STOPPED"

        html = (PROJECT_ROOT / "docs" / "project_control_center.html").read_text(encoding="utf-8")
        assert "Runtime API 未连接" in html
        assert "python services/runtime_api_server.py" in html
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)

    print("runtime_api_server_smoke_test passed")


if __name__ == "__main__":
    main()
