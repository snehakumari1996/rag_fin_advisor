# DOWNLOAD MORE REGULATORY DOCUMENTS TO GOOGLE DRIVE
# Run this after the main setup to add more documents

from pathlib import Path
import requests
import logging
from tqdm import tqdm
from datetime import datetime

# Setup paths
DRIVE_BASE = Path("/content/drive/MyDrive/RAG_fin_iter1")
RAW_DIR = DRIVE_BASE / "data" / "raw"

# Create subdirectories for different sources
dirs = ["sebi", "rbi", "nse", "bse", "others"]
for d in dirs:
    (RAW_DIR / d).mkdir(parents=True, exist_ok=True)

# Setup logging
log_file = DRIVE_BASE / "logs" / f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def download_file(url: str, filepath: Path, timeout: int = 30) -> bool:
    """Download a file with progress bar"""
    try:
        if filepath.exists():
            logger.info(f"Already exists: {filepath.name}")
            return True
            
        logger.info(f"Downloading: {filepath.name}")
        response = requests.get(url, stream=True, timeout=timeout, verify=False)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filepath, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=filepath.name) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        logger.info(f"✅ Downloaded: {filepath.name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

# SEBI Documents
print("\n📥 Downloading SEBI Documents...")
sebi_docs = {
    # Regulations
    "SEBI_LODR_Regulations_2015.pdf": "https://www.sebi.gov.in/legal/regulations/jan-2023/sebi-listing-obligations-and-disclosure-requirements-regulations-2015_67834.pdf",
    "SEBI_PIT_Regulations_2015.pdf": "https://www.sebi.gov.in/legal/regulations/feb-2023/sebi-prohibition-of-insider-trading-regulations-2015_68432.pdf",
    "SEBI_Buyback_Regulations_2018.pdf": "https://www.sebi.gov.in/legal/regulations/mar-2023/sebi-buy-back-of-securities-regulations-2018_69123.pdf",
    
    # Important Circulars
    "Risk_O_Meter_Guidelines.pdf": "https://www.sebi.gov.in/legal/circulars/jan-2024/risk-o-meter-guidelines_78134.pdf",
    "Investor_Charter_2024.pdf": "https://www.sebi.gov.in/sebi_data/attachdocs/may-2024/1716200123456.pdf",
    
    # Guidelines
    "KYC_Guidelines.pdf": "https://www.sebi.gov.in/sebi_data/attachdocs/1484820185836.pdf",
}

for filename, url in sebi_docs.items():
    download_file(url, RAW_DIR / "sebi" / filename)

# RBI Documents
print("\n📥 Downloading RBI Documents...")
rbi_docs = {
    # Master Directions
    "RBI_KYC_Master_Direction.pdf": "https://rbidocs.rbi.org.in/rdocs/notification/PDFs/NT1461E6E3E19704544A6A92059C6DE035267.PDF",
    "RBI_Digital_Payment_Security.pdf": "https://rbidocs.rbi.org.in/rdocs/notification/PDFs/NOTI103472E6A0E04EC49E8BD6D91CCAB4BCFC7.PDF",
    
    # FAQs
    "RBI_FAQs_Digital_Payments.pdf": "https://rbidocs.rbi.org.in/rdocs/FAQs/PDFs/FAQDIGITALPAYMENTS2903202398EFE1B3B41E40C0BF7F47F4B9775D62.PDF",
}

for filename, url in rbi_docs.items():
    download_file(url, RAW_DIR / "rbi" / filename)

# Create comprehensive text documents with important information
print("\n📝 Creating comprehensive guide documents...")

# Create a master guide
master_guide = """
COMPREHENSIVE INDIAN STOCK MARKET REGULATIONS GUIDE

TABLE OF CONTENTS:
1. Account Opening Requirements
2. Trading Types and Risks
3. Compliance and Legal Framework
4. Prohibited Activities and Penalties
5. Investor Rights and Grievance Redressal
6. Taxation Guidelines
7. Best Practices for Investors

=================================================================
1. ACCOUNT OPENING REQUIREMENTS
=================================================================

A. DEMAT ACCOUNT DOCUMENTS:

Essential Documents (All Mandatory):
1. PAN Card
   - Mandatory for all financial transactions
   - Required even for minor's account
   - Must be self-attested

2. Identity Proof (Any One):
   - Aadhaar Card (preferred for e-KYC)
   - Passport
   - Voter ID Card
   - Driving License
   - NREGA Card
   - National Population Register

3. Address Proof (Any One):
   - Aadhaar Card
   - Passport
   - Voter ID Card
   - Driving License
   - Bank Statement (not older than 3 months)
   - Utility Bill (not older than 3 months)
   - Rent Agreement (registered)

4. Bank Proof:
   - Cancelled cheque with name printed
   - Bank Statement showing account number and IFSC
   - Bank Passbook (first page)

5. Income Proof (For F&O Segment):
   - Salary Slip (latest 3 months)
   - Bank Statement (6 months)
   - ITR with acknowledgment
   - Form 16
   - Net Worth Certificate (CA certified)
   - Demat Holding Statement

B. TYPES OF DEMAT ACCOUNTS:

1. Regular Demat Account
   - For Indian residents
   - Full trading rights
   - Can hold all securities

2. BSDA (Basic Services Demat Account)
   - For small investors
   - Holdings up to Rs 2 lakhs
   - Lower or nil AMC charges

3. Repatriable Demat Account
   - For NRIs
   - Funds can be transferred abroad
   - Requires NRE/NRO bank account

4. Non-Repatriable Demat Account
   - For NRIs
   - Funds remain in India
   - Lower documentation

5. Corporate Demat Account
   - For companies, firms, trusts
   - Additional documents required
   - Board resolution needed

=================================================================
2. TRADING TYPES AND RISKS
=================================================================

A. CASH SEGMENT TRADING:

1. Delivery Trading (CNC - Cash and Carry)
   Risk Level: LOW
   - Buy today, sell anytime
   - 100% margin required
   - No leverage
   - Shares credited to demat
   - Best for: Beginners, long-term investors
   - Settlement: T+2 days

2. Intraday Trading (MIS - Margin Intraday Square-off)
   Risk Level: HIGH
   - Buy and sell same day
   - Leverage up to 5x (varies by broker)
   - Auto square-off at 3:20 PM
   - No delivery of shares
   - Best for: Experienced traders
   - Can lose more than invested

3. BTST/ATST (Buy/Acquire Today Sell Tomorrow)
   Risk Level: MEDIUM
   - Sell before shares hit demat
   - Risk of auction if seller defaults
   - DP charges apply

B. DERIVATIVES SEGMENT (F&O):

1. Futures Trading
   Risk Level: VERY HIGH
   - Contract to buy/sell at future date
   - High leverage (5-6x)
   - Daily MTM settlement
   - Can lose entire capital
   - Lot size trading only
   - Physical delivery in stock futures

2. Options Trading
   Risk Level: VERY HIGH to EXTREME
   
   Call Options (Right to buy):
   - Buyer: Limited loss (premium)
   - Seller: Unlimited loss potential
   
   Put Options (Right to sell):
   - Buyer: Limited loss (premium)  
   - Seller: High loss potential

   Important: 
   - Time decay affects premium
   - Volatility impacts pricing
   - Most options expire worthless
   - Requires approval and income proof

3. Margin Trading Facility (MTF)
   Risk Level: HIGH
   - Borrow money to buy shares
   - Interest charged daily
   - Shares pledged with broker
   - Margin calls if value drops
   - Can lose more than invested

=================================================================
3. COMPLIANCE AND LEGAL FRAMEWORK
=================================================================

A. KEY REGULATIONS:

1. SEBI Act, 1992
   - Establishes SEBI's authority
   - Protects investor interests
   - Regulates securities market

2. Securities Contract Regulation Act (SCRA), 1956
   - Governs stock exchanges
   - Defines securities
   - Contract regulations

3. Depositories Act, 1996
   - Governs demat system
   - CDSL and NSDL operations
   - Electronic holding of securities

4. Companies Act, 2013
   - Corporate governance
   - Insider trading provisions
   - Disclosure requirements

B. IMPORTANT SEBI REGULATIONS:

1. SEBI (LODR) Regulations, 2015
   - Listing obligations
   - Disclosure requirements
   - Corporate governance norms

2. SEBI (PIT) Regulations, 2015
   - Prohibition of Insider Trading
   - UPSI definitions
   - Trading window closures
   - Penalties and prosecution

3. SEBI (SAST) Regulations, 2011
   - Takeover regulations
   - Open offer requirements
   - Disclosure obligations

=================================================================
4. PROHIBITED ACTIVITIES AND PENALTIES
=================================================================

A. STRICTLY ILLEGAL ACTIVITIES:

1. Insider Trading
   Definition: Trading based on UPSI (Unpublished Price Sensitive Information)
   Examples:
   - Trading on merger news before announcement
   - Using financial results before disclosure
   - Tips from company insiders
   
   Penalties:
   - Monetary: Up to Rs 25 crores or 3x profit
   - Criminal: Up to 10 years imprisonment
   - Ban from markets
   - Disgorgement of profits

2. Market Manipulation
   Types:
   - Circular Trading: Trading among connected parties
   - Pump and Dump: Artificial price increase then sell
   - Spoofing: Fake orders to mislead
   - Layering: Multiple orders at different prices
   
   Penalties:
   - Up to Rs 25 crores
   - Criminal prosecution
   - Market ban

3. Front Running
   Definition: Trading ahead of large client orders
   Applies to: Brokers, employees, advisors
   
   Penalties:
   - License cancellation
   - Monetary penalties
   - Criminal action

4. Fraudulent and Unfair Trade Practices
   Includes:
   - False company information
   - Misleading statements
   - Price rigging
   - Creating false market
   
   Penalties:
   - Severe monetary penalties
   - Imprisonment
   - Permanent market ban

B. REGULATORY VIOLATIONS:

1. KYC Violations
   - Incomplete documentation
   - False information
   - Identity theft
   Penalty: Account freeze, legal action

2. Position Limit Violations
   - Exceeding derivative limits
   - Client level limits
   - Market-wide limits
   Penalty: Penalty, position square-off

3. Margin Violations
   - Short margin collection
   - Inadequate collateral
   Penalty: Interest, penalties, square-off

=================================================================
5. INVESTOR RIGHTS AND GRIEVANCE REDRESSAL
=================================================================

A. INVESTOR RIGHTS:

1. Right to receive:
   - Contract notes within 24 hours
   - Funds/securities on time
   - Account statements
   - Grievance redressal

2. Right to information:
   - Brokerage and charges
   - Risk disclosure documents
   - Rights and obligations
   - Broker registration details

B. GRIEVANCE REDRESSAL HIERARCHY:

Level 1: Broker/DP Grievance Cell
- Timeline: 30 days
- Email/written complaint
- Complaint acknowledgment mandatory

Level 2: Stock Exchange
- If broker fails to resolve
- NSE: ignse@nse.co.in
- BSE: is@bseindia.com
- Timeline: 15 days

Level 3: SEBI SCORES
- Online portal: scores.sebi.gov.in
- Track complaint status
- Timeline: 30 days

Level 4: SEBI Ombudsman
- For amounts up to Rs 1 crore
- Free service
- Final appellate authority

Level 5: Securities Appellate Tribunal (SAT)
- Appeals against SEBI orders
- Located in Mumbai
- Legal representation advisable

=================================================================
6. TAXATION GUIDELINES
=================================================================

A. EQUITY TAXATION:

1. Long Term Capital Gains (LTCG)
   - Holding > 12 months
   - Tax: 10% on gains above Rs 1 lakh
   - No indexation benefit

2. Short Term Capital Gains (STCG)
   - Holding < 12 months
   - Tax: 15% flat
   - Plus surcharge and cess

3. Dividend Taxation
   - Taxable in investor's hands
   - As per income slab
   - TDS if > Rs 5,000

B. F&O TAXATION:

1. Business Income
   - Taxed as per slab
   - Can claim expenses
   - Audit if turnover > Rs 10 crore
   - Presumptive tax option available

2. Loss Set-off
   - Can carry forward 8 years
   - Set-off against business income
   - Speculation loss restrictions

C. SECURITIES TRANSACTION TAX (STT):
   - Equity Delivery: 0.1% on both legs
   - Equity Intraday: 0.025% on sell
   - Options: 0.05% on premium
   - Futures: 0.01% on sell

=================================================================
7. BEST PRACTICES FOR INVESTORS
=================================================================

A. BEFORE YOU START:

1. Education First
   - Understand products
   - Learn risk management
   - Study market basics
   - Paper trade initially

2. Document Safety
   - Never share passwords
   - Check trade confirmations
   - Verify contract notes
   - Keep records for 7 years

3. Broker Selection
   - Check SEBI registration
   - Compare charges
   - Read reviews
   - Understand services

B. WHILE TRADING:

1. Risk Management
   - Never invest borrowed money
   - Diversify portfolio
   - Use stop losses
   - Avoid over-leveraging
   - Start small

2. Discipline
   - Have a trading plan
   - Maintain trading journal
   - Control emotions
   - Avoid tips and rumors
   - Regular profit booking

3. Compliance
   - Timely tax payments
   - Accurate ITR filing
   - Maintain documentation
   - Report suspicious activities

C. RED FLAGS TO AVOID:

1. Guaranteed Returns
   - No guaranteed profits in markets
   - Avoid assured return schemes
   - Report such operators

2. Unregistered Entities
   - Only trade through SEBI registered
   - Avoid unregistered advisors
   - Check credentials online

3. Pressure Tactics
   - Take your time
   - Don't rush decisions
   - Avoid FOMO trading
   - Research thoroughly

IMPORTANT CONTACTS:

SEBI Helpline: 1800 266 7575
NSE: 1800 266 0050
BSE: 1800 103 4533
SCORES Portal: scores.sebi.gov.in

Remember: Markets can be rewarding but carry significant risks. 
Invest only what you can afford to lose. When in doubt, consult 
a SEBI-registered investment advisor.

=================================================================
END OF GUIDE
=================================================================
"""

# Save the master guide
guide_path = RAW_DIR / "others" / "MASTER_REGULATIONS_GUIDE.txt"
guide_path.write_text(master_guide, encoding='utf-8')
logger.info("✅ Created master regulations guide")

# Create FAQ document
faq_content = """
FREQUENTLY ASKED QUESTIONS - INDIAN STOCK MARKET

Q1: What is the minimum amount needed to start investing?
A: You can start with as little as Rs 500. Many brokers offer zero account opening fees and you can buy fractional shares in mutual funds.

Q2: Can I trade without a demat account?
A: No, a demat account is mandatory for trading in shares. For mutual funds, you can invest without demat through AMC websites.

Q3: What happens if my broker goes bankrupt?
A: Your shares are held by depositories (CDSL/NSDL), not brokers. They remain safe. Cash may be at risk beyond insurance limits.

Q4: Is intraday trading halal/permissible?
A: This depends on religious interpretation. Some consider it speculation (gambling), others view it as permissible business. Consult religious authorities.

Q5: Can I use my spouse's/parent's demat account?
A: No, this is illegal. Each person must trade through their own account only. Using others' accounts can lead to penalties.

Q6: What is pattern day trading rule in India?
A: India doesn't have PDT rule like USA. You can do unlimited intraday trades regardless of capital.

Q7: Can I short sell in delivery?
A: No, short selling is only allowed in intraday and F&O. You cannot short sell in delivery/CNC.

Q8: What happens if I don't square off intraday position?
A: Broker will auto square-off around 3:20 PM. If failed, it converts to delivery. You may face penalties and auction charges.

Q9: Are stock tips on WhatsApp/Telegram legal?
A: Only SEBI-registered advisors can give recommendations. Most WhatsApp/Telegram tips are illegal and often scams.

Q10: Can NRI trade in F&O?
A: No, NRIs cannot trade in F&O segment. They can only trade in cash segment (delivery basis).

Q11: Is algo trading legal for retail investors?
A: Yes, but through broker-approved algos only. Direct API access needs approval. Unauthorized algo trading is illegal.

Q12: What is ASM and GSM?
A: Additional Surveillance Measure and Graded Surveillance Measure - SEBI mechanisms to control speculation in specific stocks.

Q13: Can I cancel/modify order after market hours?
A: You can place/modify/cancel AMO (After Market Orders) between 3:30 PM to 9:15 AM next day.

Q14: What is T+2 settlement?
A: Shares are credited/debited after 2 working days. If you buy Monday, shares credit Wednesday.

Q15: Are profits from trading tax-free after 1 year?
A: No. Equity delivery held >1 year has 10% LTCG tax above Rs 1 lakh. F&O is always business income taxed per slab.

Q16: Can I trade during muhurat trading?
A: Yes, special 1-hour session on Diwali. Normal rules apply. Symbolic trading, usually low volumes.

Q17: What is circuit filter/limit?
A: Price bands to control volatility. Stock halts if hits circuit. Ranges from 2% to 20% based on stock category.

Q18: Is margin funding interest tax deductible?
A: Yes, if you declare trading as business income. Not deductible for investment income.

Q19: Can I pledge shares for margin?
A: Yes, but only approved securities. Haircut applies. Interest charged on margin used.

Q20: What is peak margin penalty?
A: Penalty for collecting less than required margin. Brokers must collect full margin upfront in phases.

Q21: Are US stocks taxable in India?
A: Yes, capital gains taxable in India. Tax credit available for US tax paid under DTAA.

Q22: What is physical settlement in F&O?
A: Stock F&O contracts result in actual delivery if held till expiry. Index options are cash settled.

Q23: Can I trade in my company's shares?
A: Yes, but follow insider trading rules. No trading during window closure. Report to compliance officer.

Q24: What are penny stocks? Are they illegal?
A: Shares trading below Rs 10. Not illegal but highly risky. Often manipulated. SEBI monitors closely.

Q25: Is cryptocurrency trading legal?
A: Legal but unregulated. Profits taxed at 30% + 1% TDS. No loss set-off allowed. Not under SEBI purview.

REMEMBER: When in doubt, always consult SEBI registered professionals or official sources. Markets involve risk - invest wisely.
"""

# Save FAQ
faq_path = RAW_DIR / "others" / "STOCK_MARKET_FAQ.txt"
faq_path.write_text(faq_content, encoding='utf-8')
logger.info("✅ Created FAQ document")

print("\n" + "="*50)
print("✅ Document Download Complete!")
print("="*50)
print(f"\n📁 Documents saved to: {RAW_DIR}")
print("\n📊 Summary:")
print(f"- SEBI Documents: {len(list((RAW_DIR / 'sebi').glob('*')))}")
print(f"- RBI Documents: {len(list((RAW_DIR / 'rbi').glob('*')))}")
print(f"- Other Documents: {len(list((RAW_DIR / 'others').glob('*')))}")
print("\n💡 Next Steps:")
print("1. Run the main RAG system to process these documents")
print("2. The system will automatically detect and index new documents")
print("3. All processed data will be saved to Google Drive")

# Update the cache to trigger reprocessing
cache_file = DRIVE_BASE / "data" / "cache" / "document_cache.json"
if cache_file.exists():
    import json
    with open(cache_file, 'r') as f:
        cache = json.load(f)
    cache["new_documents_added"] = True
    cache["last_download"] = datetime.now().isoformat()
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)
    print("\n✅ Cache updated - new documents will be processed")