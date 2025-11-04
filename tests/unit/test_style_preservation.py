"""Tests for style preservation in Markdown rendering."""


from unpdf.models.layout import Block, BlockType, Style
from unpdf.processors.document_processor import ProcessedDocument, ProcessedPage
from unpdf.renderers.document_renderer import MarkdownRenderer


class TestStylePreservation:
    """Tests for applying text styles in Markdown rendering."""

    def test_bold_text(self):
        """Test that bold text is rendered with ** markers."""
        style = Style(weight="bold")
        renderer = MarkdownRenderer(preserve_styles=True)
        result = renderer._apply_styles("Bold text", style)
        assert result == "**Bold text**"

    def test_bold_numeric_weight(self):
        """Test bold with numeric weight >= 700."""
        style = Style(weight=700)
        renderer = MarkdownRenderer(preserve_styles=True)
        result = renderer._apply_styles("Bold text", style)
        assert result == "**Bold text**"

    def test_italic_text(self):
        """Test that italic text is rendered with * markers."""
        style = Style(style="italic")
        renderer = MarkdownRenderer(preserve_styles=True)
        result = renderer._apply_styles("Italic text", style)
        assert result == "*Italic text*"

    def test_bold_italic_text(self):
        """Test that bold+italic text is rendered with *** markers."""
        style = Style(weight="bold", style="italic")
        renderer = MarkdownRenderer(preserve_styles=True)
        result = renderer._apply_styles("Bold italic", style)
        assert result == "***Bold italic***"

    def test_monospace_text(self):
        """Test that monospace text is rendered with backticks."""
        style = Style(monospace=True)
        renderer = MarkdownRenderer(preserve_styles=True)
        result = renderer._apply_styles("Code text", style)
        assert result == "`Code text`"

    def test_strikethrough_text(self):
        """Test that strikethrough text is rendered with ~~ markers."""
        style = Style(strikethrough=True)
        renderer = MarkdownRenderer(preserve_styles=True)
        result = renderer._apply_styles("Strikethrough", style)
        assert result == "~~Strikethrough~~"

    def test_underline_text(self):
        """Test that underlined text is rendered with HTML <u> tag."""
        style = Style(underline=True)
        renderer = MarkdownRenderer(preserve_styles=True)
        result = renderer._apply_styles("Underlined", style)
        assert result == "<u>Underlined</u>"

    def test_colored_text(self):
        """Test that colored text is rendered with HTML span."""
        # Red color (1.0, 0.0, 0.0)
        style = Style(color=(1.0, 0.0, 0.0))
        renderer = MarkdownRenderer(preserve_styles=True)
        result = renderer._apply_styles("Red text", style)
        assert 'style="color:#ff0000"' in result
        assert "Red text" in result

    def test_black_text_not_colored(self):
        """Test that black text doesn't get color span."""
        style = Style(color=(0.0, 0.0, 0.0))
        renderer = MarkdownRenderer(preserve_styles=True)
        result = renderer._apply_styles("Black text", style)
        assert result == "Black text"
        assert "span" not in result

    def test_dark_gray_not_colored(self):
        """Test that dark gray text doesn't get color span."""
        style = Style(color=(0.1, 0.1, 0.1))
        renderer = MarkdownRenderer(preserve_styles=True)
        result = renderer._apply_styles("Dark gray", style)
        assert result == "Dark gray"
        assert "span" not in result

    def test_combined_styles(self):
        """Test combining multiple styles."""
        style = Style(weight="bold", strikethrough=True)
        renderer = MarkdownRenderer(preserve_styles=True)
        result = renderer._apply_styles("Combined", style)
        assert "**" in result
        assert "~~" in result

    def test_preserve_styles_disabled(self):
        """Test that styles are not applied when preserve_styles=False."""
        style = Style(weight="bold", style="italic")
        renderer = MarkdownRenderer(preserve_styles=False)
        result = renderer._apply_styles("Plain text", style)
        assert result == "Plain text"

    def test_no_style_object(self):
        """Test handling when no style object is provided."""
        renderer = MarkdownRenderer(preserve_styles=True)
        result = renderer._apply_styles("Plain text", None)
        assert result == "Plain text"

    def test_monospace_priority(self):
        """Test that monospace takes priority over other styles."""
        style = Style(monospace=True, weight="bold")
        renderer = MarkdownRenderer(preserve_styles=True)
        result = renderer._apply_styles("Code", style)
        # Monospace should be applied, not bold
        assert result == "`Code`"
        assert "**" not in result


class TestIsNonStandardColor:
    """Tests for color detection helper."""

    def test_black_is_standard(self):
        """Test that pure black is considered standard."""
        renderer = MarkdownRenderer()
        assert not renderer._is_non_standard_color((0.0, 0.0, 0.0))

    def test_dark_gray_is_standard(self):
        """Test that dark gray is considered standard."""
        renderer = MarkdownRenderer()
        assert not renderer._is_non_standard_color((0.15, 0.15, 0.15))

    def test_red_is_non_standard(self):
        """Test that red is considered non-standard."""
        renderer = MarkdownRenderer()
        assert renderer._is_non_standard_color((1.0, 0.0, 0.0))

    def test_blue_is_non_standard(self):
        """Test that blue is considered non-standard."""
        renderer = MarkdownRenderer()
        assert renderer._is_non_standard_color((0.0, 0.0, 1.0))

    def test_light_gray_is_non_standard(self):
        """Test that light gray is considered non-standard."""
        renderer = MarkdownRenderer()
        assert renderer._is_non_standard_color((0.5, 0.5, 0.5))


class TestStyleInBlocks:
    """Integration tests for styled blocks."""

    def test_styled_paragraph_rendering(self):
        """Test that styled paragraphs render correctly."""
        style = Style(weight="bold")
        block = Block(
            block_type=BlockType.TEXT,
            content="Bold paragraph",
            bbox=None,
            style=style,
        )
        page = ProcessedPage(
            page_number=1,
            blocks=[block],
            tables=[],
            images=[],
            layout_info={},
        )
        doc = ProcessedDocument(pages=[page], metadata={}, font_stats={})

        renderer = MarkdownRenderer(include_metadata=False, preserve_styles=True)
        result = renderer.render(doc)

        assert "**Bold paragraph**" in result

    def test_styled_heading_rendering(self):
        """Test that styled headings render correctly."""
        style = Style(weight="bold")
        block = Block(
            block_type=BlockType.HEADING,
            content="Main Title",
            bbox=None,
            style=style,
            metadata={"level": 1},
        )
        page = ProcessedPage(
            page_number=1,
            blocks=[block],
            tables=[],
            images=[],
            layout_info={},
        )
        doc = ProcessedDocument(pages=[page], metadata={}, font_stats={})

        renderer = MarkdownRenderer(include_metadata=False, preserve_styles=True)
        result = renderer.render(doc)

        assert "# **Main Title**" in result

    def test_styled_list_item_rendering(self):
        """Test that styled list items render correctly."""
        style = Style(style="italic")
        block = Block(
            block_type=BlockType.LIST,
            content="Important item",
            bbox=None,
            style=style,
            metadata={"list_type": "bullet", "indent_level": 0},
        )
        page = ProcessedPage(
            page_number=1,
            blocks=[block],
            tables=[],
            images=[],
            layout_info={},
        )
        doc = ProcessedDocument(pages=[page], metadata={}, font_stats={})

        renderer = MarkdownRenderer(include_metadata=False, preserve_styles=True)
        result = renderer.render(doc)

        assert "*Important item*" in result
        assert "-" in result  # Bullet marker
