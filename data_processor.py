
import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging
from tqdm import tqdm

# Document processing
import fitz  # PyMuPDF
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Project imports
from src.text_splitter import FinancialTextSplitter, ChunkMetadata
from config import RAW_DIR, INDEX_DIR, CACHE_DIR, logger

class DocumentProcessor:
    """Process financial documents into vector store"""
    
    def __init__(self, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.embedding_model = embedding_model
        self.text_splitter = FinancialTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Processing cache
        self.cache_file = CACHE_DIR / "processing_cache.json"
        self.processed_files = self._load_cache()
        
        # Statistics
        self.stats = {
            "total_files": 0,
            "processed_files": 0,
            "failed_files": 0,
            "total_chunks": 0,
            "processing_time": 0
        }
    
    def _load_cache(self) -> Dict:
        """Load processing cache"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Save processing cache"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.processed_files, f, indent=2)
    
    def process_all_documents(self, force_reprocess: bool = False) -> Tuple[List[Document], Dict]:
        """Process all documents in the raw directory"""
        start_time = datetime.now()
        all_documents = []
        
        # Find all documents
        pdf_files = list(RAW_DIR.rglob("*.pdf"))
        txt_files = list(RAW_DIR.rglob("*.txt"))
        all_files = pdf_files + txt_files
        
        self.stats["total_files"] = len(all_files)
        logger.info(f"Found {len(all_files)} documents to process")
        
        # Process each file
        for file_path in tqdm(all_files, desc="Processing documents"):
            try:
                # Check cache
                file_key = str(file_path)
                file_stats = file_path.stat()
                file_info = {
                    "size": file_stats.st_size,
                    "modified": file_stats.st_mtime
                }
                
                # Skip if already processed and not forcing reprocess
                if not force_reprocess and file_key in self.processed_files:
                    cached_info = self.processed_files[file_key]
                    if (cached_info.get("size") == file_info["size"] and 
                        cached_info.get("modified") == file_info["modified"]):
                        logger.debug(f"Skipping already processed: {file_path.name}")
                        continue
                
                # Process document
                documents = self._process_single_document(file_path)
                if documents:
                    all_documents.extend(documents)
                    self.stats["processed_files"] += 1
                    
                    # Update cache
                    self.processed_files[file_key] = {
                        **file_info,
                        "chunks": len(documents),
                        "processed_at": datetime.now().isoformat()
                    }
                else:
                    self.stats["failed_files"] += 1
                    
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                self.stats["failed_files"] += 1
        
        # Save cache and stats
        self._save_cache()
        self.stats["total_chunks"] = len(all_documents)
        self.stats["processing_time"] = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Processing complete: {self.stats}")
        
        return all_documents, self.stats
    
    def _process_single_document(self, file_path: Path) -> List[Document]:
        """Process a single document"""
        try:
            # Extract text based on file type
            if file_path.suffix.lower() == '.pdf':
                text = self._extract_text_from_pdf(file_path)
            else:
                text = file_path.read_text(encoding='utf-8')
            
            if not text.strip():
                logger.warning(f"No text extracted from {file_path}")
                return []
            
            # Extract metadata
            metadata = self._extract_metadata(file_path, text)
            
            # Split text into chunks
            chunks_with_metadata = self.text_splitter.split_text(text, metadata)
            
            # Create LangChain documents
            documents = []
            for chunk_text, chunk_metadata in chunks_with_metadata:
                doc = Document(
                    page_content=chunk_text,
                    metadata={
                        "source": file_path.name,
                        "file_path": str(file_path),
                        "chunk_index": chunk_metadata.chunk_index,
                        "total_chunks": chunk_metadata.total_chunks,
                        "section": chunk_metadata.section,
                        "regulation_type": chunk_metadata.regulation_type,
                        **metadata
                    }
                )
                documents.append(doc)
            
            logger.info(f"Processed {file_path.name}: {len(documents)} chunks")
            return documents
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return []
    
    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF with better handling"""
        try:
            doc = fitz.open(str(pdf_path))
            text = ""
            
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                
                # Clean text
                page_text = self._clean_text(page_text)
                
                if page_text.strip():
                    text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
            
            doc.close()
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        import re
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR issues
        text = text.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
        text = text.replace('—', '-').replace('–', '-')
        
        # Remove non-printable characters
        text = ''.join(char for char in text if char.isprintable() or char in '\n\t')
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([,.!?;:])', r'\1', text)
        text = re.sub(r'([,.!?;:])\s*', r'\1 ', text)
        
        return text.strip()
    
    def _extract_metadata(self, file_path: Path, text: str) -> Dict:
        """Extract metadata from document"""
        metadata = {
            "file_type": file_path.suffix.lower(),
            "file_size": file_path.stat().st_size,
            "created_date": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
            "document_category": self._categorize_document(file_path, text)
        }
        
        # Extract date from text if possible
        import re
        date_patterns = [
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(\d{1,2}\s+\w+\s+\d{4})',
            r'(\w+\s+\d{1,2},\s+\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text[:1000])  # Check first 1000 chars
            if match:
                metadata["document_date"] = match.group(1)
                break
        
        # Extract circular/notification number
        ref_patterns = [
            r'Circular\s+No[.:]\s*([A-Z0-9/-]+)',
            r'Notification\s+No[.:]\s*([A-Z0-9/-]+)',
            r'Ref[.:]\s*([A-Z0-9/-]+)'
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, text[:1000], re.IGNORECASE)
            if match:
                metadata["reference_number"] = match.group(1)
                break
        
        return metadata
    
    def _categorize_document(self, file_path: Path, text: str) -> str:
        """Categorize document based on path and content"""
        path_str = str(file_path).lower()
        text_lower = text[:2000].lower()  # Check first 2000 chars
        
        if "sebi" in path_str or "sebi" in text_lower:
            if "regulation" in text_lower:
                return "SEBI_Regulation"
            elif "circular" in text_lower:
                return "SEBI_Circular"
            else:
                return "SEBI_Other"
        elif "rbi" in path_str or "reserve bank" in text_lower:
            if "master direction" in text_lower:
                return "RBI_Master_Direction"
            else:
                return "RBI_Other"
        elif "nse" in path_str:
            return "NSE_Document"
        elif "bse" in path_str:
            return "BSE_Document"
        elif "tax" in text_lower or "income tax" in text_lower:
            return "Tax_Related"
        else:
            return "Other"
    
    def create_vector_store(self, documents: List[Document]) -> FAISS:
        """Create FAISS vector store from documents"""
        if not documents:
            raise ValueError("No documents to create vector store")
        
        logger.info(f"Creating vector store with {len(documents)} documents...")
        
        # Create vector store
        vector_store = FAISS.from_documents(
            documents,
            self.embeddings
        )
        
        # Save to disk
        vector_store.save_local(str(INDEX_DIR))
        logger.info(f"Vector store saved to {INDEX_DIR}")
        
        # Save metadata
        metadata = {
            "created_at": datetime.now().isoformat(),
            "total_documents": len(documents),
            "embedding_model": self.embedding_model,
            "chunk_size": self.text_splitter.chunk_size,
            "chunk_overlap": self.text_splitter.chunk_overlap
        }
        
        metadata_file = INDEX_DIR / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return vector_store
    
    def update_vector_store(self, new_documents: List[Document]) -> FAISS:
        """Update existing vector store with new documents"""
        try:
            # Load existing vector store
            vector_store = FAISS.load_local(
                str(INDEX_DIR),
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            
            # Add new documents
            vector_store.add_documents(new_documents)
            
            # Save updated store
            vector_store.save_local(str(INDEX_DIR))
            logger.info(f"Updated vector store with {len(new_documents)} new documents")
            
            return vector_store
            
        except Exception as e:
            logger.warning(f"Could not update existing store: {e}. Creating new one.")
            return self.create_vector_store(new_documents)
    
    def get_processing_stats(self) -> Dict:
        """Get detailed processing statistics"""
        stats = self.stats.copy()
        
        # Add cache stats
        stats["cached_files"] = len(self.processed_files)
        
        # Add vector store stats if exists
        metadata_file = INDEX_DIR / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                vs_metadata = json.load(f)
                stats["vector_store"] = vs_metadata
        
        return stats

# Main processing function
def process_all_documents(force_reprocess: bool = False) -> Dict:
    """Process all documents and create vector store"""
    processor = DocumentProcessor()
    
    # Process documents
    documents, stats = processor.process_all_documents(force_reprocess)
    
    if documents:
        # Create or update vector store
        if (INDEX_DIR / "index.faiss").exists() and not force_reprocess:
            processor.update_vector_store(documents)
        else:
            processor.create_vector_store(documents)
    
    return processor.get_processing_stats()

if __name__ == "__main__":
    # Run document processing
    stats = process_all_documents()
    print(f"\nProcessing complete: {json.dumps(stats, indent=2)}")