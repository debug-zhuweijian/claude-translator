"""Exception hierarchy for claude-translator."""


class TranslatorError(Exception):
    """Base exception for all claude-translator errors."""


class UserError(TranslatorError):
    """User environment or configuration problems."""


class ConfigError(UserError):
    """Configuration file content or structure issues."""


class PathError(UserError):
    """~/.claude/ directory missing or inaccessible."""


class InternalError(TranslatorError):
    """Program bugs — should never occur in production."""
