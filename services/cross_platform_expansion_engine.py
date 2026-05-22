"""Cross-platform expansion planning for AGOS Scout Intelligence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso
from services.strategic_interpretation_engine import StrategicInterpretationEngine


class CrossPlatformExpansionEngine:
    """Turn hot platform signals into local, human-reviewed expansion strategies."""

    TARGET_PLATFORMS = ["Reddit", "YouTube", "Instagram", "X", "SEO"]

    def __init__(self, root: str | Path = "runtime/cross_platform_expansion") -> None:
        self.root = Path(root)
        self.report_path = self.root / "CROSS_PLATFORM_EXPANSION_REPORT.json"
        self.strategies_path = self.root / "expansion_strategies.json"
        self.feed_path = self.root / "cross_platform_expansion_feed.json"

    def expand(self, interpretations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        strategic_report = StrategicInterpretationEngine().state()
        source_interpretations = interpretations or strategic_report.get("strategicInterpretations", [])
        strategies = [self._strategy_from_interpretation(item) for item in source_interpretations]
        feed = self._build_feed(strategies)
        report = {
            "report_id": "CROSS_PLATFORM_EXPANSION_REPORT",
            "created_at": utc_now_iso(),
            "status": "active",
            "scope": "local_draft_only_no_auto_publish",
            "supportedExpansion": {
                "source": ["TikTok hot signal", "Reddit hot signal", "YouTube hot signal", "Instagram hot signal", "X hot signal", "SEO hot signal"],
                "targets": self.TARGET_PLATFORMS,
            },
            "expansionStrategies": strategies,
            "crossPlatformExpansionFeed": feed,
            "expansionSummary": {
                "total_strategies": len(strategies),
                "requires_human_review": len([item for item in strategies if item["requires_human_review"]]),
                "top_strategy": strategies[0]["expansion_id"] if strategies else "none",
                "top_focus": strategies[0]["cluster_name"] if strategies else "none",
            },
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.expand()

    def persist(self, report: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.strategies_path.write_text(json.dumps(report["expansionStrategies"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["crossPlatformExpansionFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _strategy_from_interpretation(self, item: dict[str, Any]) -> dict[str, Any]:
        source_platform = self._source_platform_for(item)
        targets = [platform for platform in self.TARGET_PLATFORMS if platform != source_platform]
        platform_plans = [self._platform_plan(item, source_platform, target) for target in targets]
        return {
            "expansion_id": "expansion_" + item.get("strategy_id", "unknown").replace("strategy_", ""),
            "strategy_id": item.get("strategy_id", "unknown"),
            "cluster_name": item.get("cluster_name", "Unknown trend"),
            "source_platform": source_platform,
            "target_platforms": targets,
            "heat_level": item.get("heat_level", "watch"),
            "opportunity_score": item.get("opportunity_score", 0),
            "expansion_strategy": self._summary_for(item, source_platform, targets),
            "platform_plans": platform_plans,
            "requires_human_review": True,
            "prohibited_actions": [
                "no_auto_publish",
                "no_auto_reply",
                "no_auto_login",
                "no_platform_api_access",
            ],
            "status": "draft_ready" if item.get("heat_level") in {"hot", "warming"} else "watch_only",
        }

    @staticmethod
    def _source_platform_for(item: dict[str, Any]) -> str:
        platform_direction = item.get("platform_direction", {})
        if "TikTok" in platform_direction:
            return "TikTok"
        return "TikTok"

    @staticmethod
    def _summary_for(item: dict[str, Any], source_platform: str, targets: list[str]) -> str:
        return (
            f"Convert {source_platform} signal for {item.get('cluster_name', 'this trend')} into "
            f"{', '.join(targets)} local draft assets, preserving the same pain point while adapting tone and format."
        )

    @staticmethod
    def _platform_plan(item: dict[str, Any], source_platform: str, target: str) -> dict[str, Any]:
        cluster_name = item.get("cluster_name", "Unknown trend")
        base = {
            "target_platform": target,
            "source_platform": source_platform,
            "cluster_name": cluster_name,
            "review_status": "needs_human_review",
            "status": "draft_only",
        }
        if target == "Reddit":
            base.update(
                {
                    "content_format": "helpful reply thread",
                    "rewrite_direction": "Turn the hook into a detailed, non-promotional answer with concrete steps.",
                    "draft_prompt": f"Write a Reddit-safe answer for {cluster_name} with practical detail and no hard CTA.",
                }
            )
        elif target == "YouTube":
            base.update(
                {
                    "content_format": "short explainer outline",
                    "rewrite_direction": "Turn the trend into a checklist video outline with problem, fix, and example route.",
                    "draft_prompt": f"Create a YouTube explainer outline for {cluster_name}.",
                }
            )
        elif target == "Instagram":
            base.update(
                {
                    "content_format": "carousel card plan",
                    "rewrite_direction": "Turn the trend into visual cards with one pain point per card and a calm guide tone.",
                    "draft_prompt": f"Create an Instagram carousel plan for {cluster_name}.",
                }
            )
        elif target == "X":
            base.update(
                {
                    "content_format": "short insight thread",
                    "rewrite_direction": "Compress the trend into a crisp observation plus 2-3 practical bullets.",
                    "draft_prompt": f"Create an X thread draft for {cluster_name}.",
                }
            )
        elif target == "SEO":
            base.update(
                {
                    "content_format": "search article brief",
                    "rewrite_direction": "Turn the trend into a search-intent brief with headings, FAQs, and safe advice.",
                    "draft_prompt": f"Create an SEO article brief for {cluster_name}.",
                }
            )
        return base

    @staticmethod
    def _build_feed(strategies: list[dict[str, Any]]) -> list[dict[str, Any]]:
        feed = []
        for strategy in strategies:
            feed.append(
                {
                    "time": utc_now_iso(),
                    "type": "cross_platform_expansion",
                    "cluster_name": strategy["cluster_name"],
                    "source_platform": strategy["source_platform"],
                    "target_platforms": strategy["target_platforms"],
                    "strategy": strategy["expansion_strategy"],
                    "status": strategy["status"],
                    "review_status": "needs_human_review",
                }
            )
        return feed


if __name__ == "__main__":
    result = CrossPlatformExpansionEngine().expand()
    print(json.dumps({"status": result["status"], "strategies": len(result["expansionStrategies"])}, indent=2))
