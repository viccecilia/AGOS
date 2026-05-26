"""Problem Seeker Loop for merchant homepage promotion."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

from services.live_data_normalization_pipeline import LiveDataNormalizationPipeline
from services.merchant_promotion_workspace import MerchantPromotionWorkspace
from services.runtime_persistence import utc_now_iso
from services.seasonal_trend_import_trial import SeasonalTrendImportTrial


DEFAULT_OUTPUT_DIR = Path("runtime/problem_seeker_loop")
DEFAULT_IMPORT_DIR = DEFAULT_OUTPUT_DIR / "imports"


MANUAL_PROBLEMS = [
    {
        "source_type": "manual_import",
        "source_platform": "Reddit",
        "market": "US",
        "language": "en",
        "question_text": "Landing at Narita with snowboard bags and kids. Is a private transfer worth it?",
        "pain_points": ["large luggage", "kids", "airport transfer anxiety"],
        "detected_intent": "airport_transfer",
    },
    {
        "source_type": "manual_import",
        "source_platform": "Threads",
        "market": "Southeast Asia",
        "language": "en",
        "question_text": "Japan summer trip with elderly parents. How do we avoid too much walking between hotels and stations?",
        "pain_points": ["elderly support", "summer heat", "station transfer"],
        "detected_intent": "elderly_support",
    },
]


class ProblemSeekerLoop:
    """Collect local/read-only problem candidates for an active merchant workspace."""

    def __init__(
        self,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
        import_dir: str | Path = DEFAULT_IMPORT_DIR,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.import_dir = Path(import_dir)
        self.candidates_path = self.output_dir / "problem_candidates.json"
        self.feed_path = self.output_dir / "problem_seeker_feed.json"
        self.source_summary_path = self.output_dir / "problem_source_summary.json"
        self.summary_path = self.output_dir / "problem_seeker_summary.json"

    def run(self, manual_items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        merchant_report = MerchantPromotionWorkspace().build()
        active_profile = self._active_profile(merchant_report.get("merchantProfiles", []))
        raw_items = self._collect_inputs(merchant_report, manual_items or [])
        candidates = self._candidates(raw_items, active_profile)
        feed = self._feed(candidates)
        source_summary = self._source_summary(candidates)
        summary = self._summary(candidates, feed, source_summary, active_profile)
        payload = {
            "report_id": "PROBLEM_SEEKER_LOOP",
            "created_at": utc_now_iso(),
            "status": "problem_seeker_loop_ready",
            "phase": "MERCHANT_HOMEPAGE_GROWTH_ENGINE",
            "activeMerchantProfile": active_profile,
            "problemCandidates": candidates,
            "problemSeekerFeed": feed,
            "problemSourceSummary": source_summary,
            "problemSeekerSummary": summary,
            "supportedInputSources": [
                "CSV",
                "JSON",
                "RSS",
                "manual_import",
                "read_only_api_output",
                "runtime_normalized_live_data",
                "seasonal_trend_import_sample",
                "merchant_promotion_workspace",
            ],
            "safetyBoundary": "Problem Seeker Loop reads local/manual/read-only data only. It does not crawl login-only pages, auto-reply, auto-post, auto-DM, create accounts, contact users, bypass platform limits, or call platform write APIs.",
        }
        self.persist(payload)
        return payload

    def state(self) -> dict[str, Any]:
        if self.summary_path.exists():
            return {
                "report_id": "PROBLEM_SEEKER_LOOP",
                "status": "problem_seeker_loop_ready",
                "problemCandidates": json.loads(self.candidates_path.read_text(encoding="utf-8")) if self.candidates_path.exists() else [],
                "problemSeekerFeed": json.loads(self.feed_path.read_text(encoding="utf-8")) if self.feed_path.exists() else [],
                "problemSourceSummary": json.loads(self.source_summary_path.read_text(encoding="utf-8")) if self.source_summary_path.exists() else {},
                "problemSeekerSummary": json.loads(self.summary_path.read_text(encoding="utf-8")),
            }
        return self.run()

    def persist(self, payload: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.candidates_path.write_text(json.dumps(payload["problemCandidates"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.feed_path.write_text(json.dumps(payload["problemSeekerFeed"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.source_summary_path.write_text(json.dumps(payload["problemSourceSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.summary_path.write_text(json.dumps(payload["problemSeekerSummary"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _collect_inputs(self, merchant_report: dict[str, Any], manual_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        items.extend(self._from_merchant_workspace(merchant_report))
        items.extend(self._from_seasonal_trends())
        items.extend(self._from_normalized_live_data())
        items.extend(MANUAL_PROBLEMS)
        items.extend(manual_items)
        items.extend(self._from_import_files())
        return items

    @staticmethod
    def _active_profile(profiles: list[dict[str, Any]]) -> dict[str, Any]:
        for profile in profiles:
            if profile.get("workspace_id") == "jag_app_growth":
                return profile
        return profiles[0] if profiles else {}

    @staticmethod
    def _from_merchant_workspace(report: dict[str, Any]) -> list[dict[str, Any]]:
        items = []
        for row in report.get("homepageProblemOpportunities", []):
            items.append(
                {
                    "source_type": "merchant_promotion_workspace",
                    "source_platform": row.get("platform", "unknown"),
                    "market": row.get("market", "unknown"),
                    "language": row.get("language", "unknown"),
                    "question_text": row.get("user_problem", ""),
                    "pain_points": row.get("pain_points", []),
                    "detected_intent": row.get("intent", "unknown"),
                    "source_workspace_id": row.get("workspace_id"),
                    "source_problem_id": row.get("problem_id"),
                    "base_score": row.get("homepage_fit_score", 50),
                }
            )
        return items

    @staticmethod
    def _from_seasonal_trends() -> list[dict[str, Any]]:
        report = SeasonalTrendImportTrial().state()
        items = []
        for row in report.get("seasonalTrendMatches", []):
            if row.get("matched_season_id") == "NO_MATCH":
                continue
            items.append(
                {
                    "source_type": "seasonal_trend_import_sample",
                    "source_platform": "Google Trends style sample",
                    "market": row.get("target_market", "unknown"),
                    "language": "unknown",
                    "question_text": f"Travelers are searching for '{row.get('keyword')}'. What Japan mobility problem should the homepage answer?",
                    "pain_points": row.get("inferred_mobility_pain_points", []),
                    "detected_intent": (row.get("inferred_demand_types") or ["seasonal_travel_question"])[0],
                    "source_workspace_id": "jag_app_growth",
                    "source_problem_id": row.get("record_id"),
                    "base_score": row.get("confidence_score", 50),
                }
            )
        return items[:4]

    @staticmethod
    def _from_normalized_live_data() -> list[dict[str, Any]]:
        report = LiveDataNormalizationPipeline().state()
        items = []
        for row in report.get("normalizedLiveData", [])[:3]:
            items.append(
                {
                    "source_type": "runtime_normalized_live_data",
                    "source_platform": row.get("platform", "unknown"),
                    "market": row.get("market", "unknown"),
                    "language": row.get("language", "unknown"),
                    "question_text": row.get("question_text") or row.get("topic") or row.get("normalized_text") or "Read-only normalized signal needs a helpful answer.",
                    "pain_points": row.get("pain_points", []),
                    "detected_intent": row.get("demand_intent") or row.get("topic", "travel_question"),
                    "source_workspace_id": "jag_app_growth",
                    "source_problem_id": row.get("source_id", row.get("signal_id", "normalized-live")),
                    "base_score": row.get("training_value_score", row.get("trend_strength", 55)),
                }
            )
        return items

    def _from_import_files(self) -> list[dict[str, Any]]:
        self.import_dir.mkdir(parents=True, exist_ok=True)
        items: list[dict[str, Any]] = []
        for path in sorted(self.import_dir.glob("*.csv")):
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            items.extend({**row, "source_type": row.get("source_type", "csv"), "source_file": path.name} for row in rows)
        for path in sorted(self.import_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data = data.get("items", [])
            if isinstance(data, list):
                items.extend({**row, "source_type": row.get("source_type", "json"), "source_file": path.name} for row in data)
        for path in sorted(list(self.import_dir.glob("*.xml")) + list(self.import_dir.glob("*.rss"))):
            items.extend(self._from_rss(path))
        return items

    @staticmethod
    def _from_rss(path: Path) -> list[dict[str, Any]]:
        try:
            root = ET.fromstring(path.read_text(encoding="utf-8"))
        except ET.ParseError:
            return []
        items = []
        for node in root.findall(".//item"):
            title = node.findtext("title") or ""
            description = node.findtext("description") or ""
            items.append(
                {
                    "source_type": "rss",
                    "source_platform": "RSS",
                    "market": "unknown",
                    "language": "unknown",
                    "question_text": f"{title} {description}".strip(),
                    "pain_points": [],
                    "detected_intent": "rss_travel_question",
                    "source_file": path.name,
                }
            )
        return items

    def _candidates(self, raw_items: list[dict[str, Any]], profile: dict[str, Any]) -> list[dict[str, Any]]:
        candidates = []
        seen: set[str] = set()
        for index, raw in enumerate(raw_items, start=1):
            normalized = self._normalize_raw(raw)
            if not normalized["question_text"] or normalized["question_text"] in seen:
                continue
            seen.add(normalized["question_text"])
            workspace_id = self._route_workspace(normalized, profile)
            if workspace_id != profile.get("workspace_id"):
                continue
            score, reason = self._score(normalized, profile)
            candidates.append(
                {
                    "problem_id": f"SEEK-PROBLEM-{len(candidates) + 1:03d}",
                    "workspace_id": workspace_id,
                    "merchant_name": profile.get("merchant_name", ""),
                    "source_type": normalized["source_type"],
                    "source_platform": normalized["source_platform"],
                    "market": normalized["market"],
                    "language": normalized["language"],
                    "question_text": normalized["question_text"],
                    "pain_points": normalized["pain_points"],
                    "detected_intent": normalized["detected_intent"],
                    "homepage_fit_reason": reason,
                    "candidate_score": score,
                    "review_status": "needs_human_review",
                    "sample_data_only": True,
                    "auto_reply_allowed": False,
                    "auto_post_allowed": False,
                    "auto_dm_allowed": False,
                    "real_platform_api_called": False,
                    "write_api_called": False,
                    "source_reference": normalized.get("source_problem_id") or normalized.get("source_file") or "local_sample",
                }
            )
        return sorted(candidates, key=lambda item: (-item["candidate_score"], item["problem_id"]))

    @staticmethod
    def _normalize_raw(raw: dict[str, Any]) -> dict[str, Any]:
        pain_points = raw.get("pain_points", [])
        if isinstance(pain_points, str):
            pain_points = [item.strip() for item in pain_points.replace("|", ",").split(",") if item.strip()]
        return {
            "source_type": raw.get("source_type", "manual_import"),
            "source_platform": raw.get("source_platform", raw.get("platform", "unknown")),
            "market": raw.get("market", raw.get("target_market", "unknown")),
            "language": raw.get("language", "unknown"),
            "question_text": raw.get("question_text", raw.get("user_problem", raw.get("title", ""))).strip(),
            "pain_points": pain_points,
            "detected_intent": raw.get("detected_intent", raw.get("intent", "travel_question")),
            "source_workspace_id": raw.get("source_workspace_id", raw.get("workspace_id", "jag_app_growth")),
            "source_problem_id": raw.get("source_problem_id", raw.get("problem_id", raw.get("record_id", ""))),
            "source_file": raw.get("source_file", ""),
            "base_score": int(raw.get("base_score", raw.get("homepage_fit_score", raw.get("candidate_score", 55))) or 55),
        }

    @staticmethod
    def _route_workspace(item: dict[str, Any], profile: dict[str, Any]) -> str:
        text = " ".join([item.get("question_text", ""), item.get("detected_intent", ""), " ".join(item.get("pain_points", []))]).lower()
        appliance_terms = ["air fryer", "vacuum", "appliance", "kitchen", "maintenance"]
        travel_terms = ["japan", "tokyo", "kyoto", "airport", "transfer", "luggage", "fuji", "hotel", "station", "travel"]
        if any(term in text for term in appliance_terms) and not any(term in text for term in travel_terms):
            return "home_appliance_demo"
        return profile.get("workspace_id", "jag_app_growth")

    @staticmethod
    def _score(item: dict[str, Any], profile: dict[str, Any]) -> tuple[int, str]:
        text = " ".join([item["question_text"], item["detected_intent"], " ".join(item["pain_points"])]).lower()
        score = min(95, max(20, item.get("base_score", 55)))
        reasons = []
        for prop in profile.get("core_value_props", []):
            prop_terms = [term for term in prop.lower().replace("-", " ").split() if len(term) >= 5]
            if any(term in text for term in prop_terms):
                score += 5
                reasons.append(f"value prop overlap: {prop}")
                break
        for user in profile.get("target_users", []):
            user_terms = [term for term in user.lower().replace("-", " ").split() if len(term) >= 5]
            if any(term in text for term in user_terms):
                score += 4
                reasons.append(f"target user overlap: {user}")
                break
        if item.get("source_platform") in profile.get("target_platforms", []):
            score += 3
            reasons.append(f"target platform: {item.get('source_platform')}")
        if item.get("market") in profile.get("target_markets", []):
            score += 3
            reasons.append(f"target market: {item.get('market')}")
        if not reasons:
            reasons.append("travel mobility problem matches merchant homepage promotion scope")
        return min(100, score), "; ".join(reasons)

    @staticmethod
    def _feed(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "event": "problem_candidate_found",
                "problem_id": item["problem_id"],
                "workspace_id": item["workspace_id"],
                "merchant_name": item["merchant_name"],
                "source_platform": item["source_platform"],
                "market": item["market"],
                "candidate_score": item["candidate_score"],
                "summary": item["question_text"],
                "review_status": item["review_status"],
                "auto_reply_allowed": item["auto_reply_allowed"],
            }
            for item in candidates
        ]

    @staticmethod
    def _source_summary(candidates: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "source_type_counts": Counter(item["source_type"] for item in candidates).most_common(),
            "platform_counts": Counter(item["source_platform"] for item in candidates).most_common(),
            "market_counts": Counter(item["market"] for item in candidates).most_common(),
            "intent_counts": Counter(item["detected_intent"] for item in candidates).most_common(),
        }

    @staticmethod
    def _summary(
        candidates: list[dict[str, Any]],
        feed: list[dict[str, Any]],
        source_summary: dict[str, Any],
        profile: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "problem_seeker_ready": True,
            "active_workspace": profile.get("workspace_id", "jag_app_growth"),
            "active_merchant": profile.get("merchant_name", "Japan AI Guide App"),
            "candidate_count": len(candidates),
            "feed_items": len(feed),
            "supported_sources": [
                "CSV",
                "JSON",
                "RSS",
                "manual_import",
                "read_only_api_output",
                "runtime_normalized_live_data",
                "seasonal_trend_import_sample",
                "merchant_promotion_workspace",
            ],
            "top_sources": source_summary.get("source_type_counts", []),
            "top_platforms": source_summary.get("platform_counts", []),
            "top_markets": source_summary.get("market_counts", []),
            "all_candidates_need_human_review": all(item["review_status"] == "needs_human_review" for item in candidates),
            "auto_reply_allowed": any(item["auto_reply_allowed"] for item in candidates),
            "auto_post_allowed": any(item["auto_post_allowed"] for item in candidates),
            "write_api_called": any(item["write_api_called"] for item in candidates),
            "real_platform_api_called": any(item["real_platform_api_called"] for item in candidates),
            "sample_data_only": all(item["sample_data_only"] for item in candidates),
            "workspace_isolation_checked": True,
            "home_appliance_pollution_detected": any(item["workspace_id"] == "home_appliance_demo" for item in candidates),
        }


if __name__ == "__main__":
    result = ProblemSeekerLoop().run()
    print(json.dumps({"status": result["status"], "summary": result["problemSeekerSummary"]}, indent=2))
