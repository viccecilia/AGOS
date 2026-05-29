"""Global batch intelligence collection for read-only AGOS imports."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


DEFAULT_OUTPUT_DIR = Path("runtime/global_batch_intelligence_collection")
SUPPORTED_INPUT_SOURCES = [
    "CSV",
    "JSON",
    "RSS export",
    "manual import",
    "read-only API output",
    "Google Trends-style sample",
    "platform trend sample",
    "local research notes",
]
SUPPORTED_MARKETS = [
    "Japan",
    "US",
    "Europe",
    "Korea",
    "Taiwan",
    "Southeast Asia",
    "China outbound",
    "Global English",
]
PLATFORMS = ["Reddit", "TikTok", "YouTube", "X", "Instagram", "Threads", "SEO / Search", "Xiaohongshu"]
LANGUAGE_BY_MARKET = {
    "Japan": "ja",
    "US": "en",
    "Europe": "en",
    "Korea": "ko",
    "Taiwan": "zh-TW",
    "Southeast Asia": "en",
    "China outbound": "zh-CN",
    "Global English": "en",
}
COUNTRY_BY_MARKET = {
    "Japan": "Japan",
    "US": "United States",
    "Europe": "Europe",
    "Korea": "South Korea",
    "Taiwan": "Taiwan",
    "Southeast Asia": "Regional SEA",
    "China outbound": "China",
    "Global English": "Global",
}
TOPIC_PATTERNS = [
    {
        "topic": "airport transfer confusion",
        "keyword": "airport transfer",
        "raw_text": "Landing late with luggage and worried about airport transfer options.",
        "region": "airport corridor",
    },
    {
        "topic": "family trip mobility stress",
        "keyword": "family trip transport",
        "raw_text": "Family travel feels hard when kids, luggage, and station transfers are involved.",
        "region": "hotel zone",
    },
    {
        "topic": "event pickup demand",
        "keyword": "event pickup",
        "raw_text": "People ask how to leave a crowded event venue without waiting too long.",
        "region": "event venue",
    },
    {
        "topic": "public transport anxiety",
        "keyword": "confusing subway",
        "raw_text": "Visitors say public transport maps are confusing on the first trip.",
        "region": "city center",
    },
    {
        "topic": "seasonal crowd pressure",
        "keyword": "seasonal travel crowd",
        "raw_text": "Seasonal travel windows create concern about crowds, luggage, and transfers.",
        "region": "tourism district",
    },
]


class GlobalBatchIntelligenceCollection:
    """Collect global multi-market intelligence from local/read-only inputs."""

    def __init__(self, output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.report_path = self.output_dir / "GLOBAL_BATCH_INTELLIGENCE_COLLECTION_REPORT.json"
        self.records_path = self.output_dir / "global_intelligence_records.json"
        self.source_summary_path = self.output_dir / "global_source_summary.json"
        self.feed_path = self.output_dir / "global_batch_collection_feed.json"
        self.summary_path = self.output_dir / "global_batch_collection_summary.json"

    def collect(
        self,
        records: list[dict[str, Any]] | None = None,
        *,
        csv_path: str | Path | None = None,
        json_path: str | Path | None = None,
    ) -> dict[str, Any]:
        imported = []
        if csv_path:
            imported.extend(self._from_csv(Path(csv_path)))
        if json_path:
            imported.extend(self._from_json(Path(json_path)))
        if records:
            imported.extend(records)
        source_records = imported or self._sample_records(32)
        normalized = [self._normalize_record(index, item) for index, item in enumerate(source_records, start=1)]
        source_summary = self._source_summary(normalized)
        feed = self._feed(normalized)
        summary = self._summary(normalized, source_summary)
        report = {
            "report_id": "GLOBAL_BATCH_INTELLIGENCE_COLLECTION_REPORT",
            "round_id": "ROUND-GLOBAL-001",
            "created_at": utc_now_iso(),
            "status": "global_batch_intelligence_collected",
            "phase": "GLOBAL_INTELLIGENCE_COLLECTION",
            "supportedInputSources": SUPPORTED_INPUT_SOURCES,
            "supportedMarkets": SUPPORTED_MARKETS,
            "globalIntelligenceRecords": normalized,
            "globalSourceSummary": source_summary,
            "globalBatchCollectionFeed": feed,
            "globalBatchCollectionSummary": summary,
            "safetyBoundary": "Global Batch Intelligence Collection imports local, sample, manual, and read-only intelligence only. It does not crawl, log in, read credentials, post, reply, DM, follow, like, contact users, or call platform write APIs.",
        }
        self.persist(report)
        return report

    def state(self) -> dict[str, Any]:
        if self.report_path.exists():
            return json.loads(self.report_path.read_text(encoding="utf-8"))
        return self.collect()

    def persist(self, report: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.records_path.write_text(json.dumps(report["globalIntelligenceRecords"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.source_summary_path.write_text(json.dumps(report["globalSourceSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(report["globalBatchCollectionFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(report["globalBatchCollectionSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _from_csv(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]

    @staticmethod
    def _from_json(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("records", "items", "data"):
                if isinstance(payload.get(key), list):
                    return payload[key]
        return []

    @staticmethod
    def _sample_records(count: int) -> list[dict[str, Any]]:
        records = []
        source_types = [
            "manual import",
            "read-only API output",
            "Google Trends-style sample",
            "platform trend sample",
            "local research notes",
            "RSS export",
            "CSV",
            "JSON",
        ]
        for index in range(1, count + 1):
            market = SUPPORTED_MARKETS[(index - 1) % len(SUPPORTED_MARKETS)]
            platform = PLATFORMS[(index - 1) % len(PLATFORMS)]
            pattern = TOPIC_PATTERNS[(index - 1) % len(TOPIC_PATTERNS)]
            source_type = source_types[(index - 1) % len(source_types)]
            records.append(
                {
                    "source_type": source_type,
                    "source_platform": platform,
                    "market": market,
                    "language": LANGUAGE_BY_MARKET[market],
                    "country": COUNTRY_BY_MARKET[market],
                    "region": pattern["region"],
                    "source_url": f"sample://global-intelligence/{market.lower().replace(' ', '-')}/{platform.lower().split()[0]}/{index:03d}",
                    "raw_text": f"{pattern['raw_text']} Market={market}; Platform={platform}.",
                    "keyword": pattern["keyword"],
                    "topic": pattern["topic"],
                }
            )
        return records

    @staticmethod
    def _normalize_record(index: int, item: dict[str, Any]) -> dict[str, Any]:
        market = item.get("market") or SUPPORTED_MARKETS[(index - 1) % len(SUPPORTED_MARKETS)]
        platform = item.get("source_platform") or item.get("platform") or PLATFORMS[(index - 1) % len(PLATFORMS)]
        source_type = item.get("source_type") or "manual import"
        return {
            "record_id": item.get("record_id", f"GLOBAL-INTEL-{index:04d}"),
            "source_type": source_type,
            "source_platform": platform,
            "market": market,
            "language": item.get("language", LANGUAGE_BY_MARKET.get(market, "en")),
            "country": item.get("country", COUNTRY_BY_MARKET.get(market, market)),
            "region": item.get("region", "unknown"),
            "source_url": item.get("source_url", ""),
            "raw_text": item.get("raw_text", item.get("text", "")),
            "keyword": item.get("keyword", ""),
            "topic": item.get("topic", item.get("keyword", "unknown")),
            "created_at": item.get("created_at", utc_now_iso()),
            "sample_data_only": bool(item.get("sample_data_only", True)),
            "read_only_source": bool(item.get("read_only_source", True)),
            "human_review_required": bool(item.get("human_review_required", True)),
            "credentials_read": False,
            "platform_write_api_called": False,
            "auto_contact_user_allowed": False,
        }

    @staticmethod
    def _source_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "markets": dict(Counter(item["market"] for item in records)),
            "platforms": dict(Counter(item["source_platform"] for item in records)),
            "languages": dict(Counter(item["language"] for item in records)),
            "source_types": dict(Counter(item["source_type"] for item in records)),
            "sample_records": len([item for item in records if item["sample_data_only"]]),
            "read_only_records": len([item for item in records if item["read_only_source"]]),
            "human_review_required_records": len([item for item in records if item["human_review_required"]]),
        }

    @staticmethod
    def _feed(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "time": item["created_at"],
                "record_id": item["record_id"],
                "market": item["market"],
                "platform": item["source_platform"],
                "language": item["language"],
                "source_type": item["source_type"],
                "topic": item["topic"],
                "keyword": item["keyword"],
                "read_only_source": item["read_only_source"],
                "sample_data_only": item["sample_data_only"],
                "human_review_required": item["human_review_required"],
            }
            for item in records[:24]
        ]

    @staticmethod
    def _summary(records: list[dict[str, Any]], source_summary: dict[str, Any]) -> dict[str, Any]:
        return {
            "global_batch_collection_ready": True,
            "record_count": len(records),
            "market_count": len(source_summary["markets"]),
            "platform_count": len(source_summary["platforms"]),
            "language_count": len(source_summary["languages"]),
            "source_type_count": len(source_summary["source_types"]),
            "sample_first": True,
            "read_only": True,
            "audit_first": True,
            "human_gated": True,
            "contains_credentials": False,
            "credentials_read": False,
            "platform_write_api_called": False,
            "auto_contact_user_allowed": False,
            "all_records_read_only": all(item["read_only_source"] for item in records),
            "all_records_need_human_review": all(item["human_review_required"] for item in records),
            "next_recommendation": "Route global intelligence records into Global Pain Cluster Engine after human review.",
        }


if __name__ == "__main__":
    result = GlobalBatchIntelligenceCollection().collect()
    print(json.dumps({"status": result["status"], "summary": result["globalBatchCollectionSummary"]}, indent=2))
