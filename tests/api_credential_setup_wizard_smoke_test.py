from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.api_credential_setup_wizard import APICredentialSetupWizard
from services.platform_credential_vault import PlatformCredentialVault


def main() -> None:
    secrets = [
        "reddit-api-key-secret",
        "youtube-oauth-token-secret",
        "x-refresh-token-secret",
    ]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "api_credentials"
        vault = PlatformCredentialVault(Path(tmp) / "platform_credentials", master_secret="wizard-test-secret")
        wizard = APICredentialSetupWizard(root=root, vault=vault)

        api_key = wizard.configure("JAG-LAB", "Reddit", "api_key", secrets[0], ["read_public"])
        oauth = wizard.configure("JAG-LAB", "YouTube", "oauth_token", secrets[1], ["analytics.readonly"])
        refresh = wizard.configure("JAG-PROD", "X", "refresh_token", secrets[2], ["trend.read"])
        report = wizard.build("JAG-LAB")

        assert api_key["credential_type"] == "api_key"
        assert oauth["credential_type"] == "oauth_token"
        assert refresh["credential_type"] == "refresh_token"
        assert api_key["workspace_id"] == "JAG-LAB"
        assert refresh["workspace_id"] == "JAG-PROD"
        assert api_key["secret_redacted"] is True
        assert api_key["plaintext_logged"] is False
        assert api_key["git_commit_allowed"] is False
        assert api_key["public_upload_allowed"] is False

        assert report["report_id"] == "API_CREDENTIAL_SETUP_WIZARD"
        assert report["status"] == "credential_setup_wizard_ready"
        assert set(report["supportedCredentialTypes"]) == {"api_key", "oauth_token", "refresh_token"}
        summary = report["credentialSetupSummary"]
        assert summary["wizard_ready"] is True
        assert summary["workspace_isolation_enabled"] is True
        assert summary["local_storage_only"] is True
        assert summary["plaintext_logging_enabled"] is False
        assert summary["public_upload_allowed"] is False
        assert summary["git_commit_allowed"] is False
        assert summary["write_permission_default"] is False

        assert (root / ".gitignore").exists()
        assert "*" in (root / ".gitignore").read_text(encoding="utf-8")
        assert (root / "API_CREDENTIAL_SETUP_WIZARD_REPORT.json").exists()
        assert (root / "credential_setup_status.json").exists()
        assert (root / "credential_setup_feed.json").exists()
        assert (root / "credential_setup_summary.json").exists()

        all_written_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in list(root.rglob("*")) + list((Path(tmp) / "platform_credentials").rglob("*"))
            if path.is_file()
        )
        for secret in secrets:
            assert secret not in all_written_text
        assert "sealed_value" not in (root / "API_CREDENTIAL_SETUP_WIZARD_REPORT.json").read_text(encoding="utf-8")

        lab_status = root / "workspace_JAG-LAB" / "credential_setup_status.redacted.json"
        prod_status = root / "workspace_JAG-PROD" / "credential_setup_status.redacted.json"
        assert lab_status.exists()
        assert prod_status.exists()
        assert "JAG-PROD" not in lab_status.read_text(encoding="utf-8")
        assert "JAG-LAB" not in prod_status.read_text(encoding="utf-8")

    print("api credential setup wizard smoke test passed")


if __name__ == "__main__":
    main()
