import os
import hashlib
import pathlib
import requests
import time
from typing import Optional
from urllib.parse import urlparse, unquote
from fake_useragent import UserAgent
import logging

logger = logging.getLogger(__name__)

class RobustDownloader:
    """Downloader optimized for Colab environment"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create a session with retry logic"""
        session = requests.Session()
        
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def generate_filename(self, url: str, source: str) -> str:
        """Generate a meaningful filename from URL"""
        parsed = urlparse(url)
        filename = os.path.basename(unquote(parsed.path))
        
        if not filename or '.' not in filename:
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"{source}_{url_hash}.pdf"
        
        # Sanitize filename
        filename = "".join(c for c in filename if c.isalnum() or c in '._-')
        return filename
    
    def download(self, url: str, dest_path: pathlib.Path, 
                 chunk_size: int = 8192, timeout: int = 60) -> bool:
        """Download file with progress tracking"""
        try:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'application/pdf,*/*',
            }
            
            response = self.session.get(
                url, 
                headers=headers, 
                stream=True, 
                timeout=timeout,
                verify=False
            )
            response.raise_for_status()
            
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
            
            if dest_path.stat().st_size < 1000:
                logger.warning(f"Downloaded file too small: {dest_path}")
                dest_path.unlink()
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Download failed for {url}: {e}")
            return False
