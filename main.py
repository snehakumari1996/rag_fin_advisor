import argparse
from src.web_crawler import RegulatoryDataCrawler
from src.document_processor import DocumentProcessor
from src.rag_chain import FinancialAdvisorRAG
from src.config import logger

def crawl_data():
    """Crawl all regulatory data"""
    logger.info("Starting data crawling...")
    crawler = RegulatoryDataCrawler()
    crawler.download_all(max_workers=5)
    logger.info("Crawling completed!")

def process_documents():
    """Process and index documents"""
    logger.info("Starting document processing...")
    processor = DocumentProcessor()
    documents = processor.process_documents()
    processor.create_vector_store(documents)
    logger.info("Document processing completed!")

def test_rag():
    """Test the RAG system"""
    logger.info("Testing RAG system...")
    rag = FinancialAdvisorRAG()
    
    test_questions = [
        "What documents do I need to open a demat account?",
        "Can I do insider trading if I have material information?",
        "What are the risks of F&O trading for beginners?",
        "How do I file a complaint against my broker?",
        "What is the process for IPO application?"
    ]
    
    for question in test_questions:
        print(f"\n{'='*80}")
        print(f"Question: {question}")
        print(f"{'='*80}")
        
        response = rag.answer(question)
        
        if response["warnings"]:
            print("\n⚠️ WARNINGS:")
            for warning in response["warnings"]:
                print(f"  {warning}")
        
        print(f"\nAnswer:\n{response['answer']}")
        print(f"\nSources: {', '.join(response['sources'][:3])}")
        print(f"\n{response['disclaimer']}")

def main():
    parser = argparse.ArgumentParser(description="Financial RAG System")
    parser.add_argument("--crawl", action="store_true", help="Crawl regulatory data")
    parser.add_argument("--process", action="store_true", help="Process documents")
    parser.add_argument("--test", action="store_true", help="Test RAG system")
    parser.add_argument("--question", type=str, help="Ask a specific question")
    
    args = parser.parse_args()
    
    if args.crawl:
        crawl_data()
    
    if args.process:
        process_documents()
    
    if args.test:
        test_rag()
    
    if args.question:
        rag = FinancialAdvisorRAG()
        response = rag.answer(args.question)
        
        if response["warnings"]:
            print("\n⚠️ WARNINGS:")
            for warning in response["warnings"]:
                print(f"  {warning}")
        
        print(f"\nAnswer:\n{response['answer']}")
        print(f"\n{response['disclaimer']}")

if __name__ == "__main__":
    main()