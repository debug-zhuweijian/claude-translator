"""Frontmatter parsing and generation for Claude skill/command markdown files."""

from __future__ import annotations

import re
from io import StringIO

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap


class FrontmatterParser:
    _FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)", re.DOTALL)

    def __init__(self) -> None:
        self._yaml = YAML()
        self._yaml.preserve_quotes = True
        self._yaml.default_flow_style = False

    def parse(self, content: str) -> tuple[CommentedMap, str]:
        m = self._FRONTMATTER_RE.match(content)
        if not m:
            return CommentedMap(), content
        fm_raw = m.group(1)
        body = m.group(2)

        try:
            fm = self._yaml.load(fm_raw) or CommentedMap()
        except Exception:
            return CommentedMap(), content

        if not isinstance(fm, CommentedMap):
            return CommentedMap(), content

        return fm, body

    def get_description(self, fm: CommentedMap) -> str | None:
        value = fm.get("description")
        return str(value) if value is not None else None

    def set_description(self, fm: CommentedMap, description: str) -> CommentedMap:
        fm["description"] = description
        return fm

    def build(self, fm: CommentedMap, body: str) -> str:
        if not fm:
            return body

        stream = StringIO()
        stream.write("---\n")
        self._yaml.dump(fm, stream)
        stream.write("---\n")
        return stream.getvalue() + body
