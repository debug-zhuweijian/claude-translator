"""Governance planning, backup, apply, and restore for descriptions."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from claude_translator import __version__
from claude_translator.core.canonical import parse_canonical_id
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
    replacement_name: str = ""


@dataclass(frozen=True)
class GovernancePlan:
    actions: tuple[GovernanceAction, ...]
    duplicate_groups: tuple[DuplicateGroup, ...]
    language_violations: tuple[LanguageViolation, ...]
    scanned: int


@dataclass(frozen=True)
class GovernanceReport:
    scanned: int
    strict_language_violations: int
    duplicate_display_groups: int
    planned_description_rewrites: int
    planned_duplicate_suppressions: int = 0
    planned_name_repairs: int = 0
    applied_description_rewrites: int = 0
    applied_duplicate_suppressions: int = 0
    applied_name_repairs: int = 0
    unresolved_duplicate_groups: int = 0
    backup_manifest: str | None = None

    def summary_line(self) -> str:
        parts = [
            f"scanned={self.scanned}",
            f"strict_language_violations={self.strict_language_violations}",
            f"duplicate_display_groups={self.duplicate_display_groups}",
            f"planned_description_rewrites={self.planned_description_rewrites}",
        ]
        if self.planned_duplicate_suppressions:
            parts.append(f"planned_duplicate_suppressions={self.planned_duplicate_suppressions}")
        if self.planned_name_repairs:
            parts.append(f"planned_name_repairs={self.planned_name_repairs}")
        if self.applied_description_rewrites:
            parts.append(f"applied_description_rewrites={self.applied_description_rewrites}")
        if self.applied_duplicate_suppressions:
            parts.append(f"applied_duplicate_suppressions={self.applied_duplicate_suppressions}")
        if self.applied_name_repairs:
            parts.append(f"applied_name_repairs={self.applied_name_repairs}")
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


def _empty_description_replacement(record: Record, target_lang: str) -> str | None:
    display_name = record.canonical_id.split(":", 1)[1]
    if target_lang.startswith("zh"):
        scope_label = "用户级" if record.scope == "user" else "插件级"
        return f"{scope_label} {record.kind} {display_name} 入口说明"
    if target_lang.startswith("ja"):
        scope_label = "ユーザー" if record.scope == "user" else "プラグイン"
        return f"{scope_label} {record.kind} {display_name} の入口説明"
    if target_lang.startswith("ko"):
        scope_label = "사용자" if record.scope == "user" else "플러그인"
        return f"{scope_label} {record.kind} {display_name} 항목 설명"
    return None


def _description_replacement(record: Record, options: GovernanceOptions) -> str | None:
    translations = options.translations or {}
    if record.canonical_id in translations:
        return translations[record.canonical_id]
    if not record.current_description.strip():
        return _empty_description_replacement(record, options.target_lang)
    return None


def _name_repair_replacement(record: Record) -> str | None:
    if record.kind != "command":
        return None

    parser = FrontmatterParser()
    content = Path(record.source_path).read_text(encoding="utf-8-sig")
    fm, _ = parser.parse(content)
    current_name = parser.get_name(fm)
    if current_name is None:
        return None

    expected_name = parse_canonical_id(record.canonical_id)[3]
    if current_name == expected_name:
        return None
    return expected_name


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
        replacement = (
            _description_replacement(record, resolved_options) if violation is not None else None
        )
        name_replacement = _name_repair_replacement(record)
        if (violation is None or replacement is None) and name_replacement is None:
            continue
        path = Path(record.source_path)
        if name_replacement is not None and replacement:
            action_type = "rewrite_frontmatter"
        elif name_replacement is not None:
            action_type = "repair_name"
        else:
            action_type = "rewrite_description"
        actions = (
            *actions,
            GovernanceAction(
                action_type=action_type,
                target=record,
                reason=violation.reason if violation is not None else "name_mismatch",
                replacement_description=replacement or "",
                expected_sha256=_file_sha256(path),
                replacement_name=name_replacement or "",
            ),
        )

    return GovernancePlan(
        actions=actions,
        duplicate_groups=find_duplicate_display_groups(inventory.records),
        language_violations=violations,
        scanned=inventory.size(),
    )


def _rewrite_frontmatter_bytes(path: Path, *, description: str = "", name: str = "") -> bytes:
    raw = path.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    content = raw.decode("utf-8-sig" if has_bom else "utf-8")
    newline = detect_newline(content)
    parser = FrontmatterParser()
    fm, body = parser.parse(content)
    if description:
        parser.set_description(fm, description)
    if name:
        parser.set_name(fm, name)
    new_content = parser.build(fm, body)
    new_content = new_content.replace("\r\n", "\n").replace("\n", newline)
    out = new_content.encode("utf-8")
    return b"\xef\xbb\xbf" + out if has_bom else out


def _preferred_duplicate_record(group: DuplicateGroup) -> Record:
    user_records = tuple(record for record in group.records if record.scope == "user")
    if user_records:
        return sorted(user_records, key=lambda record: record.source_path)[0]
    return sorted(group.records, key=lambda record: record.source_path)[0]


def _duplicate_suppression_targets(plan: GovernancePlan) -> tuple[Record, ...]:
    targets: tuple[Record, ...] = ()
    for group in plan.duplicate_groups:
        preferred = _preferred_duplicate_record(group)
        for record in group.records:
            if record.source_path != preferred.source_path:
                targets = (*targets, record)
    return targets


def _available_suppressed_path(path: Path) -> Path:
    base = path.with_name(path.name + ".claude-translator-disabled")
    if not base.exists():
        return base
    index = 1
    while True:
        candidate = Path(str(base) + f".{index}")
        if not candidate.exists():
            return candidate
        index += 1


def apply_governance_plan(
    plan: GovernancePlan,
    options: GovernanceOptions | None = None,
) -> GovernanceReport:
    resolved_options = options or GovernanceOptions()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    backup_dir = _backup_root(resolved_options) / run_id
    backup_dir.mkdir(parents=True, exist_ok=True)

    manifest_items: list[dict[str, str]] = []
    applied_descriptions = 0
    applied_names = 0
    suppressed = 0

    for action in plan.actions:
        path = Path(action.target.source_path)
        current_hash = _file_sha256(path)
        if current_hash != action.expected_sha256:
            continue

        backup_path = backup_dir / f"{len(manifest_items):04d}-{path.name}"
        shutil.copy2(path, backup_path)
        new_bytes = _rewrite_frontmatter_bytes(
            path,
            description=action.replacement_description,
            name=action.replacement_name,
        )
        path.write_bytes(new_bytes)
        new_hash = _sha256_bytes(new_bytes)
        if action.replacement_description:
            applied_descriptions += 1
        if action.replacement_name:
            applied_names += 1
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

    for record in _duplicate_suppression_targets(plan):
        path = Path(record.source_path)
        if not path.exists():
            continue
        current_hash = _file_sha256(path)
        backup_path = backup_dir / f"{len(manifest_items):04d}-{path.name}"
        shutil.copy2(path, backup_path)
        suppressed_path = _available_suppressed_path(path)
        path.replace(suppressed_path)
        suppressed += 1
        display_name = record.canonical_id.split(":", 1)[1]
        manifest_items.append(
            {
                "canonical_id": record.canonical_id,
                "display_key": f"{record.kind}:{display_name}",
                "source_path": str(path),
                "backup_path": str(backup_path),
                "suppressed_path": str(suppressed_path),
                "action": "suppress_duplicate",
                "reason": "duplicate_display",
                "old_sha256": current_hash,
                "new_sha256": "moved",
                "status": "applied",
            }
        )

    manifest_path = backup_dir / "manifest.json"
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "lang": resolved_options.target_lang,
        "tool_version": __version__,
        "items": manifest_items,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    return GovernanceReport(
        scanned=plan.scanned,
        strict_language_violations=len(plan.language_violations),
        duplicate_display_groups=len(plan.duplicate_groups),
        planned_description_rewrites=sum(
            1 for action in plan.actions if action.replacement_description
        ),
        planned_duplicate_suppressions=len(_duplicate_suppression_targets(plan)),
        planned_name_repairs=sum(1 for action in plan.actions if action.replacement_name),
        applied_description_rewrites=applied_descriptions,
        applied_duplicate_suppressions=suppressed,
        applied_name_repairs=applied_names,
        unresolved_duplicate_groups=max(len(plan.duplicate_groups) - suppressed, 0),
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
        if item.get("new_sha256") == "moved":
            suppressed_path = Path(item["suppressed_path"])
            if source_path.exists():
                refused += 1
                continue
            if suppressed_path.exists():
                suppressed_path.replace(source_path)
            else:
                shutil.copy2(backup_path, source_path)
        else:
            if _file_sha256(source_path) != item["new_sha256"]:
                refused += 1
                continue
            shutil.copy2(backup_path, source_path)
        if _file_sha256(source_path) == item["old_sha256"]:
            restored += 1
        else:
            refused += 1

    return RestoreReport(planned_restores=planned, restored=restored, refused=refused)
