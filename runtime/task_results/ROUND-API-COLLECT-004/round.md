# ROUND-API-COLLECT-004

## Round Name

AGOS_COLLECTION_COMPLIANCE_GUARD

## Phase

CONTROLLED_API_INTELLIGENCE_COLLECTION

## Goal

Build Collection Compliance Guard so AGOS can safely collect intelligence by detecting rate limits, repeated queries, suspicious patterns, write API usage, excessive polling, automated login scraping, platform-limit bypass, and automated interaction.

## Scope

Allowed:

- `services/collection_compliance_guard.py`
- `tests/collection_compliance_guard_smoke_test.py`
- `runtime/compliance_guard/`
- `runtime/task_results/ROUND-API-COLLECT-004/`
- `docs/project_control_center.html`

Forbidden:

- automated login scraping
- platform-limit bypass
- write API
- automated interaction
- post / reply / DM / follow / like
