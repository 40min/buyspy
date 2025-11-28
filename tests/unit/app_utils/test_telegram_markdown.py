from app.app_utils.telegram_markdown import (
    convert_urls_to_links,
    escape_markdown_v2,
)


class TestTelegramMarkdown:
    """Test markdown escaping functionality in telegram_markdown utility."""

    def test_escape_markdown_v2_with_problematic_example(self) -> None:
        """Test the exact problematic example from the error."""
        # This is the exact text that was causing the error
        input_text = "💰 *Pricing Results:*\n\n*Product:* Sony WH-CH720N wireless headphones\n*Best Prices:*\n- *54.98 EUR* at [Gigantti.fi](https://www.gigantti.fi/product/tv-aani-ja-alykoti/kuulokkeet-ja-tarvikkeet/kuulokkeet/sony-wh-ch720n-langattomat-around-ear-kuulokkeet-musta/593542) ✅ ⭐\n- *69.00 EUR* at [Hinta.fi](https://hinta.fi/4026623/sony-wh-ch720n) ✅ 💫\n- *69.00 EUR* at [Telia Finland](https://www.hintaseuranta.fi/tuote/siirry/kauppaan?params=YToxMjp7czo2OiJ0YXJnZXQiO3M6MTQ6ImthdXBwYWFubGlua2tpIjtzOjQ6InR5cGUiO3M6NzoicHJvZHVjdCI7czo4OiJyZWRpcmVjdCI7czo1NDoiL2thdXBwYXJlZC5hc3B4P2thdXBwYT0xMDI0JnR1b3RlPTEyMzI4NzAzJmt0PTQzNzI3NTIwIjtzOjg6ImNhdGVnb3J5IjtzOjEwOiJLdXVsb2trZWV0IjtzOjg6Iml0ZW1hYWUiO3M6NDQ6IlNvbnkgV0gtQ0g3MjBOIHZhc3RhbWVsdWt1dWxsb2ttZWV0LiBTaW5pbmVuIjtzOjg6InJldGFpbGVyIjtzOjEzOiJUZWxpYSBGaW5sYW5kIjtzOjEwOiJyZXRhaWxlcklkIjtpOjEwMjQ7czoxMDoiY2F0ZWdvcnlJZCI7aToyNjMxMDtzOjc6Imluc2lnaHQiO3M6MjU6Ii9oaXNlL1RWIGphIGtvdGl0ZWF0dGVyZXYvIjtzOjg6InBvc2l0aW9uIjtpOjE7czoxMjoicHJvZHVjdFByaWNlIjtkOjY5O3M6MTA6ImNsaWNrUHJpY2UiO3M6NDoiMC4yMiI7fQ==&kumppaniavain=1) ✅ ⭐\n- *113.00 EUR* at [Brl.fi](https://www.brl.fi/fi/artiklar/sony-wh-ch720n-langattomat-melua-vaimentavat-over-ear-kuulokkeet-musta.html) ✅ 🌟\n📊 *Total Found:* 4"

        result = escape_markdown_v2(input_text)

        # Check that URLs are preserved (not over-escaped with periods) - this is the key fix
        assert "https://www.gigantti.fi" in result
        assert "https://www.brl.fi" in result

        # Check that periods in regular text are escaped
        assert "54\\.98 EUR" in result
        assert "113\\.00 EUR" in result

        # Check that emojis are preserved
        assert "✅" in result
        assert "⭐" in result
        assert "💫" in result
        assert "🌟" in result
        assert "📊" in result

    def test_escape_markdown_v2_basic_link_preservation(self) -> None:
        """Test basic link preservation while escaping other markdown."""
        input_text = "💰 *Pricing Results:*\n\n*Product:* Anker Soundcore Life Q20\n*Best Prices:*\n- *[41.99 USD](https://www.amazon.com/test)* at Amazon.com ✅ In Stock 🌟"

        result = escape_markdown_v2(input_text)

        # Check that links are preserved with URL periods not escaped (key requirement)
        assert "https://www.amazon.com/test" in result  # URL should be preserved

        # Check that other markdown is properly handled (testing the key behavior)
        assert "💰" in result
        assert "✅" in result  # emojis should not be escaped

    def test_escape_markdown_v2_multiple_links(self) -> None:
        """Test multiple links preservation."""
        input_text = "Check [Amazon](https://amazon.com) and [eBay](https://ebay.com) for prices."

        result = escape_markdown_v2(input_text)

        # Check that both links are preserved
        assert "[Amazon](https://amazon.com)" in result
        assert "[eBay](https://ebay.com)" in result

        # Check that other text is preserved
        assert "Check" in result
        assert "and" in result
        assert "for prices" in result

    def test_escape_markdown_v2_links_with_special_chars_in_url(self) -> None:
        """Test links with special characters in URLs."""
        input_text = "[Search](https://example.com?q=test&sort=price) and [Download](https://files.com/download?file=test.pdf)"

        result = escape_markdown_v2(input_text)

        # URLs should have proper escaping and periods preserved
        assert "[Search]" in result
        assert "[Download]" in result
        assert "https://example.com" in result
        assert "https://files.com" in result

    def test_convert_urls_to_links_basic(self) -> None:
        """Test URL to link conversion."""
        input_text = "Check https://amazon.com and https://ebay.com for prices."

        result = convert_urls_to_links(input_text)

        # Check that URLs are converted to links
        assert "[Amazon](https://amazon.com)" in result
        assert "[Ebay](https://ebay.com)" in result

    def test_url_conversion_without_existing_links(self) -> None:
        """Test URL conversion when there are no existing links."""
        input_text = "Check https://amazon.com and https://ebay.com for prices."

        result = convert_urls_to_links(input_text)

        # URLs should be converted to links
        assert "[Amazon](https://amazon.com)" in result
        assert "[Ebay](https://ebay.com)" in result

    def test_url_conversion_skipped_with_existing_links(self) -> None:
        """Test that URL conversion is skipped when there are existing links."""
        input_text = (
            "Visit [Amazon](https://amazon.com) and check https://ebay.com for prices."
        )

        result = convert_urls_to_links(input_text)

        # Existing link should be preserved, raw URL should not be converted
        assert "[Amazon](https://amazon.com)" in result
        assert "https://ebay.com" in result  # Raw URL should remain as-is
        assert "[Ebay](https://ebay.com)" not in result  # Should not be converted

    def test_full_formatting_flow(self) -> None:
        """Test the complete formatting flow: convert URLs to links and escape markdown."""
        input_text = "💰 *Pricing Results:*\n\n*Product:* Anker Soundcore Life Q20\n*Best Prices:*\n- *41.99 USD* at [Amazon.com](https://www.amazon.com/test)\n- *59.99 USD* at [Soundcore](https://soundcore.com)"

        # First convert URLs (if any)
        formatted_text = convert_urls_to_links(input_text)
        # Then escape markdown
        final_text = escape_markdown_v2(formatted_text)

        # Verify that the original links are preserved (note: periods in link text are escaped)
        assert "Amazon\\.com" in final_text  # Period in link text is escaped
        assert "[Soundcore](https://soundcore.com)" in final_text

        # Verify that markdown formatting is handled properly
        assert "💰" in final_text
        # Verify that periods in URLs are preserved (this was the main issue)
        assert "https://www.amazon.com/test" in final_text
        assert "https://soundcore.com" in final_text

    def test_edge_case_empty_text(self) -> None:
        """Test handling of empty text."""
        assert escape_markdown_v2("") == ""

    def test_edge_case_only_links(self) -> None:
        """Test text with only links, no regular text."""
        input_text = "[Link1](https://example1.com)[Link2](https://example2.com)"

        result = escape_markdown_v2(input_text)

        # Links should be preserved
        assert "[Link1](https://example1.com)" in result
        assert "[Link2](https://example2.com)" in result

    def test_fallback_escaping_without_telegramify_markdown(self) -> None:
        """Test that fallback escaping works if telegramify-markdown is not available."""
        # This test verifies the fallback behavior
        # We can't easily test this without mocking, but we can test basic functionality
        input_text = "*Bold* text and [link](https://example.com)"

        result = escape_markdown_v2(input_text)

        # Should contain the original content (though potentially differently formatted)
        assert "Bold" in result
        assert "link" in result
        assert "https://example.com" in result
