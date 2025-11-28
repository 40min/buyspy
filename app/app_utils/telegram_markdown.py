"""Utility module for Telegram MarkdownV2 formatting and escaping.

This module provides functions for properly escaping text according to Telegram's
MarkdownV2 format, with special handling for markdown links to ensure correct
escaping rules are applied to different parts of the markup.
"""

import re
from urllib.parse import urlparse


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2 format while preserving existing links.

    This function properly handles Telegram's MarkdownV2 escaping rules:
    - Inside link text [text]: Only escape ] and \
    - Inside link URL (url): Only escape ) and \
    - Outside links: Escape all special characters: _*[]()~`>#+-=|{}.!

    Args:
        text: Text to escape

    Returns:
        Text with MarkdownV2 special characters escaped, preserving link syntax
    """
    if not text:
        return text

    # Parse the text into segments (link text, link URLs, regular text)
    segments = _parse_markdown_segments(text)

    # Apply appropriate escaping to each segment
    escaped_segments = []
    for segment_type, content in segments:
        if segment_type == "link_text":
            escaped_segments.append(_escape_link_text(content))
        elif segment_type == "link_url":
            escaped_segments.append(_escape_link_url(content))
        else:  # regular text
            escaped_segments.append(_escape_regular_text(content))

    # Reconstruct the text
    result = ""

    # Parse again to rebuild the text with correct escaping
    current_pos = 0
    for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
        # Add any regular text before this link
        if match.start() > current_pos:
            regular_text = text[current_pos : match.start()]
            result += _escape_regular_text(regular_text)

        # Add the link with properly escaped parts
        link_text = match.group(1)
        link_url = match.group(2)
        result += f"[{_escape_link_text(link_text)}]({_escape_link_url(link_url)})"

        current_pos = match.end()

    # Add any remaining regular text
    if current_pos < len(text):
        result += _escape_regular_text(text[current_pos:])

    return result


def _parse_markdown_segments(text: str) -> list[tuple[str, str]]:
    """Parse text into segments: (type, content).

    Args:
        text: Text to parse

    Returns:
        List of tuples (segment_type, content) where segment_type is:
        - 'link_text': Content inside [link text]
        - 'link_url': Content inside (link url)
        - 'regular': Regular text
    """
    segments = []

    # Find all markdown links
    for match in re.finditer(r"\[([^\[]*?)\]\(([^)]+)\)", text):
        link_text = match.group(1)
        link_url = match.group(2)

        segments.append(("link_text", link_text))
        segments.append(("link_url", link_url))

    return segments


def _escape_link_text(text: str) -> str:
    r"""Escape special characters for link text in MarkdownV2.

    In link text [text], only ] and \ need to be escaped.

    Args:
        text: Text to escape

    Returns:
        Escaped text suitable for link text
    """
    return text.replace("\\", "\\\\").replace("]", "\\]")


def _escape_link_url(text: str) -> str:
    r"""Escape special characters for link URL in MarkdownV2.

    In link URL (url), only ) and \ need to be escaped.

    Args:
        text: URL to escape

    Returns:
        Escaped URL suitable for link URL
    """
    return (
        text.replace("\\", "\\\\")
        .replace(")", "\\)")
        .replace("?", "\\?")
        .replace("=", "\\=")
        .replace("&", "\\&")
    )


def _escape_regular_text(text: str) -> str:
    """Escape special characters for regular text in MarkdownV2.

    In regular text, these characters need escaping:
    _*[]()~`>#+-=|{}.!

    Args:
        text: Text to escape

    Returns:
        Escaped text suitable for regular markdown text
    """
    special_chars = [
        "_",
        "*",
        "[",
        "]",
        "(",
        ")",
        "~",
        "`",
        ">",
        "#",
        "+",
        "-",
        "=",
        "|",
        "{",
        "}",
        ".",
        "!",
        "$",
    ]

    for char in special_chars:
        text = text.replace(char, f"\\{char}")

    return text


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
