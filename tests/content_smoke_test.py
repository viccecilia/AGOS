from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.content_engine import ContentDraftStore
from services.knowledge_service import KnowledgeBaseStore
from services.pain_point_engine import PainPointStore
from services.workspace_service import WorkspaceStore


def main() -> None:
    root = Path("runtime/test_content_workspaces")
    if root.exists():
        shutil.rmtree(root)

    workspace_store = WorkspaceStore(root)
    workspace_store.create(
        {
            "workspace_id": "alpha_japan",
            "name": "Alpha Japan Workspace",
            "owner": "Alpha Co",
            "product_name": "Japan Guide",
            "industry": "travel",
            "target_markets": ["US"],
            "status": "active",
        }
    )

    knowledge_store = KnowledgeBaseStore(workspace_store)
    knowledge_store.upsert(
        {
            "workspace_id": "alpha_japan",
            "brand_voice": "Helpful, specific, calm travel guidance.",
            "product_facts": [{"title": "Coverage", "detail": "Tokyo, Kyoto, Osaka routes"}],
            "faqs": [{"question": "First trip?", "answer": "Yes."}],
            "industry_notes": ["Travelers need practical transit guidance."],
            "content_templates": [{"name": "tip", "template": "Problem -> tip -> next step"}],
        }
    )

    pain_store = PainPointStore(workspace_store)
    pain_store.import_many(
        "alpha_japan",
        [
            {
                "pain_point_id": "transit_confusion",
                "source": "local_sample",
                "platform": "reddit",
                "market": "US",
                "audience": "first_time_traveler",
                "category": "transport",
                "title": "Travelers are confused by train transfers",
                "evidence": "Sample users ask how to avoid wrong train transfers.",
                "trend_score": 88,
                "urgency_score": 80,
                "value_score": 92,
                "tags": ["train", "first_trip", "navigation"],
            }
        ],
    )

    content_store = ContentDraftStore(workspace_store, knowledge_store, pain_store)
    drafts = content_store.generate_for_top_pain_points(
        "alpha_japan",
        platforms=["tiktok", "instagram", "reddit", "youtube", "seo"],
        limit=1,
    )

    assert len(drafts) == 5
    assert all(draft.review_status == "needs_review" for draft in drafts)
    assert {draft.platform for draft in drafts} == {"tiktok", "instagram", "reddit", "youtube", "seo"}
    assert content_store.list("alpha_japan", platform="seo")[0].format == "seo_article"
    assert "Review required" in content_store.list("alpha_japan", platform="tiktok")[0].body

    shutil.rmtree(root)
    print("content smoke test passed")


if __name__ == "__main__":
    main()
