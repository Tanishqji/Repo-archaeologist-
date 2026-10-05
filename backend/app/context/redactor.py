import os
import re
from typing import List, Set, Tuple

# Patterns for sensitive tokens and keys
SECRET_PATTERNS = [
    # AWS Access Key
    (re.compile(r"""\b(AKIA[0-9A-Z]{16})\b"""), "[REDACTED_AWS_KEY]"),
    # GitHub Tokens
    (re.compile(r"""\b(ghp_[A-Za-z0-9_]{36,}|github_pat_[A-Za-z0-9_]{82})\b"""), "[REDACTED_GITHUB_TOKEN]"),
    # OpenAI / Anthropic Keys
    (re.compile(r"""\b(sk-[A-Za-z0-9_-]{20,}|sk-ant-[A-Za-z0-9_-]{20,})\b"""), "[REDACTED_AI_API_KEY]"),
    # Google API Key
    (re.compile(r"""\b(AIza[0-9A-Za-z-_]{35})\b"""), "[REDACTED_GOOGLE_KEY]"),
    # JWT Tokens
    (re.compile(r"""\b(eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})\b"""), "[REDACTED_JWT]"),
    # Private Key blocks
    (
        re.compile(r"""-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"""),
        "[REDACTED_PRIVATE_KEY_BLOCK]",
    ),
    # High entropy passwords or secrets in variable assignments
    (
        re.compile(r"""(?i)(password|passwd|secret|api_key|apikey|auth_token)\s*=\s*['"]([A-Za-z0-9!@#$%^&*()_+=-]{8,})['"]"""),
        r'\1="[REDACTED_SECRET]"',
    ),
]

SENSITIVE_FILENAME_PATTERNS = [
    re.compile(r"""^\.env(?!\.(?:example|sample|template)$)""", re.IGNORECASE),
    re.compile(r""".*\.pem$""", re.IGNORECASE),
    re.compile(r""".*\.key$""", re.IGNORECASE),
    re.compile(r""".*id_rsa.*""", re.IGNORECASE),
    re.compile(r"""^credentials.*""", re.IGNORECASE),
]

def is_sensitive_file(path: str) -> bool:
    """
    Returns True if the file path represents a sensitive secret file that must NEVER be read into LLM context.
    """
    base = os.path.basename(path).lower()
    for pattern in SENSITIVE_FILENAME_PATTERNS:
        if pattern.search(base):
            return True
    return False

def redact_secrets(content: str) -> Tuple[str, bool]:
    """
    Scans and redacts credentials, API keys, tokens, and private keys.
    Returns: (redacted_content, was_secret_detected)
    """
    redacted = content
    detected = False

    for pattern, replacement in SECRET_PATTERNS:
        if pattern.search(redacted):
            detected = True
            redacted = pattern.sub(replacement, redacted)

    return redacted, detected
