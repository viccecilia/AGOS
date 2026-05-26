"""Compliance guard for controlled read-only intelligence collection."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from services.live_collection_runner import FORBIDDEN_LIVE_ACTIONS, LiveCollectionRunner
from services.runtime_persistence import utc_now_iso


DEFAULT_COMPLIANCE_LIMITS = {
    "requests_per_minute": 6,
    "repeated_query_limit": 2,
    "polling_events_per_window": 5,
}
WRITE_API_OPERATIONS = {"post", "reply", "DM", "follow", "like", "write_api"}
FORBIDDEN_COLLECTION_BEHAVIORS = {
    "automated_login_scrape",
    "bypass_platform_limits",
    "write_api_usage",
    "auto_interaction",
}


class CollectionComplianceGuard:
    """Detect compliance risks before live collection becomes unsafe."""

    def __init__(
        self,
        root: str | Path = "runtime/compliance_guard",
        limits: dict[str, int] | None = None,
    ) -> None:
        self.root = Path(root)
        self.limits = limits or dict(DEFAULT_COMPLIANCE_LIMITS)
        self.report_path = self.root / "COLLECTION_COMPLIANCE_GUARD_REPORT.json"
        self.feed_path = self.root / "compliance_risk_feed.json"
        self.summary_path = self.root / "compliance_guard_summary.json"
        self.events_path = self.root / "compliance_events.json"

    def evaluate(self, events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        compliance_events = events if events is not None else self._default_events()
        risk_feed = self._risk_feed(compliance_events)
        report = {
            "report_id": "COLLECTION_COMPLIANCE_GUARD_REPORT",
            "created_at": utc_now_iso(),
            "status": "compliance_guard_ready",
            "scope": "controlled_api_intelligence_collection",
            "limits": self.limits,
            "forbiddenCollectionBehaviors": sorted(FORBIDDEN_COLLECTION_BEHAVIORS),
            "writeApiOperations": sorted(WRITE_API_OPERATIONS),
            "complianceEvents": compliance_events,
            "complianceRiskFeed": risk_feed,
            "complianceGuardSummary": self._summary(risk_feed),
            "safetyBoundary": "Collection Compliance Guard allows read-only public intelligence collection only. It blocks automated login scraping, platform-limit bypass, write API usage, and automated interaction.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.evaluate()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["complianceRiskFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["complianceGuardSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.events_path.write_text(json.dumps(report["complianceEvents"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _default_events(self) -> list[dict[str, Any]]:
        live_report = LiveCollectionRunner().state()
        events = []
        for item in live_report.get("liveCollectionItems", []):
            events.append(
                {
                    "event_id": item["collection_id"],
                    "platform": item["platform"],
                    "query": item["query"],
                    "operation": " / ".join(item.get("collection_modes_used", [])),
                    "minute_bucket": item["collected_at"][:16],
                    "polling_window": "local_public_intelligence_window",
                    "write_api_used": False,
                    "automated_login_scrape": False,
                    "bypass_platform_limits": False,
                    "auto_interaction": False,
                    "source_boundary": item["execution_boundary"],
                }
            )
        return events

    def _risk_feed(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        feed: list[dict[str, Any]] = []
        feed.extend(self._rate_limit_risks(events))
        feed.extend(self._repeated_query_risks(events))
        feed.extend(self._suspicious_pattern_risks(events))
        feed.extend(self._write_api_risks(events))
        feed.extend(self._excessive_polling_risks(events))
        feed.extend(self._forbidden_behavior_risks(events))
        if not feed:
            feed.append(
                {
                    "risk_id": "COMPLIANCE-RISK-0001",
                    "risk_type": "collection compliance",
                    "platform": "all",
                    "status": "safe",
                    "severity": "low",
                    "evidence": "No rate limit, repeated query, suspicious pattern, write API, excessive polling, or forbidden collection behavior detected.",
                    "blocked_action": "none",
                    "recommended_action": "Continue read-only public intelligence collection.",
                }
            )
        return feed

    def _rate_limit_risks(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        risks = []
        counts = Counter((item.get("platform", "unknown"), item.get("minute_bucket", "")) for item in events)
        limit = self.limits["requests_per_minute"]
        for (platform, bucket), count in sorted(counts.items()):
            status = "blocked" if count > limit else "watch" if count >= int(limit * 0.8) else "safe"
            risks.append(
                self._risk(
                    risk_type="rate limit",
                    platform=platform,
                    status=status,
                    severity="high" if status == "blocked" else "medium" if status == "watch" else "low",
                    evidence=f"{platform} collected {count}/{limit} events in minute bucket {bucket}.",
                    blocked_action="pause collection for bucket" if status == "blocked" else "none",
                    recommended_action="Slow or pause collection before platform limits are approached." if status != "safe" else "Continue read-only collection.",
                )
            )
        return risks

    def _repeated_query_risks(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        risks = []
        counts = Counter((item.get("platform", "unknown"), item.get("query", "")) for item in events if item.get("query"))
        limit = self.limits["repeated_query_limit"]
        for (platform, query), count in sorted(counts.items()):
            if count <= 1:
                continue
            status = "blocked" if count > limit else "watch"
            risks.append(
                self._risk(
                    risk_type="repeated queries",
                    platform=platform,
                    status=status,
                    severity="medium" if status == "watch" else "high",
                    evidence=f"Query repeated {count} times on {platform}: {query}",
                    blocked_action="deduplicate before next collection" if status == "blocked" else "none",
                    recommended_action="Deduplicate repeated queries and widen the collection interval.",
                )
            )
        return risks

    def _suspicious_pattern_risks(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        risks = []
        platform_operations: dict[str, set[str]] = {}
        for item in events:
            platform_operations.setdefault(item.get("platform", "unknown"), set()).add(item.get("operation", "unknown"))
        for platform, operations in sorted(platform_operations.items()):
            if len(operations) >= 4:
                risks.append(
                    self._risk(
                        risk_type="suspicious pattern",
                        platform=platform,
                        status="watch",
                        severity="medium",
                        evidence=f"{platform} used many collection operation patterns: {', '.join(sorted(operations))}.",
                        blocked_action="none",
                        recommended_action="Split collection runs and keep each run's intent narrow.",
                    )
                )
        return risks

    def _write_api_risks(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        risks = []
        for item in events:
            operation = str(item.get("operation", ""))
            write_used = bool(item.get("write_api_used")) or any(token in operation for token in WRITE_API_OPERATIONS)
            if write_used:
                risks.append(
                    self._risk(
                        risk_type="write API usage",
                        platform=item.get("platform", "unknown"),
                        status="blocked",
                        severity="critical",
                        evidence=f"Write-side operation detected in collection event {item.get('event_id', 'unknown')}: {operation}",
                        blocked_action="write API",
                        recommended_action="Stop the event and route it to Human Gate. Live collection must remain read-only.",
                    )
                )
        return risks

    def _excessive_polling_risks(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        risks = []
        counts = Counter((item.get("platform", "unknown"), item.get("polling_window", "")) for item in events)
        limit = self.limits["polling_events_per_window"]
        for (platform, window), count in sorted(counts.items()):
            if count <= limit:
                continue
            risks.append(
                self._risk(
                    risk_type="excessive polling",
                    platform=platform,
                    status="blocked",
                    severity="high",
                    evidence=f"{platform} collected {count}/{limit} events in polling window {window}.",
                    blocked_action="polling",
                    recommended_action="Back off polling interval and require human approval before resuming.",
                )
            )
        return risks

    def _forbidden_behavior_risks(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        risks = []
        checks = [
            ("automated_login_scrape", "automated login scraping"),
            ("bypass_platform_limits", "platform-limit bypass"),
            ("auto_interaction", "automated interaction"),
        ]
        for item in events:
            for field, label in checks:
                if item.get(field):
                    risks.append(
                        self._risk(
                            risk_type=label,
                            platform=item.get("platform", "unknown"),
                            status="blocked",
                            severity="critical",
                            evidence=f"Forbidden behavior detected in event {item.get('event_id', 'unknown')}: {label}.",
                            blocked_action=label,
                            recommended_action="Block collection and require manual compliance review.",
                        )
                    )
        return risks

    def _risk(
        self,
        risk_type: str,
        platform: str,
        status: str,
        severity: str,
        evidence: str,
        blocked_action: str,
        recommended_action: str,
    ) -> dict[str, Any]:
        return {
            "risk_id": f"COMPLIANCE-RISK-{self._next_id():04d}",
            "risk_type": risk_type,
            "platform": platform,
            "status": status,
            "severity": severity,
            "evidence": evidence,
            "blocked_action": blocked_action,
            "recommended_action": recommended_action,
            "write_operations_enabled": False,
            "automatic_interaction_enabled": False,
            "checked_at": utc_now_iso(),
        }

    def _next_id(self) -> int:
        if not hasattr(self, "_risk_counter"):
            self._risk_counter = 0
        self._risk_counter += 1
        return self._risk_counter

    @staticmethod
    def _summary(feed: list[dict[str, Any]]) -> dict[str, Any]:
        statuses = Counter(item["status"] for item in feed)
        severities = Counter(item["severity"] for item in feed)
        blocking = [item for item in feed if item["status"] == "blocked"]
        return {
            "guard_ready": True,
            "risk_items": len(feed),
            "safe": statuses.get("safe", 0),
            "watch": statuses.get("watch", 0),
            "blocked": statuses.get("blocked", 0),
            "critical": severities.get("critical", 0),
            "blocking_risk": bool(blocking),
            "highest_severity": "critical" if severities.get("critical") else "high" if severities.get("high") else "medium" if severities.get("medium") else "low",
            "read_only_collection_allowed": not bool(blocking),
            "automated_login_scrape_allowed": False,
            "platform_limit_bypass_allowed": False,
            "write_api_allowed": False,
            "auto_interaction_allowed": False,
            "post_enabled": False,
            "reply_enabled": False,
            "dm_enabled": False,
            "follow_enabled": False,
            "like_enabled": False,
        }


if __name__ == "__main__":
    result = CollectionComplianceGuard().evaluate()
    print(json.dumps({"status": result["status"], "risks": result["complianceGuardSummary"]["risk_items"]}, indent=2))
