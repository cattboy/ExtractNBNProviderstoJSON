import pytest
from jsonextractor import NBNProviderScraper
from selenium.common.exceptions import TimeoutException
import json
from unittest.mock import MagicMock, patch

@pytest.fixture
def scraper():
    return NBNProviderScraper()

def test_scraper_initialization(scraper):
    assert isinstance(scraper, NBNProviderScraper)
    assert scraper.url == "https://www.nbnco.com.au/residential/service-providers"
    assert isinstance(scraper.providers, list)

@patch('selenium.webdriver.Chrome')
def test_fetch_webpage(mock_chrome, scraper):
    # Mock the Chrome driver
    mock_driver = MagicMock()
    mock_driver.page_source = "<html><body>Test content</body></html>"
    mock_chrome.return_value = mock_driver
    
    content = scraper.fetch_webpage()
    assert isinstance(content, str)
    assert len(content) > 0

def test_parse_providers(scraper):
    # Test with a sample HTML content
    sample_html = """
    <html>
    <body>
        <div class="rsplist-item">
            <div class="name">Test Provider</div>
            <span class="rsplist-phone">1234567890</span>
            <a class="website-info" href="https://www.testprovider.com">Website</a>
        </div>
        <div class="rsplist-item">
            <div class="name">Another Provider</div>
            <span class="rsplist-phone">0987654321</span>
            <a class="website-info" href="https://www.anotherprovider.com">Website</a>
        </div>
    </body>
    </html>
    """
    scraper.parse_providers(sample_html)
    assert len(scraper.providers) == 2
    
    # Test first provider
    provider1 = scraper.providers[0]
    assert provider1['name'] == "Test Provider"
    assert provider1['phone'] == "1234567890"
    assert provider1['website'] == "https://www.testprovider.com"
    
    # Test second provider
    provider2 = scraper.providers[1]
    assert provider2['name'] == "Another Provider"
    assert provider2['phone'] == "0987654321"
    assert provider2['website'] == "https://www.anotherprovider.com"

def test_parse_providers_no_elements(scraper):
    sample_html = "<html><body>No provider elements</body></html>"
    scraper.parse_providers(sample_html)
    assert len(scraper.providers) == 0

def test_parse_providers_invalid_script(scraper):
    # Test with invalid script content
    sample_html = """
    <script>
        window.rspListJson = invalid_json_here;
    </script>
    """
    scraper.parse_providers(sample_html)
    assert len(scraper.providers) == 0

def test_parse_providers_no_script(scraper):
    # Test with no script tag
    sample_html = "<html><body>No script here</body></html>"
    scraper.parse_providers(sample_html)
    assert len(scraper.providers) == 0

def test_save_to_json(scraper, tmp_path):
    # Create test data
    test_data = [{"name": "Test Provider", "phone": "1234567890", "website": "https://test.com"}]
    scraper.providers = test_data
    
    # Use temporary directory for test
    test_file = tmp_path / "test_providers.json"
    scraper.save_to_json(str(test_file))
    
    # Verify file exists and content is correct
    assert test_file.exists()
    with open(test_file, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)
    assert saved_data == test_data

def test_run_integration(scraper):
    try:
        providers = scraper.run()
        assert isinstance(providers, list)
        if providers:
            provider = providers[0]
            assert isinstance(provider, dict)
            assert any(key in provider for key in ['name', 'phone', 'website'])
    except requests.RequestException:
        pytest.skip("Network request failed - skipping integration test")

def test_error_handling(scraper):
    with pytest.raises(requests.RequestException):
        scraper.url = "https://nonexistent-url.com"
        scraper.fetch_webpage() 