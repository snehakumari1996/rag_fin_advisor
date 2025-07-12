# ── demo_gradio.py (ENHANCED) ────────────────────────────────────
import gradio as gr
from typing import List, Tuple
import logging
from datetime import datetime
from src.rag_chain import FinancialAdvisorRAG
from src.config import logger

# Initialize RAG system
logger.info("Initializing RAG system...")
rag = None
try:
    rag = FinancialAdvisorRAG()
    logger.info("RAG system initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize RAG: {e}")

# Store conversation history
conversation_history = []

def format_response(response_dict):
    """Format the RAG response for display"""
    formatted = ""
    
    # Add warnings at the top if any
    if response_dict.get("warnings"):
        formatted += "## ⚠️ Important Warnings\n\n"
        for warning in response_dict["warnings"]:
            formatted += f"- {warning}\n"
        formatted += "\n---\n\n"
    
    # Add main answer
    formatted += response_dict["answer"]
    
    # Add sources
    if response_dict.get("sources"):
        formatted += "\n\n---\n### 📚 Sources\n"
        unique_sources = list(set(response_dict["sources"][:5]))  # Top 5 unique sources
        for source in unique_sources:
            formatted += f"- {source}\n"
    
    # Add disclaimer
    formatted += f"\n\n---\n*{response_dict['disclaimer']}*"
    
    return formatted

def answer_question(question: str, history: List[Tuple[str, str]]) -> Tuple[List[Tuple[str, str]], str]:
    """Process user question and return response"""
    if not rag:
        return history + [(question, "❌ RAG system not initialized. Please check logs.")], ""
    
    try:
        # Get response from RAG
        response_dict = rag.answer(question)
        formatted_response = format_response(response_dict)
        
        # Update history
        new_history = history + [(question, formatted_response)]
        
        # Store in conversation history with timestamp
        conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "response": response_dict
        })
        
        return new_history, ""
    
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        error_msg = f"❌ Error: {str(e)}\n\nPlease try rephrasing your question."
        return history + [(question, error_msg)], ""

def clear_conversation():
    """Clear the conversation history"""
    conversation_history.clear()
    return [], ""

# Example questions for quick testing
example_questions = [
    "What documents do I need to open a demat account?",
    "What are the risks of F&O trading for beginners?",
    "How can I file a complaint against my broker with SEBI?",
    "What is the lock-in period for ELSS mutual funds?",
    "Can I do intraday trading with my savings account?",
    "What are the tax implications of selling stocks within a year?",
    "Is it legal to trade based on WhatsApp tips?",
    "What is the process for IPO application through ASBA?",
    "What are the margin requirements for equity delivery trades?",
    "How do I transfer shares from one demat account to another?"
]

# Create Gradio interface
with gr.Blocks(title="Financial Advisor RAG System", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🏦 Financial Advisor RAG System
        
        Ask questions about Indian stock market regulations, compliance, and best practices.
        This system searches through SEBI, RBI, NSE, and BSE regulations to provide accurate, compliant answers.
        
        ⚡ **Features**:
        - Real-time compliance checking
        - Source citations from official documents
        - Risk warnings for dangerous activities
        - Best practices from regulatory guidelines
        """
    )
    
    with gr.Row():
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(
                label="Conversation",
                height=500,
                elem_id="chatbot"
            )
            
            with gr.Row():
                msg = gr.Textbox(
                    label="Ask your question",
                    placeholder="e.g., What are the rules for short selling in India?",
                    lines=2,
                    scale=4
                )
                submit_btn = gr.Button("Send", variant="primary", scale=1)
            
            with gr.Row():
                clear_btn = gr.Button("Clear Conversation", variant="secondary")
                
        with gr.Column(scale=1):
            gr.Markdown("### 💡 Example Questions")
            for i, example in enumerate(example_questions):
                gr.Button(
                    example,
                    variant="secondary",
                    size="sm"
                ).click(
                    lambda x=example: (x, gr.update()),
                    outputs=[msg, msg]
                )
    
    # Status indicator
    with gr.Row():
        status = gr.Markdown(
            f"**System Status**: {'✅ Ready' if rag else '❌ Not Initialized'}"
        )
    
    # Wire up the interactions
    submit_btn.click(
        answer_question,
        inputs=[msg, chatbot],
        outputs=[chatbot, msg]
    )
    
    msg.submit(
        answer_question,
        inputs=[msg, chatbot],
        outputs=[chatbot, msg]
    )
    
    clear_btn.click(
        clear_conversation,
        outputs=[chatbot, msg]
    )
    
    # Add custom CSS for better styling
    demo.css = """
    #chatbot {
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    .message.user {
        background-color: #e3f2fd !important;
    }
    .message.bot {
        background-color: #f5f5f5 !important;
    }
    """

if __name__ == "__main__":
    demo.launch(
        share=True,
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True
    )