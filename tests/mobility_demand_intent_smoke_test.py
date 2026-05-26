from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.mobility_demand_intent_engine import MobilityDemandIntentEngine


def main() -> None:
    report = MobilityDemandIntentEngine().build()
    intents = report["mobilityIntents"]
    high_value = report["highValueMobilityIntents"]
    low_value = report["lowValueSignals"]
    summary = report["mobilityIntentSummary"]

    assert report["status"] == "mobility_intents_classified"
    assert len(intents) >= 8, "must generate multiple mobility intents"
    assert high_value, "high-value mobility intents must be separated"
    assert low_value, "low-value signals must be separated"

    intent_types = {item["demand_intent"] for item in intents}
    assert "airport_transfer" in intent_types
    assert "private_charter" in intent_types
    assert "no_real_mobility_intent" in intent_types

    required_fields = {
        "intent_id",
        "source_id",
        "platform",
        "market",
        "language",
        "location",
        "season",
        "event",
        "demand_intent",
        "intent_strength_score",
        "conversion_potential_score",
        "urgency_score",
        "confidence_score",
        "recommended_route",
    }
    for item in intents:
        assert required_fields <= set(item), f"{item.get('intent_id')} missing fields"
        assert 0 <= item["intent_strength_score"] <= 100
        assert 0 <= item["conversion_potential_score"] <= 100
        assert 0 <= item["urgency_score"] <= 100
        assert 0 <= item["confidence_score"] <= 100
        assert item["auto_quote_enabled"] is False
        assert item["auto_customer_contact_enabled"] is False
        assert item["auto_dispatch_enabled"] is False
        assert item["auto_post_enabled"] is False
        assert item["auto_reply_enabled"] is False

    assert all(item["demand_intent"] != "no_real_mobility_intent" for item in high_value)
    assert any(item["demand_intent"] == "no_real_mobility_intent" for item in intents)
    assert any(item["recommended_route"] == "ignore_noise_or_monitor_only" for item in low_value)
    assert "normalized_live_data" in summary["supported_input_sources"]
    assert "question_inbox" in summary["supported_input_sources"]
    assert "google_trends_keyword_signal" in summary["supported_input_sources"]
    assert summary["write_operations_enabled"] is False
    assert summary["auto_post_enabled"] is False
    assert summary["auto_reply_enabled"] is False

    for output_name in [
        "mobility_intents.json",
        "high_value_mobility_intents.json",
        "low_value_signals.json",
        "mobility_intent_summary.json",
    ]:
        output_path = PROJECT_ROOT / "runtime" / "mobility_demand_intent" / output_name
        assert output_path.exists(), f"missing output: {output_name}"
        json.loads(output_path.read_text(encoding="utf-8"))

    print("mobility_demand_intent_smoke_test passed")


if __name__ == "__main__":
    main()
