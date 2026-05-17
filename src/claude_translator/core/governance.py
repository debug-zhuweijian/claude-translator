"""Governance planning, backup, apply, and restore for descriptions."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from claude_translator import __version__
from claude_translator.core.display import DuplicateGroup, find_duplicate_display_groups
from claude_translator.core.frontmatter import FrontmatterParser
from claude_translator.core.language_policy import LanguageViolation, check_inventory_language
from claude_translator.core.models import Inventory, Record
from claude_translator.storage.paths import get_translations_dir
from claude_translator.utils.paths import detect_newline


@dataclass(frozen=True)
class GovernanceOptions:
    target_lang: str = "zh-CN"
    translations: dict[str, str] | None = None
    backup_root: Path | None = None


@dataclass(frozen=True)
class GovernanceAction:
    action_type: str
    target: Record
    reason: str
    replacement_description: str
    expected_sha256: str


@dataclass(frozen=True)
class GovernancePlan:
    actions: tuple[GovernanceAction, ...]
    duplicate_groups: tuple[DuplicateGroup, ...]
    language_violations: tuple[LanguageViolation, ...]


@dataclass(frozen=True)
class GovernanceReport:
    scanned: int
    strict_language_violations: int
    duplicate_display_groups: int
    planned_description_rewrites: int
    planned_duplicate_suppressions: int = 0
    applied_description_rewrites: int = 0
    applied_duplicate_suppressions: int = 0
    unresolved_duplicate_groups: int = 0
    backup_manifest: str | None = None

    def summary_line(self) -> str:
        parts = [
            f"scanned={self.scanned}",
            f"strict_language_violations={self.strict_language_violations}",
            f"duplicate_display_groups={self.duplicate_display_groups}",
            f"planned_description_rewrites={self.planned_description_rewrites}",
        ]
        if self.applied_description_rewrites:
            parts.append(f"applied_description_rewrites={self.applied_description_rewrites}")
        if self.unresolved_duplicate_groups:
            parts.append(f"unresolved_duplicate_groups={self.unresolved_duplicate_groups}")
        if self.backup_manifest:
            parts.append(f"backup_manifest={self.backup_manifest}")
        return "Governance complete: " + ", ".join(parts)


@dataclass(frozen=True)
class RestoreReport:
    planned_restores: int = 0
    restored: int = 0
    refused: int = 0

    def summary_line(self) -> str:
        return (
            "Restore complete: "
            f"planned_restores={self.planned_restores}, "
            f"restored={self.restored}, "
            f"refused={self.refused}"
        )


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _backup_root(options: GovernanceOptions) -> Path:
    return options.backup_root or get_translations_dir() / "governance-backups"


def _description_replacement(record: Record, options: GovernanceOptions) -> str | None:
    translations = options.translations or {}
    return translations.get(record.canonical_id)


def create_governance_plan(
    inventory: Inventory,
    options: GovernanceOptions | None = None,
) -> GovernancePlan:
    resolved_options = options or GovernanceOptions()
    violations = check_inventory_language(inventory, resolved_options.target_lang)
    violations_by_id = {violation.canonical_id: violation for violation in violations}
    actions: tuple[GovernanceAction, ...] = ()

    for record in inventory.records:
        violation = violations_by_id.get(record.canonical_id)
        replacement = _description_replacement(record, resolved_options)
        if violation is None or replacement is None:
            continue
        path = Path(record.source_path)
        actions = (
            *actions,
            GovernanceAction(
                action_type="rewrite_description",
                target=record,
                reason=violation.reason,
                replacement_description=replacement,
                expected_sha256=_file_sha256(path),
            ),
        )

    return GovernancePlan(
        actions=actions,
        duplicate_groups=find_duplicate_display_groups(inventory.records),
        language_violations=violations,
    )


def _rewrite_description_bytes(path: Path, description: str) -> bytes:
    raw = path.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    content = raw.decode("utf-8-sig" if has_bom else "utf-8")
    newline = detect_newline(content)
    parser = FrontmatterParser()
    fm, body = parser.parse(content)
    parser.set_description(fm, description)
    new_content = parser.build(fm, body)
    new_content = new_content.replace("\r\n", "\n").replace("\n", newline)
    out = new_content.encode("utf-8")
    return b"\xef\xbb\xbf" + out if has_bom else out


def apply_governance_plan(
    plan: GovernancePlan,
    options: GovernanceOptions | None = None,
) -> GovernanceReport:
    resolved_options = options or GovernanceOptions()
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    backup_dir = _backup_root(resolved_options) / run_id
    backup_dir.mkdir(parents=True, exist_ok=True)

    manifest_items: list[dict[str, str]] = []
    applied = 0

    for action in plan.actions:
        path = Path(action.target.source_path)
        current_hash = _file_sha256(path)
        if current_hash != action.expected_sha256:
            continue

        backup_path = backup_dir / f"{len(manifest_items):04d}-{path.name}"
        shutil.copy2(path, backup_path)
        new_bytes = _rewrite_description_bytes(path, action.replacement_description)
        path.write_bytes(new_bytes)
        new_hash = _sha256_bytes(new_bytes)
        applied += 1
        display_name = action.target.canonical_id.split(":", 1)[1]
        manifest_items.append(
            {
                "canonical_id": action.target.canonical_id,
                "display_key": f"{action.target.kind}:{display_name}",
                "source_path": str(path),
                "backup_path": str(backup_path),
                "action": action.action_type,
                "reason": action.reason,
                "old_sha256": current_hash,
                "new_sha256": new_hash,
                "status": "applied",
            }
        )

    manifest_path = backup_dir / "manifest.json"
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "lang": resolved_options.target_lang,
        "tool_version": __version__,
        "items": manifest_items,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    return GovernanceReport(
        scanned=len(plan.actions),
        strict_language_violations=len(plan.language_violations),
        duplicate_display_groups=len(plan.duplicate_groups),
        planned_description_rewrites=len(plan.actions),
        applied_description_rewrites=applied,
        unresolved_duplicate_groups=len(plan.duplicate_groups),
        backup_manifest=str(manifest_path),
    )


def restore_from_manifest(manifest_path: Path, *, apply: bool = False) -> RestoreReport:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    items = tuple(manifest.get("items", ()))
    planned = len(items)
    if not apply:
        return RestoreReport(planned_restores=planned)

    restored = 0
    refused = 0
    for item in items:
        source_path = Path(item["source_path"])
        backup_path = Path(item["backup_path"])
        if _file_sha256(source_path) != item["new_sha256"]:
            refused += 1
            continue
        shutil.copy2(backup_path, source_path)
        if _file_sha256(source_path) == item["old_sha256"]:
            restored += 1
        else:
            refused += 1

    return RestoreReport(planned_restores=planned, restored=restored, refused=refused)
