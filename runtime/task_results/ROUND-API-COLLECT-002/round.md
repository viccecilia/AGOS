# ROUND-API-COLLECT-002

## Round Name

AGOS_API_CREDENTIAL_SETUP_WIZARD

## Phase

CONTROLLED_API_INTELLIGENCE_COLLECTION

## Goal

Build an API Credential Setup Wizard so AGOS can safely configure API Key, OAuth Token, and Refresh Token credentials with local-only storage, workspace isolation, redacted status, and no plaintext credential logging.

## Scope

Allowed:

- `services/`
- `tests/`
- `runtime/api_credentials/`
- `runtime/task_results/ROUND-API-COLLECT-002/`
- `docs/project_control_center.html`

Forbidden:

- Public upload of credentials
- Git commit of plaintext credentials
- Plaintext credential logs
- Write-side platform automation
- Real platform posting, replying, login, registration, follow, DM, or engagement actions
