import json
from pathlib import Path

from claude_translator.core.governance import (
    GovernanceOptions,
    apply_governance_plan,
    create_governance_plan,
    restore_from_manifest,
)
from claude_translator.core.models import Inventory, Record


def _write_entry(path: Path, description: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\ndescription: {description}\n---\n# Body\n", encoding="utf-8")


def _record(path: Path, canonical_id: str, description: str, *, scope: str = "user") -> Record:
    _write_entry(path, description)
    return Record(
        canonical_id=canonical_id,
        kind="skill",
        scope=scope,
        source_path=str(path),
        relative_path="skill/SKILL.md",
        current_description=description,
        frontmatter_present=True,
    )


def test_create_governance_plan_reports_rewrites_and_duplicates_without_writing(tmp_path: Path):
    user = _record(
        tmp_path / "user" / "nature-data" / "SKILL.md", "user.skill:nature-data", "English only"
    )
    plugin = _record(
        tmp_path / "plugin" / "nature-data" / "SKILL.md",
        "plugin.nature-skills.skill:nature-data",
        "中文说明",
        scope="plugin",
    )
    inventory = Inventory((user, plugin))

    plan = create_governance_plan(
        inventory,
        GovernanceOptions(target_lang="zh-CN", translations={"user.skill:nature-data": "中文翻译"}),
    )

    assert len(plan.language_violations) == 1
    assert len(plan.duplicate_groups) == 1
    assert len(plan.actions) == 1
    assert plan.actions[0].action_type == "rewrite_description"
    assert (
        user.source_path
        and Path(user.source_path).read_text(encoding="utf-8").count("English only") == 1
    )


def test_apply_governance_plan_rewrites_after_backup_and_writes_manifest(tmp_path: Path):
    entry = _record(tmp_path / "skill" / "SKILL.md", "user.skill:test", "English only")
    inventory = Inventory((entry,))
    options = GovernanceOptions(
        target_lang="zh-CN",
        translations={"user.skill:test": "中文翻译"},
        backup_root=tmp_path / "translations" / "backups",
    )
    plan = create_governance_plan(inventory, options)

    report = apply_governance_plan(plan, options)

    assert report.applied_description_rewrites == 1
    assert report.backup_manifest is not None
    assert "description: 中文翻译" in (tmp_path / "skill" / "SKILL.md").read_text(encoding="utf-8")
    manifest = json.loads(Path(report.backup_manifest).read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["items"][0]["old_sha256"]
    assert manifest["items"][0]["new_sha256"]
    assert Path(manifest["items"][0]["backup_path"]).exists()


def test_restore_from_manifest_defaults_to_dry_run(tmp_path: Path):
    entry = _record(tmp_path / "skill" / "SKILL.md", "user.skill:test", "English only")
    options = GovernanceOptions(
        target_lang="zh-CN",
        translations={"user.skill:test": "中文翻译"},
        backup_root=tmp_path / "translations" / "backups",
    )
    report = apply_governance_plan(create_governance_plan(Inventory((entry,)), options), options)
    manifest_path = Path(report.backup_manifest or "")

    restore_report = restore_from_manifest(manifest_path, apply=False)

    assert restore_report.restored == 0
    assert restore_report.planned_restores == 1
    assert "description: 中文翻译" in (tmp_path / "skill" / "SKILL.md").read_text(encoding="utf-8")


def test_restore_from_manifest_apply_restores_original_when_hash_matches(tmp_path: Path):
    entry = _record(tmp_path / "skill" / "SKILL.md", "user.skill:test", "English only")
    options = GovernanceOptions(
        target_lang="zh-CN",
        translations={"user.skill:test": "中文翻译"},
        backup_root=tmp_path / "translations" / "backups",
    )
    report = apply_governance_plan(create_governance_plan(Inventory((entry,)), options), options)

    restore_report = restore_from_manifest(Path(report.backup_manifest or ""), apply=True)

    assert restore_report.restored == 1
    assert "description: English only" in (tmp_path / "skill" / "SKILL.md").read_text(
        encoding="utf-8"
    )


def test_restore_from_manifest_refuses_hash_mismatch(tmp_path: Path):
    entry = _record(tmp_path / "skill" / "SKILL.md", "user.skill:test", "English only")
    options = GovernanceOptions(
        target_lang="zh-CN",
        translations={"user.skill:test": "中文翻译"},
        backup_root=tmp_path / "translations" / "backups",
    )
    report = apply_governance_plan(create_governance_plan(Inventory((entry,)), options), options)
    target = tmp_path / "skill" / "SKILL.md"
    target.write_text("---\ndescription: 用户后续修改\n---\n# Body\n", encoding="utf-8")

    restore_report = restore_from_manifest(Path(report.backup_manifest or ""), apply=True)

    assert restore_report.restored == 0
    assert restore_report.refused == 1
    assert "用户后续修改" in target.read_text(encoding="utf-8")
