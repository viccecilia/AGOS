from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.knowledge_service import KnowledgeBaseStore
from services.reply_engine import ReplyDraftStore
from services.workspace_service import WorkspaceStore


def main() -> None:
    root = Path("runtime/test_reply_workspaces")
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
            "product_facts": [{"title": "Coverage", "detail": "Tokyo routes"}],
            "faqs": [{"question": "First trip?", "answer": "Yes."}],
            "industry_notes": ["Travelers need practical guidance."],
            "content_templates": [{"name": "reply", "template": "Clarify -> suggest -> review"}],
        }
    )

    reply_store = ReplyDraftStore(workspace_store, knowledge_store)
    reply = reply_store.generate("alpha_japan", "reddit", "How do I avoid wrong train transfers?", "reply_transit_001")
    assert reply.review_status == "needs_review"
    assert reply.risk_level == "normal"
    assert "human review" in reply.draft_text
    assert len(reply_store.list("alpha_japan")) == 1

    risk_level, reasons = reply_store.assess_risk("Buy now, guaranteed result, click my link")
    assert risk_level == "blocked"
    assert "hard_sell" in reasons

    shutil.rmtree(root)
    print("reply smoke test passed")


if __name__ == "__main__":
    main()
