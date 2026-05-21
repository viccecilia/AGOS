from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.account_matrix_service import AccountMatrixStore
from services.content_engine import ContentDraftStore
from services.knowledge_service import KnowledgeBaseStore
from services.learning_engine import LearningEventStore
from services.pain_point_engine import PainPointStore
from services.reply_engine import ReplyDraftStore
from services.report_engine import ReportEngine
from services.workspace_service import WorkspaceStore


def main() -> None:
    root = Path("runtime/test_jag_phase2_workspaces")
    if root.exists():
        shutil.rmtree(root)

    workspace_store = WorkspaceStore(root)
    workspace = workspace_store.create(
        {
            "workspace_id": "jag_ai_guide",
            "name": "Japan AI Guide Growth Workspace",
            "owner": "AGOS",
            "product_name": "Japan AI Guide",
            "industry": "travel",
            "target_markets": ["US", "EU", "KR", "TW"],
            "status": "active",
            "metadata": {
                "persona": "first-time and independent Japan travelers",
                "promotion_goal": "helpful, non-hard-sell discovery content",
            },
        }
    )
    assert workspace.workspace_id == "jag_ai_guide"

    knowledge = KnowledgeBaseStore(workspace_store)
    knowledge.upsert(
        {
            "workspace_id": "jag_ai_guide",
            "brand_voice": "Helpful, local-aware, specific, calm Japan travel guidance.",
            "product_facts": [{"title": "Core use", "detail": "AI-guided Japan planning and in-trip support"}],
            "faqs": [{"question": "Is it useful for a first Japan trip?", "answer": "Yes, especially for routing and local context."}],
            "industry_notes": ["Travelers struggle with train transfers, food ordering, and hidden local choices."],
            "content_templates": [{"name": "jag_tip", "template": "Traveler problem -> specific Japan tip -> gentle next step"}],
        }
    )

    accounts = AccountMatrixStore(workspace_store)
    for account in [
        ("jag_tiktok", "tiktok", "@jag_ai_guide", "Short practical Japan travel clips", "active"),
        ("jag_instagram", "instagram", "@jag.ai.guide", "Saveable carousel travel tips", "active"),
        ("jag_reddit", "reddit", "u/jag_ai_guide", "Helpful replies without hard selling", "needs_review"),
        ("jag_youtube", "youtube", "@JapanAIGuide", "Long form route and planning walkthroughs", "draft"),
        ("jag_seo", "seo", "japan-ai-guide", "Search pages for first-time traveler questions", "active"),
    ]:
        accounts.upsert(
            {
                "workspace_id": "jag_ai_guide",
                "account_id": account[0],
                "platform": account[1],
                "handle": account[2],
                "display_name": "Japan AI Guide",
                "status": account[4],
                "content_strategy": account[3],
                "risk_status": "watch" if account[1] == "reddit" else "normal",
            }
        )
    assert len(accounts.list("jag_ai_guide")) == 5

    pain = PainPointStore(workspace_store)
    pain.import_many(
        "jag_ai_guide",
        [
            {
                "pain_point_id": "jag_train_transfer",
                "source": "phase2_local_sample",
                "platform": "reddit",
                "market": "US",
                "audience": "first_time_traveler",
                "category": "transport",
                "title": "First-time travelers fear taking the wrong train transfer",
                "evidence": "Sample questions mention station complexity and limited Japanese.",
                "trend_score": 90,
                "urgency_score": 86,
                "value_score": 94,
                "tags": ["train", "station", "first_trip"],
            },
            {
                "pain_point_id": "jag_food_language",
                "source": "phase2_local_sample",
                "platform": "seo",
                "market": "EU",
                "audience": "family_traveler",
                "category": "food",
                "title": "Families worry about ordering food without Japanese",
                "evidence": "Sample search intent includes allergy, menu, and children.",
                "trend_score": 76,
                "urgency_score": 75,
                "value_score": 83,
                "tags": ["food", "language", "family"],
            },
        ],
    )
    assert pain.top("jag_ai_guide", 1)[0].pain_point_id == "jag_train_transfer"

    content = ContentDraftStore(workspace_store, knowledge, pain)
    drafts = content.generate_for_top_pain_points("jag_ai_guide", ["tiktok", "instagram", "reddit", "youtube", "seo"], limit=1)
    assert len(drafts) == 5
    assert all(draft.review_status == "needs_review" for draft in drafts)

    replies = ReplyDraftStore(workspace_store, knowledge)
    reply = replies.generate("jag_ai_guide", "reddit", "How do I avoid the wrong train in Tokyo?", "jag_reply_train_001")
    assert reply.review_status == "needs_review"
    assert reply.risk_level == "normal"

    learning = LearningEventStore(workspace_store)
    learning.record({"event_id": "jag_saved_train", "workspace_id": "jag_ai_guide", "target_type": "content_draft", "target_id": "jag_train_transfer_tiktok", "signal": "saved", "weight": 20})
    learning.record({"event_id": "jag_converted_train", "workspace_id": "jag_ai_guide", "target_type": "content_draft", "target_id": "jag_train_transfer_tiktok", "signal": "converted", "weight": 60})
    assert learning.recommendations("jag_ai_guide")[0]["target_id"] == "jag_train_transfer_tiktok"

    reports = [ReportEngine(workspace_store).generate("jag_ai_guide", kind) for kind in ["daily", "weekly", "monthly"]]
    assert {report.report_type for report in reports} == {"daily", "weekly", "monthly"}
    assert all("Sample" in report.summary for report in reports)

    shutil.rmtree(root)
    print("jag phase2 smoke test passed")


if __name__ == "__main__":
    main()
