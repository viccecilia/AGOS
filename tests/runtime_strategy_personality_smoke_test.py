from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.runtime_strategy_personality import RuntimeStrategyPersonalityEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        engine = RuntimeStrategyPersonalityEngine(Path(tmp) / "strategy_personality")
        state = engine.build_all(
            {
                "workspace": "JAG-LAB",
                "industry_pack": "Travel Pack / Lab",
                "market": "Japan",
                "pain_point": "Tokyo station transfer anxiety",
            }
        )

        matrix = state["strategyPersonalityMatrix"]
        by_platform = {item["platform"]: item for item in matrix}

        assert {"reddit", "tiktok", "x", "youtube"}.issubset(by_platform)
        assert "depth" in by_platform["reddit"]["operating_philosophy"].lower()
        assert "attention" in by_platform["tiktok"]["operating_philosophy"].lower()
        assert "live conversations" in by_platform["x"]["operating_philosophy"].lower()
        assert "searchable" in by_platform["youtube"]["content_shape"].lower()

        content_shapes = {item["content_shape"] for item in matrix}
        interaction_styles = {item["interaction_style"] for item in matrix}
        success_signals = {item["success_signal"] for item in matrix}
        assert len(content_shapes) == 4, "Each platform needs a distinct content shape"
        assert len(interaction_styles) == 4, "Each platform needs a distinct interaction style"
        assert len(success_signals) == 4, "Each platform needs distinct success signals"

        assert all(item["human_review_status"] == "needs_human_review" for item in matrix)
        assert state["platformOperatingPhilosophies"]["reddit"] != state["platformOperatingPhilosophies"]["tiktok"]
        assert len(state["strategyPersonalityFeed"]) == 4

        assert engine.state_path.exists(), "strategy personality state must be persisted"
        assert engine.matrix_path.exists(), "strategy personality matrix must be persisted"

    print("runtime strategy personality smoke test passed")


if __name__ == "__main__":
    main()
