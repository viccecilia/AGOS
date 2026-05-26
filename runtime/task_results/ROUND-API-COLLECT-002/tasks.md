# ROUND-API-COLLECT-002 Tasks

## Execution Tasks

- TASK-001: Added `services/api_credential_setup_wizard.py`.
- TASK-002: Supported API Key, OAuth Token, and Refresh Token credential setup types.
- TASK-003: Enforced local-only storage, no public upload, no Git plaintext files, and no plaintext logging in wizard reports.
- TASK-004: Added Workspace Credential Isolation through per-workspace redacted setup status and vault-backed storage.
- TASK-005: Added `runtime/api_credentials/` outputs with Git-safe report files and `.gitignore` protection for secret-bearing workspace files.

## Test Tasks

- TEST-001: Added and ran `python tests\api_credential_setup_wizard_smoke_test.py`.

## Review Tasks

- Review target: user can see API credential setup status in the War Room without exposing credentials.
