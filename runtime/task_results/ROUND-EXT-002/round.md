# ROUND-EXT-002

## Round Name

EXTERNAL_EVIDENCE_CAPTURE_LEDGER

## Phase

CONTROLLED_REAL_EXTERNAL_INTERACTION_PREPARATION

## Goal

Create an evidence ledger for human external execution after manual promotion export.

## Scope

Allowed:

- services/external_evidence_ledger.py
- tests/external_evidence_ledger_smoke_test.py
- runtime/external_evidence_ledger/
- services/runtime_ui_bridge.py
- docs/project_control_center.html
- runtime/task_results/ROUND-EXT-002/

Forbidden:

- Do not crawl platforms.
- Do not auto-verify external pages.
- Do not post, reply, DM, follow, like, or call write APIs.
- Do not log in or scrape login-only data.

## Definition of Done

Every manual export item can bind to an evidence record. Missing evidence blocks feedback learning.
