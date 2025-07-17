"""
add_sample_documents.py - Run this to add sample regulatory documents
"""
import os
from pathlib import Path
import requests
import logging

# Setup paths
DRIVE_BASE = Path("/content/drive/MyDrive/RAG_fin_iter1")
RAW_DIR = DRIVE_BASE / "data" / "raw"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_documents():
    """Create comprehensive sample documents for testing"""
    
    documents = {
        "sebi/demat_account_guide.txt": """
SEBI GUIDELINES - DEMAT ACCOUNT OPENING REQUIREMENTS

1. MANDATORY DOCUMENTS FOR DEMAT ACCOUNT:

A. Identity Proof (Any One):
   - PAN Card (Mandatory for all)
   - Aadhaar Card
   - Passport
   - Voter ID Card
   - Driving License

B. Address Proof (Any One):
   - Aadhaar Card  
   - Bank Statement (not older than 3 months)
   - Utility Bill (not older than 3 months)
   - Passport
   - Rent Agreement (registered)

C. Bank Proof:
   - Cancelled cheque with name printed
   - Bank Statement/Passbook

D. Income Proof (For F&O):
   - Salary Slip (latest 3 months)
   - ITR with acknowledgment
   - Form 16
   - Bank Statement (6 months)

2. ACCOUNT OPENING CHARGES:
   - Account Opening Fee: Rs 0-750
   - Annual Maintenance: Rs 300-900
   - Transaction Charges: 0.01% to 0.05%
   - DP Charges: Rs 15-25 per transaction

3. KYC PROCESS:
   - In-Person Verification (IPV) mandatory
   - Video IPV allowed for online
   - Re-KYC required periodically
   - Aadhaar-based e-KYC available
""",
        
        "sebi/trading_regulations.txt": """
SEBI TRADING REGULATIONS AND COMPLIANCE

1. PROHIBITED ACTIVITIES:

A. Insider Trading:
   - Trading on UPSI (Unpublished Price Sensitive Information)
   - Penalty: Up to Rs 25 crores or 3x profit
   - Criminal prosecution possible
   - Imprisonment up to 10 years

B. Market Manipulation:
   - Circular Trading
   - Pump and Dump schemes
   - Creating artificial volumes
   - Price rigging
   - Penalty: Severe monetary penalties and ban

C. Front Running:
   - Trading ahead of client orders
   - Applicable to brokers, fund managers
   - License cancellation risk

2. TRADING TYPES AND RISKS:

A. Equity Delivery (CNC):
   - Risk: Limited to investment
   - No leverage
   - Settlement: T+2
   - Suitable for all investors

B. Intraday Trading (MIS):
   - Risk: HIGH - Can lose more than margin
   - Leverage up to 5x
   - Auto square-off at 3:20 PM
   - For experienced traders only

C. Futures & Options:
   - Risk: VERY HIGH - Unlimited loss potential
   - Requires income proof
   - Lot size trading
   - Not for beginners

3. COMPLIANCE REQUIREMENTS:
   - Maintain trading records for 7 years
   - Report suspicious transactions
   - Follow position limits
   - Comply with margin requirements
""",

        "rbi/payment_guidelines.txt": """
RBI GUIDELINES FOR DIGITAL PAYMENTS AND BANKING

1. PAYMENT SYSTEM REGULATIONS:

A. Fund Transfer Limits:
   - NEFT: No limit
   - RTGS: Minimum Rs 2 lakh
   - IMPS: Up to Rs 5 lakh
   - UPI: Rs 1 lakh per transaction

B. KYC Requirements:
   - Full KYC for accounts above Rs 50,000
   - Video KYC allowed
   - Periodic updation mandatory
   - Aadhaar linkage optional

2. INVESTOR PROTECTION:
   - Unauthorized transaction reporting: Within 3 days
   - Zero liability if reported immediately
   - Limited liability based on delay
   - Grievance redressal within 30 days

3. DIGITAL BANKING SECURITY:
   - 2-factor authentication mandatory
   - OTP validity: 3-5 minutes
   - Password complexity requirements
   - Regular security audits required
""",

        "nse/investor_charter.txt": """
NSE INVESTOR CHARTER AND RIGHTS

1. INVESTOR RIGHTS:
   - Right to receive contract notes within 24 hours
   - Right to receive funds/securities on settlement
   - Right to grievance redressal
   - Right to investor protection fund

2. BROKER OBLIGATIONS:
   - Provide risk disclosure document
   - Maintain client records
   - Segregate client securities
   - Provide regular statements

3. COMPLAINT MECHANISM:
   Level 1: Broker grievance cell (7 days)
   Level 2: NSE IGC - ignse@nse.co.in (15 days)
   Level 3: SEBI SCORES portal (30 days)
   Level 4: SEBI Ombudsman
   
4. INVESTOR PROTECTION FUND:
   - Covers broker default
   - Up to Rs 25 lakh per investor
   - Claims within 3 years
   - Documentation required
""",

        "common_practices.txt": """
COMMON MARKET PRACTICES AND INVESTOR BEHAVIOR

1. BEGINNER INVESTOR PRACTICES:
   - Start with blue-chip stocks
   - Invest through SIPs in mutual funds
   - Avoid F&O for first 2 years
   - Paper trade before real money
   - Typical allocation: 60% equity, 40% debt

2. RISK MANAGEMENT:
   - Never invest borrowed money
   - Diversify across 15-20 stocks
   - Stop loss typically at 5-8%
   - Book partial profits at 20-25%
   - Keep 6 months emergency fund

3. TAX PLANNING:
   - LTCG tax saving by holding >1 year
   - Tax loss harvesting in March
   - ELSS for 80C deduction
   - Dividend reinvestment common

4. COMMON MISTAKES TO AVOID:
   - Trading on tips/rumors
   - Panic selling in crashes
   - Averaging losing positions
   - Over-leveraging in F&O
   - Ignoring fundamentals

5. BROKER SELECTION:
   - Full-service vs Discount brokers
   - Typical brokerage: 0.01% to 0.5%
   - Hidden charges to check
   - Technology platform importance
"""
    }
    
    # Create documents
    created = 0
    for filepath, content in documents.items():
        full_path = RAW_DIR / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')
        logger.info(f"✅ Created: {filepath}")
        created += 1
    
    print(f"\n✅ Created {created} sample documents in {RAW_DIR}")
    print("\nNext steps:")
    print("1. Run: python data_processor.py")
    print("2. Then run: python app.py")

def download_real_documents():
    """Download real SEBI regulatory PDFs with better reliability"""
    pdfs = pdfs = {
    "sebi/SEBI_Investor_Charter.pdf":
        "https://www.sebi.gov.in/sebi_data/commondocs/nov-2021/InvestorCharter_p.pdf",

    "sebi/SEBI_LODR_Regulations.pdf":
        "https://www.sebi.gov.in/sebi_data/commondocs/jan-2023/LODRRegulations.pdf"
}


    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    print("\n📥 Attempting to download real PDFs...")
    downloaded = 0

    for filepath, url in pdfs.items():
        try:
            full_path = RAW_DIR / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)

            response = requests.get(url, headers=headers, timeout=30, verify=True)
            if response.status_code == 200:
                full_path.write_bytes(response.content)
                logger.info(f"✅ Downloaded: {filepath}")
                downloaded += 1
            else:
                logger.warning(f"❌ Failed to download {filepath} (Status Code: {response.status_code})")
        except Exception as e:
            logger.error(f"⚠️ Error downloading {filepath}: {e}")

    if downloaded > 0:
        print(f"\n✅ Successfully downloaded {downloaded} PDF(s)")
    else:
        print("\n⚠️ Could not download PDFs. Try verifying URLs manually.")

if __name__ == "__main__":
    print("="*60)
    print("📄 Adding Sample Documents to RAG System")
    print("="*60)
    
    # Create text documents
    create_sample_documents()
    
    # Try to download PDFs (optional)
    try:
        download_real_documents()
    except:
        print("⚠️ PDF download skipped")
    
    print("\n✅ Documents ready for processing!")