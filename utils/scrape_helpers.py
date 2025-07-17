# utils/scrape_helpers.py
import os
import time
import hashlib
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
from tqdm import tqdm

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36"
}

# Download tracking
def sha1_of_url(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:10]

def already_downloaded(dest: Path, url: str) -> bool:
    token = sha1_of_url(url)
    marker = dest / f"{token}__.marker"
    return marker.exists()

def mark_downloaded(dest: Path, url: str):
    token = sha1_of_url(url)
    marker = dest / f"{token}__.marker"
    marker.write_text(url)

# PDF downloader with optional Selenium fallback
def fetch_pdfs(base_url, selector, dest, use_selenium=False):
    dest.mkdir(parents=True, exist_ok=True)
    links = []
    try:
        r = requests.get(base_url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        links = [urljoin(base_url, a['href']) for a in soup.select(selector) if a.get("href", "").endswith(".pdf")]
    except Exception as e:
        logging.warning(f"[WARN] Fallback to Selenium for {base_url}: {e}")
        if use_selenium:
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                options = Options()
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                driver = webdriver.Chrome(options=options)
                driver.get(base_url)
                time.sleep(4)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                links = [urljoin(base_url, a.get("href")) for a in soup.select("a") if a.get("href", "").endswith(".pdf")]
                driver.quit()
            except Exception as e2:
                logging.error(f"[ERROR] Failed with Selenium too: {e2}")
                return

    for url in tqdm(links, desc=f"{dest.name} links"):
        try:
            if already_downloaded(dest, url):
                logging.info(f"[SKIP] Already downloaded: {url}")
                continue
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            filename = url.split("/")[-1].split("?")[0]
            (dest / filename).write_bytes(r.content)
            mark_downloaded(dest, url)
            logging.info(f"[+] Saved: {filename}")
        except Exception as e:
            logging.warning(f"[ERROR] failed to download {url}: {e}")

# Top-level orchestrator
def scrape_all_sources(root):
    SOURCES = [
        ("sebi", "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListingAll=yes&sid=1&smid=6", "a[href$='.pdf']", True),
        ("rbi", "https://rbi.org.in/Scripts/NotificationUser.aspx", "a[href*='.pdf']", False),
        ("bse", "https://www.bseindia.com/legal/list.aspx", "a[href$='.pdf']", True),
        ("nse", "https://www.nseindia.com/market-data/regulations", "a[href$='.pdf']", True),
        ("legislative", "https://www.indiacode.nic.in/handle/123456789/1362?view_type=browse", "a[href$='.pdf']", False),
        ("mca", "https://www.mca.gov.in/MinistryV2/acts+and+rules.html", "a[href$='.pdf']", True),
        ("irdai", "https://irdai.gov.in/document-detail", "a[href$='.pdf']", False),
        ("pfrda", "https://www.pfrda.org.in/WriteReadData/Links/Regulations.html", "a[href$='.pdf']", False),
        ("dpiit", "https://dpiit.gov.in/whats-new", "a[href$='.pdf']", True)
    ]
    for name, base_url, selector, use_selenium in SOURCES:
        logging.info(f"\n🔍 Scraping {name.upper()} :: {base_url}")
        fetch_pdfs(base_url, selector, root / name, use_selenium)
