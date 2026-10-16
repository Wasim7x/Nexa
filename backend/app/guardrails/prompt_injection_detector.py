import re
from typing import Tuple, List, Optional
from pydantic import BaseModel

class PromptInjectionResult(BaseModel):
    is_injection: bool
    confidence: float
    trigger_pattern: Optional[str] = None
    reason: Optional[str] = None

class PromptInjectionDetector:
    """
    Detects prompt injection, instruction bypass, role-play jailbreaks,
    system prompt exfiltration, and malicious delimiters.
    """

    # High-confidence prompt injection patterns
    INJECTION_PATTERNS = [
        # Instruction override
        (r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules|guidelines)", "Instruction override attempt"),
        (r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)", "Instruction disregard attempt"),
        (r"forget\s+(all\s+)?(previous|prior)\s+(instructions|rules|context)", "Context wipe attempt"),
        (r"you\s+are\s+now\s+(unrestricted|in\s+developer\s+mode|dan|jailbroken)", "Persona override / DAN jailbreak attempt"),
        (r"system\s*override", "System override attempt"),
        (r"new\s+system\s+instruction:", "Fake system instruction delimiter"),
        
        # System prompt exfiltration
        (r"(reveal|print|show|repeat|dump|output)\s+(your\s+)?(entire\s+|full\s+|all\s+)?(system\s+prompt|initial\s+prompt|developer\s+instructions|system\s+instructions|internal\s+rules)", "Prompt exfiltration attempt"),
        (r"what\s+(is|are)\s+your\s+(exact\s+)?(entire\s+|full\s+)?(system\s+prompt|system\s+instructions|hidden\s+rules)", "Prompt inspection attempt"),
        (r"tell\s+me\s+your\s+secret\s+key|reveal\s+api\s+key|show\s+me\s+the\s+token", "Credential exfiltration attempt"),
        
        # Delimiter escapes & structural spoofing
        (r"(\[INST\]|\[\/INST\]|<<SYS>>|<\/<<SYS>>|<\|im_start\|>|<\|im_end\|>)", "Model control token injection"),
        (r"---+\s*(system|admin|root)\s*---+", "Delimiter spoofing"),
        (r"<\s*script\b[^>]*>", "Script injection attempt"),
        
        # Code execution & SQL exploit patterns
        (r"(drop\s+table|delete\s+from\s+users|select\s+\*\s+from\s+information_schema|union\s+select)", "SQL injection pattern"),
        (r"(exec\(|eval\(|__import__|os\.system|subprocess\.Popen)", "Remote code execution attempt")
    ]

    COMPILED_PATTERNS = [(re.compile(p, re.IGNORECASE), reason) for p, reason in INJECTION_PATTERNS]

    @classmethod
    def analyze(cls, text: str) -> PromptInjectionResult:
        """Analyze a string for prompt injection or system override attempts."""
        if not text:
            return PromptInjectionResult(is_injection=False, confidence=0.0)

        normalized = text.strip()

        for pattern, reason in cls.COMPILED_PATTERNS:
            match = pattern.search(normalized)
            if match:
                return PromptInjectionResult(
                    is_injection=True,
                    confidence=0.95,
                    trigger_pattern=match.group(0),
                    reason=reason
                )

        # Heuristic check: high density of markdown command delimiters or system impersonation
        lowered = normalized.lower()
        impersonation_keywords = ["admin mode enabled", "bypass guardrails", "unlimited access granted", "sudo mode"]
        for kw in impersonation_keywords:
            if kw in lowered:
                return PromptInjectionResult(
                    is_injection=True,
                    confidence=0.85,
                    trigger_pattern=kw,
                    reason=f"Impersonation keyword detected: {kw}"
                )

        return PromptInjectionResult(is_injection=False, confidence=0.0)
