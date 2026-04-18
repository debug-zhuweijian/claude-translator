from claude_translator.utils.paths import detect_newline, normalize_path


def test_normalize_path_forward_slash():
    assert normalize_path("skills/brainstorm/SKILL.md") == "skills/brainstorm/SKILL.md"


def test_normalize_path_backslash():
    assert normalize_path("skills\\brainstorm\\SKILL.md") == "skills/brainstorm/SKILL.md"


def test_normalize_path_mixed():
    assert normalize_path("skills\\brainstorm/SKILL.md") == "skills/brainstorm/SKILL.md"


def test_normalize_path_empty():
    assert normalize_path("") == ""


def test_detect_newline_lf():
    assert detect_newline("line1\nline2") == "\n"


def test_detect_newline_crlf():
    assert detect_newline("line1\r\nline2") == "\r\n"


def test_detect_newline_no_newline():
    assert detect_newline("no newline") == "\n"


def test_detect_newline_crlf_priority():
    assert detect_newline("line1\r\nline2\nline3") == "\r\n"
