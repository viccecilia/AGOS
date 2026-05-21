"""File-backed workspace service.

This service intentionally handles only workspace boundaries and metadata.
Promotion workflows, content generation, and Japan AI Guide-specific logic are
kept out of R002 scope.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from models.workspace import Workspace, utc_now_iso
from schemas.workspace_schema import validate_workspace_payload


class WorkspaceAlreadyExistsError(ValueError):
    pass


class WorkspaceNotFoundError(KeyError):
    pass


class WorkspaceStore:
    def __init__(self, root: str | Path = "runtime/workspaces") -> None:
        self.root = Path(root)

    def create(self, payload: dict) -> Workspace:
        validate_workspace_payload(payload)
        workspace = Workspace.from_dict({**payload, "updated_at": utc_now_iso()})
        path = self._workspace_file(workspace.workspace_id)
        if path.exists():
            raise WorkspaceAlreadyExistsError(workspace.workspace_id)
        path.parent.mkdir(parents=True, exist_ok=False)
        self._write_workspace(path, workspace)
        return workspace

    def get(self, workspace_id: str) -> Workspace:
        path = self._workspace_file(workspace_id)
        if not path.exists():
            raise WorkspaceNotFoundError(workspace_id)
        return Workspace.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list(self) -> list[Workspace]:
        if not self.root.exists():
            return []
        workspaces: Iterable[Path] = self.root.glob("*/workspace.json")
        return sorted(
            (Workspace.from_dict(json.loads(path.read_text(encoding="utf-8"))) for path in workspaces),
            key=lambda item: item.workspace_id,
        )

    def _workspace_file(self, workspace_id: str) -> Path:
        validate_workspace_payload(
            {
                "workspace_id": workspace_id,
                "name": "placeholder",
                "owner": "placeholder",
                "product_name": "placeholder",
                "industry": "placeholder",
            }
        )
        path = (self.root / workspace_id / "workspace.json").resolve()
        root = self.root.resolve()
        if root not in path.parents:
            raise ValueError("Workspace path escaped store root")
        return path

    @staticmethod
    def _write_workspace(path: Path, workspace: Workspace) -> None:
        path.write_text(
            json.dumps(workspace.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
