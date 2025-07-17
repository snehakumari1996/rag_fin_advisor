"""
Document processing module for Financial RAG System
Handles PDF extraction, text processing, and vector store creation
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import hashlib

import fitz  # PyMuPDF
from tqdm import tqdm
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from config import (
    RAW_DIR, PROCESSED_DIR, INDEX_DIR, CACHE_DIR,
    MODEL_CONFIG, CHUNK_CONFIG, logger
)

class DocumentProcessor:
    """Process documents and create vector embeddings"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_CONFIG["chunk_size"],
            chunk_overlap=CHUNK_CONFIG["chunk_overlap"],
            separators=CHUNK_CONFIG["separators"]
        )
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=MODEL_CONFIG["embedding_model"],
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        self.cache_file = CACHE_DIR / "processed_documents.json"
        self.load_cache()
        
    def load_cache(self):
        """Load processing cache"""
        if self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                self.cache = json.load(f)
        else:
            self.cache = {"processed_files": {}, "last_updated": None}
    
    def save_cache(self):
        """Save processing cache"""
        self.cache["last_updated"] = datetime.now().isoformat()
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def extract_text_from_pdf(self, pdf_path: Path) -> Optional[str]:
        """Extract text from PDF file"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                if page_text.strip():
                    text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
            
            doc.close()
            
            if not text.strip():
                logger.warning(f"No text extracted from {pdf_path}")
                return None
                
            return self.clean_text(text)
            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text"""
        import re
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Fix common OCR issues
        replacements = {
            'ﬁ': 'fi', 'ﬂ': 'fl', 'ﬀ': 'ff',
            'ﬃ': 'ffi', 'ﬄ': 'ffl',
            '"': '"', '"': '"', ''': "'", ''': "'",
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove non-printable characters
        text = ''.join(char for char in text if char.isprintable() or char in '\n\t')
        
        return text.strip()
    
    def get_file_hash(self, filepath: Path) -> str:
        """Get hash of file for cache checking"""
        return hashlib.md5(filepath.read_bytes()).hexdigest()
    
    def extract_metadata(self, filepath: Path, text: str) -> Dict:
        """Extract metadata from document"""
        metadata = {
            "source": filepath.name,
            "file_path": str(filepath),
            "file_size": filepath.stat().st_size,
            "extraction_date": datetime.now().isoformat(),
        }
        
        # Determine document type and regulator
        path_parts = filepath.parts
        if "sebi" in str(filepath).lower():
            metadata["regulator"] = "SEBI"
            metadata["doc_type"] = self._identify_sebi_type(text)
        elif "rbi" in str(filepath).lower():
            metadata["regulator"] = "RBI"
            metadata["doc_type"] = self._identify_rbi_type(text)
        elif "nse" in str(filepath).lower():
            metadata["regulator"] = "NSE"
            metadata["doc_type"] = "circular"
        elif "bse" in str(filepath).lower():
            metadata["regulator"] = "BSE"
            metadata["doc_type"] = "notice"
        else:
            metadata["regulator"] = "Other"
            metadata["doc_type"] = "general"
        
        # Try to extract date from text
        import re
        date_patterns = [
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(\d{1,2}\s+\w+\s+\d{4})',
            r'(\w+\s+\d{1,2},\s+\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text[:1000])
            if match:
                metadata["document_date"] = match.group(1)
                break
        
        return metadata
    
    def _identify_sebi_type(self, text: str) -> str:
        """Identify SEBI document type"""
        text_lower = text[:2000].lower()
        
        if "regulation" in text_lower:
            return "regulation"
        elif "circular" in text_lower:
            return "circular"
        elif "guideline" in text_lower:
            return "guideline"
        elif "notification" in text_lower:
            return "notification"
        elif "consultation" in text_lower:
            return "consultation_paper"
        else:
            return "other"
    
    def _identify_rbi_type(self, text: str) -> str:
        """Identify RBI document type"""
        text_lower = text[:2000].lower()
        
        if "master direction" in text_lower:
            return "master_direction"
        elif "circular" in text_lower:
            return "circular"
        elif "notification" in text_lower:
            return "notification"
        elif "faq" in text_lower:
            return "faq"
        else:
            return "other"
    
    def process_single_document(self, filepath: Path) -> List[Document]:
        """Process a single document"""
        # Check cache
        file_hash = self.get_file_hash(filepath)
        if str(filepath) in self.cache["processed_files"]:
            if self.cache["processed_files"][str(filepath)]["hash"] == file_hash:
                logger.info(f"Skipping {filepath.name} (already processed)")
                return []
        
        logger.info(f"Processing {filepath.name}...")
        
        # Extract text based on file type
        if filepath.suffix.lower() == '.pdf':
            text = self.extract_text_from_pdf(filepath)
        elif filepath.suffix.lower() in ['.txt', '.text']:
            text = filepath.read_text(encoding='utf-8', errors='ignore')
        else:
            logger.warning(f"Unsupported file type: {filepath.suffix}")
            return []
        
        if not text:
            return []
        
        # Extract metadata
        metadata = self.extract_metadata(filepath, text)
        
        # Split into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Create documents
        documents = []
        for i, chunk in enumerate(chunks):
            doc_metadata = metadata.copy()
            doc_metadata.update({
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk),
            })
            
            doc = Document(
                page_content=chunk,
                metadata=doc_metadata
            )
            documents.append(doc)
        
        # Update cache
        self.cache["processed_files"][str(filepath)] = {
            "hash": file_hash,
            "processed_date": datetime.now().isoformat(),
            "chunks": len(chunks),
            "metadata": metadata
        }
        self.save_cache()
        
        logger.info(f"Created {len(chunks)} chunks from {filepath.name}")
        return documents
    
    def process_all_documents(self) -> List[Document]:
        """Process all documents in raw directory"""
        all_documents = []
        
        # Find all documents
        file_patterns = ['*.pdf', '*.txt', '*.text']
        all_files = []
        
        for pattern in file_patterns:
            all_files.extend(RAW_DIR.rglob(pattern))
        
        if not all_files:
            logger.warning(f"No documents found in {RAW_DIR}")
            return []
        
        logger.info(f"Found {len(all_files)} documents to process")
        
        # Process each file
        for filepath in tqdm(all_files, desc="Processing documents"):
            try:
                docs = self.process_single_document(filepath)
                all_documents.extend(docs)
            except Exception as e:
                logger.error(f"Error processing {filepath}: {e}")
                continue
        
        logger.info(f"Total documents created: {len(all_documents)}")
        return all_documents
    
    def create_vector_store(self, documents: List[Document], update_existing: bool = True):
        """Create or update FAISS vector store"""
        if not documents:
            logger.error("No documents to index")
            return None
        
        logger.info(f"Creating vector store with {len(documents)} documents...")
        
        if update_existing and (INDEX_DIR / "index.faiss").exists():
            # Load existing vector store
            try:
                vector_store = FAISS.load_local(
                    str(INDEX_DIR),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                # Add new documents
                vector_store.add_documents(documents)
                logger.info("Updated existing vector store")
            except Exception as e:
                logger.error(f"Error loading existing vector store: {e}")
                # Create new one
                vector_store = FAISS.from_documents(documents, self.embeddings)
                logger.info("Created new vector store")
        else:
            # Create new vector store
            vector_store = FAISS.from_documents(documents, self.embeddings)
            logger.info("Created new vector store")
        
        # Save to disk
        vector_store.save_local(str(INDEX_DIR))
        logger.info(f"Vector store saved to {INDEX_DIR}")
        
        # Save index metadata
        index_metadata = {
            "created_date": datetime.now().isoformat(),
            "total_documents": len(documents),
            "embedding_model": MODEL_CONFIG["embedding_model"],
            "chunk_config": CHUNK_CONFIG,
        }
        
        with open(INDEX_DIR / "metadata.json", 'w') as f:
            json.dump(index_metadata, f, indent=2)
        
        return vector_store
    
    def get_statistics(self) -> Dict:
        """Get processing statistics"""
        stats = {
            "total_files_processed": len(self.cache["processed_files"]),
            "total_chunks": sum(f["chunks"] for f in self.cache["processed_files"].values()),
            "last_updated": self.cache["last_updated"],
            "file_types": {},
            "regulators": {},
        }
        
        for filepath, info in self.cache["processed_files"].items():
            # Count by file type
            ext = Path(filepath).suffix.lower()
            stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1
            
            # Count by regulator
            reg = info["metadata"].get("regulator", "Unknown")
            stats["regulators"][reg] = stats["regulators"].get(reg, 0) + 1
        
        return stats

def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process documents for RAG system")
    parser.add_argument("--file", type=str, help="Process specific file")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--update", action="store_true", help="Update existing index")
    
    args = parser.parse_args()
    
    processor = DocumentProcessor()
    
    if args.stats:
        stats = processor.get_statistics()
        print("\n📊 Processing Statistics:")
        print(f"Total files: {stats['total_files_processed']}")
        print(f"Total chunks: {stats['total_chunks']}")
        print(f"Last updated: {stats['last_updated']}")
        print("\nFile types:")
        for ext, count in stats['file_types'].items():
            print(f"  {ext}: {count}")
        print("\nRegulators:")
        for reg, count in stats['regulators'].items():
            print(f"  {reg}: {count}")
    
    elif args.file:
        filepath = Path(args.file)
        if filepath.exists():
            docs = processor.process_single_document(filepath)
            if docs:
                processor.create_vector_store(docs, update_existing=args.update)
        else:
            print(f"File not found: {filepath}")
    
    else:
        # Process all documents
        docs = processor.process_all_documents()
        if docs:
            processor.create_vector_store(docs, update_existing=args.update)

if __name__ == "__main__":
    main()