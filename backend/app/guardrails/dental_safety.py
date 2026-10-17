import re
from typing import Tuple, Optional
from pydantic import BaseModel

class DentalSafetyResult(BaseModel):
    is_clinical_query: bool
    is_emergency: bool
    refusal_message: Optional[str] = None
    reason: Optional[str] = None

class DentalSafetyGuardrail:
    """
    Enforces dental and medical safety policies for SmileCare Dental Clinic.
    Blocks clinical diagnosis, symptom analysis, treatment prescriptions,
    and medicine recommendations while routing administrative queries
    (booking, prices, opening hours, general hygiene) normally.
    """

    # Emergency symptoms requiring urgent medical referral
    EMERGENCY_PATTERNS = [
        r"(uncontrollable|heavy|severe)\s+bleeding",
        r"(difficulty|trouble|can't)\s+(breathing|swallowing)",
        r"(severe|acute|intense|extreme|unbearable|excruciating)\s+(dental\s+)?(pain|toothache|swelling|infection)",
        r"(facial\s+swelling|swollen\s+face|swollen\s+jaw)",
        r"(broken|fractured)\s+jaw",
        r"(facial\s+trauma|knocked\s+out\s+tooth)",
        r"(high\s+fever\s+with\s+tooth\s+pain)"
    ]

    # Clinical diagnosis & prescription patterns
    CLINICAL_PATTERNS = [
        r"(what|which)\s+(antibiotic|painkiller|medicine|medication|drug|pill)\s+should\s+i\s+(take|use)",
        r"(can\s+you\s+prescribe|give\s+me\s+a\s+prescription)",
        r"(do\s+i\s+have|diagnose\s+me\s+with)\s+(oral\s+cancer|gum\s+disease|periodontitis|an\s+abscess|infection)",
        r"why\s+is\s+my\s+(tooth|gum|jaw)\s+(throbbing|bleeding|pus|swollen|aching)",
        r"is\s+it\s+safe\s+to\s+take\s+\w+\s+for\s+my\s+tooth",
        r"(how\s+to\s+pull\s+my\s+own\s+tooth|diy\s+tooth\s+extraction)"
    ]

    COMPILED_EMERGENCY = [re.compile(p, re.IGNORECASE) for p in EMERGENCY_PATTERNS]
    COMPILED_CLINICAL = [re.compile(p, re.IGNORECASE) for p in CLINICAL_PATTERNS]

    @classmethod
    def evaluate(cls, message: str) -> DentalSafetyResult:
        """Evaluate a customer message for clinical advice or medical emergencies."""
        if not message:
            return DentalSafetyResult(is_clinical_query=False, is_emergency=False)

        lowered = message.lower()

        # 1. Check for urgent dental/medical emergencies
        for pattern in cls.COMPILED_EMERGENCY:
            if pattern.search(lowered):
                emergency_msg = (
                    "⚠️ Urgent Medical Advisory: Your symptoms may indicate a medical emergency. "
                    "Nexa cannot provide medical diagnoses or emergency triage. "
                    "Please visit your nearest hospital emergency room, urgent care center, "
                    "or call our emergency front desk immediately."
                )
                return DentalSafetyResult(
                    is_clinical_query=True,
                    is_emergency=True,
                    refusal_message=emergency_msg,
                    reason="Emergency dental symptoms detected"
                )

        # 2. Check for clinical diagnosis or medication prescription questions
        for pattern in cls.COMPILED_CLINICAL:
            if pattern.search(lowered):
                clinical_msg = (
                    "SmileCare Clinical Policy: As an administrative AI assistant, I cannot diagnose "
                    "dental conditions or recommend medications/prescriptions. "
                    "I would be glad to help you schedule a consultation or examination with Dr. Vance "
                    "or Dr. Lin so a licensed dentist can evaluate you in person. Would you like to view our available appointment slots?"
                )
                return DentalSafetyResult(
                    is_clinical_query=True,
                    is_emergency=False,
                    refusal_message=clinical_msg,
                    reason="Clinical diagnosis or prescription query detected"
                )

        return DentalSafetyResult(is_clinical_query=False, is_emergency=False)
