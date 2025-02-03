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
import os
from datetime import datetime

class NBNProviderScraper:
    # Hardcode url
    #  def __init__(self, url: str = "https://www.nbnco.com.au/residential/service-providers"):
    #     self.url = url
    def __init__(self, url_file: str = "NBN_RSP_URL.txt"):
        # Read URL from file
        try:
            with open(url_file, 'r') as f:
                self.url = f.read().strip()
        except IOError as e:
            raise IOError(f"Failed to read URL from file {url_file}: {e}")
            
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
        # Create Logs directory if it doesn't exist
        log_dir = os.path.join(os.getcwd(), 'Logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Add datetime stamp to log filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f'ExtractNBNProviderstoJSON_{timestamp}.log'
        log_file = os.path.join(log_dir, log_filename)
        
        # Check and manage log files
        log_files = [f for f in os.listdir(log_dir) 
                    if f.startswith('ExtractNBNProviderstoJSON_') and f.endswith('.log')]
        
        if len(log_files) >= 5:
            # Sort files by creation time and remove the oldest
            log_files.sort(key=lambda x: os.path.getctime(os.path.join(log_dir, x)))
            oldest_file = os.path.join(log_dir, log_files[0])
            try:
                os.remove(oldest_file)
                print(f"\n \n Removed oldest log file: {oldest_file}")
            except OSError as e:
                print(f"\n \n Error removing old log file: {e}")
        
        # Setup logging with file output
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
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
            # Create OUTPUT and OUTPUTHistory directories if they don't exist
            output_dir = os.path.join(os.getcwd(), 'OUTPUT')
            os.makedirs(output_dir, exist_ok=True)
            history_dir = os.path.join(os.getcwd(), 'OUTPUT\OUTPUT_History')
            os.makedirs(history_dir, exist_ok=True)
            
            # Add datetime stamp to filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name, ext = os.path.splitext(filename)
            filename_with_timestamp = f"{base_name}_{timestamp}{ext}"
            full_path = os.path.join(output_dir, filename_with_timestamp)
            
            # Generate the new JSON content
            new_content = json.dumps(self.providers, indent=2, ensure_ascii=False)
            
            # Check for existing files in OUTPUT directory
            existing_files = [f for f in os.listdir(output_dir) if f.startswith(base_name) and f.endswith(ext)]
            if existing_files:
                latest_file = max(existing_files, key=lambda x: os.path.getctime(os.path.join(output_dir, x)))
                latest_file_path = os.path.join(output_dir, latest_file)
                
                # Compare content with latest file
                with open(latest_file_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                
                if existing_content == new_content:
                    self.logger.info("No changes detected in content. Skipping save operation.")
                    return
                
                # Move existing file to history
                history_path = os.path.join(history_dir, latest_file)
                os.rename(latest_file_path, history_path)
                self.logger.info(f"Moved previous file to history: {latest_file}")
                
                # Check and manage history files
                history_files = [f for f in os.listdir(history_dir) 
                               if f.startswith(base_name) and f.endswith(ext)]
                if len(history_files) > 5:
                    oldest_file = min(history_files, 
                                    key=lambda x: os.path.getctime(os.path.join(history_dir, x)))
                    os.remove(os.path.join(history_dir, oldest_file))
                    self.logger.info(f"Removed oldest history file: {oldest_file}")
            
            # Save new file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            self.logger.info(f"Successfully extracted {len(self.providers)} providers")
            self.logger.info(f"Successfully saved providers to {full_path}")
            
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
        print(f"Successfully found {len(providers)} providers")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
