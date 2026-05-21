from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.knowledge_service import KnowledgeBaseStore
from services.reply_engine import ReplyDraftStore
from services.workspace_service import WorkspaceStore


def load_sample(name: str) -> dict:
    return json.loads((PROJECT_ROOT / "runtime" / "samples" / name).read_text(encoding="utf-8"))


def main() -> None:
    templates = load_sample("eu_us_english_content_templates.json")
    rules = load_sample("eu_us_reply_workflow_rules.json")
    assert templates["workspace_id"] == rules["workspace_id"]

    root = Path("runtime/test_reply_workflow_workspaces")
    if root.exists():
        shutil.rmtree(root)

    workspace_store = WorkspaceStore(root)
    workspace_store.create(
        {
            "workspace_id": rules["workspace_id"],
            "name": "Europe and US Growth Lab",
            "owner": "AGOS",
            "product_name": "AI Growth Operating System",
            "industry": "growth_software",
            "target_markets": ["US", "UK", "DE", "FR"],
            "status": "active",
            "metadata": {"reply_rule_set_id": rules["rule_set_id"]},
        }
    )

    knowledge = KnowledgeBaseStore(workspace_store)
    knowledge.upsert(
        {
            "workspace_id": rules["workspace_id"],
            "brand_voice": "Helpful, specific, evidence-led, and non-hype.",
            "product_facts": [
                {
                    "title": "Core workflow",
                    "detail": "AGOS connects pain radar, content drafts, reply review, learning, and reporting.",
                }
            ],
            "faqs": [],
            "industry_notes": ["Discussion replies must be useful before they mention a product."],
            "content_templates": [],
        }
    )

    replies = ReplyDraftStore(workspace_store, knowledge)
    generated = [
        replies.generate(
            rules["workspace_id"],
            sample["platform"],
            sample["question"],
            sample["reply_id"],
        )
        for sample in rules["sample_questions"]
    ]

    assert {reply.source_platform for reply in generated} == {"reddit", "seo"}
    assert all(reply.review_status == "needs_review" for reply in generated)
    assert all(reply.risk_level == "normal" for reply in generated)
    assert all("automatic reply" in reply.draft_text for reply in generated)
    assert all("buy now" not in reply.draft_text.lower() for reply in generated)

    blocked_text = "Buy now, this is a limited offer. We guarantee results. Click my link."
    risk_level, reasons = ReplyDraftStore.assess_risk(blocked_text)
    blocked = replies.upsert(
        {
            "reply_id": "blocked_hard_sell_reply",
            "workspace_id": rules["workspace_id"],
            "source_platform": "reddit",
            "source_text": "Can someone recommend a practical workflow?",
            "draft_text": blocked_text,
            "review_status": "rejected",
            "risk_level": risk_level,
            "risk_reasons": reasons,
        }
    )
    assert blocked.risk_level == "blocked"
    assert blocked.review_status == "rejected"
    assert {"hard_sell", "impersonation"} <= set(blocked.risk_reasons)

    shutil.rmtree(root)
    print("reply workflow smoke test passed")


if __name__ == "__main__":
    main()
