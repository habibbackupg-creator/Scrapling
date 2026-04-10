from unittest.mock import patch, MagicMock

from scrapling.core.webui import _extract_from_form, _render_page


class TestWebUI:
    """Tests for built-in web UI helpers"""

    def test_extract_from_form_success(self):
        """Form extraction should return success with normalized options"""
        fake_response = MagicMock()
        fake_response.status = 200

        with patch('scrapling.core.webui.Fetcher.get', return_value=fake_response) as mock_get:
            with patch('scrapling.core.webui._convert_response', return_value='Example Domain') as mock_convert:
                result, state = _extract_from_form(
                    b'url=https%3A%2F%2Fexample.com&fmt=txt&css_selector=h1&ai_targeted=on'
                )

        assert result.ok is True
        assert result.status == 200
        assert result.output == 'Example Domain'
        assert state.url == 'https://example.com'
        assert state.css_selector == 'h1'
        assert state.fmt == 'txt'
        assert state.ai_targeted is True
        assert state.timeout == 30
        assert state.impersonate == 'chrome'
        assert state.follow_redirects is False
        assert state.verify is False
        assert state.stealthy_headers is False
        mock_get.assert_called_once_with(
            'https://example.com',
            headers=None,
            cookies=None,
            params=None,
            timeout=30,
            proxy=None,
            follow_redirects=False,
            verify=False,
            impersonate='chrome',
            stealthy_headers=False,
        )
        mock_convert.assert_called_once_with(fake_response, 'h1', 'txt', True)

    def test_extract_from_form_missing_url(self):
        """Missing URL should return a user-facing validation error"""
        result, state = _extract_from_form(b'fmt=html')

        assert result.ok is False
        assert 'URL is required' in result.message
        assert state.url == ''
        assert state.css_selector == ''
        assert state.fmt == 'html'
        assert state.ai_targeted is False

    def test_render_page_contains_ui_header(self):
        """Render page should include top-level UI title"""
        page = _render_page().decode('utf-8')
        assert 'Scrapling Built-in Interface' in page
        assert 'Fetch & Extract' in page
