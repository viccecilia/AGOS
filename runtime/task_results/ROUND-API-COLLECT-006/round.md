# ROUND-API-COLLECT-006

## Round Name
AGOS_LIVE_DATA_IMPORT_TO_MEMORY

## Phase
CONTROLLED_API_INTELLIGENCE_COLLECTION

## Goal
Build Live Data Import to Memory so AGOS can import normalized live intelligence into training memory.

## Scope
- Add `services/live_data_import_to_memory.py`
- Write local memory outputs under `runtime/live_memory_import/`
- Import into Question Inbox, Pain Point Library, Pattern Memory, Trend Cluster, and Scout Intelligence views
- Trigger Replay Training, Pattern Learning, and Intelligence Ranking locally
- Update `docs/project_control_center.html`

## Safety Boundary
This round only writes local JSON memory and local training outputs. It does not post, reply, follow, DM, log in, register accounts, call platform write APIs, or bypass platform limits.
