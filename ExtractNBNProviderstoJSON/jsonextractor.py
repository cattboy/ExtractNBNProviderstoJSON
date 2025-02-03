from bs4 import BeautifulSoup
import json
from typing import List, Dict
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time

class NBNProviderScraper:
    def __init__(self, url: str = "https://www.nbnco.com.au/residential/service-providers"):
        self.url = url
        self.providers: List[Dict[str, str]] = []
        self.setup_logging()
        self.setup_selenium()

    def setup_selenium(self) -> None:
        """Configure Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Selenium WebDriver: {e}")
            raise

    def setup_logging(self) -> None:
        """Configure logging for the scraper"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def fetch_webpage(self) -> str:
        """Fetch the webpage content using Selenium"""
        try:
            self.logger.info(f"Navigating to {self.url}")
            self.driver.get(self.url)

            # Wait for the provider list to be loaded
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "rsplist-item")))
            
            # Add a small delay to ensure all content is loaded
            time.sleep(2)
            
            # Get the page source after JavaScript execution
            page_source = self.driver.page_source
            
            # Save the rendered HTML for debugging
            # DEBUGGING ONLY SAVE TO FILE
            # with open('output.html', 'w', encoding='utf-8') as file:
            #     file.write(page_source)
                
            return page_source
            
        except TimeoutException:
            self.logger.error("Timeout waiting for provider list to load")
            raise
        except Exception as e:
            self.logger.error(f"Failed to fetch webpage: {e}")
            raise
        finally:
            self.driver.quit()

    def parse_providers(self, html_content: str) -> None:
        """Parse the HTML content to extract provider information"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all provider elements
        provider_elements = soup.find_all('div', class_='rsplist-item')
        
        if not provider_elements:
            self.logger.warning("No provider elements found")
            return

        for element in provider_elements:
            provider = {}
            try:
                # Extract name
                name_elem = element.find('div', class_='name')
                if name_elem:
                    provider['name'] = name_elem.text.strip()

                # Extract phone
                phone_elem = element.find('span', class_='rsplist-phone')
                if phone_elem:
                    provider['phone'] = phone_elem.text.strip()

                # Extract website
                # website_elem = element.find('a', class_='website-info')
                website_elem = element.find('a')
                if website_elem and website_elem.get('href'):
                    provider['website'] = website_elem['href'].strip()

                if all(provider.values()):  # Only add if all fields have values
                    self.providers.append(provider)
                    self.logger.info(f"Found provider: {provider['name']}")
            except AttributeError as e:
                self.logger.error(f"Error processing provider element: {e}")
                continue

    def save_to_json(self, filename: str = 'nbn_providers.json') -> None:
        """Save the extracted data to a JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.providers, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Successfully saved providers to {filename}")
        except IOError as e:
            self.logger.error(f"Failed to save JSON file: {e}")
            raise

    def run(self) -> List[Dict[str, str]]:
        """Execute the complete scraping process"""
        try:
            html_content = self.fetch_webpage()
            self.parse_providers(html_content)
            self.save_to_json()
            return self.providers
        except Exception as e:
            self.logger.error(f"Scraping process failed: {e}")
            raise

def main():
    scraper = NBNProviderScraper()
    try:
        providers = scraper.run()
        print(f"Successfully extracted {len(providers)} providers")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
