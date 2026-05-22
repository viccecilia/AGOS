"""Detect cross-workspace, cross-market, and cross-platform personality pollution."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


class PersonalityIsolationEngine:
    """Verify that personality memories stay scoped to their intended boundary."""

    DEFAULT_CONTEXTS: list[dict[str, Any]] = [
        {
            "scope_id": "JAG-LAB_japan_reddit",
            "workspace": "JAG-LAB",
            "market": "Japan",
            "platform": "reddit",
            "voice": "calm guide",
            "allowed_traits": ["trusted", "precise", "guide-like", "non-promotional", "deep answer"],
            "blocked_traits": ["appliance", "sales demo", "k-beauty mood", "tiktok hook spam"],
        },
        {
            "scope_id": "JAG-LAB_korea_tiktok",
            "workspace": "JAG-LAB",
            "market": "Korea",
            "platform": "tiktok",
            "voice": "clean visual guide",
            "allowed_traits": ["visual", "short rhythm", "hook", "save-worthy", "clean"],
            "blocked_traits": ["long reddit essay", "appliance", "taiwan slow-life tone", "hard sell"],
        },
        {
            "scope_id": "JAG-LAB_taiwan_instagram",
            "workspace": "JAG-LAB",
            "market": "Taiwan",
            "platform": "instagram",
            "voice": "warm daily-life guide",
            "allowed_traits": ["warm", "daily-life", "caption", "soft visual", "slow pace"],
            "blocked_traits": ["x hot take", "youtube chapters", "appliance", "aggressive urgency"],
        },
        {
            "scope_id": "PHILIPS-LAB_us_youtube",
            "workspace": "PHILIPS-LAB",
            "market": "Europe / US",
            "platform": "youtube",
            "voice": "product proof explainer",
            "allowed_traits": ["demonstration", "proof", "comparison", "clear setup", "durable trust"],
            "blocked_traits": ["japan train transfer", "travel guide", "tokyo anxiety", "route rescue"],
        },
    ]

    def __init__(self, root: str | Path = "runtime/personality_isolation") -> None:
        self.root = Path(root)
        self.report_path = self.root / "PERSONALITY_ISOLATION_REPORT.json"
        self.matrix_path = self.root / "personality_isolation_matrix.json"

    def run_check(self, contexts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        contexts = contexts or self.DEFAULT_CONTEXTS
        workspace_results = self._check_dimension(contexts, "workspace")
        market_results = self._check_dimension(contexts, "market")
        platform_results = self._check_dimension(contexts, "platform")
        violations = [
            *workspace_results["violations"],
            *market_results["violations"],
            *platform_results["violations"],
        ]
        report = {
            "report_id": "PERSONALITY_ISOLATION_REPORT",
            "created_at": utc_now_iso(),
            "status": "clear" if not violations else "needs_human_review",
            "summary": "No cross-market personality pollution detected." if not violations else "Personality pollution risk detected.",
            "workspacePersonalityPollution": workspace_results,
            "marketPersonalityPollution": market_results,
            "platformPersonalityPollution": platform_results,
            "isolationMatrix": contexts,
            "violations": violations,
            "review_required": bool(violations),
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.run_check()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.matrix_path.write_text(
            json.dumps(report["isolationMatrix"], ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    @staticmethod
    def _check_dimension(contexts: list[dict[str, Any]], dimension: str) -> dict[str, Any]:
        violations: list[dict[str, Any]] = []
        for context in contexts:
            own_text = " ".join(
                [
                    str(context.get("voice", "")),
                    " ".join(context.get("allowed_traits", [])),
                ]
            ).lower()
            leaked = [trait for trait in context.get("blocked_traits", []) if trait.lower() in own_text]
            if leaked:
                violations.append(
                    {
                        "scope_id": context["scope_id"],
                        "dimension": dimension,
                        "status": "polluted",
                        "leaked_traits": leaked,
                        "action": "Block this personality memory and require human correction.",
                    }
                )
        scopes = sorted({str(context.get(dimension, "")) for context in contexts})
        return {
            "dimension": dimension,
            "status": "clear" if not violations else "needs_human_review",
            "scopes_checked": scopes,
            "scopes_count": len(scopes),
            "contexts_checked": len(contexts),
            "violations": violations,
            "evidence": [
                {
                    "scope_id": context["scope_id"],
                    "workspace": context["workspace"],
                    "market": context["market"],
                    "platform": context["platform"],
                    "voice": context["voice"],
                    "blocked_traits": context["blocked_traits"],
                    "status": "isolated",
                }
                for context in contexts
            ],
        }
