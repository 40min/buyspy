from app.app_utils.telegram_markdown import convert_urls_to_links, escape_markdown_v2


class TestMarkdownEscaping:
    """Test markdown escaping utility functions."""

    def test_escape_markdown_v2_basic(self) -> None:
        """Test basic link preservation while escaping other markdown."""
        input_text = "💰 *Pricing Results:*\n\n*Product:* Anker Soundcore Life Q20\n*Best Prices:*\n- *[41.99 USD](https://www.amazon.com/test)* at Amazon.com ✅ In Stock 🌟"

        result = escape_markdown_v2(input_text)

        # Check that links are preserved
        assert "[41.99 USD](https://www.amazon.com/test)" in result

        # Check that other markdown is escaped
        assert "\\*Pricing Results:\\*" in result
        assert "\\*Product:\\*" in result
        assert "\\*Best Prices:\\*" in result
        assert "\\- \\*" in result
        assert "✅" in result  # emojis should not be escaped

    def test_escape_markdown_v2_multiple(self) -> None:
        """Test multiple links preservation."""
        input_text = "Check [Amazon](https://amazon.com) and [eBay](https://ebay.com) for prices."

        result = escape_markdown_v2(input_text)

        # Check that both links are preserved
        assert "[Amazon](https://amazon.com)" in result
        assert "[eBay](https://ebay.com)" in result

        # Check that other text is properly escaped
        assert "Check" in result
        assert "and" in result
        assert "for prices" in result

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
        """Test the complete formatting flow: preserve links while escaping markdown."""
        # This simulates the actual flow that happens in handle_message
        # Real format from orchestrator: *price* at [Store](url) - no raw URLs
        input_text = "💰 *Pricing Results:*\n\n*Product:* Anker Soundcore Life Q20\n*Best Prices:*\n- *41.99 USD* at [Amazon.com](https://www.amazon.com/test)\n- *59.99 USD* at [Soundcore](https://soundcore.com)"

        # In real usage, the orchestrator should already generate proper links
        # So we just escape markdown while preserving existing links
        final_text = escape_markdown_v2(input_text)

        # Verify that the original links are preserved
        assert "[Amazon.com](https://www.amazon.com/test)" in final_text
        assert "[Soundcore](https://soundcore.com)" in final_text

        # Verify that other markdown is escaped
        assert "\\*Pricing Results:\\*" in final_text
        assert "\\*Product:\\*" in final_text
        assert "\\*Best Prices:\\*" in final_text
        assert "\\*41\\.99 USD\\*" in final_text  # Note: . is escaped to \.
        assert "\\*59\\.99 USD\\*" in final_text  # Note: . is escaped to \.

        # Verify that emojis are preserved
        assert "💰" in final_text
