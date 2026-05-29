# ROUND-REALDATA-003_QUERY_SCOPE_AND_SOURCE_POLICY

## Round Goal

Define real-data query scope, source rules, language rules, region tags, and search guidance before any API dry-run.

## Safety Boundary

- No real API calls.
- No platform scraping.
- No real data ingestion.
- No AGOS training.
- All source rules remain read-only and human-review gated.

## Outputs

- `schemas/real_data_query_scope.schema.json`
- `runtime/real_data_access/QUERY_SCOPE_POLICY.json`
- `runtime/real_data_access/SOURCE_POLICY.json`
- `runtime/real_data_access/LANGUAGE_REGION_TAGGING_POLICY.json`
- `runtime/real_data_access/CONTENT_TYPE_POLICY.json`
- `runtime/real_data_access/QUERY_SCOPE_EVIDENCE.json`
