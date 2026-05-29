# ROUND-REALDATA-002_CREDENTIAL_VAULT_AND_SECRET_BOUNDARY

## Round Name
CREDENTIAL_VAULT_AND_SECRET_BOUNDARY

## Phase
AGOS_REAL_DATA_CONTROLLED_ACCESS

## Goal
Define credential vault and secret handling rules before any real platform API connection.

## Forbidden Credential Handling
- No tokens in Git.
- No tokens in runtime JSON.
- No `.env` writes by AGOS.
- No logs containing secrets.
- No screenshots containing secrets.

## Allowed Credential Handling
- External vault reference.
- Local operator-provided runtime injection.
- Least-privilege scopes.
- Revocation support.
- Rotation support.

## Safety Boundary
- Do not request real secrets in chat.
- Do not store real tokens.
- Do not write `.env` files.
- Do not call real APIs.
- Do not start AGOS training.
