from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.cross_platform_expansion_engine import CrossPlatformExpansionEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "cross_platform_expansion"
        report = CrossPlatformExpansionEngine(root).expand()

        assert report["report_id"] == "CROSS_PLATFORM_EXPANSION_REPORT"
        assert report["status"] == "active"
        assert report["scope"] == "local_draft_only_no_auto_publish"
        assert (root / "CROSS_PLATFORM_EXPANSION_REPORT.json").exists()
        assert (root / "expansion_strategies.json").exists()
        assert (root / "cross_platform_expansion_feed.json").exists()

        strategies = report["expansionStrategies"]
        feed = report["crossPlatformExpansionFeed"]
        assert strategies
        assert feed
        assert len(feed) == len(strategies)
        assert any(item["source_platform"] == "TikTok" for item in strategies)

        top = strategies[0]
        assert {"Reddit", "YouTube", "Instagram", "X", "SEO"}.intersection(set(top["target_platforms"]))
        assert top["requires_human_review"] is True
        assert "no_auto_publish" in top["prohibited_actions"]
        assert "no_platform_api_access" in top["prohibited_actions"]
        assert top["platform_plans"]
        assert all(plan["review_status"] == "needs_human_review" for plan in top["platform_plans"])
        assert any(plan["target_platform"] == "Reddit" for plan in top["platform_plans"])
        assert any(plan["target_platform"] == "SEO" for plan in top["platform_plans"])
        assert any("Tokyo" in item["cluster_name"] for item in strategies)

        saved = json.loads((root / "CROSS_PLATFORM_EXPANSION_REPORT.json").read_text(encoding="utf-8"))
        assert saved["expansionSummary"]["requires_human_review"] == len(strategies)

    print("cross platform expansion smoke test passed")


if __name__ == "__main__":
    main()
