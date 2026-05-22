from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.trend_clustering_engine import TrendClusteringEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "trend_clusters"
        report = TrendClusteringEngine(root).cluster()

        assert report["report_id"] == "TREND_CLUSTERING_REPORT"
        assert report["status"] == "active"
        assert report["scope"] == "local_only_no_external_platform_access"
        assert (root / "TREND_CLUSTERING_REPORT.json").exists()
        assert (root / "trend_clusters.json").exists()

        clusters = report["trendClusters"]
        assert clusters
        assert any(cluster["cross_platform"] for cluster in clusters)
        assert any(cluster["cluster_name"] == "Tokyo transport anxiety" for cluster in clusters)
        assert any("high_emotion" in cluster["emotion_tags"] for cluster in clusters)

        rainy_day = next(cluster for cluster in clusters if cluster["cluster_id"] == "trend_cluster_tokyo_rainy_day")
        assert rainy_day["cross_platform"] is True
        assert {"Reddit", "TikTok", "YouTube", "Instagram"}.issubset(set(rainy_day["platforms"]))
        assert rainy_day["similar_questions"]
        assert rainy_day["similar_trends"]

        saved = json.loads((root / "TREND_CLUSTERING_REPORT.json").read_text(encoding="utf-8"))
        assert saved["clusterSummary"]["cross_platform_clusters"] >= 1

    print("trend clustering smoke test passed")


if __name__ == "__main__":
    main()
