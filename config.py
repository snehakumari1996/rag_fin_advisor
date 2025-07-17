"""
Configuration file for Financial RAG System
Handles all paths, settings, and environment variables
"""

import os
import logging
from pathlib import Path
from datetime import datetime

# Base directory - works both in Colab and local
if os.path.exists("/content/drive/MyDrive"):
    # Running in Colab
    ROOT = Path("/content/drive/MyDrive/RAG_fin_iter1")
else:
    # Running locally
    ROOT = Path(__file__).parent.parent

# Create directories if they don't exist
ROOT.mkdir(parents=True, exist_ok=True)

# Directory paths
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
INDEX_DIR = DATA_DIR / "faiss_index"
CACHE_DIR = DATA_DIR / "cache"
LOGS_DIR = ROOT / "logs"
CONFIG_DIR = ROOT / "config"

# Create all directories
for dir_path in [RAW_DIR, PROCESSED_DIR, INDEX_DIR, CACHE_DIR, LOGS_DIR, CONFIG_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Load API key
API_KEY_FILE = CONFIG_DIR / "api_key.txt"
if API_KEY_FILE.exists():
    OPENAI_API_KEY = API_KEY_FILE.read_text().strip()
else:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Model settings
MODEL_CONFIG = {
    "llm_model": "gpt-3.5-turbo",  # or "gpt-4" for better quality
    "temperature": 0.1,
    "max_tokens": 1000,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",  # Fast and efficient
    # "embedding_model": "BAAI/bge-large-en-v1.5",  # Better quality but slower
}

# Document processing settings
CHUNK_CONFIG = {
    "chunk_size": 800,
    "chunk_overlap": 100,
    "separators": ["\n\n", "\n", ". ", " ", ""]
}

# Retrieval settings
RETRIEVAL_CONFIG = {
    "k": 3,  # Number of documents to retrieve
    "search_type": "similarity",  # or "mmr" for diversity
    "fetch_k": 10,  # For MMR
}

# Compliance patterns
COMPLIANCE_PATTERNS = {
    "illegal": [
        (r"insider\s+trading", "🚫 ILLEGAL: Insider trading violates SEBI (Prohibition of Insider Trading) Regulations 2015. Penalty up to ₹25 crores or 3x profit."),
        (r"front[\s-]?running", "🚫 ILLEGAL: Front-running is market manipulation under SEBI Act. Can lead to license cancellation."),
        (r"pump\s+and\s+dump", "🚫 ILLEGAL: Market manipulation schemes are strictly prohibited under SEBI Act."),
        (r"ponzi|pyramid\s+scheme|mlm\s+investment", "🚫 ILLEGAL: Such schemes are banned by SEBI. Report to authorities immediately."),
        (r"circular\s+trading", "🚫 ILLEGAL: Circular trading is market manipulation and prohibited."),
        (r"wash\s+trading", "🚫 ILLEGAL: Wash trading creates false market activity and is prohibited."),
    ],
    "high_risk": [
        (r"margin\s+trading|leverage", "⚠️ HIGH RISK: Margin trading can lead to losses exceeding your investment."),
        (r"F&O|futures|options|derivatives", "⚠️ HIGH RISK: Derivatives can cause unlimited losses. Requires experience and income proof."),
        (r"penny\s+stocks|small[\s-]?cap", "⚠️ HIGH RISK: Highly volatile and often manipulated. Research thoroughly."),
        (r"intraday|day\s+trading", "⚠️ HIGH RISK: 90% of day traders lose money. Requires experience and discipline."),
    ],
    "compliance": [
        (r"demat\s+account|trading\s+account", "ℹ️ Ensure your broker is SEBI registered. Check at www.sebi.gov.in"),
        (r"IPO|initial\s+public\s+offering", "ℹ️ Read the Red Herring Prospectus carefully. Check SEBI SCORES for complaints."),
        (r"tips|recommendations|advisory", "ℹ️ Only take advice from SEBI-registered investment advisors."),
        (r"PAN|KYC", "ℹ️ PAN and KYC are mandatory for all market transactions."),
    ]
}

# Logging configuration
LOG_FILE = LOGS_DIR / f"rag_system_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Document sources
DOCUMENT_SOURCES = {
    "sebi": {
        "base_url": "https://www.sebi.gov.in",
        "types": ["regulations", "circulars", "guidelines"],
    },
    "rbi": {
        "base_url": "https://www.rbi.org.in",
        "types": ["notifications", "master_directions", "faqs"],
    },
    "nse": {
        "base_url": "https://www.nseindia.com",
        "types": ["circulars", "rules"],
    },
    "bse": {
        "base_url": "https://www.bseindia.com",
        "types": ["notices", "circulars"],
    }
}

# Cache settings
CACHE_CONFIG = {
    "query_cache_file": CACHE_DIR / "query_cache.json",
    "document_cache_file": CACHE_DIR / "document_cache.json",
    "cache_ttl_days": 7,  # Cache time-to-live
}

def get_config():
    """Return all configuration as a dictionary"""
    return {
        "paths": {
            "root": str(ROOT),
            "data": str(DATA_DIR),
            "raw": str(RAW_DIR),
            "processed": str(PROCESSED_DIR),
            "index": str(INDEX_DIR),
            "cache": str(CACHE_DIR),
            "logs": str(LOGS_DIR),
            "config": str(CONFIG_DIR),
        },
        "models": MODEL_CONFIG,
        "chunks": CHUNK_CONFIG,
        "retrieval": RETRIEVAL_CONFIG,
        "compliance": COMPLIANCE_PATTERNS,
        "sources": DOCUMENT_SOURCES,
        "cache": CACHE_CONFIG,
        "api_key_set": bool(OPENAI_API_KEY),
    }

# Verify setup
if not OPENAI_API_KEY:
    logger.warning("OpenAI API key not found. Set it in config/api_key.txt or OPENAI_API_KEY environment variable")
else:
    logger.info("Configuration loaded successfully")
    
# Export key variables
__all__ = [
    'ROOT', 'DATA_DIR', 'RAW_DIR', 'PROCESSED_DIR', 'INDEX_DIR', 
    'CACHE_DIR', 'LOGS_DIR', 'CONFIG_DIR', 'OPENAI_API_KEY',
    'MODEL_CONFIG', 'CHUNK_CONFIG', 'RETRIEVAL_CONFIG', 
    'COMPLIANCE_PATTERNS', 'logger', 'get_config'
]