from __future__ import annotations

import re
import unicodedata

_INJECTION_PATTERNS = [
    r"игнор[иу]руй\s+(все\s+)?правила",
    r"забудь\s+(все\s+)?инструкции",
    r"ты\s+теперь",
    r"новые?\s+инструкции",
    r"system\s*prompt",
    r"ignore\s+(all\s+)?previous",
    r"jailbreak",
    r"DAN\b",
    r"покажи\s+(пароль|ключ|секрет|токен)",
    r"выведи\s+(системный\s+)?промпт",
    r"расскажи\s+о\s+(своих\s+)?ограничениях.{0,20}обойди",
    r"act\s+as\s+if",
    r"pretend\s+(you\s+are|to\s+be)",
    r"roleplay\s+as",
    r"you\s+are\s+now",
    r"disregard\s+(all\s+)?instructions",
    r"override\s+(safety|instructions|rules)",
    r"bypass\s+(filter|restrict|censor)",
    r"без\s+ограничений",
    r"выйди\s+из\s+роли",
    r"забудь\s+(кто\s+ты|свою\s+роль)",
    r"режим\s+(разработчика|developer)",
]

_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize(text: str) -> tuple[str, bool]:
    cleaned = _CONTROL_CHARS_RE.sub("", text).strip()
    normalized = unicodedata.normalize("NFKC", cleaned)
    return cleaned, bool(_INJECTION_RE.search(normalized.lower()))
