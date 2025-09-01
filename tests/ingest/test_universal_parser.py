from unittest.mock import patch

import pytest
import requests

from universal_parser import UniversalPlaceParser

pytest.importorskip("requests")
pytest.importorskip("bs4")


class MockResponse:
    def __init__(self, html: str):
        self.content = html.encode("utf-8")

    def raise_for_status(self):
        pass


@pytest.mark.parametrize(
    "html,expected_source",
    [
        ("<div class='card'><h2>Cafe One</h2><p>Nice</p><img src='img.jpg'></div>", "card"),
        ("<h2>Blue Restaurant</h2><p>Great food</p>", "heading"),
        ("<ul><li><a href='/place'>List Place</a><img src='img.jpg'>Desc</li></ul>", "list_item"),
        ("<p>Bar Foo. Great drinks.</p>", "paragraph"),
        ("<a href='https://example.com/club'>Club Baz</a>", "link"),
    ],
)
def test_parse_article_strategies(html, expected_source):
    parser = UniversalPlaceParser()
    with patch.object(parser.session, "get", return_value=MockResponse(html)):
        places = parser.parse_article("https://example.com/article")
    assert len(places) == 1
    assert places[0]["source"] == expected_source
    assert places[0]["title"]


def test_parse_article_http_error_returns_empty_list():
    parser = UniversalPlaceParser()
    with patch.object(parser.session, "get", side_effect=requests.HTTPError):
        places = parser.parse_article("https://example.com/article")
    assert places == []


def test_parse_article_timeout_returns_empty_list():
    parser = UniversalPlaceParser()
    with patch.object(parser.session, "get", side_effect=requests.Timeout):
        places = parser.parse_article("https://example.com/article")
    assert places == []
