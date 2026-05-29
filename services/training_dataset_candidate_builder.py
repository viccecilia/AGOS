"""Build replayable training dataset candidates from normalized social samples."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


ROUND_ID = "ROUND-REALDATA-007_TRAINING_DATASET_CANDIDATE_BUILDER"
DATASET_VERSION = "training-candidate-v0.1.0"
FILTER_VERSION = "sample-ingestion-privacy-filter-v0.1.0"
NORMALIZATION_VERSION = "social-signal-normalization-v0.1.0"
DEFAULT_INPUT_PATH = Path("runtime/real_data_samples/NORMALIZED_SOCIAL_SIGNAL_SAMPLE.json")
DEFAULT_OUTPUT_DIR = Path("runtime/training_candidates")

GROUPING_DIMENSIONS = [
    "language",
    "region",
    "platform",
    "content_type",
    "pain_category",
    "use_case_category",
    "mobility_relevance",
    "confidence_tier",
]


class TrainingDatasetCandidateBuilder:
    """Create candidate-only training dataset artifacts without starting training."""

    def __init__(
        self,
        input_path: str | Path = DEFAULT_INPUT_PATH,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ) -> None:
        self.input_path = Path(input_path)
        self.output_dir = Path(output_dir)
        self.policy_path = self.output_dir / "TRAINING_DATASET_CANDIDATE_POLICY.json"
        self.manifest_path = self.output_dir / "TRAINING_DATASET_CANDIDATE_MANIFEST.json"
        self.duplication_path = self.output_dir / "DUPLICATION_AND_NOVELTY_REPORT.json"
        self.replay_path = self.output_dir / "DATASET_REPLAY_MANIFEST.json"
        self.evidence_path = self.output_dir / "TRAINING_DATASET_CANDIDATE_EVIDENCE.json"

    def build(self) -> dict[str, Any]:
        created_at = utc_now_iso()
        normalized_sample = self._load_normalized_sample()
        source_records = normalized_sample.get("records", [])
        candidate_records, excluded_records = self._build_candidate_records(source_records, created_at)
        groups = self._build_groups(candidate_records)
        duplication = self._duplication_report(candidate_records, created_at)
        stage_signal = self._stage_transition_signal(candidate_records, excluded_records, duplication, groups)
        policy = self._policy(created_at)
        manifest = self._manifest(candidate_records, excluded_records, groups, stage_signal, normalized_sample, created_at)
        replay = self._replay_manifest(candidate_records, excluded_records, normalized_sample, created_at)
        evidence = self._evidence(policy, manifest, duplication, replay, created_at)
        result = {
            "trainingDatasetCandidatePolicy": policy,
            "trainingDatasetCandidateManifest": manifest,
            "duplicationAndNoveltyReport": duplication,
            "datasetReplayManifest": replay,
            "trainingDatasetCandidateEvidence": evidence,
        }
        self.persist(result)
        return result

    def state(self) -> dict[str, Any]:
        if self.evidence_path.exists():
            return {
                "trainingDatasetCandidatePolicy": json.loads(self.policy_path.read_text(encoding="utf-8")),
                "trainingDatasetCandidateManifest": json.loads(self.manifest_path.read_text(encoding="utf-8")),
                "duplicationAndNoveltyReport": json.loads(self.duplication_path.read_text(encoding="utf-8")),
                "datasetReplayManifest": json.loads(self.replay_path.read_text(encoding="utf-8")),
                "trainingDatasetCandidateEvidence": json.loads(self.evidence_path.read_text(encoding="utf-8")),
            }
        return self.build()

    def persist(self, result: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        write_map = {
            self.policy_path: result["trainingDatasetCandidatePolicy"],
            self.manifest_path: result["trainingDatasetCandidateManifest"],
            self.duplication_path: result["duplicationAndNoveltyReport"],
            self.replay_path: result["datasetReplayManifest"],
            self.evidence_path: result["trainingDatasetCandidateEvidence"],
        }
        for path, payload in write_map.items():
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _load_normalized_sample(self) -> dict[str, Any]:
        if not self.input_path.exists():
            raise FileNotFoundError(f"missing normalized social signal sample: {self.input_path}")
        return json.loads(self.input_path.read_text(encoding="utf-8"))

    @staticmethod
    def _policy(created_at: str) -> dict[str, Any]:
        return {
            "policy_id": "TRAINING_DATASET_CANDIDATE_POLICY",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "dataset_version": DATASET_VERSION,
            "input_requirements": {
                "privacy_filtered": True,
                "normalized_social_signal": True,
                "lineage_required": True,
                "replayable_required": True,
                "auditable_required": True,
                "human_review_required": True,
            },
            "grouping_dimensions": GROUPING_DIMENSIONS,
            "duplication_logic": [
                "exact duplicate",
                "semantic duplicate",
                "same question different language",
                "same pain different platform",
                "repeated demand cluster",
                "novelty score",
            ],
            "stage_transition_signals": [
                "repeated content ratio",
                "new demand ratio",
                "high-value pain cluster count",
                "unresolved category count",
                "confidence threshold",
                "sample coverage threshold",
            ],
            "safety_boundary": {
                "dataset_candidate_only": True,
                "training_allowed": False,
                "provider_execution_allowed": False,
                "memory_writeback_allowed": False,
                "promotion_allowed": False,
                "writeback_allowed": False,
                "contact_user_allowed": False,
                "private_messages_allowed": False,
                "sensitive_pii_allowed": False,
            },
        }

    def _build_candidate_records(self, records: list[dict[str, Any]], created_at: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        candidates: list[dict[str, Any]] = []
        excluded: list[dict[str, Any]] = []
        for index, record in enumerate(records, start=1):
            exclusion_reasons = self._exclusion_reasons(record)
            if exclusion_reasons:
                excluded.append(self._excluded_record(record, exclusion_reasons))
                continue
            use_case = self._use_case_category(record)
            confidence_tier = self._confidence_tier(record)
            mobility_tier = self._mobility_relevance_tier(record)
            candidate_id = f"TDC-{index:03d}"
            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "source_signal_id": record.get("signal_id", ""),
                    "source_record_id": record.get("source_record_id", ""),
                    "language": record.get("language", "unknown"),
                    "region": record.get("region", "region unknown"),
                    "platform": record.get("platform_id", record.get("platform", "unknown")),
                    "content_type": record.get("question_type", "uncategorized"),
                    "content_format": record.get("content_format", "unknown"),
                    "pain_category": record.get("pain_category", "uncategorized_pain"),
                    "use_case_category": use_case,
                    "mobility_relevance": mobility_tier,
                    "confidence_tier": confidence_tier,
                    "quality_scores": record.get("quality_scores", {}),
                    "noise_status": (record.get("noise_filter") or {}).get("noise_status", ""),
                    "lineage": record.get("lineage", {}),
                    "source_sample_data_only": True,
                    "candidate_data_only": True,
                    "human_review_required": True,
                    "training_allowed": False,
                    "provider_execution_allowed": False,
                    "memory_writeback_allowed": False,
                    "promotion_allowed": False,
                    "writeback_allowed": False,
                    "contact_user_allowed": False,
                    "replayable": True,
                    "auditable": True,
                    "created_at": created_at,
                }
            )
        return candidates, excluded

    @staticmethod
    def _exclusion_reasons(record: dict[str, Any]) -> list[str]:
        reasons: list[str] = []
        noise_filter = record.get("noise_filter") or {}
        lineage = record.get("lineage") or {}
        if noise_filter.get("unsafe_personal_data"):
            reasons.append("unsafe personal data or privacy redaction")
        if noise_filter.get("spam") or noise_filter.get("ads") or noise_filter.get("bot_like_content"):
            reasons.append("spam, ad, or bot-like content")
        if noise_filter.get("off_topic_content"):
            reasons.append("off-topic content")
        if record.get("review_status") != "needs_human_review":
            reasons.append("unexpected review status")
        if not lineage.get("lineage_complete"):
            reasons.append("missing lineage")
        if not record.get("replayable"):
            reasons.append("not replayable")
        if not record.get("auditable"):
            reasons.append("not auditable")
        if not lineage.get("sample_data_only"):
            reasons.append("source sample flag missing")
        return reasons

    @staticmethod
    def _excluded_record(record: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
        return {
            "source_signal_id": record.get("signal_id", ""),
            "source_record_id": record.get("source_record_id", ""),
            "platform": record.get("platform_id", record.get("platform", "unknown")),
            "language": record.get("language", "unknown"),
            "pain_category": record.get("pain_category", "uncategorized_pain"),
            "excluded_data_reason": reasons,
            "lineage": record.get("lineage", {}),
            "training_allowed": False,
            "replayable": bool(record.get("replayable", False)),
            "auditable": bool(record.get("auditable", False)),
        }

    @staticmethod
    def _use_case_category(record: dict[str, Any]) -> str:
        pain = record.get("pain_category", "")
        question = record.get("question_type", "")
        if "airport" in pain:
            return "airport_transfer_training_candidate"
        if "transport" in pain:
            return "transport_anxiety_training_candidate"
        if "luggage" in pain or "family" in pain:
            return "family_luggage_support_candidate"
        if "food" in pain or "visit" in pain or "recommendation" in question:
            return "visit_recommendation_candidate"
        return "unresolved_category"

    @staticmethod
    def _confidence_tier(record: dict[str, Any]) -> str:
        score = int((record.get("quality_scores") or {}).get("confidence_score", 0) or 0)
        if score >= 75:
            return "high_confidence"
        if score >= 55:
            return "medium_confidence"
        return "low_confidence"

    @staticmethod
    def _mobility_relevance_tier(record: dict[str, Any]) -> str:
        score = int((record.get("quality_scores") or {}).get("mobility_relevance", 0) or 0)
        if score >= 80:
            return "high_mobility_relevance"
        if score >= 50:
            return "medium_mobility_relevance"
        return "low_mobility_relevance"

    @staticmethod
    def _build_groups(records: list[dict[str, Any]]) -> dict[str, Any]:
        groups: dict[str, Any] = {}
        for dimension in GROUPING_DIMENSIONS:
            counter = Counter(str(record.get(dimension, "unknown")) for record in records)
            groups[dimension] = [
                {
                    "value": key,
                    "count": count,
                    "candidate_ids": [record["candidate_id"] for record in records if str(record.get(dimension, "unknown")) == key],
                }
                for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
            ]
        return groups

    @staticmethod
    def _duplication_report(records: list[dict[str, Any]], created_at: str) -> dict[str, Any]:
        exact_keys: dict[str, list[str]] = defaultdict(list)
        semantic_keys: dict[str, list[str]] = defaultdict(list)
        language_keys: dict[str, set[str]] = defaultdict(set)
        pain_platforms: dict[str, set[str]] = defaultdict(set)
        clusters: dict[str, list[str]] = defaultdict(list)

        for record in records:
            exact_key = "|".join([record["platform"], record["language"], record["pain_category"], record["content_type"]])
            semantic_key = "|".join([record["pain_category"], record["use_case_category"], record["mobility_relevance"]])
            exact_keys[exact_key].append(record["candidate_id"])
            semantic_keys[semantic_key].append(record["candidate_id"])
            language_keys[record["pain_category"]].add(record["language"])
            pain_platforms[record["pain_category"]].add(record["platform"])
            clusters[record["pain_category"]].append(record["candidate_id"])

        exact_duplicates = [
            {"duplicate_key": key, "candidate_ids": ids}
            for key, ids in exact_keys.items()
            if len(ids) > 1
        ]
        semantic_duplicates = [
            {"duplicate_key": key, "candidate_ids": ids}
            for key, ids in semantic_keys.items()
            if len(ids) > 1
        ]
        same_question_different_language = [
            {"pain_category": pain, "languages": sorted(languages)}
            for pain, languages in language_keys.items()
            if len(languages) > 1
        ]
        same_pain_different_platform = [
            {"pain_category": pain, "platforms": sorted(platforms)}
            for pain, platforms in pain_platforms.items()
            if len(platforms) > 1
        ]
        repeated_demand_clusters = [
            {"pain_category": pain, "candidate_ids": ids, "cluster_size": len(ids)}
            for pain, ids in clusters.items()
            if len(ids) > 1
        ]
        candidate_count = len(records)
        repeated_candidate_ids = {cid for item in repeated_demand_clusters for cid in item["candidate_ids"]}
        novelty_items = []
        for record in records:
            novelty_score = 55 if record["candidate_id"] in repeated_candidate_ids else 90
            if record["confidence_tier"] == "high_confidence":
                novelty_score += 5
            novelty_items.append(
                {
                    "candidate_id": record["candidate_id"],
                    "pain_category": record["pain_category"],
                    "novelty_score": min(100, novelty_score),
                    "novelty_reason": "repeated demand cluster" if record["candidate_id"] in repeated_candidate_ids else "new demand candidate",
                }
            )
        repeated_content_ratio = round(len(repeated_candidate_ids) / candidate_count, 3) if candidate_count else 0
        new_demand_ratio = round(1 - repeated_content_ratio, 3) if candidate_count else 0
        return {
            "report_id": "DUPLICATION_AND_NOVELTY_REPORT",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "candidate_count": candidate_count,
            "exact_duplicates": exact_duplicates,
            "semantic_duplicates": semantic_duplicates,
            "same_question_different_language": same_question_different_language,
            "same_pain_different_platform": same_pain_different_platform,
            "repeated_demand_clusters": repeated_demand_clusters,
            "novelty_scores": novelty_items,
            "repeated_content_ratio": repeated_content_ratio,
            "new_demand_ratio": new_demand_ratio,
            "training_allowed": False,
        }

    @staticmethod
    def _stage_transition_signal(
        records: list[dict[str, Any]],
        excluded_records: list[dict[str, Any]],
        duplication: dict[str, Any],
        groups: dict[str, Any],
    ) -> dict[str, Any]:
        high_value_count = sum(
            1
            for record in records
            if record["confidence_tier"] in {"high_confidence", "medium_confidence"}
            and record["mobility_relevance"] == "high_mobility_relevance"
        )
        unresolved_count = sum(1 for record in records if record["use_case_category"] == "unresolved_category")
        language_count = len(groups.get("language", []))
        platform_count = len(groups.get("platform", []))
        sample_coverage_threshold_met = len(records) >= 5 and language_count >= 2 and platform_count >= 2
        confidence_threshold_met = any(record["confidence_tier"] == "high_confidence" for record in records)
        return {
            "repeated_content_ratio": duplication["repeated_content_ratio"],
            "new_demand_ratio": duplication["new_demand_ratio"],
            "high_value_pain_cluster_count": high_value_count,
            "unresolved_category_count": unresolved_count,
            "confidence_threshold_met": confidence_threshold_met,
            "sample_coverage_threshold_met": sample_coverage_threshold_met,
            "excluded_record_count": len(excluded_records),
            "candidate_dataset_ready_for_review": len(records) > 0,
            "training_ready": False,
            "stage_transition_allowed": False,
            "stage_transition_recommendation": "Review candidate coverage, exclusions, bias, and duplicate pressure before any supervised dry-run or training gate.",
        }

    @staticmethod
    def _manifest(
        records: list[dict[str, Any]],
        excluded_records: list[dict[str, Any]],
        groups: dict[str, Any],
        stage_signal: dict[str, Any],
        normalized_sample: dict[str, Any],
        created_at: str,
    ) -> dict[str, Any]:
        return {
            "manifest_id": "TRAINING_DATASET_CANDIDATE_MANIFEST",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "dataset_version": DATASET_VERSION,
            "source_normalized_sample_id": normalized_sample.get("sample_id", ""),
            "source_record_count": normalized_sample.get("normalized_record_count", 0),
            "candidate_record_count": len(records),
            "excluded_record_count": len(excluded_records),
            "grouping_dimensions": GROUPING_DIMENSIONS,
            "groups": groups,
            "candidate_records": records,
            "excluded_records": excluded_records,
            "stage_transition_signal": stage_signal,
            "dataset_candidate_only": True,
            "training_allowed": False,
            "provider_execution_allowed": False,
            "memory_writeback_allowed": False,
            "replayable": True,
            "auditable": True,
        }

    @staticmethod
    def _replay_manifest(
        records: list[dict[str, Any]],
        excluded_records: list[dict[str, Any]],
        normalized_sample: dict[str, Any],
        created_at: str,
    ) -> dict[str, Any]:
        return {
            "manifest_id": "DATASET_REPLAY_MANIFEST",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "dataset_version": DATASET_VERSION,
            "filter_version": FILTER_VERSION,
            "normalization_version": NORMALIZATION_VERSION,
            "source_lineage": [
                {
                    "candidate_id": record["candidate_id"],
                    "source_signal_id": record["source_signal_id"],
                    "source_record_id": record["source_record_id"],
                    "lineage": record["lineage"],
                }
                for record in records
            ],
            "excluded_data_reasons": [
                {
                    "source_signal_id": record["source_signal_id"],
                    "excluded_data_reason": record["excluded_data_reason"],
                }
                for record in excluded_records
            ],
            "replay_instructions": [
                "Load NORMALIZED_SOCIAL_SIGNAL_SAMPLE.json.",
                "Apply exclusion rules for unsafe personal data, spam, ads, bot-like, off-topic, missing lineage, non-replayable, and non-auditable records.",
                "Regenerate grouping dimensions, duplication report, novelty scores, and stage transition signal.",
                "Do not start training from this manifest.",
                "Use this candidate only for audit, bias review, and supervised readiness review.",
            ],
            "input_hash_reference": normalized_sample.get("source_manifest_id", ""),
            "training_allowed": False,
            "provider_execution_allowed": False,
            "memory_writeback_allowed": False,
            "replayable": True,
            "auditable": True,
        }

    @staticmethod
    def _evidence(
        policy: dict[str, Any],
        manifest: dict[str, Any],
        duplication: dict[str, Any],
        replay: dict[str, Any],
        created_at: str,
    ) -> dict[str, Any]:
        candidates = manifest["candidate_records"]
        return {
            "evidence_id": "TRAINING_DATASET_CANDIDATE_EVIDENCE",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "schema_defined": True,
            "policy_defined": policy["policy_id"] == "TRAINING_DATASET_CANDIDATE_POLICY",
            "manifest_generated": manifest["manifest_id"] == "TRAINING_DATASET_CANDIDATE_MANIFEST",
            "duplication_report_generated": duplication["report_id"] == "DUPLICATION_AND_NOVELTY_REPORT",
            "replay_manifest_generated": replay["manifest_id"] == "DATASET_REPLAY_MANIFEST",
            "candidate_record_count": manifest["candidate_record_count"],
            "excluded_record_count": manifest["excluded_record_count"],
            "all_candidate_records_have_lineage": all(bool(record.get("lineage", {}).get("lineage_complete")) for record in candidates),
            "all_candidate_records_replayable": all(record.get("replayable") for record in candidates),
            "all_candidate_records_auditable": all(record.get("auditable") for record in candidates),
            "sensitive_pii_included": False,
            "private_messages_included": False,
            "training_started": False,
            "provider_execution_started": False,
            "memory_writeback_started": False,
            "promotion_started": False,
            "writeback_started": False,
            "users_contacted": False,
            "dataset_candidate_only": True,
            "training_allowed": False,
            "next_gate": "ROUND-REALDATA-008_DATASET_QUALITY_AND_BIAS_REVIEW",
        }


def main() -> None:
    TrainingDatasetCandidateBuilder().build()
    print("training dataset candidate artifacts generated")


if __name__ == "__main__":
    main()
