from unittest.mock import patch

import requests

from universal_timeout_parser import UniversalTimeOutParser


def test_parse_article_timeout_returns_empty_list():
    parser = UniversalTimeOutParser()
    with patch.object(parser.session, 'get', side_effect=requests.Timeout):
        result = parser.parse_article('https://example.com/article')
        assert result == []
