# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from unittest.mock import Mock, patch

from app.tools.link_finder import find_shopping_links


def test_find_shopping_links_function_signature() -> None:
    """Test that find_shopping_links requires both product_name and region parameters."""
    # This should work with both parameters
    with patch("app.tools.link_finder.DDGS") as mock_ddgs:
        mock_instance = Mock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.return_value = [
            {"title": "Test", "href": "http://example.com", "body": "Test"}
        ]

        result = find_shopping_links("Sony WH-CH720N", "fi-fi")
        assert isinstance(result, str)

        # Verify it was called with the right parameters
        mock_instance.text.assert_called_once_with(
            "Sony WH-CH720N price", region="fi-fi", max_results=3
        )


def test_find_shopping_links_returns_json_string() -> None:
    """Test that find_shopping_links returns a valid JSON string."""
    with patch("app.tools.link_finder.DDGS") as mock_ddgs:
        mock_instance = Mock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.return_value = [
            {
                "title": "Sony WH-CH720N",
                "href": "http://example.com",
                "body": "Great headphones",
            }
        ]

        result = find_shopping_links("Sony WH-CH720N", "fi-fi")

        # Should be a valid JSON string
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert isinstance(parsed, list)


def test_find_shopping_links_returns_required_fields() -> None:
    """Test that results contain the required fields (title, href, body)."""
    with patch("app.tools.link_finder.DDGS") as mock_ddgs:
        mock_instance = Mock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.return_value = [
            {
                "title": "Sony WH-CH720N",
                "href": "http://example.com",
                "body": "Great headphones",
            }
        ]

        result = find_shopping_links("Sony WH-CH720N", "fi-fi")
        parsed = json.loads(result)

        assert len(parsed) == 1
        item = parsed[0]
        assert "title" in item
        assert "href" in item
        assert "body" in item


def test_find_shopping_links_error_handling() -> None:
    """Test that find_shopping_links handles errors gracefully."""
    with patch("app.tools.link_finder.DDGS") as mock_ddgs:
        mock_instance = Mock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.side_effect = Exception("Network error")

        result = find_shopping_links("Sony WH-CH720N", "fi-fi")

        assert "Error searching for links" in result
        assert "Network error" in result


def test_find_shopping_links_query_construction() -> None:
    """Test that the query is constructed correctly as 'product_name price'."""
    with patch("app.tools.link_finder.DDGS") as mock_ddgs:
        mock_instance = Mock()
        mock_ddgs.return_value = mock_instance
        mock_instance.text.return_value = []

        find_shopping_links("Sony WH-CH720N", "fi-fi")

        # Verify the query was constructed correctly
        call_args = mock_instance.text.call_args
        assert call_args[0][0] == "Sony WH-CH720N price"
