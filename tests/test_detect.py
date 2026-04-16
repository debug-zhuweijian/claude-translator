from claude_translator.lang.detect import detect_script

def test_detect_korean():
    assert detect_script("안녕하세요 세계") == "ko"
def test_detect_japanese_kana():
    assert detect_script("こんにちは世界") == "ja"
def test_detect_chinese_only():
    assert detect_script("你好世界") == "zh"
def test_detect_english():
    assert detect_script("hello world") == "unknown"
def test_detect_mixed_korean_cjk():
    assert detect_script("안녕 中文混合") == "ko"
def test_detect_mixed_japanese_cjk():
    assert detect_script("こんにちは 中文混合") == "ja"
def test_detect_empty():
    assert detect_script("") == "unknown"
def test_detect_numbers():
    assert detect_script("12345") == "unknown"
