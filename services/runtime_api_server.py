"""Local-only HTTP API for the AGOS Runtime Engine.

This server is intentionally scoped to local JAG-LAB Runtime Training. It never
posts to social platforms, replies to real users, registers accounts, logs in to
platforms, calls public platform APIs, or bypasses platform limits.
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.human_feedback_learning import HumanFeedbackLearning
from services.human_review_runtime import HumanReviewRuntime
from services.runtime_correction_engine import RuntimeCorrectionEngine
from services.runtime_drift_monitor import RuntimeDriftMonitor
from services.runtime_engine import RuntimeEngine
from services.runtime_persistence import RuntimePersistence
from services.runtime_review_session import RuntimeReviewSession
from services.runtime_ui_bridge import RuntimeUIBridge


SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8766
ALLOWED_ORIGINS = {"http://127.0.0.1:8765", "http://localhost:8765"}
SAFETY_BOUNDARY = [
    "local_jag_lab_runtime_training_only",
    "local_json_state_only",
    "local_runtime_logs_only",
    "local_review_gate_only",
    "no_social_platform_api",
    "no_auto_posting",
    "no_auto_replying",
    "no_auto_registration",
    "no_social_login",
    "no_public_bind",
]


class RuntimeApiController:
    def __init__(self) -> None:
        self.persistence = RuntimePersistence()
        self.engine = RuntimeEngine(
            persistence=self.persistence,
            review_session=RuntimeReviewSession("runtime/runtime_reviews"),
        )
        self.bridge = RuntimeUIBridge(self.engine)
        self.review = HumanReviewRuntime(self.persistence.root)
        self.correction = RuntimeCorrectionEngine(self.persistence.root)
        self.feedback = HumanFeedbackLearning()
        self.drift = RuntimeDriftMonitor()

    def status(self) -> dict[str, Any]:
        ui_state = self._load_or_export_ui_state()
        return {
            "ok": True,
            "status": self._runtime_status(ui_state),
            "workspace": (ui_state.get("systemControl") or {}).get("currentWorkspace", "JAG-LAB"),
            "cycle": (ui_state.get("systemControl") or {}).get("currentCycle", "JAG-LAB-CYCLE-0001"),
            "current_stage": ui_state.get("current_runtime_stage", "Scout"),
            "runtime_feed": ui_state.get("warRoomFeed", []),
            "opportunity_ranking": ui_state.get("opportunityRanking", []),
            "mislearning_alerts": ui_state.get("mislearningAlerts", []),
            "memory_deposits": ui_state.get("learningDeposits", []),
            "review_queue": ui_state.get("reviewQueue", []),
            "runtime_queue": ui_state.get("runtimeQueue", []),
            "ui_state": ui_state,
            "safety_boundary": SAFETY_BOUNDARY,
        }

    def start(self) -> dict[str, Any]:
        self.engine.run_training_cycle()
        ui_state = self.bridge.export_ui_state()
        return {
            "ok": True,
            "status": "running",
            "message": "JAG-LAB runtime training cycle started",
            "ui_state": ui_state,
            "safety_boundary": SAFETY_BOUNDARY,
        }

    def stop(self) -> dict[str, Any]:
        self.engine.stop()
        ui_state = self.bridge.export_ui_state()
        return {
            "ok": True,
            "status": "stopped",
            "ui_state": ui_state,
            "safety_boundary": SAFETY_BOUNDARY,
        }

    def correction_record(self, body: dict[str, Any]) -> dict[str, Any]:
        correction = self.correction.reject(
            {
                "target_type": body.get("correction_type", body.get("target_type", "learning")),
                "target_id": body.get("target_id", "unknown"),
                "reason": body.get("correction_reason", body.get("reason", "")),
                "rejected_learning": {
                    "workspace": body.get("workspace", "JAG-LAB"),
                    "decision": body.get("decision", "reject"),
                    "industry_pack": body.get("industry_pack", "Travel Pack / Lab"),
                    "affected_runtime_stage": body.get("affected_runtime_stage", "Human Review"),
                },
            }
        )
        correction_decision = self.feedback.record_correction(
            correction,
            {
                "workspace": body.get("workspace", "JAG-LAB"),
                "industry_pack": body.get("industry_pack", "Travel Pack / Lab"),
                "affected_runtime_stage": body.get("affected_runtime_stage", "Human Review"),
                "correction_type": body.get("correction_type", body.get("target_type", "learning")),
                "correction_reason": body.get("correction_reason", body.get("reason", "")),
            },
        )
        state = self.engine.current_state()
        drift_events = self.drift.detect({**body, **correction})
        alerts = list(state.get("mislearning_alerts", []))
        alert = {
            "issue": f"Human Correction: {correction['target_type']}",
            "status": "needs_human_review",
            "severity": "high",
            "signal": correction.get("reason", ""),
            "action": "Correction recorded; do not learn this branch as best answer.",
            "target_id": correction.get("target_id"),
            "correction_id": correction.get("correction_id"),
        }
        alerts.append(alert)
        alerts.extend(drift_events)
        state["mislearning_alerts"] = alerts
        state["correction_alerts"] = list(state.get("correction_alerts", [])) + [alert]
        state["runtime_drift_events"] = self.drift.history()
        state["human_feedback_summary"] = self.feedback.summary()
        state["current_event"] = "human_correction_recorded"
        self.engine.persistence.append_event(
            {
                "workspace": body.get("workspace", state.get("workspace", "JAG-LAB")),
                "industry_pack": state.get("industry_pack", "Travel Pack / Lab"),
                "cycle": state.get("cycle", "JAG-LAB-CYCLE-0001"),
                "stage": state.get("current_stage", "Human Review"),
                "event": "human_correction",
                "result": body.get("correction_reason", body.get("reason", "Human correction recorded")),
            }
        )
        self.engine.persistence.save_state(state)
        ui_state = self.bridge.export_ui_state()
        return {
            "ok": True,
            "status": self._runtime_status(ui_state),
            "correction": correction,
            "correction_decision": correction_decision,
            "drift_events": drift_events,
            "ui_state": ui_state,
        }

    def review_decision(self, body: dict[str, Any]) -> dict[str, Any]:
        review_id = body.get("review_id")
        if not review_id:
            raise ValueError("review_id is required")
        decision = body.get("decision", "approve")
        if decision == "approve":
            review = self.review.approve(review_id)
        elif decision == "reject":
            review = self.review.reject(review_id, body.get("reject_reason", body.get("reason", "Rejected by human review")))
        elif decision == "modify":
            review = self.review.modify(
                review_id,
                {
                    "modified_text": body.get("human_modified_version", body.get("modified_text", "")),
                    "human_modified_version": body.get("human_modified_version", body.get("modified_text", "")),
                },
            )
        else:
            raise ValueError("decision must be approve, reject, or modify")

        feedback_decision = self.feedback.record_review_decision(
            review,
            decision,
            {
                "reason": body.get("reject_reason", body.get("reason", "")),
                "human_modified_version": body.get("human_modified_version", body.get("modified_text", "")),
            },
        )
        state = self.engine.current_state()
        state["human_review"] = review
        state["review_queue"] = self.review.pending()
        state["current_event"] = f"human_review_{decision}"
        intelligence = dict(state.get("runtime_intelligence", {}))
        if decision in {"reject", "modify"}:
            state["status"] = "needs_human_review"
        if decision == "reject":
            intelligence.setdefault("failed_strategy", []).append(body.get("reject_reason", body.get("reason", "Rejected by human review")))
            intelligence.setdefault("failed_reply", []).append(str(review.get("content", {})))
        if decision == "modify":
            intelligence.setdefault("human_optimized_output", []).append(body.get("human_modified_version", body.get("modified_text", "")))
            state["status"] = "running"
        elif state.get("status") == "needs_human_review":
            state["status"] = "running"
        if decision == "approve":
            intelligence.setdefault("approved_by_human", []).append(review.get("target_type", "strategy"))
        state["runtime_intelligence"] = intelligence
        drift_events = self.drift.detect({"decision": decision, "review": review, "body": body})
        if drift_events:
            state["status"] = "needs_human_review"
            state["mislearning_alerts"] = list(state.get("mislearning_alerts", [])) + drift_events
        state["runtime_drift_events"] = self.drift.history()
        state["human_feedback_summary"] = self.feedback.summary()
        self.engine.persistence.append_event(
            {
                "workspace": state.get("workspace", "JAG-LAB"),
                "industry_pack": state.get("industry_pack", "Travel Pack / Lab"),
                "cycle": state.get("cycle", "JAG-LAB-CYCLE-0001"),
                "stage": "Human Review",
                "event": f"human_review_{decision}",
                "result": review_id,
            }
        )
        self.engine.persistence.save_state(state)
        ui_state = self.bridge.export_ui_state()
        return {
            "ok": True,
            "status": self._runtime_status(ui_state),
            "review": review,
            "feedback_decision": feedback_decision,
            "drift_events": drift_events,
            "ui_state": ui_state,
        }

    def _load_or_export_ui_state(self) -> dict[str, Any]:
        if self.persistence.ui_state_file.exists():
            try:
                payload = json.loads(self.persistence.ui_state_file.read_text(encoding="utf-8"))
                if "runtimeStatus" in payload:
                    return payload
            except json.JSONDecodeError:
                pass
        return self.bridge.export_ui_state()

    @staticmethod
    def _runtime_status(ui_state: dict[str, Any]) -> str:
        value = str(ui_state.get("runtimeStatus", "STOPPED")).lower()
        if value == "paused":
            return "paused"
        if value == "running":
            return "running"
        return "stopped"


class RuntimeApiHandler(BaseHTTPRequestHandler):
    controller = RuntimeApiController()

    def do_OPTIONS(self) -> None:
        self._send_json({}, status=204)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/runtime/status":
            self._send_json(self.controller.status())
            return
        self._send_json({"ok": False, "error": "not_found"}, status=404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            body = self._read_json()
            if path == "/api/runtime/start":
                self._send_json(self.controller.start())
                return
            if path == "/api/runtime/stop":
                self._send_json(self.controller.stop())
                return
            if path == "/api/runtime/correction":
                self._send_json(self.controller.correction_record(body))
                return
            if path == "/api/runtime/review":
                self._send_json(self.controller.review_decision(body))
                return
            self._send_json({"ok": False, "error": "not_found"}, status=404)
        except KeyError as exc:
            self._send_json({"ok": False, "error": f"not_found: {exc}"}, status=404)
        except Exception as exc:
            self._send_json({"ok": False, "error": str(exc)}, status=400)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[runtime-api] {self.address_string()} - {format % args}")

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length == 0:
            return {}
        data = self.rfile.read(length)
        return json.loads(data.decode("utf-8"))

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(text)))
        origin = self.headers.get("Origin")
        self.send_header("Access-Control-Allow-Origin", origin if origin in ALLOWED_ORIGINS else "http://127.0.0.1:8765")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        if status != 204:
            self.wfile.write(text)


def run_server(host: str = SERVER_HOST, port: int = SERVER_PORT) -> ThreadingHTTPServer:
    if host != SERVER_HOST:
        raise ValueError("Runtime API Server must bind only to 127.0.0.1")
    server = ThreadingHTTPServer((host, port), RuntimeApiHandler)
    print(f"AGOS Runtime API Server listening on http://{host}:{port}")
    print("Safety: local JAG-LAB Runtime Training only; no social platform automation.")
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return server


if __name__ == "__main__":
    run_server()
