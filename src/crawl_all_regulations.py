# web_crawler.py - Web Crawler for Regulatory Documents
import os
import time
import logging
import requests
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import RAW_DIR, CACHE_DIR, SAMPLE_DOCUMENTS

logger = logging.getLogger(__name__)

class DocumentCrawler:
    """Crawler for downloading regulatory documents"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = self._create_session()
        self.download_cache_file = CACHE_DIR / "download_cache.json"
        self.load_download_cache()
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
        session = requests.Session()
        session.headers.update({
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })
        return session
    
    def load_download_cache(self):
        """Load download cache"""
        if self.download_cache_file.exists():
            try:
                with open(self.download_cache_file, 'r') as f:
                    self.download_cache = json.load(f)
            except:
                self.download_cache = {"downloaded": [], "failed": []}
        else:
            self.download_cache = {"downloaded": [], "failed": []}
    
    def save_download_cache(self):
        """Save download cache"""
        with open(self.download_cache_file, 'w') as f:
            json.dump(self.download_cache, f, indent=2)
    
    def download_file(self, url: str, filepath: Path, max_retries: int = 3) -> bool:
        """Download a file with retry logic"""
        # Check cache
        if url in self.download_cache["downloaded"]:
            logger.info(f"Already downloaded: {filepath.name}")
            return True
        
        if url in self.download_cache["failed"]:
            logger.info(f"Skipping previously failed: {filepath.name}")
            return False
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Downloading {filepath.name} (attempt {attempt + 1}/{max_retries})")
                
                # Update user agent
                self.session.headers["User-Agent"] = self.ua.random
                
                response = self.session.get(url, timeout=30, verify=False)
                response.raise_for_status()
                
                # Save file
                filepath.write_bytes(response.content)
                
                # Verify file size
                if filepath.stat().st_size < 1000:
                    logger.warning(f"File too small: {filepath.name}")
                    filepath.unlink()
                    continue
                
                # Update cache
                self.download_cache["downloaded"].append(url)
                self.save_download_cache()
                
                logger.info(f"✅ Downloaded: {filepath.name}")
                return True
                
            except Exception as e:
                logger.error(f"Download failed (attempt {attempt + 1}): {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
        
        # Mark as failed
        self.download_cache["failed"].append(url)
        self.save_download_cache()
        return False
    
    def download_sample_documents(self) -> Dict[str, int]:
        """Download sample documents from config"""
        stats = {"success": 0, "failed": 0, "skipped": 0}
        
        for category, urls in SAMPLE_DOCUMENTS.items():
            category_dir = RAW_DIR / category
            
            for filename, url in urls.items():
                filepath = category_dir / filename
                
                if filepath.exists():
                    stats["skipped"] += 1
                    continue
                
                if self.download_file(url, filepath):
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
        
        return stats
    
    def create_regulatory_documents(self):
        """Create comprehensive regulatory documents locally"""
        documents = {
            "sebi/SEBI_Regulations_Guide.txt": self._create_sebi_guide(),
            "rbi/RBI_Guidelines.txt": self._create_rbi_guide(),
            "general/Stock_Market_FAQ.txt": self._create_faq(),
            "general/Trading_Best_Practices.txt": self._create_best_practices()
        }
        
        created = 0
        for filepath, content in documents.items():
            full_path = RAW_DIR / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            if not full_path.exists():
                full_path.write_text(content, encoding='utf-8')
                logger.info(f"✅ Created: {filepath}")
                created += 1
        
        return created
    
    def _create_sebi_guide(self) -> str:
        """Create SEBI regulations guide"""
        return """
SEBI COMPREHENSIVE REGULATIONS GUIDE

1. SEBI (LISTING OBLIGATIONS AND DISCLOSURE REQUIREMENTS) REGULATIONS, 2015

Key Provisions:
- Quarterly financial results within 45 days
- Annual report within 21 days before AGM
- Material events disclosure within 24 hours
- Board meeting intimation 2-11 days prior
- Shareholding pattern every quarter

Penalties for Non-Compliance:
- Warning letter
- Monetary fine up to Rs 1 crore
- Suspension of trading
- Freezing of promoter holdings

2. SEBI (PROHIBITION OF INSIDER TRADING) REGULATIONS, 2015

Definitions:
- UPSI: Unpublished Price Sensitive Information
- Insider: Connected person with access to UPSI
- Trading Window: Period when trading is allowed

Key Provisions:
- Trading window closure during UPSI
- Pre-clearance for trades above threshold
- Disclosure of trades within 2 days
- Maintenance of structured digital database

Penalties:
- Minimum: Rs 10 lakhs
- Maximum: Rs 25 crores or 3x profit
- Criminal prosecution up to 10 years

3. SEBI (SUBSTANTIAL ACQUISITION OF SHARES AND TAKEOVERS) REGULATIONS, 2011

Thresholds:
- 25% - Mandatory open offer
- 5% - Creeping acquisition limit per year
- 75% - Delisting threshold

Open Offer Requirements:
- Minimum 26% of total shares
- Price: Higher of multiple parameters
- Detailed public announcement
- SEBI approval required

4. SEBI (BUYBACK OF SECURITIES) REGULATIONS, 2018

Methods:
- Tender offer through stock exchange
- Open market through stock exchange
- Book building process

Limits:
- 25% of paid-up capital + free reserves
- Debt-equity ratio post buyback ≤ 2:1
- Gap of 1 year between buybacks

5. SEBI (MUTUAL FUNDS) REGULATIONS, 1996

Key Requirements:
- Minimum net worth Rs 50 crores for AMC
- Independent trustee company
- Custodian separate from sponsor
- NAV disclosure daily
- Portfolio disclosure monthly

Investment Restrictions:
- Single company: 10% of NAV
- Group companies: 25% of NAV
- Unlisted equity: 10% of NAV
- Single sector: 25% (except sector funds)

6. SEBI (PORTFOLIO MANAGERS) REGULATIONS, 2020

Eligibility:
- Net worth: Rs 5 crores
- Experience: 10 years in financial services
- Certification: NISM Series VIII

Client Requirements:
- Minimum investment: Rs 50 lakhs
- Discretionary/Non-discretionary/Advisory
- Disclosure of conflicts of interest
- Quarterly performance reporting

7. SEBI (INVESTMENT ADVISERS) REGULATIONS, 2013

Registration Requirements:
- Individual: Net worth Rs 5 lakhs, NISM certification
- Body Corporate: Net worth Rs 50 lakhs
- LLP/Partnership: Net worth Rs 50 lakhs

Compliance:
- Risk profiling of clients mandatory
- Suitability assessment required
- Written advisory agreement
- Segregation of advisory and distribution

8. SEBI (ALTERNATIVE INVESTMENT FUNDS) REGULATIONS, 2012

Categories:
- Category I: Start-up, social venture, SME funds
- Category II: Private equity, debt funds
- Category III: Hedge funds, PIPE funds

Requirements:
- Minimum corpus: Rs 20 crores
- Minimum investment: Rs 1 crore
- Manager contribution: 2.5% or Rs 5 crores
- Defined investment strategy

9. SEBI (FOREIGN PORTFOLIO INVESTORS) REGULATIONS, 2019

Categories:
- Category I: Government funds, regulated entities
- Category II: Broad based funds, university funds

Investment Limits:
- Single FPI: 10% of paid-up capital
- All FPIs combined: 24% (can increase to sectoral cap)
- Government securities: 30% of outstanding
- Corporate bonds: 15% of outstanding

10. SEBI (CREDIT RATING AGENCIES) REGULATIONS, 1999

Requirements:
- Net worth: Rs 25 crores
- Promoter eligibility criteria
- Independent board structure
- Disclosure of rating methodology

Compliance:
- Half-yearly results review
- Annual surveillance
- Disclosure of rating rationale
- Tracking rating performance

INVESTOR PROTECTION MEASURES:

1. Investor Protection Fund
2. Investor Service Centers
3. SCORES complaint portal
4. Arbitration mechanism
5. Investor awareness programs
6. SEBI Complaint Redress System (SCORES)
7. ODR (Online Dispute Resolution) platform

RECENT UPDATES (2023-2024):

1. T+1 Settlement Cycle
2. ASBA mandatory for all public issues
3. Enhanced ESG disclosures
4. Cybersecurity framework
5. Social Stock Exchange regulations
6. REITs and InvITs reforms
"""
    
    def _create_rbi_guide(self) -> str:
        """Create RBI guidelines"""
        return """
RBI MASTER DIRECTIONS AND GUIDELINES

1. KNOW YOUR CUSTOMER (KYC) MASTER DIRECTION

Customer Due Diligence:
- Identity proof verification
- Address proof verification
- Recent photograph
- PAN mandatory for all

Risk Categorization:
- Low Risk: Salaried, government employees
- Medium Risk: Business entities, high net worth
- High Risk: PEPs, shell companies, trusts

Periodic Updation:
- High Risk: 2 years
- Medium Risk: 8 years
- Low Risk: 10 years

Enhanced Due Diligence:
- Source of funds verification
- Financial statements review
- Field verification if required
- Senior management approval

2. FOREIGN EXCHANGE MANAGEMENT ACT (FEMA) GUIDELINES

Permissible Capital Account Transactions:
- Investment in securities
- Investment in properties
- Guarantees by residents
- Loans and borrowings
- Export/Import of currency

Liberalized Remittance Scheme (LRS):
- Limit: USD 250,000 per financial year
- Permitted: Education, travel, investment
- Prohibited: Margin trading, lottery
- TCS: 5% above Rs 7 lakhs (20% without PAN)

Foreign Investment in India:
- FDI: Through automatic/approval route
- FPI: Through registered entities
- Sectoral caps applicable
- Pricing guidelines for transfers

3. DIGITAL PAYMENT SECURITY CONTROLS

Mandatory Requirements:
- 2-factor authentication
- End-to-end encryption
- Transaction alerts mandatory
- Cooling period for beneficiary addition
- Risk-based transaction limits

Customer Protection:
- Zero liability for unauthorized transactions
- Limited liability with conditions
- Reversal timelines defined
- Complaint resolution within 30 days

4. NBFC REGULATIONS

Categories:
- NBFC-ICC (Investment and Credit)
- NBFC-MFI (Microfinance)
- NBFC-Factors
- NBFC-P2P

Capital Requirements:
- Minimum NOF: Rs 2 crores
- Tier 1 Capital: 10%
- Capital Adequacy: 15%
- Leverage Ratio: 7 times

Prudential Norms:
- Income recognition on 90 DPD
- Asset classification norms
- Provisioning requirements
- Corporate governance standards

5. PRIORITY SECTOR LENDING

Targets for Banks:
- Total: 40% of ANBC
- Agriculture: 18%
- Micro Enterprises: 7.5%
- Export Credit: 2%

Eligible Categories:
- Agriculture
- Micro, Small and Medium Enterprises
- Export Credit
- Education
- Housing
- Social Infrastructure
- Renewable Energy

6. BASEL III NORMS

Capital Requirements:
- Common Equity Tier 1: 5.5%
- Tier 1 Capital: 7%
- Total Capital: 9%
- Capital Conservation Buffer: 2.5%

Liquidity Requirements:
- Liquidity Coverage Ratio: 100%
- Net Stable Funding Ratio: 100%
- Liquidity risk monitoring tools
- Stress testing requirements

7. GUIDELINES ON DIGITAL LENDING

Mandatory Requirements:
- Direct disbursement to borrower account
- No automatic debit without consent
- Cooling off/look-up period
- Key Fact Statement mandatory
- Grievance redressal mechanism

Prohibited Practices:
- Lending through unauthorized apps
- Charging of hidden fees
- Access to unnecessary phone data
- Recovery through unauthorized agents

8. INTEREST RATE GUIDELINES

Base Rate System:
- All loans linked to external benchmark
- Reset at least once in 3 months
- Spread over benchmark fixed
- Transparent methodology

MCLR (Marginal Cost of Funds):
- Tenure-based calculation
- Components defined by RBI
- Monthly review required
- Switch option to borrowers

9. STRESSED ASSET RESOLUTION

Framework Components:
- Special Mention Accounts (SMA)
- Early warning signals
- Resolution plans within timelines
- IBC reference for defaults

Categories:
- SMA-0: 1-30 days overdue
- SMA-1: 31-60 days overdue
- SMA-2: 61-90 days overdue
- NPA: 90+ days overdue

10. CUSTOMER SERVICE GUIDELINES

Banking Ombudsman Scheme:
- Grounds for complaint defined
- Time limits for resolution
- Appealable to RBI
- Award binding on banks

Service Standards:
- Account opening TAT
- Loan processing timelines
- Complaint resolution matrix
- Compensation policy

RECENT CIRCULARS (2023-2024):

1. Card tokenization mandatory
2. Compromise settlement revised
3. Default Loss Guarantee in digital lending
4. Climate risk disclosures
5. Regulatory sandbox for fintech
"""
    
    def _create_faq(self) -> str:
        """Create comprehensive FAQ"""
        return """
FREQUENTLY ASKED QUESTIONS - INDIAN STOCK MARKET

ACCOUNT OPENING:

Q: What is the minimum age to open a demat account?
A: 18 years. Minors can open through guardians.

Q: Can I have multiple demat accounts?
A: Yes, but not with the same depository participant (DP).

Q: Is Aadhaar mandatory for demat account?
A: Yes, for new accounts. Existing can continue with PAN.

Q: What if I don't have income proof for F&O?
A: You can provide bank statements showing regular deposits or net worth certificate.

Q: Can NRI open trading account?
A: Yes, but only for delivery-based trades. No F&O allowed.

TRADING RELATED:

Q: What happens if I sell shares I don't have?
A: It becomes short selling. Must cover same day or face auction penalty.

Q: Can I cancel order after market hours?
A: Yes, AMO orders can be modified/cancelled till 9:15 AM next day.

Q: What is circuit limit?
A: Price band to control volatility. Ranges from 2% to 20%.

Q: Why was my order rejected?
A: Common reasons: Insufficient margin, price outside circuit, stock in ban period.

Q: What is T+2 settlement?
A: Shares credited/debited after 2 working days of trade.

CHARGES AND TAXES:

Q: Are there hidden charges in trading?
A: All charges must be disclosed. Check contract note for details.

Q: How is intraday taxed differently?
A: Treated as speculative income if not F&O. Taxed as per slab.

Q: What is STT?
A: Securities Transaction Tax. 0.1% on equity delivery, 0.025% on intraday sell.

Q: Can I claim trading losses?
A: Yes. Carry forward for 8 years (4 for speculative).

Q: Is algo trading taxed differently?
A: No, same tax treatment based on holding period.

COMPLIANCE AND LEGAL:

Q: Is penny stock trading illegal?
A: Not illegal but highly risky. SEBI monitors for manipulation.

Q: Can I trade in my spouse's account?
A: No, each person must trade in own account only.

Q: What if broker doesn't pay my money?
A: Complain to exchange, then SEBI. Investor protection fund available.

Q: Are trading tips legal?
A: Only from SEBI registered advisors. Unregistered tips are illegal.

Q: Can I trade during insider trading window closure?
A: Only if you're not an insider of that company.

MUTUAL FUNDS:

Q: Difference between regular and direct plans?
A: Direct has no distributor commission. 0.5-1% lower expense ratio.

Q: Can I invest without demat?
A: Yes, through AMC website or MF utilities.

Q: What is exit load?
A: Penalty for early redemption. Usually 1% if redeemed within 1 year.

Q: Are mutual fund returns guaranteed?
A: No. All investments subject to market risks.

Q: How are MF gains taxed?
A: Equity funds: 15% STCG, 10% LTCG. Debt funds: As per slab.

F&O TRADING:

Q: What is lot size?
A: Minimum quantity to trade. Varies by stock, typically Rs 5-10 lakhs.

Q: Can losses be unlimited in options?
A: For option sellers yes. Buyers' loss limited to premium.

Q: What is physical settlement?
A: Stock F&O results in actual delivery if held till expiry.

Q: What happens if I don't square off?
A: Futures: Physical settlement. Options: Auto-exercised if ITM.

Q: Is F&O suitable for beginners?
A: No. Requires experience. 90% traders lose money.

IPO AND INVESTMENTS:

Q: How to increase IPO allotment chances?
A: Apply through multiple demat accounts (family members).

Q: Can I sell IPO shares on listing day?
A: Yes, once credited to demat.

Q: What is grey market premium?
A: Unofficial market before listing. Not regulated, risky.

Q: Are IPO gains taxable?
A: Yes. If sold within 1 year: 15% STCG.

Q: Can I apply for IPO without demat?
A: No, demat account mandatory.

TECHNICAL ISSUES:

Q: What if order stuck due to technical glitch?
A: Take screenshot, complain immediately. Broker liable for losses.

Q: Can I place orders through phone?
A: Yes, through dealer terminals. Call-n-trade facility.

Q: What is blockchain in stock market?
A: SEBI exploring for settlement. Not yet implemented.

Q: Are my securities safe if broker shuts down?
A: Yes, held by depository (CDSL/NSDL), not broker.

Q: How to transfer shares between demat accounts?
A: Through DIS (Delivery Instruction Slip) or online.

INVESTMENT ADVICE:

Q: Should I invest borrowed money?
A: Never. Only invest what you can afford to lose.

Q: Is it good time to enter market?
A: Time in market beats timing the market. Start with SIP.

Q: How much of salary to invest?
A: Common rule: 50-30-20 (needs-wants-savings).

Q: Should I quit job for trading?
A: No. Only 1-2% make consistent profits. Keep it as secondary income.

Q: Are stock market courses worth it?
A: Learn basics free online first. Paid courses offer no guarantee.

Remember: Stock market investing carries risk. Do your own research and invest responsibly.
"""
    
    def _create_best_practices(self) -> str:
        """Create best practices guide"""
        return """
STOCK MARKET BEST PRACTICES GUIDE

FOR BEGINNERS:

1. Education First
- Understand basic terminology
- Learn about different asset classes
- Study risk-return relationship
- Practice with virtual trading

2. Start Small
- Begin with index funds or large-cap stocks
- Invest only surplus funds
- Avoid leveraged products initially
- Build experience gradually

3. Documentation
- Keep all contract notes
- Maintain trade diary
- File ITR on time
- Save account statements

RISK MANAGEMENT:

1. Position Sizing
- Never risk more than 2% per trade
- Diversify across sectors
- Avoid concentration risk
- Keep emergency fund separate

2. Stop Loss Discipline
- Always use stop loss
- Don't average losing positions
- Exit at predetermined levels
- Protect profits with trailing SL

3. Capital Allocation
- Equity: Based on risk appetite
- Debt: For stability
- Gold: 5-10% for hedge
- Cash: For opportunities

TRADING STRATEGIES:

1. Delivery Trading
- Research fundamentals
- Check valuations
- Long-term perspective
- Ignore daily volatility

2. Intraday Trading
- Strict timing discipline
- High liquidity stocks only
- Risk-reward minimum 1:2
- Maximum 2-3 trades daily

3. Swing Trading
- Technical analysis based
- Hold for days to weeks
- Follow trend direction
- Book partial profits

COMMON MISTAKES TO AVOID:

1. Emotional Trading
- FOMO buying at peaks
- Panic selling at bottoms
- Revenge trading after loss
- Overconfidence after profits

2. Poor Discipline
- No trading plan
- Ignoring stop losses
- Overtrading
- Changing strategy frequently

3. Information Sources
- WhatsApp/Telegram tips
- Unverified news
- Paid tips services
- Following blindly

ADVANCED CONCEPTS:

1. Portfolio Management
- Asset allocation by age
- Rebalancing quarterly
- Tax loss harvesting
- Core-satellite approach

2. Derivatives Strategy
- Hedging portfolio
- Covered calls for income
- Protective puts
- Spreads for range bound

3. Fundamental Analysis
- Financial ratios
- Industry analysis
- Management quality
- Competitive advantage

REGULATORY COMPLIANCE:

1. KYC Requirements
- Update regularly
- Link Aadhaar-PAN
- Verify email/mobile
- Nomination mandatory

2. Tax Compliance
- Report all trades
- Pay advance tax
- Maintain records 7 years
- Declare foreign assets

3. Trading Rules
- No insider trading
- No market manipulation
- Follow position limits
- Respect circuit filters

BROKER SELECTION:

1. Key Factors
- SEBI registration
- Technology platform
- Customer service
- Transparent charges

2. Red Flags
- Promises of guaranteed returns
- Asks for trading on behalf
- Hidden charges
- Poor grievance handling

INVESTMENT PHILOSOPHY:

1. Long Term Approach
- Power of compounding
- Rupee cost averaging
- Quality over quantity
- Patience pays

2. Continuous Learning
- Read annual reports
- Attend investor meets
- Follow market news
- Learn from mistakes

3. Wealth Creation
- Regular investing habit
- Increase with income
- Reinvest dividends
- Stay invested

TECHNOLOGY USAGE:

1. Trading Platforms
- Use official apps only
- Enable 2-factor auth
- Secure internet connection
- Regular password change

2. Information Sources
- Company websites
- Exchange notifications
- SEBI regulations
- Verified news sources

3. Analysis Tools
- Charting software
- Screeners
- Portfolio trackers
- Risk calculators

MARKET PSYCHOLOGY:

1. Bull Markets
- Don't get overconfident
- Book partial profits
- Maintain cash reserves
- Prepare for correction

2. Bear Markets
- Quality stocks on sale
- Accumulate gradually
- Don't catch falling knives
- Focus on fundamentals

3. Sideways Markets
- Reduce position size
- Focus on stock picking
- Use options strategies
- Preserve capital

ETHICAL INVESTING:

1. ESG Considerations
- Environmental impact
- Social responsibility
- Governance standards
- Sustainable growth

2. Avoid
- Sin stocks if against values
- Highly leveraged companies
- Opaque managements
- Regulatory violators

EMERGENCY PROTOCOLS:

1. Market Crash
- Don't panic sell
- Review fundamentals
- Add quality stocks
- Maintain asset allocation

2. Personal Emergency
- Liquid fund reserves
- Don't break long-term investments
- Insurance adequate
- Contingency planning

3. Broker Issues
- Immediate complaint
- Document everything
- Escalate to exchange
- Know investor rights

GOLDEN RULES:

1. Never invest borrowed money
2. Diversification is key
3. Time in market > Timing market
4. Invest regularly via SIP
5. Review portfolio quarterly
6. Keep learning always
7. Separate investing from trading
8. Maintain investment diary
9. Don't mix insurance with investment
10. Plan for taxes

Remember: Successful investing is a marathon, not a sprint. Focus on process, not outcomes.
"""

class SeleniumCrawler:
    """Selenium-based crawler for dynamic content"""
    
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver for Colab"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            self.driver = webdriver.Chrome(options=options)
            logger.info("Selenium driver initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            return False
    
    def get_pdf_links(self, url: str) -> List[str]:
        """Extract PDF links from a dynamic webpage"""
        if not self.driver and not self.setup_driver():
            return []
        
        pdf_links = []
        try:
            self.driver.get(url)
            
            # Wait for page load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "a"))
            )
            
            # Find PDF links
            links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")
            
            for link in links:
                href = link.get_attribute('href')
                if href:
                    pdf_links.append(href)
            
            logger.info(f"Found {len(pdf_links)} PDF links on {url}")
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
        
        return pdf_links
    
    def close(self):
        """Close the driver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

if __name__ == "__main__":
    # Test the crawler
    crawler = DocumentCrawler()
    
    # Create regulatory documents
    created = crawler.create_regulatory_documents()
    print(f"Created {created} regulatory documents")
    
    # Try to download sample documents
    stats = crawler.download_sample_documents()
    print(f"Download stats: {stats}")