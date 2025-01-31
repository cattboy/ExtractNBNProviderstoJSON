import tkinter as tk
from tkinter import ttk
import pandas as pd
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re

class InternetPlanScraper:
    def __init__(self):
        self.providers = {
            'Telstra': 'https://www.telstra.com.au/internet/plans',
            'Optus': 'https://www.optus.com.au/broadband-nbn/home-broadband/plans',
            'TPG': 'https://www.tpg.com.au/nbn',
        }
        self.plans_data = []

    def setup_driver(self):
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        return driver
        # chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Run in headless mode
        # service = Service('path/to/chromedriver')  # Update with your chromedriver path
        # return webdriver.Chrome(service=service, options=chrome_options)

    def extract_telstra_plans(self, driver):
        driver.get(self.providers['Telstra'])
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'plan-card'))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        plans = soup.find_all('div', class_='plan-card')
        
        for plan in plans:
            speed = re.search(r'(\d+)Mbps', plan.text)
            price = re.search(r'\$(\d+)', plan.text)
            if speed and price:
                self.plans_data.append({
                    'Provider': 'Telstra',
                    'Speed': int(speed.group(1)),
                    'Price': float(price.group(1)),
                })

    def scrape_all_providers(self):
        driver = self.setup_driver()
        try:
            self.extract_telstra_plans(driver)
            # Add similar methods for other providers
        finally:
            driver.quit()
        return pd.DataFrame(self.plans_data)

class InternetPlanGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Australian Internet Plans Comparison")
        self.root.geometry("800x600")
        
        # Search frame
        search_frame = ttk.Frame(root)
        search_frame.pack(pady=10, padx=10, fill='x')
        
        ttk.Label(search_frame, text="Search:").pack(side='left')
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_table)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side='left', padx=5)
        
        # Table
        self.tree = ttk.Treeview(root, columns=('Provider', 'Speed', 'Price'), show='headings')
        self.tree.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Configure columns
        self.tree.heading('Provider', text='Provider', command=lambda: self.sort_column('Provider'))
        self.tree.heading('Speed', text='Speed (Mbps)', command=lambda: self.sort_column('Speed'))
        self.tree.heading('Price', text='Price ($)', command=lambda: self.sort_column('Price'))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(root, orient='vertical', command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Load data
        self.load_data()

    def load_data(self):
        scraper = InternetPlanScraper()
        self.df = scraper.scrape_all_providers()
        self.update_table()

    def update_table(self, df=None):
        if df is None:
            df = self.df
        
        self.tree.delete(*self.tree.get_children())
        for _, row in df.iterrows():
            self.tree.insert('', 'end', values=(row['Provider'], row['Speed'], f"${row['Price']:.2f}"))

    def filter_table(self, *args):
        search_term = self.search_var.get().lower()
        filtered_df = self.df[
            self.df['Provider'].str.lower().str.contains(search_term) |
            self.df['Speed'].astype(str).str.contains(search_term) |
            self.df['Price'].astype(str).str.contains(search_term)
        ]
        self.update_table(filtered_df)

    def sort_column(self, column):
        self.df = self.df.sort_values(by=[column])
        self.update_table()

def main():
    root = tk.Tk()
    app = InternetPlanGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()