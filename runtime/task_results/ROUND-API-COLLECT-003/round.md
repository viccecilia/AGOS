# ROUND-API-COLLECT-003

## Round Name

AGOS_READ_ONLY_LIVE_COLLECTION_RUNNER

## Phase

CONTROLLED_API_INTELLIGENCE_COLLECTION

## Goal

Build a Read-Only Live Collection Runner so AGOS can collect public trend search, keyword search, hashtag search, and public analytics intelligence while blocking every write-side platform action.

## Scope

Allowed:

- `services/live_collection_runner.py`
- `tests/live_collection_runner_smoke_test.py`
- `runtime/live_collection/`
- `runtime/task_results/ROUND-API-COLLECT-003/`
- `docs/project_control_center.html`

Forbidden:

- post
- reply
- DM
- follow
- like
- login automation
- account registration
- write-side platform API calls
