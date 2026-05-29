from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.global_batch_intelligence_collection import GlobalBatchIntelligenceCollection


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "global_batch_intelligence_collection"
        report = GlobalBatchIntelligenceCollection(root).collect()

        assert report["report_id"] == "GLOBAL_BATCH_INTELLIGENCE_COLLECTION_REPORT"
        assert report["round_id"] == "ROUND-GLOBAL-001"
        assert report["status"] == "global_batch_intelligence_collected"
        records = report["globalIntelligenceRecords"]
        assert len(records) >= 20
        assert len({item["market"] for item in records}) >= 5
        assert len({item["source_platform"] for item in records}) >= 4
        assert len({item["source_type"] for item in records}) >= 4

        required_fields = {
            "record_id",
            "source_type",
            "source_platform",
            "market",
            "language",
            "country",
            "region",
            "source_url",
            "raw_text",
            "keyword",
            "topic",
            "created_at",
            "sample_data_only",
            "read_only_source",
            "human_review_required",
        }
        for item in records:
            assert required_fields.issubset(item)
            assert item["read_only_source"] is True
            assert item["human_review_required"] is True
            assert item["credentials_read"] is False
            assert item["platform_write_api_called"] is False
            assert item["auto_contact_user_allowed"] is False

        summary = report["globalBatchCollectionSummary"]
        assert summary["record_count"] >= 20
        assert summary["market_count"] >= 5
        assert summary["platform_count"] >= 4
        assert summary["sample_first"] is True
        assert summary["read_only"] is True
        assert summary["audit_first"] is True
        assert summary["human_gated"] is True
        assert summary["contains_credentials"] is False
        assert summary["credentials_read"] is False
        assert summary["platform_write_api_called"] is False
        assert summary["all_records_read_only"] is True
        assert summary["all_records_need_human_review"] is True

        source_summary = report["globalSourceSummary"]
        assert source_summary["markets"]
        assert source_summary["platforms"]
        assert source_summary["languages"]
        assert source_summary["source_types"]

        for output_name in [
            "GLOBAL_BATCH_INTELLIGENCE_COLLECTION_REPORT.json",
            "global_intelligence_records.json",
            "global_source_summary.json",
            "global_batch_collection_feed.json",
            "global_batch_collection_summary.json",
        ]:
            path = root / output_name
            assert path.exists(), f"missing output: {output_name}"
            json.loads(path.read_text(encoding="utf-8"))

    print("global_batch_intelligence_collection_smoke_test passed")


if __name__ == "__main__":
    main()
