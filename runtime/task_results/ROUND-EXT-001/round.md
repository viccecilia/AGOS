# ROUND-EXT-001

## Round Name

MANUAL_PROMOTION_EXPORT_PACK

## Phase

CONTROLLED_REAL_EXTERNAL_INTERACTION_PREPARATION

## Goal

Export approved promotion drafts, cross-platform plans, and best promotion patterns into a human-copy manual promotion pack.

## Scope

Allowed:

- services/manual_promotion_export_pack.py
- tests/manual_promotion_export_pack_smoke_test.py
- runtime/manual_promotion_export_pack/
- services/runtime_ui_bridge.py
- docs/project_control_center.html
- runtime/task_results/ROUND-EXT-001/

Forbidden:

- Platform API write operations.
- Automatic post, reply, DM, follow, or like.
- Credentials or `.env` changes.
- Real business data writeback.

## Definition of Done

The export pack is readable, auditable, and manually copyable. Every export item keeps `external_execution_allowed=false` and `human_gate_required=true`.
