# ROUND-RUNTIME-PERSONALITY-005 Tasks

| Task | Status | Evidence |
| --- | --- | --- |
| TASK-001 Reddit Strategy Personality | done | `services/runtime_strategy_personality.py` includes Reddit operating philosophy, content shape, interaction style, and success signal. |
| TASK-002 TikTok Strategy Personality | done | TikTok strategy emphasizes hook, visual action, retention, saves, and anti-clickbait guardrails. |
| TASK-003 X Strategy Personality | done | X strategy emphasizes timely opinion, conversation, micro-threads, and trend reactions. |
| TASK-004 YouTube Strategy Personality | done | YouTube strategy emphasizes searchable evergreen guidance, chapters, walkthroughs, and retention. |
| TASK-005 Platform Operating Philosophy | done | `RuntimeUIBridge` exports `strategyPersonality` and `strategyPersonalityFeed` to the War Room. |

## Required Test
`python tests\runtime_strategy_personality_smoke_test.py`
