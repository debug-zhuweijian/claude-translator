from pytest import raises

from claude_translator.errors import (
    ConfigError,
    FileSystemError,
    InternalError,
    PathError,
    TranslatorError,
    UserError,
)


def test_exception_hierarchy():
    assert issubclass(UserError, TranslatorError)
    assert issubclass(ConfigError, UserError)
    assert issubclass(FileSystemError, UserError)
    assert issubclass(PathError, UserError)
    assert issubclass(InternalError, TranslatorError)


def test_config_error_is_user_error():
    with raises(UserError):
        raise ConfigError("bad config")


def test_path_error_is_user_error():
    with raises(UserError):
        raise PathError("~/.claude/ missing")


def test_internal_error_not_user_error():
    assert not issubclass(InternalError, UserError)


def test_all_carry_message():
    for cls in [ConfigError, FileSystemError, PathError, InternalError]:
        e = cls("test msg")
        assert str(e) == "test msg"
