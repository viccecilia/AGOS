from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.keyword_expansion_engine import KeywordExpansionEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        engine = KeywordExpansionEngine(Path(tmp) / "keyword_expansion")
        state = engine.build_from_patrol_groups()

        assert state["state_id"] == "KEYWORD_EXPANSION_STATE"
        assert state["status"] == "active"
        assert "tokyo transfer" in state["seedKeywords"]
        assert "air fryer cleaning" in state["seedKeywords"]
        assert "Tokyo transport anxiety" in state["canonicalPainPoints"]

        tokyo = engine.expand_keyword("tokyo transfer")
        assert tokyo["canonical_pain_point"] == "Tokyo transport anxiety"
        assert "tokyo subway confusing" in tokyo["synonyms"]
        assert "tokyo station maze" in tokyo["slang"]
        assert "i am scared of getting lost in tokyo" in tokyo["emotion_expressions"]
        assert "tokyo train hack" in tokyo["platform_lingo"]
        assert "东京地铁复杂" in tokyo["multilingual"]

        assert engine.normalize_phrase("Tokyo subway confusing") == "Tokyo transport anxiety"
        assert engine.normalize_phrase("东京地铁复杂") == "Tokyo transport anxiety"

        appliance = engine.expand_keyword("vacuum suction")
        assert appliance["canonical_pain_point"] == "Vacuum performance anxiety"
        assert "吸尘器吸力弱" in appliance["multilingual"]

        assert engine.state_path.exists()
        assert engine.matrix_path.exists()
        saved = json.loads(engine.state_path.read_text(encoding="utf-8"))
        assert len(saved["keywordExpansions"]) >= 8

    print("keyword expansion smoke test passed")


if __name__ == "__main__":
    main()
