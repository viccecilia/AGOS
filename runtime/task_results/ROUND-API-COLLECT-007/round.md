# ROUND-API-COLLECT-007

## Round Name
AGOS_API_COLLECTION_REVIEW_AND_CORRECTION

## Phase
CONTROLLED_API_INTELLIGENCE_COLLECTION

## Goal
Build API Collection Review & Correction so AGOS can batch-correct real intelligence data before training.

## Scope
- Add `services/api_collection_review_and_correction.py`
- Support batch approve, reject, classify, mark low value, and mark high value
- Support corrections for pain point, emotion, trend strength, and source confidence
- Write `runtime/api_collection_review/`
- Update `docs/project_control_center.html`

## Safety Boundary
This round only edits local intelligence records and review outputs. It does not post, reply, follow, DM, log in, register accounts, call platform write APIs, or bypass platform limits.
