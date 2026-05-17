from claude_translator.core.frontmatter import FrontmatterParser


def test_parse_with_frontmatter():
    content = "---\ndescription: Hello world\n---\nBody text here"
    parser = FrontmatterParser()
    fm, body = parser.parse(content)
    assert parser.get_description(fm) == "Hello world"
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
    fm, _ = p.parse("---\ndescription: old\n---\nBody")
    assert p.set_description(fm, "new")["description"] == "new"


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


def test_parse_multiline_description():
    """Multi-line description is fully captured."""
    content = "---\ndescription: |\n  Line one\n  Line two\n  Line three\n---\nBody"
    fm, body = FrontmatterParser().parse(content)
    assert "Line one" in fm["description"]
    assert "Line two" in fm["description"]
    assert "Line three" in fm["description"]
    assert body == "Body"


def test_build_multiline_description():
    """Multi-line description round-trips through YAML safely."""
    parser = FrontmatterParser()
    fm = parser.set_description({}, "Line one\nLine two\nLine three")
    result = parser.build(fm, "# Body")
    parsed, body = parser.parse(result)
    assert parser.get_description(parsed) == "Line one\nLine two\nLine three"
    assert body == "# Body"


def test_round_trip_quotes_and_colon():
    parser = FrontmatterParser()
    content = '---\ndescription: "hello: world"\n---\nBody'
    fm, body = parser.parse(content)
    rebuilt = parser.build(fm, body)
    parsed, rebuilt_body = parser.parse(rebuilt)
    assert parser.get_description(parsed) == "hello: world"
    assert rebuilt_body == "Body"
