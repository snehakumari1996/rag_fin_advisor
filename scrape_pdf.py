# scrape_and_process.py
"""
End-to-end script to scrape, deduplicate, and process legal PDFs and text
from SEBI, RBI, BSE, NSE, IndiaCode, MCA, IRDAI, PFRDA, DPIIT, etc.
"""
import os
import sys
import time
import logging
import subprocess
from pathlib import Path
from utils.scrape_helpers import scrape_all_sources

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
ROOT = Path(__file__).parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

# Entry point
def main():
    logging.info("Starting scraping of regulatory/legal sources...")
    scrape_all_sources(RAW)

    logging.info("\n✅ Download complete. Now invoking data_processor...\n")
    subprocess.run([sys.executable, str(ROOT / "data_processor.py")], check=True)

if __name__ == "__main__":
    main()
