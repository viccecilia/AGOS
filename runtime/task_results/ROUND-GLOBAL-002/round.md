# ROUND-GLOBAL-002

## Round Name

AGOS_GLOBAL_PAIN_CLUSTER_ENGINE

## Phase

GLOBAL_INTELLIGENCE_COLLECTION

## Goal

Build Global Pain Cluster Engine so AGOS can group global multi-market intelligence records into reviewed pain clusters by topic, market, platform, language, emotion, intent, season, and location.

## Boundary

- Reads local Global Batch Intelligence records only
- Clusters pain points for analysis only
- No answer generation
- No automatic promotion
- No automatic replies
- No real user contact
- No platform write API

## Output

- `services/global_pain_cluster_engine.py`
- `runtime/global_pain_clusters/`
- `tests/global_pain_cluster_engine_smoke_test.py`
- Control Center Global Pain Clusters panel
