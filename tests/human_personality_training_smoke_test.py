from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.human_personality_training import HumanPersonalityTraining


def main() -> None:
    root = Path("runtime/test_human_personality_training")
    if root.exists():
        shutil.rmtree(root)

    trainer = HumanPersonalityTraining(root)
    base = {
        "workspace": "JAG-LAB",
        "platform": "reddit",
        "market": "Japan",
        "tone": "trusted_guide",
        "style": ["真实", "可信", "专业", "像导游", "不营销"],
        "reason": "This personality fits JAG operating style.",
    }
    approved = trainer.approve(base)
    rejected = trainer.reject({**base, "tone": "aggressive_hook", "reason": "Too promotional."})
    modified = trainer.modify(base, {**base, "tone": "community_helper", "style": ["真实", "耐心", "不营销"]})

    assert approved["decision"] == "approve"
    assert rejected["decision"] == "reject"
    assert modified["decision"] == "modify"
    summary = trainer.summary()
    memory = summary["preferenceMemory"]
    assert memory["approved_personality"]["JAG-LAB::reddit::trusted_guide"] == 1
    assert memory["rejected_personality"]["JAG-LAB::reddit::aggressive_hook"] == 1
    assert memory["modified_personality"]["JAG-LAB::reddit::trusted_guide"] == 1
    assert len(summary["events"]) == 3
    assert (root / "human_personality_training_events.json").exists()
    assert (root / "human_personality_preference_memory.json").exists()

    shutil.rmtree(root)
    print("human_personality_training_smoke_test passed")


if __name__ == "__main__":
    main()
