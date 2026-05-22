"""Patrol group configuration for AGOS Scout Intelligence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.runtime_persistence import utc_now_iso


class PatrolGroupEngine:
    """Create local-only patrol groups by workspace and industry pack."""

    SUPPORTED_PLATFORMS = ["Reddit", "TikTok", "X", "YouTube", "Threads"]

    INDUSTRY_PACKS: dict[str, dict[str, Any]] = {
        "Travel Pack": {
            "workspace": "JAG-LAB",
            "markets": ["Japan", "Europe / US", "Korea", "Taiwan", "Southeast Asia"],
            "targets": ["JapanTravel", "Tokyo", "Osaka", "travelhacks"],
            "keywords": ["tokyo transfer", "japan itinerary", "osaka transport", "lost in station"],
            "audience": "independent travelers planning or solving Japan trip problems",
        },
        "Home Appliance Pack": {
            "workspace": "PHILIPS-LAB",
            "markets": ["Europe / US", "Japan", "Korea", "Taiwan"],
            "targets": ["SmartHome", "AirFryer", "Vacuum"],
            "keywords": ["air fryer cleaning", "vacuum suction", "smart home setup", "kitchen appliance problem"],
            "audience": "home appliance buyers and troubleshooting users",
        },
    }

    def __init__(self, root: str | Path = "runtime/patrol_groups") -> None:
        self.root = Path(root)
        self.state_path = self.root / "PATROL_GROUPS_STATE.json"
        self.matrix_path = self.root / "patrol_groups_matrix.json"

    def build_workspace_groups(self, industry_pack: str, workspace: str | None = None) -> list[dict[str, Any]]:
        if industry_pack not in self.INDUSTRY_PACKS:
            raise ValueError(f"Unsupported industry pack: {industry_pack}")
        pack = self.INDUSTRY_PACKS[industry_pack]
        workspace_id = workspace or pack["workspace"]
        groups: list[dict[str, Any]] = []
        for platform in self.SUPPORTED_PLATFORMS:
            groups.append(
                {
                    "group_id": self._group_id(workspace_id, industry_pack, platform),
                    "workspace": workspace_id,
                    "industry_pack": industry_pack,
                    "platform": platform,
                    "markets": pack["markets"],
                    "targets": pack["targets"],
                    "keywords": pack["keywords"],
                    "audience": pack["audience"],
                    "status": "active",
                    "collection_mode": "manual_import_or_public_api_only",
                    "safety_boundary": [
                        "no login scraping",
                        "no automated posting",
                        "no automated replying",
                        "no platform limit bypass",
                    ],
                    "next_action": f"Monitor {platform} for public questions matching {industry_pack} pain points.",
                }
            )
        return groups

    def build_all(self) -> dict[str, Any]:
        groups: list[dict[str, Any]] = []
        for industry_pack, pack in self.INDUSTRY_PACKS.items():
            groups.extend(self.build_workspace_groups(industry_pack, pack["workspace"]))
        state = {
            "state_id": "PATROL_GROUPS_STATE",
            "created_at": utc_now_iso(),
            "status": "active",
            "supportedPlatforms": self.SUPPORTED_PLATFORMS,
            "activePatrolGroups": groups,
            "workspacePatrolGroups": self._by_workspace(groups),
            "industryPackPatrolGroups": self._by_industry_pack(groups),
            "patrolSummary": {
                "total_groups": len(groups),
                "industry_packs": sorted(self.INDUSTRY_PACKS),
                "workspaces": sorted({group["workspace"] for group in groups}),
                "platforms": self.SUPPORTED_PLATFORMS,
            },
        }
        self.persist(state)
        return state

    def state(self) -> dict[str, Any]:
        if self.state_path.exists():
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        return self.build_all()

    def persist(self, state: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        self.matrix_path.write_text(
            json.dumps(state["activePatrolGroups"], ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    @staticmethod
    def _group_id(workspace: str, industry_pack: str, platform: str) -> str:
        normalized = f"{workspace}_{industry_pack}_{platform}".lower()
        return "patrol_" + "".join(ch if ch.isalnum() else "_" for ch in normalized).strip("_")

    @staticmethod
    def _by_workspace(groups: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        result: dict[str, list[dict[str, Any]]] = {}
        for group in groups:
            result.setdefault(group["workspace"], []).append(group)
        return result

    @staticmethod
    def _by_industry_pack(groups: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        result: dict[str, list[dict[str, Any]]] = {}
        for group in groups:
            result.setdefault(group["industry_pack"], []).append(group)
        return result
