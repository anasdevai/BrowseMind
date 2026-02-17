"""
Unit tests for tool implementations
"""
import pytest
from app.tools.browser_tools import NavigateTool, ClickElementTool, TypeTextTool, ScrollTool, ScreenshotTool
from app.tools.extraction_tools import ExtractTextTool, ExtractLinksTool, ExtractTablesTool, GetDOMTool, HighlightElementTool


@pytest.mark.asyncio
async def test_navigate_tool():
    """Test navigate tool"""
    tool = NavigateTool()

    assert tool.name == "navigate"
    assert tool.category == "browser_control"

    # Test schema
    schema = tool.get_schema()
    assert "url" in schema["properties"]


@pytest.mark.asyncio
async def test_click_element_tool():
    """Test click element tool"""
    tool = ClickElementTool()

    assert tool.name == "click_element"

    # Test schema
    schema = tool.get_schema()
    assert "selector" in schema["properties"] or "text" in schema["properties"]


@pytest.mark.asyncio
async def test_type_text_tool():
    """Test type text tool"""
    tool = TypeTextTool()

    assert tool.name == "type_text"

    # Test schema
    schema = tool.get_schema()
    assert "selector" in schema["properties"]
    assert "text" in schema["properties"]


@pytest.mark.asyncio
async def test_scroll_tool():
    """Test scroll tool"""
    tool = ScrollTool()

    assert tool.name == "scroll"

    # Test schema
    schema = tool.get_schema()
    assert "direction" in schema["properties"]


@pytest.mark.asyncio
async def test_screenshot_tool():
    """Test screenshot tool"""
    tool = ScreenshotTool()

    assert tool.name == "screenshot"


@pytest.mark.asyncio
async def test_extract_text_tool():
    """Test extract text tool"""
    tool = ExtractTextTool()

    assert tool.name == "extract_text"
    assert tool.category == "extraction"

    # Test schema
    schema = tool.get_schema()
    assert "selector" in schema["properties"]


@pytest.mark.asyncio
async def test_extract_links_tool():
    """Test extract links tool"""
    tool = ExtractLinksTool()

    assert tool.name == "extract_links"


@pytest.mark.asyncio
async def test_extract_tables_tool():
    """Test extract tables tool"""
    tool = ExtractTablesTool()

    assert tool.name == "extract_tables"


@pytest.mark.asyncio
async def test_get_dom_tool():
    """Test get DOM tool"""
    tool = GetDOMTool()

    assert tool.name == "get_dom"


@pytest.mark.asyncio
async def test_highlight_element_tool():
    """Test highlight element tool"""
    tool = HighlightElementTool()

    assert tool.name == "highlight_element"
