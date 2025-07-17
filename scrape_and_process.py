# scrape_and_process.py

import os
import re
import time
import logging
import requests
import urllib.robotparser
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm
from typing import List

from langchain_community.document_loaders import PyPDFLoader

# Optional Selenium fallback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

RAW_DIR = "/content/drive/MyDrive/RAG_fin_iter1/data/raw"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


headers = {"User-Agent": USER_AGENT}

# ───────────────────────────────────────────────────────────────
def save_pdf_from_url(url: str, save_dir: str) -> bool:
    filename = os.path.basename(url.split("?")[0])
    filepath = os.path.join(save_dir, filename)
    if os.path.exists(filepath):
        logging.info(f"[SKIP] Already downloaded: {url}")
        return False
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(r.content)
        logging.info(f"[+] Saved: {filename}")
        return True
    except Exception as e:
        logging.warning(f"[ERROR] failed to download {url}: {e}")
        return False


# ───────────────────────────────────────────────────────────────
def parse_links(base_url: str, pattern=r"\.pdf") -> List[str]:
    try:
        r = requests.get(base_url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        links = [urljoin(base_url, a['href']) for a in soup.find_all('a', href=True) if re.search(pattern, a['href'])]
        return links
    except Exception as e:
        logging.warning(f"[WARN] Fallback to Selenium for {base_url}: {e}")
        return selenium_fallback_links(base_url, pattern)


def selenium_fallback_links(base_url: str, pattern=r"\.pdf") -> List[str]:
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(base_url)
        time.sleep(5)
        links = []
        for a in driver.find_elements(By.TAG_NAME, "a"):
            href = a.get_attribute("href")
            if href and re.search(pattern, href):
                links.append(href)
        driver.quit()
        return links
    except Exception as e:
        logging.error(f"[ERROR] Selenium failed: {e}")
        return []


# ───────────────────────────────────────────────────────────────
def parse_sitemap(sitemap_url: str) -> List[str]:
    try:
        res = requests.get(sitemap_url, headers=headers, timeout=10)
        res.raise_for_status()
        xml = re.sub(r'&nbsp;', ' ', res.text)  # sanitize bad XML
        soup = BeautifulSoup(xml, 'xml')
        locs = [tag.text for tag in soup.find_all('loc') if tag.text.endswith('.pdf') or '/pdf/' in tag.text]
        return list(set(locs))
    except Exception as e:
        logging.warning(f"[WARN] Failed to parse sitemap {sitemap_url}: {e}")
        return []


# ───────────────────────────────────────────────────────────────
def crawl_and_download(base: str, link_list: List[str]):
    if not os.path.exists(base):
        os.makedirs(base)
    for link in tqdm(link_list, desc=f"{base} links"):
        save_pdf_from_url(link, base)


# ───────────────────────────────────────────────────────────────
def scrape_all():
    logging.info("Starting scraping of regulatory/legal sources...")

    sources = {
        "sebi": parse_sitemap("https://www.sebi.gov.in/sitemap.xml"),
        "rbi": parse_sitemap("https://www.rbi.org.in/sitemap.xml"),
        "mca": parse_sitemap("https://www.mca.gov.in/sitemap.xml"),
        "irdai": parse_sitemap("https://irdai.gov.in/sitemap.xml"),
        "pfrda": parse_sitemap("https://www.pfrda.org.in/sitemap.xml"),
        "dpiit": parse_sitemap("https://dpiit.gov.in/sitemap.xml")
    }

    for key, links in sources.items():
        logging.info(f"\n🔍 Scraping {key.upper()} :: {key}")
        crawl_and_download(os.path.join(RAW_DIR, key), links)


if __name__ == "__main__":
    scrape_all()
    os.system("python /content/drive/MyDrive/RAG_fin_iter1/data_processor.py")
