# ROUND-RUNTIME-PERSONALITY-006 Tasks

| Task | Status | Evidence |
| --- | --- | --- |
| TASK-001 Workspace Personality Pollution | done | `PersonalityIsolationEngine` checks JAG-LAB and PHILIPS-LAB boundaries. |
| TASK-002 Market Personality Pollution | done | The isolation matrix checks Japan, Korea, Taiwan, and Europe / US personality scopes. |
| TASK-003 Platform Personality Pollution | done | The isolation matrix checks Reddit, TikTok, Instagram, and YouTube scope separation. |
| TASK-004 Personality Isolation Report | done | `runtime/personality_isolation/PERSONALITY_ISOLATION_REPORT.json` is generated and exported to the War Room. |

## Required Test
`python tests\cross_market_personality_isolation_smoke_test.py`
