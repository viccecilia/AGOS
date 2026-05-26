from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.answer_to_homepage_draft_engine import AnswerToHomepageDraftEngine
from services.opportunity_qualification_engine import OpportunityQualificationEngine


def main() -> None:
    OpportunityQualificationEngine().qualify()
    report = AnswerToHomepageDraftEngine().build()
    drafts = report["answerDrafts"]
    variants = report["platformDraftVariants"]
    risk_review = report["draftRiskReview"]
    summary = report["answerToHomepageSummary"]

    assert report["status"] == "answer_to_homepage_drafts_ready"
    assert len(drafts) >= 3
    assert len(variants) >= len(drafts) * 8
    assert summary["answer_to_homepage_ready"] is True
    assert summary["draft_count"] == len(drafts)
    assert summary["drafts_need_human_review"] is True
    assert summary["auto_publish_allowed"] is False
    assert summary["forbidden_claims_passed"] is True
    assert risk_review["forbidden_claims_passed"] is True
    assert risk_review["all_need_human_review"] is True
    assert risk_review["auto_publish_allowed"] is False

    required = {
        "draft_id",
        "opportunity_id",
        "workspace_id",
        "merchant_name",
        "platform",
        "market",
        "direct_answer",
        "helpful_steps",
        "soft_cta",
        "homepage_reference",
        "platform_tone",
        "risk_notes",
        "forbidden_claim_check",
        "review_status",
        "auto_publish_allowed",
    }
    for draft in drafts:
        assert required <= set(draft), f"missing draft fields: {draft}"
        assert draft["direct_answer"].strip()
        assert draft["soft_cta"].strip()
        assert draft["helpful_steps"]
        assert draft["forbidden_claim_check"]["status"] == "passed"
        assert draft["review_status"] == "needs_human_review"
        assert draft["auto_publish_allowed"] is False
        assert draft["auto_reply_allowed"] is False
        assert "guaranteed booking" not in " ".join([draft["direct_answer"], draft["soft_cta"]]).lower()

    for output_name in [
        "answer_drafts.json",
        "platform_draft_variants.json",
        "draft_risk_review.json",
        "answer_to_homepage_summary.json",
    ]:
        path = PROJECT_ROOT / "runtime" / "answer_to_homepage_drafts" / output_name
        assert path.exists(), f"missing output: {output_name}"
        json.loads(path.read_text(encoding="utf-8"))

    print("answer_to_homepage_draft_smoke_test passed")


if __name__ == "__main__":
    main()
