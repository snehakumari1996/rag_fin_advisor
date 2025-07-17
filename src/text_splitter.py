"""
src/text_splitter.py - Advanced text splitting for financial documents
Handles different document types with appropriate chunking strategies
"""
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ChunkMetadata:
    """Metadata for document chunks"""
    source: str
    chunk_index: int
    total_chunks: int
    section: Optional[str] = None
    regulation_type: Optional[str] = None
    page_number: Optional[int] = None

class FinancialTextSplitter:
    """Custom text splitter for financial regulatory documents"""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        length_function: callable = len
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function
        
        # Financial document section markers
        self.section_markers = [
            r"CHAPTER\s+[IVXLC]+",
            r"PART\s+[IVXLC]+",
            r"Section\s+\d+",
            r"Regulation\s+\d+",
            r"Article\s+\d+",
            r"Schedule\s+[IVXLC]+",
            r"Annexure\s+[A-Z]",
            r"\d+\.\s+[A-Z][A-Za-z\s]+:",  # Numbered sections
        ]
        
        # Regulation types
        self.regulation_patterns = {
            "SEBI_LODR": r"listing.*obligation.*disclosure",
            "SEBI_PIT": r"insider.*trading|prohibition.*insider",
            "SEBI_TAKEOVER": r"takeover.*regulation|substantial.*acquisition",
            "RBI_MASTER": r"master.*direction|master.*circular",
            "NSE_CIRCULAR": r"nse.*circular|exchange.*notice",
            "INCOME_TAX": r"income.*tax|section.*80|capital.*gain",
        }
        
    def split_text(self, text: str, metadata: Dict = None) -> List[Tuple[str, ChunkMetadata]]:
        """Split text into chunks with metadata"""
        if not text:
            return []
        
        # Detect document type
        doc_type = self._detect_document_type(text)
        
        # Split based on document type
        if doc_type in ["regulation", "act"]:
            chunks = self._split_legal_document(text)
        elif doc_type == "circular":
            chunks = self._split_circular(text)
        elif doc_type == "faq":
            chunks = self._split_faq(text)
        else:
            chunks = self._split_generic(text)
        
        # Add metadata to chunks
        result = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = ChunkMetadata(
                source=metadata.get("source", "unknown") if metadata else "unknown",
                chunk_index=i + 1,
                total_chunks=len(chunks),
                regulation_type=self._identify_regulation_type(chunk),
                section=self._extract_section(chunk)
            )
            result.append((chunk, chunk_metadata))
        
        return result
    
    def _detect_document_type(self, text: str) -> str:
        """Detect the type of financial document"""
        text_lower = text.lower()[:2000]  # Check first 2000 chars
        
        if "regulation" in text_lower and "chapter" in text_lower:
            return "regulation"
        elif "circular" in text_lower and "ref" in text_lower:
            return "circular"
        elif "frequently asked questions" in text_lower or "faq" in text_lower:
            return "faq"
        elif "act" in text_lower and "section" in text_lower:
            return "act"
        else:
            return "generic"
    
    def _split_legal_document(self, text: str) -> List[str]:
        """Split legal documents by sections/chapters"""
        chunks = []
        
        # Find all section markers
        section_pattern = "|".join(self.section_markers)
        sections = re.split(f"({section_pattern})", text, flags=re.IGNORECASE)
        
        current_chunk = ""
        for part in sections:
            if re.match(section_pattern, part, re.IGNORECASE):
                # Start new section
                if current_chunk and len(current_chunk) > 100:
                    chunks.extend(self._split_by_size(current_chunk))
                current_chunk = part
            else:
                current_chunk += part
                
                # Split if too large
                if self.length_function(current_chunk) > self.chunk_size * 1.5:
                    chunks.extend(self._split_by_size(current_chunk))
                    current_chunk = ""
        
        if current_chunk:
            chunks.extend(self._split_by_size(current_chunk))
        
        return chunks
    
    def _split_circular(self, text: str) -> List[str]:
        """Split circulars by paragraphs and numbered points"""
        chunks = []
        
        # Split by numbered points
        points = re.split(r'\n\s*\d+\.\s+', text)
        
        for point in points:
            if self.length_function(point) <= self.chunk_size:
                chunks.append(point.strip())
            else:
                # Further split large points
                chunks.extend(self._split_by_size(point))
        
        return chunks
    
    def _split_faq(self, text: str) -> List[str]:
        """Split FAQ documents by Q&A pairs"""
        chunks = []
        
        # Pattern for Q&A
        qa_pattern = r'(?:Q\d*[:.]?\s*|Question[:.]?\s*)(.*?)(?:A\d*[:.]?\s*|Answer[:.]?\s*)(.*?)(?=(?:Q\d*[:.]?\s*|Question[:.]?\s*)|$)'
        
        matches = re.finditer(qa_pattern, text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            qa_pair = match.group(0).strip()
            if self.length_function(qa_pair) <= self.chunk_size:
                chunks.append(qa_pair)
            else:
                # Keep Q&A together if possible
                question = match.group(1).strip()
                answer = match.group(2).strip()
                
                if self.length_function(answer) > self.chunk_size:
                    # Split long answer
                    chunks.append(f"Q: {question}\nA: {answer[:self.chunk_size-len(question)-10]}...")
                    remaining = answer[self.chunk_size-len(question)-10:]
                    chunks.extend(self._split_by_size(f"...continued: {remaining}"))
                else:
                    chunks.append(qa_pair)
        
        # Handle any remaining text
        if not chunks:
            chunks = self._split_generic(text)
        
        return chunks
    
    def _split_generic(self, text: str) -> List[str]:
        """Generic text splitting with overlap"""
        return self._split_by_size(text)
    
    def _split_by_size(self, text: str) -> List[str]:
        """Split text by size with overlap"""
        if self.length_function(text) <= self.chunk_size:
            return [text.strip()]
        
        chunks = []
        sentences = self._split_sentences(text)
        current_chunk = ""
        current_length = 0
        
        for sentence in sentences:
            sentence_length = self.length_function(sentence)
            
            if current_length + sentence_length <= self.chunk_size:
                current_chunk += sentence + " "
                current_length += sentence_length + 1
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap
                if self.chunk_overlap > 0 and chunks:
                    # Get last few sentences for overlap
                    overlap_text = self._get_overlap_text(current_chunk, self.chunk_overlap)
                    current_chunk = overlap_text + sentence + " "
                    current_length = self.length_function(current_chunk)
                else:
                    current_chunk = sentence + " "
                    current_length = sentence_length + 1
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Financial document specific sentence splitting
        sentence_endings = r'[.!?]'
        abbreviations = ['Rs', 'Dr', 'Mr', 'Mrs', 'Ms', 'Ltd', 'Pvt', 'Inc', 'Corp', 'vs', 'etc', 'viz', 'e.g', 'i.e']
        
        # Basic sentence split
        sentences = re.split(f'({sentence_endings})', text)
        
        # Reconstruct sentences
        result = []
        current = ""
        
        for i, part in enumerate(sentences):
            current += part
            
            # Check if this is really end of sentence
            if re.match(sentence_endings, part):
                # Check for abbreviations
                words = current.split()
                if words and words[-1].rstrip('.') not in abbreviations:
                    # Check next part doesn't start with lowercase
                    if i + 1 < len(sentences) and sentences[i + 1].strip():
                        if sentences[i + 1].strip()[0].isupper():
                            result.append(current.strip())
                            current = ""
                    else:
                        result.append(current.strip())
                        current = ""
        
        if current:
            result.append(current.strip())
        
        return result
    
    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """Get text for overlap from end of chunk"""
        if self.length_function(text) <= overlap_size:
            return text
        
        # Get last portion of text
        words = text.split()
        overlap_text = ""
        current_length = 0
        
        for word in reversed(words):
            if current_length + len(word) + 1 <= overlap_size:
                overlap_text = word + " " + overlap_text
                current_length += len(word) + 1
            else:
                break
        
        return overlap_text.strip()
    
    def _identify_regulation_type(self, text: str) -> Optional[str]:
        """Identify the type of regulation from text"""
        text_lower = text.lower()
        
        for reg_type, pattern in self.regulation_patterns.items():
            if re.search(pattern, text_lower):
                return reg_type
        
        return None
    
    def _extract_section(self, text: str) -> Optional[str]:
        """Extract section identifier from chunk"""
        # Look for section markers at start of text
        for pattern in self.section_markers:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def combine_chunks(self, chunks: List[str], max_size: int) -> List[str]:
        """Combine small chunks into larger ones"""
        combined = []
        current = ""
        
        for chunk in chunks:
            if self.length_function(current + chunk) <= max_size:
                current += "\n\n" + chunk if current else chunk
            else:
                if current:
                    combined.append(current)
                current = chunk
        
        if current:
            combined.append(current)
        
        return combined

# Convenience functions
def split_financial_document(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    metadata: Dict = None
) -> List[Tuple[str, ChunkMetadata]]:
    """Split a financial document into chunks with metadata"""
    splitter = FinancialTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_text(text, metadata)

def create_langchain_splitter(chunk_size: int = 1000, chunk_overlap: int = 200):
    """Create a LangChain-compatible splitter"""
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\nCHAPTER",
            "\n\nSection",
            "\n\nRegulation",
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]
    )