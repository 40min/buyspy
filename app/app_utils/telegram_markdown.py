"""Utility module for Telegram MarkdownV2 formatting and escaping.

This module provides functions for properly escaping text according to Telegram's
MarkdownV2 format, with special handling for markdown links to ensure correct
escaping rules are applied to different parts of the markup.

The telegramify_markdown library is used for proper Telegram MarkdownV2 escaping
but we apply additional post-processing to fix period escaping in URLs.
"""

import re
from urllib.parse import urlparse

import telegramify_markdown


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2 format using telegramify_markdown.

    This function uses the telegramify_markdown library's standardize function to properly
    escape text according to Telegram's MarkdownV2 format rules, then applies post-processing
    to fix periods in URLs which should not be escaped.

    This fixes the issue with period (.) escaping in URLs that was causing Telegram API errors
    like "character '.' is reserved and must be escaped with the preceding '\'".

    Args:
        text: Text to escape

    Returns:
        Text with MarkdownV2 special characters escaped, preserving correct link syntax
    """
    if not text:
        return text

    # Use telegramify_markdown for proper escaping
    escaped_text = telegramify_markdown.standardize(text)

    # Post-process to fix periods in URLs (they should not be escaped)
    escaped_text = _fix_periods_in_urls(escaped_text)

    return escaped_text


def _fix_periods_in_urls(text: str) -> str:
    """Fix escaped periods in URLs while preserving other escaping.

    URLs should have periods (.) preserved, but other special characters
    should remain escaped.

    Args:
        text: Text that may have escaped periods in URLs

    Returns:
        Text with periods in URLs unescaped
    """
    # Find all markdown links and fix periods in URLs
    result = ""
    current_pos = 0

    for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
        # Add any regular text before this link (with current escaping)
        if match.start() > current_pos:
            result += text[current_pos : match.start()]

        # Add the link with fixed URL escaping
        link_text = match.group(1)
        link_url = match.group(2)

        # Fix escaped periods in URL only
        fixed_url = link_url.replace(r"\.", ".")

        # Keep other escaping intact
        result += f"[{link_text}]({fixed_url})"

        current_pos = match.end()

    # Add any remaining regular text (after the last link)
    if current_pos < len(text):
        result += text[current_pos:]

    return result


def convert_urls_to_links(text: str) -> str:
    """Convert raw URLs to Markdown links with store names.

    Converts:
        https://verkkokauppa.com/fi/product/123
    To:
        [Verkkokauppa](https://verkkokauppa.com/fi/product/123)

    Only converts URLs if there are no existing markdown links in the text.

    Args:
        text: Text containing raw URLs

    Returns:
        Text with URLs converted to Markdown links
    """
    # Check if there are any existing markdown links
    existing_link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    if re.search(existing_link_pattern, text):
        # There are already links, don't modify anything
        return text

    # URL pattern that matches raw URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'

    def replace_url(match: re.Match) -> str:
        """Convert a matched URL to a Markdown link with the store name.

        Extracts the domain from the URL, capitalizes the store name,
        and returns a Markdown-formatted link.

        Args:
            match: Regex match object containing the URL

        Returns:
            Markdown-formatted link string in format [StoreName](URL)
        """
        url = match.group(0)

        # Extract store name from domain
        domain = urlparse(url).netloc.replace("www.", "")
        store_name = domain.split(".")[0].capitalize()
        return f"[{store_name}]({url})"

    return re.sub(url_pattern, replace_url, text)
