"""
src/compliance.py - Compliance checking and risk assessment module
Detects illegal activities, risky practices, and provides warnings
"""
import re
from typing import List, Dict, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    ILLEGAL = "illegal"
    HIGH_RISK = "high_risk"
    MEDIUM_RISK = "medium_risk"
    LOW_RISK = "low_risk"
    INFO = "info"

class ComplianceChecker:
    def __init__(self):
        self.patterns = self._load_compliance_patterns()
        self.sebi_acts = self._load_sebi_acts()
        
    def _load_compliance_patterns(self) -> Dict[RiskLevel, List[Tuple[str, str]]]:
        return {
            RiskLevel.ILLEGAL: [
                (r"insider\s+trading|trade.*inside.*information", 
                 "🚫 ILLEGAL: Insider trading violates SEBI (PIT) Regulations 2015. Penalty up to ₹25 crores or 3x profits"),
                (r"front[\s-]?running|front\s+run", 
                 "🚫 ILLEGAL: Front-running is market manipulation under SEBI Act Section 12A"),
                (r"pump\s+and\s+dump|pump\s+dump|artificial.*price", 
                 "🚫 ILLEGAL: Market manipulation prohibited under SEBI (PFUTP) Regulations"),
                (r"ponzi|pyramid\s+scheme|chit\s+fund.*investment", 
                 "🚫 ILLEGAL: Such schemes are banned under SEBI Act and PCMC Act"),
                (r"circular\s+trading|wash\s+trad|synchronized\s+trad", 
                 "🚫 ILLEGAL: Fraudulent trading practices under SEBI regulations"),
                (r"fake.*dmat|someone\s+else.*account|benami.*trad", 
                 "🚫 ILLEGAL: Trading in others' accounts violates KYC norms and Benami Act"),
            ],
            RiskLevel.HIGH_RISK: [
                (r"margin\s+trading|leverage.*trad|mtf", 
                 "⚠️ HIGH RISK: Margin trading can lead to losses exceeding capital. Interest charged daily"),
                (r"F&O|futures|options|derivatives", 
                 "⚠️ HIGH RISK: Derivatives can cause unlimited losses. 89% retail traders lose money in F&O"),
                (r"intraday|day\s+trading|mis\s+order", 
                 "⚠️ HIGH RISK: Intraday requires experience. Auto square-off can cause losses"),
                (r"penny\s+stock|illiquid.*stock|sme\s+stock", 
                 "⚠️ HIGH RISK: Penny stocks are highly volatile and often manipulated"),
                (r"commodity|mcx|ncdex", 
                 "⚠️ HIGH RISK: Commodity trading requires specialized knowledge"),
            ],
            RiskLevel.MEDIUM_RISK: [
                (r"ipo.*grey\s+market|grey\s+market|kostak", 
                 "⚡ MEDIUM RISK: Grey market trading is unregulated and risky"),
                (r"btst|atst|sell\s+tomorrow", 
                 "⚡ MEDIUM RISK: BTST carries auction risk if seller defaults"),
                (r"sip.*small\s+cap|small\s+cap.*fund", 
                 "⚡ MEDIUM RISK: Small cap investments are volatile"),
                (r"crypto|bitcoin|cryptocurrency", 
                 "⚡ MEDIUM RISK: Crypto is unregulated in India. 30% tax + 1% TDS applies"),
            ],
            RiskLevel.INFO: [
                (r"demat\s+account|trading\s+account|broker", 
                 "ℹ️ IMPORTANT: Ensure your broker is SEBI registered. Check on www.sebi.gov.in"),
                (r"ipo|initial\s+public\s+offering", 
                 "ℹ️ INFO: Read the Red Herring Prospectus carefully before IPO investment"),
                (r"mutual\s+fund|mf\s+investment", 
                 "ℹ️ INFO: Check expense ratio and exit load. Past performance doesn't guarantee future returns"),
                (r"kyc|know\s+your\s+customer", 
                 "ℹ️ INFO: KYC is mandatory. In-person verification (IPV) required for demat account"),
            ]
        }

    def _load_sebi_acts(self) -> Dict[str, str]:
        return {
            "SEBI Act 1992": "Primary act establishing SEBI's authority",
            "SEBI (PIT) Regulations 2015": "Prohibition of Insider Trading",
            "SEBI (LODR) Regulations 2015": "Listing Obligations and Disclosure Requirements",
            "SEBI (PFUTP) Regulations 2003": "Prohibition of Fraudulent and Unfair Trade Practices",
            "SEBI (SAST) Regulations 2011": "Substantial Acquisition of Shares and Takeovers",
            "SCRA 1956": "Securities Contracts (Regulation) Act",
            "Depositories Act 1996": "Electronic holding of securities",
        }

    def check_query(self, query: str) -> List[Dict[str, str]]:
        warnings = []
        query_lower = query.lower()
        for risk_level, patterns in self.patterns.items():
            for pattern, warning in patterns:
                if re.search(pattern, query_lower):
                    logger.info(f"Compliance warning triggered: {risk_level.value} - {pattern}")
                    warnings.append({
                        "category": risk_level.value,
                        "pattern": pattern,
                        "warning": warning
                    })
        return warnings

    def check_response(self, response: str) -> List[Dict[str, str]]:
        warnings = []
        response_lower = response.lower()
        illegal_encouragements = [
            (r"you\s+can.*insider\s+trad", "Response should not encourage insider trading"),
            (r"easy.*manipulat.*market", "Response should not suggest market manipulation"),
            (r"avoid.*tax.*illegal", "Response should not suggest tax evasion"),
        ]
        for pattern, warning in illegal_encouragements:
            if re.search(pattern, response_lower):
                logger.warning(f"Compliance violation pattern found in response: {pattern}")
                warnings.append({
                    "category": "response_check",
                    "pattern": pattern,
                    "warning": f"⚠️ COMPLIANCE CHECK: {warning}"
                })
        return warnings

    def get_risk_level(self, activity: str) -> RiskLevel:
        activity_lower = activity.lower()
        for risk_level, patterns in self.patterns.items():
            for pattern, _ in patterns:
                if re.search(pattern, activity_lower):
                    return risk_level
        return RiskLevel.LOW_RISK

    def generate_disclaimer(self, risk_level: RiskLevel) -> str:
        disclaimers = {
            RiskLevel.ILLEGAL: "⚠️ WARNING: This activity is illegal under Indian securities law.",
            RiskLevel.HIGH_RISK: "⚠️ HIGH RISK WARNING: This activity can result in significant financial losses.",
            RiskLevel.MEDIUM_RISK: "⚡ RISK WARNING: This investment carries moderate risk.",
            RiskLevel.LOW_RISK: "ℹ️ Please ensure you follow all SEBI guidelines and regulations.",
            RiskLevel.INFO: "ℹ️ This is for informational purposes only. Consult a SEBI-registered advisor."
        }
        return disclaimers.get(risk_level, disclaimers[RiskLevel.INFO])

    def validate_broker_registration(self, broker_name: str) -> Dict[str, any]:
        registered_brokers = [
            "zerodha", "upstox", "groww", "angel one", "hdfc securities",
            "icici direct", "kotak securities", "motilal oswal", "5paisa",
            "sharekhan", "edelweiss", "axis direct"
        ]
        broker_lower = broker_name.lower()
        is_registered = any(broker in broker_lower for broker in registered_brokers)
        return {
            "is_registered": is_registered,
            "message": "✅ SEBI Registered Broker" if is_registered else "⚠️ Please verify SEBI registration",
            "check_url": "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes"
        }

    def get_penalty_info(self, violation_type: str) -> Dict[str, any]:
        penalties = {
            "insider_trading": {
                "monetary": "Up to ₹25 crores or 3 times the profit made",
                "criminal": "Up to 10 years imprisonment",
                "other": "Debarment from markets, disgorgement of profits"
            },
            "market_manipulation": {
                "monetary": "Up to ₹25 crores",
                "criminal": "Up to 10 years imprisonment",
                "other": "Cancellation of broker license"
            },
            "front_running": {
                "monetary": "Up to ₹1 crore",
                "criminal": "Prosecution under SEBI Act",
                "other": "Suspension of trading rights"
            },
            "kyc_violation": {
                "monetary": "₹10,000 per day of violation",
                "criminal": "Not applicable",
                "other": "Account freeze, trading suspension"
            }
        }
        return penalties.get(violation_type, {
            "monetary": "As per SEBI regulations",
            "criminal": "As per applicable laws",
            "other": "As determined by SEBI"
        })

# Standalone function
def check_compliance(query: str) -> List[Dict[str, str]]:
    checker = ComplianceChecker()
    return checker.check_query(query)
