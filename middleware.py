# middleware.py
# Safety and control layer for the appointment assistant
# Implements: PII masking, moderation, tool call limits, and retry logic

import re
import logging

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# 1. PII MIDDLEWARE
# Masks sensitive personal information
# ─────────────────────────────────────────

PII_PATTERNS = {
    "phone":   (r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', "***-***-****"),
    "email":   (r'\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b',     "***@***.***"),
    "ssn":     (r'\b\d{3}-\d{2}-\d{4}\b',               "***-**-****"),
    "dob":     (r'\b(0[1-9]|1[0-2])[/-](0[1-9]|[12]\d|3[01])[/-]\d{4}\b', "**/**/****"),
}

def pii_middleware(text: str) -> dict:
    """
    Scans text for PII and masks it.
    Returns masked text and a flag indicating if PII was found.
    """
    masked_text = text
    pii_found = []

    for pii_type, (pattern, replacement) in PII_PATTERNS.items():
        if re.search(pattern, masked_text, re.IGNORECASE):
            masked_text = re.sub(pattern, replacement, masked_text, flags=re.IGNORECASE)
            pii_found.append(pii_type)

    if pii_found:
        logger.info(f"[PIIMiddleware] Masked PII types: {pii_found}")

    return {
        "original_text": text,
        "masked_text": masked_text,
        "pii_detected": len(pii_found) > 0,
        "pii_types": pii_found
    }


# ─────────────────────────────────────────
# 2. MODERATION MIDDLEWARE
# Blocks harmful or inappropriate input
# ─────────────────────────────────────────

BLOCKED_KEYWORDS = [
    "kill", "bomb", "attack", "hack", "illegal",
    "fraud", "abuse", "threat", "weapon", "explosive"
]

def moderation_middleware(text: str) -> dict:
    """
    Checks input for harmful content.
    Returns a flag and reason if content is blocked.
    """
    text_lower = text.lower()
    triggered = [kw for kw in BLOCKED_KEYWORDS if kw in text_lower]

    if triggered:
        logger.warning(f"[ModerationMiddleware] Blocked keywords detected: {triggered}")
        return {
            "approved": False,
            "reason": f"Input contains inappropriate content: {triggered}",
            "triggered_keywords": triggered
        }

    return {
        "approved": True,
        "reason": None,
        "triggered_keywords": []
    }


# ─────────────────────────────────────────
# 3. TOOL CALL LIMIT MIDDLEWARE
# Prevents infinite loops or abuse
# ─────────────────────────────────────────

MAX_TOOL_CALLS = 5

def tool_call_limit_middleware(current_count: int) -> dict:
    """
    Checks if the number of tool calls has exceeded the limit.
    """
    if current_count >= MAX_TOOL_CALLS:
        logger.warning(f"[ToolCallLimitMiddleware] Limit reached: {current_count}/{MAX_TOOL_CALLS}")
        return {
            "allowed": False,
            "reason": f"Tool call limit of {MAX_TOOL_CALLS} reached. Escalating to human agent."
        }

    return {
        "allowed": True,
        "reason": None
    }


# ─────────────────────────────────────────
# 4. RETRY MIDDLEWARE
# Retries a function up to max_retries times
# ─────────────────────────────────────────

def retry_middleware(func, max_retries: int = 3, *args, **kwargs):
    """
    Retries a tool function up to max_retries times on failure.
    """
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            result = func(*args, **kwargs)
            if attempt > 1:
                logger.info(f"[RetryMiddleware] Succeeded on attempt {attempt}")
            return {"success": True, "result": result, "attempts": attempt}
        except Exception as e:
            last_error = e
            logger.warning(f"[RetryMiddleware] Attempt {attempt} failed: {e}")

    logger.error(f"[RetryMiddleware] All {max_retries} attempts failed.")
    return {
        "success": False,
        "result": None,
        "attempts": max_retries,
        "error": str(last_error)
    }


# ─────────────────────────────────────────
# 5. RUN ALL MIDDLEWARE (combined check)
# ─────────────────────────────────────────

def run_middleware_checks(user_input: str, tool_call_count: int) -> dict:
    """
    Runs all middleware checks on the user input.
    Returns a combined result with status and any issues found.
    """
    # Step 1: Moderation check
    mod_result = moderation_middleware(user_input)
    if not mod_result["approved"]:
        return {
            "passed": False,
            "stage": "moderation",
            "reason": mod_result["reason"],
            "clean_input": user_input
        }

    # Step 2: PII masking
    pii_result = pii_middleware(user_input)
    clean_input = pii_result["masked_text"]

    # Step 3: Tool call limit check
    limit_result = tool_call_limit_middleware(tool_call_count)
    if not limit_result["allowed"]:
        return {
            "passed": False,
            "stage": "tool_limit",
            "reason": limit_result["reason"],
            "clean_input": clean_input
        }

    return {
        "passed": True,
        "stage": "all_passed",
        "reason": None,
        "clean_input": clean_input,
        "pii_detected": pii_result["pii_detected"],
        "pii_types": pii_result["pii_types"]
    }