#!/usr/bin/env python3
"""
Setup script for Financial RAG System in Google Colab
Run this first to install all dependencies and create directory structure
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_colab():
    """Complete setup for Google Colab environment"""
    
    print("🚀 Financial RAG System - Colab Setup")
    print("="*50)
    
    # 1. Mount Google Drive
    try:
        from google.colab import drive
        drive.mount('/content/drive')
        print("✅ Google Drive mounted")
    except:
        print("❌ Not running in Colab or Drive already mounted")
    
    # 2. Set base directory
    BASE_DIR = Path("/content/drive/MyDrive/RAG_financial_advisor_iter1")
    os.makedirs(BASE_DIR, exist_ok=True)
    os.chdir(BASE_DIR)
    print(f"✅ Working directory: {BASE_DIR}")
    
    # 3. Install system dependencies
    print("\n📦 Installing system dependencies...")
    try:
        subprocess.run(["apt-get", "update", "-qq"], capture_output=True)
        subprocess.run(["apt-get", "install", "-y", "poppler-utils", "-qq"], capture_output=True)
        print("✅ System dependencies installed")
    except Exception as e:
        print(f"⚠️ System dependency error: {e}")
    
    # 4. Create directory structure
    directories = [
        "src", "src/utils",
        "data/raw/sebi", "data/raw/rbi", "data/raw/nse", "data/raw/others",
        "data/processed", "data/faiss_index", "data/cache",
        "logs", "config"
    ]
    
    for dir_path in directories:
        Path(BASE_DIR / dir_path).mkdir(parents=True, exist_ok=True)
    print("✅ Directory structure created")
    
    # 5. Create __init__.py files
    init_files = ["src/__init__.py", "src/utils/__init__.py"]
    for init_file in init_files:
        Path(BASE_DIR / init_file).touch()
    
    # 6. Create requirements.txt
    requirements = """# Core dependencies
langchain==0.1.0
langchain-community
langchain-openai
openai
faiss-cpu==1.7.4
tiktoken

# Document processing
PyMuPDF==1.23.8
beautifulsoup4==4.12.2
pandas==2.1.4

# ML/Embeddings
sentence-transformers==2.2.2
torch

# Web/API
gradio==4.16.0
fastapi==0.108.0
uvicorn==0.25.0

# Utilities
python-dotenv==1.0.0
tqdm==4.66.1
requests==2.31.0
fake-useragent==1.4.0
"""
    
    with open(BASE_DIR / "requirements.txt", "w") as f:
        f.write(requirements)
    
    # 7. Install Python packages
    print("\n📦 Installing Python packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"])
    print("✅ Python packages installed")
    
    # 8. API Key setup
    api_key_file = BASE_DIR / "config" / "api_key.txt"
    if not api_key_file.exists():
        print("\n🔑 OpenAI API Key Setup")
        print("-"*30)
        api_key = input("Enter your OpenAI API key: ").strip()
        if api_key:
            api_key_file.write_text(api_key)
            print("✅ API key saved")
        else:
            print("⚠️ No API key provided. Set it later in config/api_key.txt")
    else:
        print("✅ API key already configured")
    
    print("\n✅ Setup complete!")
    print(f"📁 Project location: {BASE_DIR}")
    print("\nNext steps:")
    print("1. Run: python main.py --process")
    print("2. Run: python app.py")

if __name__ == "__main__":
    setup_colab()