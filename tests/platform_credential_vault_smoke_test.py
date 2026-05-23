from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.platform_credential_vault import PlatformCredentialVault


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "platform_credentials"
        vault = PlatformCredentialVault(root, master_secret="test-secret")

        jag = vault.store_credential("JAG-LAB", "Reddit", "api_key", "reddit-secret", ["read_public"])
        prod = vault.store_credential("JAG-PROD", "Reddit", "api_key", "prod-reddit-secret", ["read_public"])
        token = vault.store_credential("JAG-LAB", "YouTube", "oauth_token", "youtube-token", ["analytics.readonly"])
        refresh = vault.store_credential("JAG-LAB", "Instagram", "refresh_token", "ig-refresh", ["account_analytics"])

        assert jag["workspace_id"] == "JAG-LAB"
        assert prod["workspace_id"] == "JAG-PROD"
        assert jag["fingerprint"] != prod["fingerprint"]
        assert token["credential_type"] == "oauth_token"
        assert refresh["credential_type"] == "refresh_token"
        assert "reddit-secret" not in str(jag)
        assert "prod-reddit-secret" not in str(prod)

        assert vault.get_credential("JAG-LAB", "Reddit", "api_key") == "reddit-secret"
        assert vault.get_credential("JAG-PROD", "Reddit", "api_key") == "prod-reddit-secret"

        jag_path = root / "workspace_JAG-LAB" / "vault.json"
        prod_path = root / "workspace_JAG-PROD" / "vault.json"
        assert jag_path.exists()
        assert prod_path.exists()
        assert "reddit-secret" not in jag_path.read_text(encoding="utf-8")
        assert "prod-reddit-secret" not in prod_path.read_text(encoding="utf-8")

        status = vault.status()
        assert status["report_id"] == "PLATFORM_CREDENTIAL_VAULT_STATUS"
        assert status["status"] == "vault_ready"
        assert status["credentialVaultSummary"]["workspaces"] == 2
        assert status["credentialVaultSummary"]["credentials"] == 4
        assert status["credentialVaultSummary"]["workspace_isolation_enabled"] is True
        assert status["credentialVaultSummary"]["plaintext_logging_enabled"] is False
        assert status["credentialVaultSummary"]["public_upload_allowed"] is False
        assert status["credentialVaultSummary"]["git_commit_allowed"] is False

        workspaces = {item["workspace_id"]: item for item in status["workspaceCredentialStatus"]}
        assert workspaces["JAG-LAB"]["credential_count"] == 3
        assert workspaces["JAG-PROD"]["credential_count"] == 1
        assert workspaces["JAG-LAB"]["workspace_isolated"] is True
        assert status["credentialVaultFeed"], "credential vault feed is required"
        assert "reddit-secret" not in str(status)
        assert "prod-reddit-secret" not in str(status)

    print("platform credential vault smoke test passed")


if __name__ == "__main__":
    main()
