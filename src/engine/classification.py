
import re


CATEGORY_KEYWORDS = {
    "benefits": [
        "insurance", "medical", "benefit",
        "dependent", "health coverage"
    ],
    "leave": [
        "leave", "holiday", "vacation",
        "absence", "leave balance"
    ],
    "payroll": [
        "salary", "payslip", "payroll",
        "deduction", "tax", "payment"
    ],
    "onboarding": [
        "joining", "onboarding", "new hire",
        "joining documents", "employee account"
    ]
}

SENSITIVE_KEYWORDS = [
    "harassment",
    "discrimination",
    "confidential complaint",
    "employee relations",
    "workplace misconduct",
    "retaliation"
]

MISSING_CONTEXT_PHRASES = [
    "help me",
    "need assistance",
    "please help",
    "my issue",
    "my problem"
]


def normalize_text(text):
    return re.sub(r"\s+", " ", text.lower()).strip()


def classify_ticket(text):
    text = normalize_text(text)

    for keyword in SENSITIVE_KEYWORDS:
        if keyword in text:
            return {
                "category": "employee_relations",
                "confidence": 1.0,
                "classification_reason": "SENSITIVE_KEYWORD",
                "sensitive": True
            }

    matches = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        matches[category] = sum(
            1 for keyword in keywords
            if keyword in text
        )

    best_category = max(matches, key=matches.get)
    best_score = matches[best_category]

    if best_score == 0:
        return {
            "category": "unknown",
            "confidence": 0.0,
            "classification_reason": "NO_KEYWORD_MATCH",
            "sensitive": False
        }

    confidence = min(0.99, 0.60 + best_score * 0.10)

    return {
        "category": best_category,
        "confidence": round(confidence, 2),
        "classification_reason": "KEYWORD_MATCH",
        "sensitive": False
    }


def check_ambiguity(text, required_fields=None):
    text = normalize_text(text)

    missing_context = any(
        phrase in text
        for phrase in MISSING_CONTEXT_PHRASES
    )

    required_fields = required_fields or []

    missing_fields = [
        field for field in required_fields
        if not field.get("value")
    ]

    ambiguous = missing_context or bool(missing_fields)

    return {
        "is_ambiguous": ambiguous,
        "missing_context": missing_context,
        "missing_fields": [
            field["name"] for field in missing_fields
        ],
        "action": (
            "REQUEST_CLARIFICATION"
            if ambiguous
            else "CONTINUE_PROCESSING"
        )
    }
