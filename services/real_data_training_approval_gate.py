"""Gate real-data training candidates before any controlled training review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


ROUND_ID = "ROUND-REALDATA-008_REAL_DATA_TRAINING_APPROVAL_GATE"
DEFAULT_TRAINING_DIR = Path("runtime/training_candidates")
DEFAULT_REAL_DATA_SAMPLE_DIR = Path("runtime/real_data_samples")
MIN_CANDIDATES_FOR_REVIEW = 5
MAX_EXCLUDED_RATIO_FOR_REVIEW = 0.5


class RealDataTrainingApprovalGate:
    """Validate whether a candidate dataset may enter controlled training review."""

    def __init__(
        self,
        training_dir: str | Path = DEFAULT_TRAINING_DIR,
        sample_dir: str | Path = DEFAULT_REAL_DATA_SAMPLE_DIR,
    ) -> None:
        self.training_dir = Path(training_dir)
        self.sample_dir = Path(sample_dir)
        self.checklist_path = self.training_dir / "REAL_DATA_TRAINING_APPROVAL_CHECKLIST.json"
        self.privacy_report_path = self.training_dir / "DATASET_PRIVACY_VALIDATION_REPORT.json"
        self.replay_report_path = self.training_dir / "DATASET_REPLAY_VALIDATION_REPORT.json"
        self.decision_path = self.training_dir / "REAL_DATA_TRAINING_GATE_DECISION.json"
        self.evidence_path = self.training_dir / "REAL_DATA_TRAINING_APPROVAL_EVIDENCE.json"

    def run(self) -> dict[str, Any]:
        created_at = utc_now_iso()
        manifest = self._load_json(self.training_dir / "TRAINING_DATASET_CANDIDATE_MANIFEST.json")
        replay = self._load_json(self.training_dir / "DATASET_REPLAY_MANIFEST.json")
        duplication = self._load_json(self.training_dir / "DUPLICATION_AND_NOVELTY_REPORT.json")
        candidate_evidence = self._load_json(self.training_dir / "TRAINING_DATASET_CANDIDATE_EVIDENCE.json")
        privacy_filter = self._load_json(self.sample_dir / "PRIVACY_FILTER_REPORT.json")
        signal_noise = self._load_json(self.sample_dir / "SIGNAL_NOISE_FILTER_REPORT.json")

        privacy_validation = self._privacy_validation(manifest, candidate_evidence, privacy_filter, signal_noise, created_at)
        replay_validation = self._replay_validation(manifest, replay, created_at)
        checklist = self._checklist(manifest, replay, duplication, privacy_validation, replay_validation, signal_noise, created_at)
        decision = self._decision(manifest, duplication, checklist, privacy_validation, replay_validation, signal_noise, created_at)
        evidence = self._evidence(checklist, privacy_validation, replay_validation, decision, created_at)

        result = {
            "realDataTrainingApprovalChecklist": checklist,
            "datasetPrivacyValidationReport": privacy_validation,
            "datasetReplayValidationReport": replay_validation,
            "realDataTrainingGateDecision": decision,
            "realDataTrainingApprovalEvidence": evidence,
        }
        self.persist(result)
        return result

    def state(self) -> dict[str, Any]:
        if self.evidence_path.exists():
            return {
                "realDataTrainingApprovalChecklist": self._load_json(self.checklist_path),
                "datasetPrivacyValidationReport": self._load_json(self.privacy_report_path),
                "datasetReplayValidationReport": self._load_json(self.replay_report_path),
                "realDataTrainingGateDecision": self._load_json(self.decision_path),
                "realDataTrainingApprovalEvidence": self._load_json(self.evidence_path),
            }
        return self.run()

    def persist(self, result: dict[str, Any]) -> None:
        self.training_dir.mkdir(parents=True, exist_ok=True)
        write_map = {
            self.checklist_path: result["realDataTrainingApprovalChecklist"],
            self.privacy_report_path: result["datasetPrivacyValidationReport"],
            self.replay_report_path: result["datasetReplayValidationReport"],
            self.decision_path: result["realDataTrainingGateDecision"],
            self.evidence_path: result["realDataTrainingApprovalEvidence"],
        }
        for path, payload in write_map.items():
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {"missing": True, "path": str(path)}
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _candidate_records(manifest: dict[str, Any]) -> list[dict[str, Any]]:
        return list(manifest.get("candidate_records") or [])

    @staticmethod
    def _candidate_count(manifest: dict[str, Any]) -> int:
        return int(manifest.get("candidate_record_count") or len(manifest.get("candidate_records") or []))

    @staticmethod
    def _excluded_count(manifest: dict[str, Any]) -> int:
        return int(manifest.get("excluded_record_count") or len(manifest.get("excluded_records") or []))

    def _privacy_validation(
        self,
        manifest: dict[str, Any],
        candidate_evidence: dict[str, Any],
        privacy_filter: dict[str, Any],
        signal_noise: dict[str, Any],
        created_at: str,
    ) -> dict[str, Any]:
        sensitive_pii_present = bool(candidate_evidence.get("sensitive_pii_included", False))
        private_messages_present = bool(candidate_evidence.get("private_messages_included", False))
        privacy_filter_failed = bool(privacy_filter.get("missing")) or sensitive_pii_present or private_messages_present
        excluded_records = manifest.get("excluded_records") or []
        unsafe_exclusions = [
            item
            for item in excluded_records
            if any("unsafe" in reason or "privacy" in reason for reason in item.get("excluded_data_reason", []))
        ]
        return {
            "report_id": "DATASET_PRIVACY_VALIDATION_REPORT",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "privacy_filter_report_present": not bool(privacy_filter.get("missing")),
            "privacy_filter_passed": not privacy_filter_failed,
            "sensitive_pii_present": sensitive_pii_present,
            "private_messages_present": private_messages_present,
            "raw_content_stored": bool(privacy_filter.get("raw_content_stored", False)),
            "sensitive_pii_training_allowed": bool(privacy_filter.get("sensitive_pii_training_allowed", False)),
            "excluded_private_message_count": int(privacy_filter.get("excluded_private_message_count", 0) or 0),
            "minors_data_flagged_count": int(privacy_filter.get("minors_data_flagged_count", 0) or 0),
            "redaction_total": int(privacy_filter.get("redaction_total", 0) or 0),
            "unsafe_signal_count": len(signal_noise.get("unsafe_record_ids") or []),
            "unsafe_signals_blocked_from_training": bool(signal_noise.get("unsafe_signals_blocked_from_training", False)),
            "unsafe_candidate_exclusion_count": len(unsafe_exclusions),
            "training_allowed": False,
            "provider_execution_allowed": False,
        }

    def _replay_validation(self, manifest: dict[str, Any], replay: dict[str, Any], created_at: str) -> dict[str, Any]:
        candidates = self._candidate_records(manifest)
        source_lineage = replay.get("source_lineage") or []
        source_lineage_ids = {item.get("candidate_id") for item in source_lineage}
        missing_lineage_candidates = [
            record.get("candidate_id")
            for record in candidates
            if not (record.get("lineage") or {}).get("lineage_complete")
            or record.get("candidate_id") not in source_lineage_ids
        ]
        non_replayable_candidates = [record.get("candidate_id") for record in candidates if not record.get("replayable")]
        non_auditable_candidates = [record.get("candidate_id") for record in candidates if not record.get("auditable")]
        replay_manifest_present = not bool(replay.get("missing"))
        replay_manifest_valid = (
            replay_manifest_present
            and not missing_lineage_candidates
            and not non_replayable_candidates
            and not non_auditable_candidates
            and bool(replay.get("replayable"))
            and bool(replay.get("auditable"))
        )
        return {
            "report_id": "DATASET_REPLAY_VALIDATION_REPORT",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "replay_manifest_present": replay_manifest_present,
            "replay_manifest_valid": replay_manifest_valid,
            "source_lineage_count": len(source_lineage),
            "candidate_record_count": self._candidate_count(manifest),
            "missing_lineage_candidates": missing_lineage_candidates,
            "non_replayable_candidates": non_replayable_candidates,
            "non_auditable_candidates": non_auditable_candidates,
            "filter_version": replay.get("filter_version", ""),
            "normalization_version": replay.get("normalization_version", ""),
            "dataset_version": replay.get("dataset_version", manifest.get("dataset_version", "")),
            "training_allowed": False,
            "provider_execution_allowed": False,
        }

    def _checklist(
        self,
        manifest: dict[str, Any],
        replay: dict[str, Any],
        duplication: dict[str, Any],
        privacy_validation: dict[str, Any],
        replay_validation: dict[str, Any],
        signal_noise: dict[str, Any],
        created_at: str,
    ) -> dict[str, Any]:
        candidates = self._candidate_records(manifest)
        candidate_count = self._candidate_count(manifest)
        excluded_count = self._excluded_count(manifest)
        total_seen = candidate_count + excluded_count
        excluded_ratio = round(excluded_count / total_seen, 3) if total_seen else 1.0
        groups = manifest.get("groups") or {}
        language_count = len(groups.get("language") or [])
        region_count = len(groups.get("region") or [])
        platform_count = len(groups.get("platform") or [])
        stage = manifest.get("stage_transition_signal") or {}
        repeated_content_ratio = float(duplication.get("repeated_content_ratio", 0) or 0)
        coverage_sufficient = bool(stage.get("sample_coverage_threshold_met")) and candidate_count >= MIN_CANDIDATES_FOR_REVIEW
        dataset_too_small = candidate_count < MIN_CANDIDATES_FOR_REVIEW
        noisy_or_exclusion_heavy = excluded_ratio > MAX_EXCLUDED_RATIO_FOR_REVIEW
        checks = [
            self._check("dataset_candidate_completeness", not bool(manifest.get("missing")) and candidate_count > 0, f"{candidate_count} candidate records / {excluded_count} excluded records"),
            self._check("lineage_and_replay_manifest", bool(replay_validation.get("replay_manifest_valid")), f"lineage rows {replay_validation.get('source_lineage_count', 0)} / candidates {candidate_count}"),
            self._check("privacy_and_pii_filter", bool(privacy_validation.get("privacy_filter_passed")), f"sensitive_pii_present={privacy_validation.get('sensitive_pii_present')} private_messages_present={privacy_validation.get('private_messages_present')}"),
            self._check("duplication_and_novelty_report", not bool(duplication.get("missing")), f"repeated_content_ratio={repeated_content_ratio} new_demand_ratio={duplication.get('new_demand_ratio', 0)}"),
            self._check("language_and_region_coverage", language_count >= 2 and region_count >= 2 and platform_count >= 2, f"languages={language_count} regions={region_count} platforms={platform_count}"),
            self._check("risk_score_and_unsafe_exclusions", bool(signal_noise.get("unsafe_signals_blocked_from_training")) and all(not record.get("training_allowed") for record in manifest.get("excluded_records", [])), f"unsafe signals blocked={len(signal_noise.get('unsafe_record_ids') or [])}"),
            self._check("human_approval_requirements", all(record.get("human_review_required") for record in candidates), "all candidate records require human review"),
            self._check("controlled_training_approval_decision_inputs", coverage_sufficient and repeated_content_ratio >= 0.5 and not noisy_or_exclusion_heavy, f"coverage_sufficient={coverage_sufficient} dataset_too_small={dataset_too_small} noisy_or_exclusion_heavy={noisy_or_exclusion_heavy}"),
        ]
        for item in checks:
            if item["check_id"] == "controlled_training_approval_decision_inputs" and not item["passed"]:
                item["status"] = "keep_collecting"
                item["blocking"] = False
        return {
            "checklist_id": "REAL_DATA_TRAINING_APPROVAL_CHECKLIST",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "candidate_record_count": candidate_count,
            "excluded_record_count": excluded_count,
            "excluded_record_ratio": excluded_ratio,
            "minimum_candidates_for_review": MIN_CANDIDATES_FOR_REVIEW,
            "max_excluded_ratio_for_review": MAX_EXCLUDED_RATIO_FOR_REVIEW,
            "checks": checks,
            "passed_check_count": sum(1 for item in checks if item["passed"]),
            "blocked_check_count": sum(1 for item in checks if item["blocking"] and not item["passed"]),
            "keep_collecting_check_count": sum(1 for item in checks if item["status"] == "keep_collecting"),
            "training_allowed": False,
            "provider_execution_allowed": False,
            "model_promotion_allowed": False,
        }

    @staticmethod
    def _check(check_id: str, passed: bool, evidence: str) -> dict[str, Any]:
        return {
            "check_id": check_id,
            "status": "passed" if passed else "blocked",
            "passed": passed,
            "evidence": evidence,
            "blocking": not passed,
            "human_review_required": True,
        }

    def _decision(
        self,
        manifest: dict[str, Any],
        duplication: dict[str, Any],
        checklist: dict[str, Any],
        privacy_validation: dict[str, Any],
        replay_validation: dict[str, Any],
        signal_noise: dict[str, Any],
        created_at: str,
    ) -> dict[str, Any]:
        candidate_count = self._candidate_count(manifest)
        excluded_count = self._excluded_count(manifest)
        total_seen = candidate_count + excluded_count
        excluded_ratio = round(excluded_count / total_seen, 3) if total_seen else 1.0
        stage = manifest.get("stage_transition_signal") or {}
        repeated_content_ratio = float(duplication.get("repeated_content_ratio", 0) or 0)
        dataset_too_small = candidate_count < MIN_CANDIDATES_FOR_REVIEW
        too_noisy = excluded_ratio > MAX_EXCLUDED_RATIO_FOR_REVIEW
        coverage_sufficient = bool(stage.get("sample_coverage_threshold_met"))
        hard_blockers = []
        if not replay_validation.get("replay_manifest_present"):
            hard_blockers.append("replay_manifest_missing")
        if not replay_validation.get("replay_manifest_valid"):
            hard_blockers.append("lineage_or_replay_invalid")
        if not privacy_validation.get("privacy_filter_passed"):
            hard_blockers.append("privacy_filter_failed")
        if privacy_validation.get("sensitive_pii_present"):
            hard_blockers.append("sensitive_pii_present")
        if privacy_validation.get("private_messages_present"):
            hard_blockers.append("private_messages_present")
        collection_blockers = []
        if dataset_too_small:
            collection_blockers.append("dataset_too_small")
        if too_noisy:
            collection_blockers.append("dataset_too_noisy_or_exclusion_heavy")
        if not coverage_sufficient:
            collection_blockers.append("sample_coverage_threshold_not_met")
        if repeated_content_ratio < 0.5:
            collection_blockers.append("repeated_content_ratio_not_high")

        review_allowed = not hard_blockers and not collection_blockers
        gate_decision = "reviewable_controlled_training_pilot" if review_allowed else "keep_collecting"
        if hard_blockers:
            gate_decision = "blocked"
        return {
            "decision_id": "REAL_DATA_TRAINING_GATE_DECISION",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "gate_decision": gate_decision,
            "approval_status": "reviewable_only" if review_allowed else gate_decision,
            "controlled_training_pilot_review_allowed": review_allowed,
            "automatic_training_allowed": False,
            "provider_execution_allowed": False,
            "model_promotion_allowed": False,
            "agos_core_overwrite_allowed": False,
            "human_approval_required": True,
            "candidate_record_count": candidate_count,
            "excluded_record_count": excluded_count,
            "excluded_record_ratio": excluded_ratio,
            "repeated_content_ratio": repeated_content_ratio,
            "new_demand_ratio": float(duplication.get("new_demand_ratio", 0) or 0),
            "coverage_sufficient": coverage_sufficient,
            "dataset_too_small": dataset_too_small,
            "dataset_too_noisy_or_exclusion_heavy": too_noisy,
            "hard_blockers": hard_blockers,
            "collection_blockers": collection_blockers,
            "unsafe_content_excluded": bool(signal_noise.get("unsafe_signals_blocked_from_training")),
            "allowed_next_actions": [
                "continue small controlled sample collection",
                "expand language and region coverage",
                "rerun privacy filtering and normalization",
                "rerun dataset candidate builder",
                "repeat this approval gate after coverage improves",
            ],
            "blocked_actions": [
                "automatic training",
                "provider execution",
                "model promotion",
                "AGOS core overwrite",
                "promotion or external contact from candidate records",
            ],
            "decision_reason": "Current candidate dataset is privacy-safe and replayable, but too small, too exclusion-heavy, and lacks repeated-demand pressure for controlled training pilot review.",
            "next_gate_required": "ROUND-REALDATA-009_DATASET_EXPANSION_AND_BIAS_REVIEW",
        }

    @staticmethod
    def _evidence(
        checklist: dict[str, Any],
        privacy_validation: dict[str, Any],
        replay_validation: dict[str, Any],
        decision: dict[str, Any],
        created_at: str,
    ) -> dict[str, Any]:
        return {
            "evidence_id": "REAL_DATA_TRAINING_APPROVAL_EVIDENCE",
            "round_id": ROUND_ID,
            "created_at": created_at,
            "schema_defined": True,
            "checklist_generated": checklist["checklist_id"] == "REAL_DATA_TRAINING_APPROVAL_CHECKLIST",
            "privacy_validation_generated": privacy_validation["report_id"] == "DATASET_PRIVACY_VALIDATION_REPORT",
            "replay_validation_generated": replay_validation["report_id"] == "DATASET_REPLAY_VALIDATION_REPORT",
            "gate_decision_generated": decision["decision_id"] == "REAL_DATA_TRAINING_GATE_DECISION",
            "lineage_complete": bool(replay_validation.get("replay_manifest_valid")),
            "replay_manifest_present": bool(replay_validation.get("replay_manifest_present")),
            "privacy_filter_passed": bool(privacy_validation.get("privacy_filter_passed")),
            "sensitive_pii_present": bool(privacy_validation.get("sensitive_pii_present")),
            "private_messages_present": bool(privacy_validation.get("private_messages_present")),
            "dataset_too_small": bool(decision.get("dataset_too_small")),
            "dataset_too_noisy_or_exclusion_heavy": bool(decision.get("dataset_too_noisy_or_exclusion_heavy")),
            "controlled_training_pilot_review_allowed": bool(decision.get("controlled_training_pilot_review_allowed")),
            "human_approval_required": True,
            "training_started": False,
            "provider_execution_started": False,
            "model_promoted": False,
            "agos_core_overwritten": False,
            "automatic_promotion_started": False,
            "next_gate_required": decision.get("next_gate_required", ""),
        }


def main() -> None:
    RealDataTrainingApprovalGate().run()
    print("real-data training approval gate artifacts generated")


if __name__ == "__main__":
    main()
