# ROUND-SCOUT-003

## Round Name
AGOS_TOPIC_DISCOVERY_ENGINE

## Phase
SCOUT_INTELLIGENCE / AI_SCOUT_NETWORK

## Goal
Build Topic Discovery Engine so AGOS can actively discover questions.

## Scope
- Add `services/topic_discovery_engine.py`.
- Support RSS, manual import, JSON, CSV, and local text sources.
- Detect frequent questions.
- Detect repeated questions.
- Detect emerging questions.
- Detect high-emotion questions.
- Output `runtime/discovered_topics/`.

## Safety Boundary
- Local source processing only.
- No external crawling.
- No platform login.
- No automated posting or replying.
