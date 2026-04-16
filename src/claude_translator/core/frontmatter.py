"""Frontmatter parsing and generation for Claude skill/command markdown files."""

from __future__ import annotations

import re


class FrontmatterParser:
    _FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)", re.DOTALL)

    def parse(self, content: str) -> tuple[dict[str, str], str]:
        m = self._FRONTMATTER_RE.match(content)
        if not m:
            return {}, content
        fm_raw = m.group(1)
        body = m.group(2)
        fm: dict[str, str] = {}
        for line in fm_raw.split("\n"):
            line = line.strip()
            if ":" in line:
                key, _, value = line.partition(":")
                fm[key.strip()] = value.strip()
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
            lines.append(f"{key}: {value}")
        lines.append("---")
        return "\n".join(lines) + "\n" + body
