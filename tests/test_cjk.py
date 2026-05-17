from claude_translator.lang.cjk import has_cjk, has_ja, has_ko


def test_has_cjk_chinese():
    assert has_cjk("你好世界") is True


def test_has_cjk_english():
    assert has_cjk("hello world") is False


def test_has_cjk_mixed():
    assert has_cjk("hello 你好") is True


def test_has_ja_hiragana():
    assert has_ja("こんにちは") is True


def test_has_ja_katakana():
    assert has_ja("コンニチハ") is True


def test_has_ja_chinese_only():
    assert has_ja("你好世界") is False


def test_has_ko_hangul():
    assert has_ko("안녕하세요") is True


def test_has_ko_chinese():
    assert has_ko("你好") is False


def test_empty_string():
    assert has_cjk("") is False
    assert has_ja("") is False
    assert has_ko("") is False
