"""
app.py - Main Gradio Application for Financial RAG System
Run this after setting up the environment and processing documents
"""
import os
import sys
from pathlib import Path

# Add project root to path
DRIVE_BASE = Path("/content/drive/MyDrive/RAG_fin_iter1")
sys.path.append(str(DRIVE_BASE))

import gradio as gr
from datetime import datetime
import json
import logging

# Import project modules
from src.rag_chain import FinancialRAGChain
from src.compliance import ComplianceChecker
from config import INDEX_DIR, CACHE_DIR, logger

# Initialize components
compliance_checker = ComplianceChecker()
rag = None

def initialize_rag():
    """Initialize RAG system"""
    global rag
    try:
        logger.info("Initializing RAG system...")
        rag = FinancialRAGChain()
        logger.info("✅ RAG system initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize RAG: {e}")
        return False

def format_response(response_dict):
    """Format RAG response for display"""
    output = ""

    # Add compliance warnings at the top
    if response_dict.get("warnings"):
        output += "### ⚠️ Compliance Alerts:\n\n"
        for warning in response_dict["warnings"]:
            output += f"- {warning}\n"
        output += "\n---\n\n"

    # Add main answer
    output += response_dict["answer"]

    # Add sources
    if response_dict.get("sources"):
        output += "\n\n### 📚 Sources:\n"
        unique_sources = list(set(response_dict["sources"][:5]))
        for source in unique_sources:
            output += f"- {source}\n"

    # Add disclaimer
    output += "\n\n---\n*Disclaimer: This is educational information based on SEBI/RBI regulations. Always consult a SEBI-registered investment advisor for personalized advice.*"

    return output

def save_query_log(question, response, warnings):
    """Save query to log file"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "warnings": warnings,
        "sources": response.get("sources", [])
    }

    log_file = CACHE_DIR / "query_history.jsonl"
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
def chat_interface(message, history):
    """Main chat interface function"""
    if not rag:
        return history + [(message, "❌ System not initialized. Please wait...")]

    try:
        # Get structured response from RAG
        response = rag.answer(message)

        # Format structured compliance warnings
        formatted_warnings = ""
        if isinstance(response.get("warnings"), list):
            for w in response["warnings"]:
                if isinstance(w, dict):
                    formatted_warnings += f"⚠️ **{w.get('category', '').upper()}**: {w.get('warning', '')}\n"
                else:
                    formatted_warnings += f"⚠️ {w}\n"

        # Format the final answer
        formatted_response = response.get("answer", "")
        if formatted_warnings:
            formatted_response = f"### ⚠ Compliance Alerts:\n{formatted_warnings}\n---\n{formatted_response}"

        # Save to log
        save_query_log(message, response, response.get("warnings", []))

        # ✅ Return new history
        return history + [(message, formatted_response)]

    except Exception as e:
        logger.error(f"Error in chat interface: {e}")
        return history + [(message, f"❌ Error: {str(e)}\n\nPlease check your OpenAI API key and try again.")]

def get_example_questions():
    """Get example questions for the interface"""
    return [
        "What documents do I need to open a demat account?",
        "Can I do insider trading if I have material information?",
        "What are the risks of F&O trading for beginners?",
        "How do I file a complaint with SEBI against my broker?",
        "What are the charges for a demat account?",
        "Is margin trading safe for new investors?",
        "What happens if I don't square off my intraday position?",
        "How much tax do I pay on stock market profits?",
        "Can I trade in my company's shares?",
        "What is the difference between CNC and MIS orders?"
    ]

def create_interface():
    """Create and configure Gradio interface"""
    with gr.Blocks(title="🏦 Financial RAG System", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # 🏦 Indian Financial Market Compliance Advisor

            Ask questions about SEBI regulations, stock market rules, and investment compliance.
            This system provides accurate information with compliance warnings and source citations.

            ## Features:
            - ✅ Real-time compliance checking
            - ⚠️ Risk warnings for dangerous activities  
            - 📚 Source citations from official documents
            - 🛡️ Based on SEBI/RBI/NSE regulations
            """
        )

        chatbot = gr.Chatbot(
            label="Conversation",
            height=500,
            elem_id="chatbot",
            type="tuples"
        )

        with gr.Row():
            msg = gr.Textbox(
                label="Ask your question",
                placeholder="e.g., What are the requirements for opening a demat account?",
                lines=2,
                scale=4
            )
            submit_btn = gr.Button("Send", variant="primary", scale=1)

        with gr.Row():
            clear_btn = gr.Button("Clear Conversation", variant="secondary")

        gr.Examples(
            examples=get_example_questions(),
            inputs=msg,
            label="Example Questions"
        )

        with gr.Row():
            status = gr.Markdown(
                f"**System Status**: {'✅ Ready' if rag else '❌ Not Initialized'} | "
                f"**Data Location**: {DRIVE_BASE}"
            )

        submit_btn.click(
            chat_interface,
            inputs=[msg, chatbot],
            outputs=[chatbot]
        ).then(
            lambda: "",
            outputs=[msg]
        )

        msg.submit(
            chat_interface,
            inputs=[msg, chatbot],
            outputs=[chatbot]
        ).then(
            lambda: "",
            outputs=[msg]
        )

        clear_btn.click(
            lambda: ([], ""),
            outputs=[chatbot, msg]
        )

    return demo

if __name__ == "__main__":
    print("="*60)
    print("🚀 Financial RAG System - Starting Application")
    print("="*60)

    if initialize_rag():
        print("✅ System initialized successfully")
        demo = create_interface()
        print("\n📊 Launching Gradio interface...")
        demo.launch(
            share=True,
            server_name="0.0.0.0",
            server_port=7860,
            show_error=True
        )
    else:
        print("❌ Failed to initialize system. Check logs for details.")
