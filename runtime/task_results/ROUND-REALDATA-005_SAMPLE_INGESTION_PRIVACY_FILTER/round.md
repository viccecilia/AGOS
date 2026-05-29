# ROUND-REALDATA-005_SAMPLE_INGESTION_PRIVACY_FILTER

## Round Goal

Ingest a small controlled sample and apply privacy, PII, language, region, and lineage filters.

## Safety Boundary

- Small sample only.
- No private messages.
- No sensitive PII training.
- No large-scale ingestion.
- No training.
- No automatic promotion.
- No raw content storage in the persistent outputs.

## Outputs

- `schemas/sample_ingestion_record.schema.json`
- `runtime/real_data_samples/SAMPLE_INGESTION_POLICY.json`
- `runtime/real_data_samples/PRIVACY_FILTER_POLICY.json`
- `runtime/real_data_samples/SAMPLE_LINEAGE_MANIFEST.json`
- `runtime/real_data_samples/PRIVACY_FILTER_REPORT.json`
- `runtime/real_data_samples/SAMPLE_INGESTION_EVIDENCE.json`
