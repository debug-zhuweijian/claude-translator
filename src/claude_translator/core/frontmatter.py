"""Frontmatter parsing and generation for Claude skill/command markdown files."""

from __future__ import annotations

import re


class FrontmatterParser:
    _FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)", re.DOTALL)

    @staticmethod
    def _strip_quotes(value: str) -> str:
        if len(value) >= 2:
            if (value[0] == '"' and value[-1] == '"') or \
               (value[0] == "'" and value[-1] == "'"):
                return value[1:-1]
        return value

    def parse(self, content: str) -> tuple[dict[str, str], str]:
        m = self._FRONTMATTER_RE.match(content)
        if not m:
            return {}, content
        fm_raw = m.group(1)
        body = m.group(2)
        fm: dict[str, str] = {}
        current_key: str | None = None
        for line in fm_raw.split("\n"):
            stripped = line.strip()
            if not stripped:
                current_key = None
                continue
            if ":" in stripped and not stripped[0].isspace():
                key, _, value = stripped.partition(":")
                current_key = key.strip()
                fm[current_key] = self._strip_quotes(value.strip())
            elif current_key and line[0:1] == " ":
                fm[current_key] = fm[current_key] + "\n" + stripped
        return fm, body

    def get_description(self, fm: dict[str, str]) -> str | None:
        return fm.get("description")

    def set_description(self, fm: dict[str, str], description: str) -> dict[str, str]:
        return {**fm, "description": description}

    def build(self, fm: dict[str, str], body: str) -> str:
        if not fm:
            return body
        lines = ["---"]
        for key, value in fm.items():
            if "\n" in value:
                lines.append(f"{key}:")
                for vline in value.split("\n"):
                    lines.append(f"  {vline}")
            else:
                lines.append(f"{key}: {value}")
        lines.append("---")
        return "\n".join(lines) + "\n" + body
