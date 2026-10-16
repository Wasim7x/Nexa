import re
from enum import Enum
from typing import Optional, List, Tuple
from pydantic import BaseModel
from backend.app.guardrails.prompt_injection_detector import PromptInjectionDetector

class QueryCategory(str, Enum):
    ALLOWED_BUSINESS_QUERY = "ALLOWED_BUSINESS_QUERY"
    OUT_OF_SCOPE_QUERY = "OUT_OF_SCOPE_QUERY"
    ILLEGAL_REQUEST = "ILLEGAL_REQUEST"
    HARMFUL_REQUEST = "HARMFUL_REQUEST"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    UNAUTHORIZED_ACTION = "UNAUTHORIZED_ACTION"
    SENSITIVE_DATA_REQUEST = "SENSITIVE_DATA_REQUEST"
    AMBIGUOUS_QUERY = "AMBIGUOUS_QUERY"

class ClassificationResult(BaseModel):
    category: QueryCategory
    confidence: float
    detected_merchant_intent: Optional[str] = None  # 'grocery', 'sweets', 'salon', 'dental', or None
    is_switch_context: bool = False
    explanation: Optional[str] = None

class QueryClassifier:
    """
    Classifies customer queries into safe business categories or violation types.
    Also detects intended merchant domain from natural language queries.
    """

    ILLEGAL_PATTERNS = [
        (r"(make|synthesize|cook|produce|create)\s+.*(meth|drugs|explosives|bombs|weapons|narcotics)", "Illegal substances or weapons manufacture"),
        (r"(stolen|fake|counterfeit|forge)\s+.*(credit\s+card|identity|passport|license|documents)", "Financial fraud or identity theft"),
        (r"(hack|ddos|bypass|exploit|crack|breach)\s+.*(server|database|auth|password|credentials|api)", "Cyberattack facilitation"),
        (r"(launder\s+money|evade\s+taxes|fraudulent\s+transaction|financial\s+fraud)", "Financial crimes")
    ]

    HARMFUL_PATTERNS = [
        (r"(how\s+to\s+)?(commit\s+suicide|kill\s+myself|harm\s+myself|end\s+my\s+life)", "Self-harm facilitation"),
        (r"(how\s+to\s+)?(poison|injure|assault|harm|attack|kill)\s+(someone|others|people|\w+)", "Harm to others"),
        (r"(hate\s+speech|racial\s+slur|threaten|harass)", "Harmful harassment")
    ]

    SENSITIVE_DATA_PATTERNS = [
        (r"(show|give|list|tell|display|leak)\s+me\s+.*(other|another|all|everyone'?s)\s+.*(customer|user|patient|client|merchant|order|appointment|phone|number|email|address|record|database|data)", "Cross-customer private data harvest"),
        (r"what\s+is\s+.*(alex|priya|john|mary|another\s+customer|other\s+customer)'?s\s+.*(phone|order|appointment|address|record|email)", "Targeted customer PII inquiry"),
        (r"dump\s+.*(customer|user|merchant|database|tables|data)", "Database dumping request"),
        (r"(access|view|see|switch\s+to|hack\s+into)\s+.*(another|other)\s+merchant'?s?\s+(database|data|records|profile|account)", "Cross-tenant unauthorized database access")
    ]

    # Domain keyword indicators
    GROCERY_KEYWORDS = [
        "milk", "eggs", "bread", "apple", "banana", "produce", "grocery", "groceries",
        "vegetable", "fruit", "rice", "olive oil", "yogurt", "pantry", "flour", "cereal"
    ]
    SWEETS_KEYWORDS = [
        "kaju katli", "gulab jamun", "rasgulla", "ladoo", "barfi", "mithai", "sweets",
        "confectionery", "gift box", "gift hamper", "halwa", "sugar-free sweet", "peda"
    ]
    SALON_KEYWORDS = [
        "haircut", "hair cut", "hair spa", "facial", "manicure", "pedicure", "keratin",
        "salon", "stylist", "blowout", "makeup", "bridal", "massage", "waxing", "beauty"
    ]
    DENTAL_KEYWORDS = [
        "dentist", "dental", "teeth", "tooth", "toothache", "cleaning", "cavity", "whitening",
        "invisalign", "root canal", "crown", "braces", "oral exam", "smilecare", "gum", "gums", "bleeding"
    ]

    OUT_OF_SCOPE_PATTERNS = [
        r"write\s+(me\s+)?.*(python|javascript|code|script|poem|essay|story)",
        r"who\s+(won|is\s+the\s+president|is\s+the\s+prime\s+minister|is\s+the\s+current)",
        r"(solve|calculate)\s+this\s+math\s+equation",
        r"(crypto|bitcoin|forex|stock\s+tips)",
        r"(movie\s+recommendation|weather\s+forecast)"
    ]

    @classmethod
    def classify(cls, text: str, active_merchant_id: Optional[str] = None) -> ClassificationResult:
        """Classify user query and resolve merchant context."""
        if not text:
            return ClassificationResult(
                category=QueryCategory.AMBIGUOUS_QUERY,
                confidence=0.5,
                explanation="Empty query"
            )

        clean_text = text.strip()
        lowered = clean_text.lower()

        # 1. Prompt Injection Check
        injection_res = PromptInjectionDetector.analyze(clean_text)
        if injection_res.is_injection:
            return ClassificationResult(
                category=QueryCategory.PROMPT_INJECTION,
                confidence=injection_res.confidence,
                explanation=injection_res.reason
            )

        # 2. Illegal Check
        for pat, reason in cls.ILLEGAL_PATTERNS:
            if re.search(pat, lowered):
                return ClassificationResult(
                    category=QueryCategory.ILLEGAL_REQUEST,
                    confidence=0.98,
                    explanation=reason
                )

        # 3. Harmful Check
        for pat, reason in cls.HARMFUL_PATTERNS:
            if re.search(pat, lowered):
                return ClassificationResult(
                    category=QueryCategory.HARMFUL_REQUEST,
                    confidence=0.98,
                    explanation=reason
                )

        # 4. Sensitive Data / PII Harvest Check
        for pat, reason in cls.SENSITIVE_DATA_PATTERNS:
            if re.search(pat, lowered):
                return ClassificationResult(
                    category=QueryCategory.SENSITIVE_DATA_REQUEST,
                    confidence=0.95,
                    explanation=reason
                )

        # 5. Out of scope check
        for pat in cls.OUT_OF_SCOPE_PATTERNS:
            if re.search(pat, lowered):
                return ClassificationResult(
                    category=QueryCategory.OUT_OF_SCOPE_QUERY,
                    confidence=0.90,
                    explanation="General chatbot query outside merchant business scope"
                )

        # 6. Merchant Intent Identification
        detected_domain = None
        domain_scores = {
            "grocery": sum(1 for kw in cls.GROCERY_KEYWORDS if kw in lowered),
            "sweets": sum(1 for kw in cls.SWEETS_KEYWORDS if kw in lowered),
            "salon": sum(1 for kw in cls.SALON_KEYWORDS if kw in lowered),
            "dental": sum(1 for kw in cls.DENTAL_KEYWORDS if kw in lowered),
        }

        # Check explicit merchant mentions
        if "freshmart" in lowered or "grocery" in lowered:
            domain_scores["grocery"] += 3
        if "royal sweets" in lowered or "sweet shop" in lowered:
            domain_scores["sweets"] += 3
        if "glow salon" in lowered or "glamour" in lowered:
            domain_scores["salon"] += 3
        if "smilecare" in lowered or "dental clinic" in lowered:
            domain_scores["dental"] += 3

        best_domain = max(domain_scores, key=domain_scores.get)
        if domain_scores[best_domain] > 0:
            detected_domain = best_domain

        # Map domain name to merchant ID
        domain_to_id = {
            "grocery": "grocery-store",
            "sweets": "sweets-shop",
            "salon": "glow-salon",
            "dental": "dental-clinic"
        }
        detected_merchant_id = domain_to_id.get(detected_domain) if detected_domain else None

        # Check if user is requesting a context switch
        is_switch = False
        if detected_merchant_id and active_merchant_id and detected_merchant_id != active_merchant_id:
            is_switch = True

        # Common business actions (orders, appointments, cancellations, greetings)
        business_action_words = [
            "order", "book", "appointment", "price", "cost", "cancel", "reschedule",
            "status", "hours", "timing", "open", "slot", "catalog", "help", "hello", "hi", "hey"
        ]
        has_business_intent = any(bw in lowered for bw in business_action_words)

        if detected_domain or has_business_intent or active_merchant_id:
            return ClassificationResult(
                category=QueryCategory.ALLOWED_BUSINESS_QUERY,
                confidence=0.92,
                detected_merchant_intent=detected_merchant_id,
                is_switch_context=is_switch,
                explanation="Valid business operation or inquiry"
            )

        # If too ambiguous (e.g. "tell me more" or "what about tomorrow?" with no active merchant)
        return ClassificationResult(
            category=QueryCategory.AMBIGUOUS_QUERY,
            confidence=0.60,
            explanation="Ambiguous query requiring merchant or task clarification"
        )
