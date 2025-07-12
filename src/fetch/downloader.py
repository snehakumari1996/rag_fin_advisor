import hashlib
import pathlib
import requests
import time
from typing import Optional
from urllib.parse import urlparse, unquote
from fake_useragent import UserAgent
from src.config import logger

class RobustDownloader:
    """Enhanced downloader with better error handling and filename generation"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create a session with retry logic"""
        session = requests.Session()
        
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=5,
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
        
        # Try to get filename from URL
        filename = os.path.basename(unquote(parsed.path))
        
        # If no filename or no extension, generate one
        if not filename or '.' not in filename:
            # Create filename from URL hash
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"{source}_{url_hash}.pdf"
        
        # Sanitize filename
        filename = "".join(c for c in filename if c.isalnum() or c in '._-')
        
        return filename
    
    def download(self, url: str, dest_path: pathlib.Path, 
                 chunk_size: int = 8192, timeout: int = 60) -> bool:
        """Download file with progress tracking and error handling"""
        try:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'application/pdf,*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Add referer based on domain
            domain = urlparse(url).netloc
            if 'sebi' in domain:
                headers['Referer'] = 'https://www.sebi.gov.in/'
            elif 'rbi' in domain:
                headers['Referer'] = 'https://www.rbi.org.in/'
            elif 'nse' in domain:
                headers['Referer'] = 'https://www.nseindia.com/'
                
            response = self.session.get(
                url, 
                headers=headers, 
                stream=True, 
                timeout=timeout,
                verify=False  # Some govt sites have cert issues
            )
            response.raise_for_status()
            
            # Check if it's actually a PDF
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower() and not url.endswith('.pdf'):
                logger.warning(f"Non-PDF content type for {url}: {content_type}")
                # Still try to download if it's substantial content
                if int(response.headers.get('content-length', 0)) < 1000:
                    return False
            
            # Download with progress
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(dest_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Log progress for large files
                        if total_size > 0 and downloaded % (chunk_size * 100) == 0:
                            progress = (downloaded / total_size) * 100
                            logger.debug(f"Downloading {dest_path.name}: {progress:.1f}%")
            
            # Verify file size
            if dest_path.stat().st_size < 1000:
                logger.warning(f"Downloaded file too small: {dest_path}")
                dest_path.unlink()
                return False
                
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Download failed for {url}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading {url}: {e}")
            return False
