from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from schemas.knowledge_schema import KnowledgeValidationError
from services.knowledge_service import KnowledgeBaseNotFoundError, KnowledgeBaseStore
from services.workspace_service import WorkspaceNotFoundError, WorkspaceStore


def main() -> None:
    root = Path("runtime/test_knowledge_workspaces")
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
    workspace_store.create(
        {
            "workspace_id": "beta_saas",
            "name": "Beta SaaS Workspace",
            "owner": "Beta Co",
            "product_name": "Growth SaaS",
            "industry": "software",
            "target_markets": ["JP"],
            "status": "active",
        }
    )

    knowledge_store = KnowledgeBaseStore(workspace_store)
    knowledge_store.upsert(
        {
            "workspace_id": "alpha_japan",
            "brand_voice": "Helpful, specific, calm travel guidance.",
            "product_facts": [{"title": "Coverage", "detail": "Tokyo, Kyoto, Osaka routes"}],
            "faqs": [{"question": "Can I use it for a first Japan trip?", "answer": "Yes."}],
            "industry_notes": ["Travelers need practical transit and food guidance."],
            "content_templates": [{"name": "short_tip", "template": "Problem -> tip -> next step"}],
        }
    )
    knowledge_store.upsert(
        {
            "workspace_id": "beta_saas",
            "brand_voice": "Clear, operational, B2B software tone.",
            "product_facts": [{"title": "Core value", "detail": "AI workflow automation"}],
            "faqs": [{"question": "Does it support reports?", "answer": "Yes."}],
            "industry_notes": ["Customers compare workflow automation speed."],
            "content_templates": [{"name": "case_note", "template": "Pain -> workflow -> result"}],
        }
    )

    assert knowledge_store.get("alpha_japan").brand_voice.startswith("Helpful")
    assert knowledge_store.get("beta_saas").brand_voice.startswith("Clear")
    assert knowledge_store.get("alpha_japan").faqs[0]["question"] != knowledge_store.get("beta_saas").faqs[0]["question"]

    try:
        knowledge_store.upsert(
            {
                "workspace_id": "missing_workspace",
                "brand_voice": "Should fail because workspace does not exist.",
                "product_facts": [],
                "faqs": [],
                "industry_notes": ["note"],
                "content_templates": [],
            }
        )
        raise AssertionError("Knowledge base accepted a missing workspace")
    except WorkspaceNotFoundError:
        pass

    try:
        knowledge_store.upsert(
            {
                "workspace_id": "alpha_japan",
                "brand_voice": "",
                "industry_notes": ["note"],
            }
        )
        raise AssertionError("Knowledge base accepted missing required fields")
    except KnowledgeValidationError:
        pass

    try:
        knowledge_store.get("unknown_workspace")
        raise AssertionError("Unknown workspace was accepted")
    except WorkspaceNotFoundError:
        pass

    shutil.rmtree(root)
    print("knowledge smoke test passed")


if __name__ == "__main__":
    main()
