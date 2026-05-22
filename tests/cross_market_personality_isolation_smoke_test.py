from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.personality_isolation_engine import PersonalityIsolationEngine


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        engine = PersonalityIsolationEngine(Path(tmp) / "personality_isolation")
        report = engine.run_check()

        assert report["status"] == "clear"
        assert report["review_required"] is False
        assert report["workspacePersonalityPollution"]["status"] == "clear"
        assert report["marketPersonalityPollution"]["status"] == "clear"
        assert report["platformPersonalityPollution"]["status"] == "clear"
        assert len(report["isolationMatrix"]) >= 4

        workspaces = {item["workspace"] for item in report["isolationMatrix"]}
        markets = {item["market"] for item in report["isolationMatrix"]}
        platforms = {item["platform"] for item in report["isolationMatrix"]}
        assert {"JAG-LAB", "PHILIPS-LAB"}.issubset(workspaces)
        assert {"Japan", "Korea", "Taiwan", "Europe / US"}.issubset(markets)
        assert {"reddit", "tiktok", "instagram", "youtube"}.issubset(platforms)

        philips = [item for item in report["isolationMatrix"] if item["workspace"] == "PHILIPS-LAB"][0]
        assert "travel guide" in philips["blocked_traits"]
        assert "japan train transfer" in philips["blocked_traits"]
        assert "travel guide" not in " ".join(philips["allowed_traits"]).lower()

        polluted_report = engine.run_check(
            [
                {
                    "scope_id": "bad_cross_market_case",
                    "workspace": "PHILIPS-LAB",
                    "market": "Europe / US",
                    "platform": "youtube",
                    "voice": "travel guide",
                    "allowed_traits": ["product proof", "tokyo anxiety"],
                    "blocked_traits": ["travel guide", "tokyo anxiety"],
                }
            ]
        )
        assert polluted_report["status"] == "needs_human_review"
        assert polluted_report["workspacePersonalityPollution"]["violations"]
        assert polluted_report["marketPersonalityPollution"]["violations"]
        assert polluted_report["platformPersonalityPollution"]["violations"]
        assert engine.report_path.exists()
        assert engine.matrix_path.exists()

    print("cross market personality isolation smoke test passed")


if __name__ == "__main__":
    main()
