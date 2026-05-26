"""Read-only seasonal trend import trial for local Google Trends-style samples."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso
from services.seasonal_demand_calendar_engine import SeasonalDemandCalendarEngine


DEFAULT_SAMPLE_DIR = Path("runtime/seasonal_demand_calendar/import_samples")
DEFAULT_OUTPUT_DIR = Path("runtime/seasonal_trend_import_trial")
SUPPORTED_INPUTS = ["csv", "json", "manual_dict_list", "future_google_trends_api_placeholder"]


class SeasonalTrendImportTrial:
    """Import local sample trend records and map them to the seasonal calendar."""

    def __init__(
        self,
        sample_dir: str | Path = DEFAULT_SAMPLE_DIR,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ) -> None:
        self.sample_dir = Path(sample_dir)
        self.output_dir = Path(output_dir)
        self.records_path = self.output_dir / "trend_import_records.json"
        self.matches_path = self.output_dir / "seasonal_trend_matches.json"
        self.heatmap_path = self.output_dir / "seasonal_market_heatmap.json"
        self.interpretation_path = self.output_dir / "seasonal_demand_interpretation.json"
        self.summary_path = self.output_dir / "seasonal_trend_import_summary.json"

    def run(self, manual_records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        calendar_report = SeasonalDemandCalendarEngine().state()
        seasons = calendar_report.get("seasonalCalendar", [])
        records = self.load_records(manual_records or [])
        matches = [self._match_record(record, seasons) for record in records]
        heatmap = self._market_heatmap(matches)
        interpretation = self._interpret(matches, heatmap)
        summary = self._summary(records, matches, heatmap, interpretation)
        payload = {
            "report_id": "SEASONAL_TREND_IMPORT_TRIAL",
            "created_at": utc_now_iso(),
            "status": "seasonal_trend_import_trial_ready",
            "phase": "PREDICTIVE_DEMAND_INTELLIGENCE",
            "supportedInputs": SUPPORTED_INPUTS,
            "trendImportRecords": records,
            "seasonalTrendMatches": matches,
            "seasonalMarketHeatmap": heatmap,
            "seasonalDemandInterpretation": interpretation,
            "seasonalTrendImportSummary": summary,
            "futureGoogleTrendsApiAdapter": {
                "reserved": True,
                "connected": False,
                "status": "not_connected",
                "allowed_now": False,
            },
            "safetyBoundary": "Seasonal Trend Import Trial reads local CSV/JSON/manual sample records only. It does not call Google Trends, Google Search, social platforms, login pages, browser scraping, posting, replies, customer contact, driver dispatch, or platform write APIs.",
        }
        self.persist(payload)
        return payload

    def state(self) -> dict[str, Any]:
        if self.summary_path.exists():
            return {
                "report_id": "SEASONAL_TREND_IMPORT_TRIAL",
                "status": "seasonal_trend_import_trial_ready",
                "trendImportRecords": json.loads(self.records_path.read_text(encoding="utf-8")) if self.records_path.exists() else [],
                "seasonalTrendMatches": json.loads(self.matches_path.read_text(encoding="utf-8")) if self.matches_path.exists() else [],
                "seasonalMarketHeatmap": json.loads(self.heatmap_path.read_text(encoding="utf-8")) if self.heatmap_path.exists() else [],
                "seasonalDemandInterpretation": json.loads(self.interpretation_path.read_text(encoding="utf-8")) if self.interpretation_path.exists() else {},
                "seasonalTrendImportSummary": json.loads(self.summary_path.read_text(encoding="utf-8")),
            }
        return self.run()

    def load_records(self, manual_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        self.sample_dir.mkdir(parents=True, exist_ok=True)
        for path in sorted(self.sample_dir.glob("*.csv")):
            records.extend(self._load_csv(path))
        for path in sorted(self.sample_dir.glob("*.json")):
            records.extend(self._load_json(path))
        records.extend(self._normalize_record(item, f"manual-{index:03d}", "manual_import") for index, item in enumerate(manual_records, start=1))
        return records

    def persist(self, payload: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.records_path.write_text(json.dumps(payload["trendImportRecords"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.matches_path.write_text(json.dumps(payload["seasonalTrendMatches"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.heatmap_path.write_text(json.dumps(payload["seasonalMarketHeatmap"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.interpretation_path.write_text(json.dumps(payload["seasonalDemandInterpretation"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(payload["seasonalTrendImportSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _load_csv(self, path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        return [self._normalize_record(row, f"{path.stem}-{index:03d}", "csv") for index, row in enumerate(rows, start=1)]

    def _load_json(self, path: Path) -> list[dict[str, Any]]:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("records", [])
        if not isinstance(data, list):
            raise ValueError(f"JSON trend import must contain a list: {path}")
        return [self._normalize_record(row, f"{path.stem}-{index:03d}", "json") for index, row in enumerate(data, start=1)]

    @staticmethod
    def _normalize_record(row: dict[str, Any], record_id: str, fallback_source: str) -> dict[str, Any]:
        score = SeasonalTrendImportTrial._to_int(row.get("trend_score", row.get("trend_interest_score", row.get("score", 0))))
        return {
            "record_id": record_id,
            "keyword": str(row.get("keyword", "")).strip(),
            "target_market": str(row.get("market", row.get("target_market", row.get("target_market_hint", "unknown")))).strip() or "unknown",
            "language": str(row.get("language", "unknown")).strip() or "unknown",
            "trend_score": score,
            "source_type": str(row.get("source_type", fallback_source)).strip() or fallback_source,
            "source_file": str(row.get("source_file", "")).strip(),
            "notes": str(row.get("notes", "")).strip(),
            "sample_data_only": True,
            "real_google_trends_api_connected": False,
            "write_operations_enabled": False,
            "imported_at": utc_now_iso(),
        }

    @staticmethod
    def _match_record(record: dict[str, Any], seasons: list[dict[str, Any]]) -> dict[str, Any]:
        keyword = record.get("keyword", "")
        normalized_keyword = SeasonalTrendImportTrial._normalize_text(keyword)
        best: tuple[int, dict[str, Any], list[str]] = (0, {}, [])
        for season in seasons:
            score, reasons = SeasonalTrendImportTrial._season_score(normalized_keyword, record, season)
            if score > best[0]:
                best = (score, season, reasons)
        score, season, reasons = best
        matched = bool(season) and score >= 18
        confidence = min(95, max(12, score + int(record.get("trend_score", 0) * 0.35))) if matched else min(42, int(record.get("trend_score", 0) * 0.5))
        return {
            "record_id": record.get("record_id", ""),
            "keyword": keyword,
            "trend_score": record.get("trend_score", 0),
            "matched_season_id": season.get("season_id", "NO_MATCH") if matched else "NO_MATCH",
            "matched_season_name": season.get("season_name", "No confident seasonal match") if matched else "No confident seasonal match",
            "match_reason": "; ".join(reasons) if matched else "No strong keyword, location, market, or demand overlap with current seasonal calendar.",
            "target_market": record.get("target_market", "unknown"),
            "likely_locations": season.get("likely_locations", []) if matched else [],
            "inferred_mobility_pain_points": season.get("mobility_pain_points", []) if matched else [],
            "inferred_demand_types": season.get("predicted_demand_types", []) if matched else [],
            "confidence_score": confidence,
            "review_status": "needs_human_review" if matched and confidence >= 50 else "low_confidence_review",
            "source_type": record.get("source_type", "unknown"),
            "sample_data_only": True,
            "confirmed_demand": False,
            "real_google_trends_api_connected": False,
            "write_operations_enabled": False,
        }

    @staticmethod
    def _season_score(keyword: str, record: dict[str, Any], season: dict[str, Any]) -> tuple[int, list[str]]:
        score = 0
        reasons: list[str] = []
        market = str(record.get("target_market", "")).lower()
        for demand_keyword in season.get("demand_keywords", []):
            tokens = [token for token in SeasonalTrendImportTrial._normalize_text(demand_keyword).split() if len(token) >= 4]
            overlap = sorted({token for token in tokens if token in keyword})
            if overlap:
                delta = min(32, 8 * len(overlap))
                score += delta
                reasons.append(f"keyword overlap: {', '.join(overlap[:4])}")
        for location in season.get("likely_locations", []):
            if SeasonalTrendImportTrial._normalize_text(location) in keyword:
                score += 12
                reasons.append(f"location signal: {location}")
        for demand in season.get("predicted_demand_types", []):
            demand_tokens = demand.replace("_", " ").split()
            if any(token in keyword for token in demand_tokens):
                score += 8
                reasons.append(f"demand signal: {demand}")
        if any(str(item).lower() == market for item in season.get("target_markets", [])):
            score += 6
            reasons.append(f"target market overlap: {record.get('target_market')}")
        special_map = {
            "sakura": "SEASON-SAKURA",
            "cherry blossom": "SEASON-SAKURA",
            "golden week": "SEASON-GOLDEN-WEEK",
            "summer": "SEASON-SUMMER",
            "autumn": "SEASON-AUTUMN-LEAVES",
            "leaves": "SEASON-AUTUMN-LEAVES",
            "christmas": "SEASON-CHRISTMAS",
            "chinese new year": "SEASON-CHINESE-NEW-YEAR",
            "new year": "SEASON-JAPAN-NEW-YEAR",
            "suzuka": "SEASON-EVENTS",
            "event": "SEASON-EVENTS",
        }
        for phrase, season_id in special_map.items():
            if phrase in keyword and season.get("season_id") == season_id:
                score += 28
                reasons.append(f"season phrase: {phrase}")
        return score, reasons

    @staticmethod
    def _market_heatmap(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
        heat: dict[tuple[str, str, str], dict[str, Any]] = {}
        for item in matches:
            key = (item["matched_season_id"], item["matched_season_name"], item["target_market"])
            if key not in heat:
                heat[key] = {
                    "season_id": item["matched_season_id"],
                    "season_name": item["matched_season_name"],
                    "target_market": item["target_market"],
                    "heat_score": 0,
                    "signal_count": 0,
                    "average_confidence": 0,
                    "sample_data_only": True,
                    "review_status": "needs_human_review",
                }
            heat[key]["signal_count"] += 1
            heat[key]["heat_score"] += int(item.get("trend_score", 0))
            heat[key]["average_confidence"] += int(item.get("confidence_score", 0))
        rows = []
        for row in heat.values():
            count = max(1, row["signal_count"])
            row["heat_score"] = round(row["heat_score"] / count, 2)
            row["average_confidence"] = round(row["average_confidence"] / count, 2)
            if row["season_id"] == "NO_MATCH" or row["average_confidence"] < 50:
                row["review_status"] = "low_confidence_review"
            rows.append(row)
        return sorted(rows, key=lambda item: item["heat_score"], reverse=True)

    @staticmethod
    def _interpret(matches: list[dict[str, Any]], heatmap: list[dict[str, Any]]) -> dict[str, Any]:
        demand_counter: Counter[str] = Counter()
        pain_counter: Counter[str] = Counter()
        keyword_matches = []
        noisy = []
        review_queue = []
        for item in matches:
            if item["matched_season_id"] == "NO_MATCH" or item["confidence_score"] < 50:
                noisy.append(item)
            else:
                keyword_matches.append(
                    {
                        "keyword": item["keyword"],
                        "season_id": item["matched_season_id"],
                        "season_name": item["matched_season_name"],
                        "confidence_score": item["confidence_score"],
                        "sample_data_only": True,
                    }
                )
                demand_counter.update(item.get("inferred_demand_types", []))
                pain_counter.update(item.get("inferred_mobility_pain_points", []))
            review_queue.append(
                {
                    "review_id": f"TREND-REVIEW-{len(review_queue) + 1:03d}",
                    "record_id": item["record_id"],
                    "keyword": item["keyword"],
                    "matched_season_name": item["matched_season_name"],
                    "confidence_score": item["confidence_score"],
                    "reason": item["match_reason"],
                    "review_status": item["review_status"],
                    "sample_data_only": True,
                }
            )
        return {
            "keyword_by_season_matches": keyword_matches,
            "demand_type_ranking": SeasonalTrendImportTrial._rank(demand_counter, "demand_type"),
            "mobility_pain_point_ranking": SeasonalTrendImportTrial._rank(pain_counter, "pain_point"),
            "noisy_low_confidence_signals": noisy,
            "human_review_queue": review_queue,
            "top_market_heat": heatmap[:8],
            "interpretation_status": "sample_analysis_ready",
            "confirmed_demand": False,
            "api_status": "real_google_trends_api_not_connected",
            "write_action_status": "blocked",
        }

    @staticmethod
    def _summary(
        records: list[dict[str, Any]],
        matches: list[dict[str, Any]],
        heatmap: list[dict[str, Any]],
        interpretation: dict[str, Any],
    ) -> dict[str, Any]:
        matched = [item for item in matches if item["matched_season_id"] != "NO_MATCH"]
        high_confidence = [item for item in matched if item["confidence_score"] >= 60]
        return {
            "import_trial_ready": True,
            "imported_keyword_count": len(records),
            "matched_seasonal_signals": len(matched),
            "high_confidence_matches": len(high_confidence),
            "market_heatmap_rows": len(heatmap),
            "demand_type_count": len(interpretation.get("demand_type_ranking", [])),
            "mobility_pain_point_count": len(interpretation.get("mobility_pain_point_ranking", [])),
            "noisy_low_confidence_signals": len(interpretation.get("noisy_low_confidence_signals", [])),
            "human_review_queue_items": len(interpretation.get("human_review_queue", [])),
            "data_source_status": "sample_csv_json_manual_import_only",
            "api_status": "real_google_trends_api_not_connected",
            "write_action_status": "blocked",
            "sample_data_only": True,
            "confirmed_demand": False,
        }

    @staticmethod
    def _rank(counter: Counter[str], key_name: str) -> list[dict[str, Any]]:
        return [
            {key_name: key, "signal_count": value, "sample_data_only": True, "review_status": "needs_human_review"}
            for key, value in counter.most_common()
        ]

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(str(value).lower().replace("-", " ").replace("_", " ").split())

    @staticmethod
    def _to_int(value: Any) -> int:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0


if __name__ == "__main__":
    result = SeasonalTrendImportTrial().run()
    print(json.dumps({"status": result["status"], "summary": result["seasonalTrendImportSummary"]}, indent=2))
