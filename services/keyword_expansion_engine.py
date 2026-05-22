"""Keyword expansion for AGOS Scout Intelligence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.patrol_group_engine import PatrolGroupEngine
from services.runtime_persistence import utc_now_iso


class KeywordExpansionEngine:
    """Expand seed keywords into multilingual and platform-aware search variants."""

    RULES: dict[str, dict[str, Any]] = {
        "tokyo transfer": {
            "canonical_pain_point": "Tokyo transport anxiety",
            "synonyms": ["tokyo subway confusing", "tokyo train transfer", "tokyo station transfer", "jr metro connection"],
            "slang": ["tokyo station maze", "train transfer hell", "lost in shinjuku station"],
            "emotion_expressions": ["i am scared of getting lost in tokyo", "tokyo subway makes me anxious"],
            "platform_lingo": ["tokyo train hack", "tokyo station survival tip", "save this before tokyo"],
            "multilingual": ["东京地铁复杂", "东京换乘看不懂", "東京駅 乗り換え 不安", "도쿄 지하철 환승 어려움"],
        },
        "lost in station": {
            "canonical_pain_point": "Tokyo transport anxiety",
            "synonyms": ["lost in tokyo station", "cannot find platform", "station navigation problem"],
            "slang": ["station maze", "platform panic", "transfer nightmare"],
            "emotion_expressions": ["afraid i will miss my train", "i panic in big stations"],
            "platform_lingo": ["station mistake to avoid", "tokyo platform tip", "first time japan warning"],
            "multilingual": ["车站迷路", "日本车站看不懂", "駅で迷う", "역에서 길을 잃음"],
        },
        "japan itinerary": {
            "canonical_pain_point": "Japan itinerary overwhelm",
            "synonyms": ["japan trip plan", "japan travel route", "tokyo osaka kyoto itinerary"],
            "slang": ["japan planning overload", "too many japan options", "itinerary chaos"],
            "emotion_expressions": ["i feel overwhelmed planning japan", "i do not know how many days to spend"],
            "platform_lingo": ["japan itinerary hack", "save this japan route", "first japan trip plan"],
            "multilingual": ["日本行程怎么安排", "日本旅游路线", "日本旅行 計画 不安", "일본 여행 일정 고민"],
        },
        "osaka transport": {
            "canonical_pain_point": "Kansai transport confusion",
            "synonyms": ["osaka subway confusing", "kansai train pass", "osaka to kyoto transport"],
            "slang": ["kansai pass headache", "osaka route mess"],
            "emotion_expressions": ["i am confused by osaka passes", "i worry about choosing the wrong kansai pass"],
            "platform_lingo": ["osaka pass tip", "kansai train hack"],
            "multilingual": ["大阪交通复杂", "关西交通券怎么选", "大阪 交通 わからない", "오사카 교통패스 헷갈림"],
        },
        "air fryer cleaning": {
            "canonical_pain_point": "Air fryer cleaning friction",
            "synonyms": ["clean air fryer basket", "air fryer grease problem", "air fryer smells bad"],
            "slang": ["greasy air fryer mess", "basket gunk", "air fryer stink"],
            "emotion_expressions": ["i hate cleaning my air fryer", "air fryer grease is frustrating"],
            "platform_lingo": ["air fryer cleaning hack", "before you scrub your air fryer"],
            "multilingual": ["空气炸锅清洁", "空气炸锅油污", "ノンフライヤー 掃除", "에어프라이어 청소"],
        },
        "vacuum suction": {
            "canonical_pain_point": "Vacuum performance anxiety",
            "synonyms": ["vacuum lost suction", "vacuum not picking up dust", "weak vacuum cleaner"],
            "slang": ["vacuum is useless", "dust still there", "suction died"],
            "emotion_expressions": ["my vacuum is driving me crazy", "i regret buying this vacuum"],
            "platform_lingo": ["vacuum suction fix", "check this before replacing vacuum"],
            "multilingual": ["吸尘器吸力弱", "吸尘器不吸灰", "掃除機 吸引力 弱い", "청소기 흡입력 약함"],
        },
        "smart home setup": {
            "canonical_pain_point": "Smart home setup confusion",
            "synonyms": ["smart home pairing problem", "device will not connect", "wifi smart plug setup"],
            "slang": ["smart home headache", "device refuses to pair"],
            "emotion_expressions": ["i feel dumb setting up smart home devices", "setup keeps failing"],
            "platform_lingo": ["smart home setup fix", "before you reset your device"],
            "multilingual": ["智能家居设置", "智能设备连不上", "スマートホーム 設定", "스마트홈 연결 문제"],
        },
        "kitchen appliance problem": {
            "canonical_pain_point": "Kitchen appliance troubleshooting",
            "synonyms": ["appliance stopped working", "kitchen gadget issue", "small appliance troubleshooting"],
            "slang": ["kitchen gadget fail", "countertop appliance problem"],
            "emotion_expressions": ["this appliance is frustrating", "i cannot make it work"],
            "platform_lingo": ["appliance troubleshooting tip", "try this before returning it"],
            "multilingual": ["厨房电器问题", "小家电故障", "キッチン家電 トラブル", "주방가전 문제"],
        },
    }

    def __init__(self, root: str | Path = "runtime/keyword_expansion") -> None:
        self.root = Path(root)
        self.state_path = self.root / "KEYWORD_EXPANSION_STATE.json"
        self.matrix_path = self.root / "keyword_expansion_matrix.json"

    def expand_keyword(self, keyword: str) -> dict[str, Any]:
        key = keyword.lower().strip()
        rule = self.RULES.get(key)
        if not rule:
            rule = {
                "canonical_pain_point": keyword.title(),
                "synonyms": [keyword],
                "slang": [],
                "emotion_expressions": [],
                "platform_lingo": [],
                "multilingual": [],
            }
        expanded_terms = []
        for bucket in ("synonyms", "slang", "emotion_expressions", "platform_lingo", "multilingual"):
            expanded_terms.extend(rule.get(bucket, []))
        return {
            "seed_keyword": keyword,
            "canonical_pain_point": rule["canonical_pain_point"],
            "synonyms": rule.get("synonyms", []),
            "slang": rule.get("slang", []),
            "emotion_expressions": rule.get("emotion_expressions", []),
            "platform_lingo": rule.get("platform_lingo", []),
            "multilingual": rule.get("multilingual", []),
            "expanded_terms": sorted(set(expanded_terms)),
            "status": "expanded",
        }

    def normalize_phrase(self, phrase: str) -> str:
        text = phrase.lower().strip()
        for keyword, rule in self.RULES.items():
            candidates = [keyword]
            for bucket in ("synonyms", "slang", "emotion_expressions", "platform_lingo", "multilingual"):
                candidates.extend(rule.get(bucket, []))
            if text in {candidate.lower() for candidate in candidates}:
                return rule["canonical_pain_point"]
        return phrase

    def build_from_patrol_groups(self) -> dict[str, Any]:
        patrol_state = PatrolGroupEngine().state()
        seed_keywords = sorted({keyword for group in patrol_state.get("activePatrolGroups", []) for keyword in group.get("keywords", [])})
        expansions = [self.expand_keyword(keyword) for keyword in seed_keywords]
        state = {
            "state_id": "KEYWORD_EXPANSION_STATE",
            "created_at": utc_now_iso(),
            "status": "active",
            "seedKeywords": seed_keywords,
            "keywordExpansions": expansions,
            "canonicalPainPoints": sorted({item["canonical_pain_point"] for item in expansions}),
            "normalizationExamples": [
                {
                    "input": "Tokyo subway confusing",
                    "canonical_pain_point": self.normalize_phrase("Tokyo subway confusing"),
                },
                {
                    "input": "东京地铁复杂",
                    "canonical_pain_point": self.normalize_phrase("东京地铁复杂"),
                },
            ],
        }
        self.persist(state)
        return state

    def state(self) -> dict[str, Any]:
        if self.state_path.exists():
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        return self.build_from_patrol_groups()

    def persist(self, state: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.matrix_path.write_text(
            json.dumps(state["keywordExpansions"], ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
