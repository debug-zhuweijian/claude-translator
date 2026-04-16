from claude_translator.core.frontmatter import FrontmatterParser


def test_parse_with_frontmatter():
    content = "---\ndescription: Hello world\n---\nBody text here"
    parser = FrontmatterParser()
    fm, body = parser.parse(content)
    assert fm == {"description": "Hello world"}
    assert body == "Body text here"

def test_parse_no_frontmatter():
    content = "# Just a heading\nSome text"
    fm, body = FrontmatterParser().parse(content)
    assert fm == {}
    assert body == content

def test_parse_crlf():
    fm, body = FrontmatterParser().parse("---\r\ndescription: Test\r\n---\r\nBody")
    assert fm == {"description": "Test"}
    assert body == "Body"

def test_get_description():
    p = FrontmatterParser()
    assert p.get_description({"description": "Hello"}) == "Hello"
    assert p.get_description({}) is None

def test_set_description():
    p = FrontmatterParser()
    assert p.set_description({"description": "old"}, "new")["description"] == "new"

def test_set_description_adds_key():
    assert FrontmatterParser().set_description({}, "new")["description"] == "new"

def test_build_with_frontmatter():
    result = FrontmatterParser().build({"description": "Test"}, "# Heading")
    assert "---" in result
    assert "description: Test" in result
    assert "# Heading" in result

def test_build_preserves_existing_keys():
    result = FrontmatterParser().build({"description": "A", "name": "B"}, "body")
    assert "name: B" in result

def test_build_no_frontmatter():
    assert FrontmatterParser().build({}, "just body") == "just body"
