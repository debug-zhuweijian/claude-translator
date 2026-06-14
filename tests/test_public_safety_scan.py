from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_SCRIPT = ROOT / "scripts" / "scan-public-safety.py"


def run_scan(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCAN_SCRIPT), "--repo-root", str(repo), *args],
        check=False,
        text=True,
        capture_output=True,
    )


def init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)


def test_public_placeholders_are_allowed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        init_repo(repo)
        readme = repo / "README.md"
        readme.write_text(
            "Created config at C:\\Users\\you\\.claude\\translations\\config.json\n"
            "CLAUDE_TRANSLATE_LLM_BASE_URL=http://localhost:11434/v1\n"
            "CLAUDE_TRANSLATE_LLM_API_KEY=ollama\n"
            "OPENAI_API_KEY=your-key-here\n"
            "base_url=https://api.openai.com/v1\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)

        result = run_scan(repo, "--tree")

        assert result.returncode == 0, result.stdout + result.stderr


def test_real_bearer_token_is_blocked_without_printing_value() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        init_repo(repo)
        token = "A" * 24
        config = repo / "config.md"
        config.write_text(f"Authorization: Bearer {token}\n", encoding="utf-8")
        subprocess.run(["git", "add", "config.md"], cwd=repo, check=True)

        result = run_scan(repo, "--staged")

        assert result.returncode != 0
        assert "bearer-token" in result.stdout
        assert token not in result.stdout


def test_private_model_default_is_blocked() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        init_repo(repo)
        model = "glm" + "-5.2"
        config = repo / "config.md"
        config.write_text(f"model={model}\n", encoding="utf-8")
        subprocess.run(["git", "add", "config.md"], cwd=repo, check=True)

        result = run_scan(repo, "--staged")

        assert result.returncode != 0
        assert "private-model-default" in result.stdout
