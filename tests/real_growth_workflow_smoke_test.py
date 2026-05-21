from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.answer_branch_engine import AnswerBranchStore
from services.learning_engine import LearningEventStore
from services.prospect_discovery_engine import ProspectDiscoveryEngine
from services.question_inbox_engine import QuestionInboxStore
from services.reply_attempt_engine import ReplyAttemptStore
from services.workspace_service import WorkspaceStore


def create_workspace(store: WorkspaceStore, workspace_id: str, product_name: str) -> None:
    store.create(
        {
            "workspace_id": workspace_id,
            "name": f"{product_name} Growth Workspace",
            "owner": "AGOS",
            "product_name": product_name,
            "industry": "growth",
            "target_markets": ["US"],
            "status": "active",
        }
    )


def main() -> None:
    root = Path("runtime/test_real_growth_workflow")
    if root.exists():
        shutil.rmtree(root)

    workspace_store = WorkspaceStore(root)
    create_workspace(workspace_store, "jag_ai_guide", "Japan AI Guide")
    create_workspace(workspace_store, "philips_home", "Philips Home Appliances")

    questions = QuestionInboxStore(workspace_store)
    discovery = ProspectDiscoveryEngine(workspace_store, questions)
    imported = discovery.import_questions(
        "jag_ai_guide",
        [
            {
                "question_id": "jag_train_help_001",
                "platform": "reddit",
                "language": "en",
                "market": "US",
                "audience": "first_time_japan_traveler",
                "source_url": "https://example.com/manual/reddit/jag_train_help_001",
                "question_text": "I am confused about Tokyo train transfers on my first Japan trip. What should I check first?",
                "pain_points": ["train_transfer", "first_trip"],
            }
        ],
    )
    assert imported[0].status == "new"
    assert "confused" in imported[0].emotion_tags
    questions.update_status("jag_ai_guide", "jag_train_help_001", "reviewing")

    branches = AnswerBranchStore(workspace_store, questions)
    reddit_branch = branches.upsert(
        {
            "branch_id": "jag_train_reddit_helpful",
            "workspace_id": "jag_ai_guide",
            "question_id": "jag_train_help_001",
            "platform": "reddit",
            "tone": "helpful peer advice",
            "reply_text": "Start by checking the exact station names, transfer count, and last-train risk. Keep the first route simple and review it before the trip.",
            "soft_cta": "If you share the route, I can help you sanity-check the transfer points.",
            "engagement_score": 0,
            "ignore_score": 0,
            "save_score": 0,
            "best_answer": False,
            "review_status": "needs_review",
        }
    )
    seo_branch = branches.upsert(
        {
            "branch_id": "jag_train_seo_structured",
            "workspace_id": "jag_ai_guide",
            "question_id": "jag_train_help_001",
            "platform": "seo",
            "tone": "structured checklist",
            "reply_text": "Use a checklist: origin station, destination station, transfer station, platform number, fare, and backup route.",
            "soft_cta": "Save the checklist before choosing the route.",
            "review_status": "needs_review",
        }
    )
    assert reddit_branch.review_status == "needs_review"
    assert seo_branch.platform == "seo"

    branches.approve("jag_ai_guide", "jag_train_reddit_helpful")
    questions.update_status("jag_ai_guide", "jag_train_help_001", "reply_ready")

    attempts = ReplyAttemptStore(workspace_store, questions, branches)
    attempt = attempts.upsert(
        {
            "reply_attempt_id": "jag_train_attempt_001",
            "workspace_id": "jag_ai_guide",
            "question_id": "jag_train_help_001",
            "branch_id": "jag_train_reddit_helpful",
            "platform": "reddit",
            "status": "draft",
        }
    )
    try:
        attempts.approve("jag_ai_guide", "missing_attempt")
        raise AssertionError("missing attempt was approved")
    except KeyError:
        pass
    approved_attempt = attempts.approve("jag_ai_guide", attempt.reply_attempt_id)
    assert approved_attempt.status == "approved"

    feedback_attempt = attempts.record_feedback(
        "jag_ai_guide",
        approved_attempt.reply_attempt_id,
        liked=2,
        replied=1,
        saved=1,
        shared=0,
    )
    assert feedback_attempt.status == "high_engagement"
    questions.update_status("jag_ai_guide", "jag_train_help_001", "learned")

    learning = LearningEventStore(workspace_store)
    events = learning.ingest_reply_attempt("jag_ai_guide", feedback_attempt.reply_attempt_id, attempts)
    assert {event.signal for event in events} >= {"liked", "positive_reply", "saved"}
    best = learning.update_best_answer_branch("jag_ai_guide", branches)
    assert best is not None
    assert best["target_id"] == "jag_train_reddit_helpful"
    assert branches.get("jag_ai_guide", "jag_train_reddit_helpful").best_answer is True
    assert branches.get("jag_ai_guide", "jag_train_seo_structured").best_answer is False

    discovery.import_questions(
        "philips_home",
        [
            {
                "question_id": "philips_airfryer_001",
                "platform": "seo",
                "language": "en",
                "market": "US",
                "audience": "home_cook",
                "source_url": "https://example.com/manual/seo/philips_airfryer_001",
                "question_text": "My air fryer food is unevenly cooked. What setting should I check?",
                "pain_points": ["cooking_quality"],
            }
        ],
    )
    assert questions.list("philips_home")[0].question_id == "philips_airfryer_001"
    assert questions.list("jag_ai_guide")[0].question_id == "jag_train_help_001"
    assert branches.list("philips_home") == []
    assert learning.recommendations("philips_home") == []

    shutil.rmtree(root)
    print("real growth workflow smoke test passed")


if __name__ == "__main__":
    main()
