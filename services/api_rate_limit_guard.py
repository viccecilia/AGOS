"""API rate limit and safety guard for read-only scout integrations."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


DEFAULT_LIMITS = {
    "requests_per_minute": 6,
    "requests_per_hour": 120,
    "requests_per_day": 600,
}

DEFAULT_API_EVENTS = [
    {
        "event_id": "API-EVT-0001",
        "platform": "Reddit",
        "query": "Tokyo transport anxiety",
        "minute_bucket": "2026-05-23T10:00",
        "hour_bucket": "2026-05-23T10",
        "day_bucket": "2026-05-23",
        "operation": "trend search",
    },
    {
        "event_id": "API-EVT-0002",
        "platform": "Reddit",
        "query": "Tokyo transport anxiety",
        "minute_bucket": "2026-05-23T10:00",
        "hour_bucket": "2026-05-23T10",
        "day_bucket": "2026-05-23",
        "operation": "keyword search",
    },
    {
        "event_id": "API-EVT-0003",
        "platform": "Reddit",
        "query": "Tokyo transport anxiety",
        "minute_bucket": "2026-05-23T10:00",
        "hour_bucket": "2026-05-23T10",
        "day_bucket": "2026-05-23",
        "operation": "hashtag search",
    },
    {
        "event_id": "API-EVT-0004",
        "platform": "Reddit",
        "query": "Tokyo station mistakes",
        "minute_bucket": "2026-05-23T10:00",
        "hour_bucket": "2026-05-23T10",
        "day_bucket": "2026-05-23",
        "operation": "public analytics",
    },
    {
        "event_id": "API-EVT-0005",
        "platform": "Reddit",
        "query": "Tokyo subway confusing",
        "minute_bucket": "2026-05-23T10:00",
        "hour_bucket": "2026-05-23T10",
        "day_bucket": "2026-05-23",
        "operation": "trend search",
    },
    {
        "event_id": "API-EVT-0006",
        "platform": "TikTok",
        "query": "Tokyo first trip mistakes",
        "minute_bucket": "2026-05-23T10:01",
        "hour_bucket": "2026-05-23T10",
        "day_bucket": "2026-05-23",
        "operation": "hashtag search",
    },
    {
        "event_id": "API-EVT-0007",
        "platform": "YouTube",
        "query": "IC card vs rail pass",
        "minute_bucket": "2026-05-23T10:02",
        "hour_bucket": "2026-05-23T10",
        "day_bucket": "2026-05-23",
        "operation": "public analytics",
    },
]


class APIRateLimitGuard:
    """Detect API usage that may approach platform safety boundaries."""

    def __init__(
        self,
        root: str | Path = "runtime/api_risk",
        limits: dict[str, int] | None = None,
    ) -> None:
        self.root = Path(root)
        self.limits = limits or dict(DEFAULT_LIMITS)
        self.report_path = self.root / "API_RATE_LIMIT_GUARD_REPORT.json"
        self.feed_path = self.root / "api_risk_feed.json"
        self.usage_path = self.root / "api_usage_summary.json"

    def evaluate(self, events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        api_events = events if events is not None else list(DEFAULT_API_EVENTS)
        usage = self._usage_summary(api_events)
        risk_feed = self._risk_feed(usage)
        report = {
            "report_id": "API_RATE_LIMIT_GUARD_REPORT",
            "created_at": utc_now_iso(),
            "status": "safety_guard_ready",
            "scope": "read_only_api_rate_limit_and_safety_guard",
            "limits": self.limits,
            "apiEvents": api_events,
            "apiUsageSummary": usage,
            "apiRiskFeed": risk_feed,
            "apiRiskSummary": self._summary(risk_feed),
            "safetyBoundary": "Guard evaluates read-only API usage only. It does not post, reply, follow, DM, or bypass platform limits.",
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
        self.feed_path.write_text(json.dumps(report["apiRiskFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.usage_path.write_text(json.dumps(report["apiUsageSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _usage_summary(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        minute_counts = Counter((item.get("platform", "unknown"), item.get("minute_bucket", "")) for item in events)
        hour_counts = Counter((item.get("platform", "unknown"), item.get("hour_bucket", "")) for item in events)
        day_counts = Counter((item.get("platform", "unknown"), item.get("day_bucket", "")) for item in events)
        repeated_queries = Counter((item.get("platform", "unknown"), item.get("query", "")) for item in events)
        platform_operations: dict[str, set[str]] = defaultdict(set)
        for item in events:
            platform_operations[item.get("platform", "unknown")].add(item.get("operation", "unknown"))
        return {
            "requests_per_minute": self._counter_records(minute_counts, "minute_bucket"),
            "requests_per_hour": self._counter_records(hour_counts, "hour_bucket"),
            "requests_per_day": self._counter_records(day_counts, "day_bucket"),
            "repeated_queries": [
                {"platform": platform, "query": query, "count": count}
                for (platform, query), count in repeated_queries.items()
                if query and count > 1
            ],
            "platform_operations": [
                {"platform": platform, "operations": sorted(operations)}
                for platform, operations in sorted(platform_operations.items())
            ],
        }

    @staticmethod
    def _counter_records(counter: Counter[tuple[str, str]], bucket_name: str) -> list[dict[str, Any]]:
        return [
            {"platform": platform, bucket_name: bucket, "count": count}
            for (platform, bucket), count in sorted(counter.items())
        ]

    def _risk_feed(self, usage: dict[str, Any]) -> list[dict[str, Any]]:
        feed: list[dict[str, Any]] = []
        checks = [
            ("requests_per_minute", "requests/minute", self.limits["requests_per_minute"], "minute_bucket"),
            ("requests_per_hour", "requests/hour", self.limits["requests_per_hour"], "hour_bucket"),
            ("requests_per_day", "requests/day", self.limits["requests_per_day"], "day_bucket"),
        ]
        for usage_key, label, limit, bucket_name in checks:
            for item in usage.get(usage_key, []):
                count = int(item["count"])
                feed.append(
                    {
                        "risk_id": f"RISK-{len(feed) + 1:04d}",
                        "platform": item["platform"],
                        "risk_type": label,
                        "current_count": count,
                        "limit": limit,
                        "usage_ratio": round(count / limit, 3),
                        "status": self._status(count, limit),
                        "bucket": item[bucket_name],
                        "why": f"{item['platform']} used {count}/{limit} {label} in {item[bucket_name]}.",
                        "recommended_action": self._action(count, limit),
                    }
                )
        for item in usage.get("repeated_queries", []):
            count = int(item["count"])
            feed.append(
                {
                    "risk_id": f"RISK-{len(feed) + 1:04d}",
                    "platform": item["platform"],
                    "risk_type": "repeated queries",
                    "current_count": count,
                    "limit": 2,
                    "usage_ratio": round(count / 2, 3),
                    "status": "watch" if count == 2 else "near_platform_risk",
                    "bucket": item["query"],
                    "why": f"Repeated query detected: {item['query']} appeared {count} times.",
                    "recommended_action": "Deduplicate query before sending another request.",
                }
            )
        suspicious = self._suspicious_patterns(usage)
        for item in suspicious:
            feed.append({"risk_id": f"RISK-{len(feed) + 1:04d}", **item})
        return feed

    @staticmethod
    def _status(count: int, limit: int) -> str:
        ratio = count / limit
        if ratio >= 1:
            return "blocked"
        if ratio >= 0.8:
            return "near_platform_risk"
        if ratio >= 0.5:
            return "watch"
        return "safe"

    @staticmethod
    def _action(count: int, limit: int) -> str:
        ratio = count / limit
        if ratio >= 1:
            return "Stop requests for this bucket and wait for reset."
        if ratio >= 0.8:
            return "Slow down and require human review before more requests."
        if ratio >= 0.5:
            return "Monitor frequency and avoid repeated searches."
        return "Continue read-only usage."

    def _suspicious_patterns(self, usage: dict[str, Any]) -> list[dict[str, Any]]:
        patterns = []
        for item in usage.get("platform_operations", []):
            operations = set(item.get("operations", []))
            if len(operations) >= 4:
                patterns.append(
                    {
                        "platform": item["platform"],
                        "risk_type": "suspicious pattern",
                        "current_count": len(operations),
                        "limit": 4,
                        "usage_ratio": 1.0,
                        "status": "watch",
                        "bucket": "mixed read operations",
                        "why": f"{item['platform']} used many read operation types in one window: {', '.join(sorted(operations))}.",
                        "recommended_action": "Split collection windows and keep query intent narrow.",
                    }
                )
        return patterns

    @staticmethod
    def _summary(feed: list[dict[str, Any]]) -> dict[str, Any]:
        statuses = Counter(item["status"] for item in feed)
        platform_risk = Counter(item["platform"] for item in feed if item["status"] in {"watch", "near_platform_risk", "blocked"})
        return {
            "risk_items": len(feed),
            "safe": statuses.get("safe", 0),
            "watch": statuses.get("watch", 0),
            "near_platform_risk": statuses.get("near_platform_risk", 0),
            "blocked": statuses.get("blocked", 0),
            "approaching_platform_risk": any(item["status"] in {"near_platform_risk", "blocked"} for item in feed),
            "highest_risk_platform": platform_risk.most_common(1)[0][0] if platform_risk else "none",
            "write_operations_enabled": False,
        }


if __name__ == "__main__":
    result = APIRateLimitGuard().evaluate()
    print(json.dumps({"status": result["status"], "risk_items": result["apiRiskSummary"]["risk_items"]}, indent=2))
