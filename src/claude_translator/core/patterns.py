"""Shared regex patterns for Claude Code metadata handling."""

from __future__ import annotations

import re

SLASH_COMMAND_RE = re.compile(r"(?<![:/\w.-])/[a-z][a-z0-9:_-]*(?:/[a-z0-9:_-]+)*")
