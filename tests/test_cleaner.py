import pytest

from claude_translator.errors import TranslatorError
from claude_translator.lang.cleaner import clean_llm_response


def test_cleaner_strips_wrapping_quotes():
    assert clean_llm_response('"你好世界"') == "你好世界"


def test_cleaner_strips_common_prefix():
    assert clean_llm_response("Translation: hello") == "hello"


def test_cleaner_merges_multiline_output():
    """Internal newlines are merged to spaces."""
    assert clean_llm_response("line one\nline two") == "line one line two"


def test_cleaner_merges_multiple_newlines():
    """Multiple consecutive newlines collapse to a single space."""
    assert clean_llm_response("line one\n\n\nline two") == "line one line two"


def test_cleaner_merges_carriage_returns():
    """CRLF is also merged."""
    assert clean_llm_response("line one\r\nline two") == "line one line two"


def test_cleaner_rejects_frontmatter_boundary():
    with pytest.raises(TranslatorError):
        clean_llm_response("hello --- world")
