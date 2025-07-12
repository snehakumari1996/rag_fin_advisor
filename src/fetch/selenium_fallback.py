"""
Colab-optimized Selenium crawler
"""
import os
import time
import logging
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class SeleniumCrawler:
    """Selenium crawler optimized for Google Colab"""
    
    def __init__(self):
        self.driver = None
        
    def _get_chrome_options(self) -> webdriver.ChromeOptions:
        """Configure Chrome options for Colab"""
        options = webdriver.ChromeOptions()
        
        # Essential options for Colab
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # Additional stability options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Set Chrome binary location for Colab
        options.binary_location = '/usr/bin/chromium-browser'
        
        return options
    
    def _init_driver(self):
        """Initialize Chrome driver for Colab"""
        if self.driver:
            return
            
        try:
            self.driver = webdriver.Chrome(
                executable_path='/usr/lib/chromium-browser/chromedriver',
                options=self._get_chrome_options()
            )
            logger.info("Chrome driver initialized successfully in Colab")
        except Exception as e:
            logger.error(f"Chrome initialization failed: {e}")
            raise
    
    def get_pdf_links(self, url: str, wait_time: int = 10) -> List[str]:
        """Extract PDF links from a webpage"""
        pdf_links = []
        
        try:
            self._init_driver()
            self.driver.get(url)
            
            # Wait for page load
            try:
                WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located((By.TAG_NAME, "a"))
                )
            except TimeoutException:
                logger.warning(f"Timeout waiting for page load: {url}")
            
            time.sleep(3)  # Additional wait for JS
            
            # Extract PDF links
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '.pdf' in href.lower():
                    if not href.startswith('http'):
                        from urllib.parse import urljoin
                        href = urljoin(url, href)
                    pdf_links.append(href)
            
            pdf_links = list(set(pdf_links))
            logger.info(f"Found {len(pdf_links)} PDF links on {url}")
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
        
        return pdf_links
    
    def close(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()
