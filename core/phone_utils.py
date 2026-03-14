import re


PH_E164_REGEX = re.compile(r"^\+639\d{9}$")
E164_REGEX = re.compile(r"^\+[1-9]\d{7,14}$")


def _clean_phone_input(value: str) -> str:
    if value is None:
        return ""
    value = str(value).strip()
    value = re.sub(r"[\s\-\(\)]", "", value)
    return value


def normalize_ph_to_e164(value: str) -> str | None:
    cleaned = _clean_phone_input(value)
    if not cleaned:
        return None

    if cleaned.startswith("+"):
        candidate = "+" + re.sub(r"\D", "", cleaned[1:])
    else:
        digits = re.sub(r"\D", "", cleaned)
        if digits.startswith("09") and len(digits) == 11:
            candidate = "+63" + digits[1:]
        elif digits.startswith("9") and len(digits) == 10:
            candidate = "+63" + digits
        elif digits.startswith("639") and len(digits) == 12:
            candidate = "+" + digits
        else:
            return None

    if PH_E164_REGEX.match(candidate):
        return candidate
    return None


def is_e164(value: str) -> bool:
    return bool(E164_REGEX.match(_clean_phone_input(value)))


def display_ph_local(value: str) -> str:
    normalized = normalize_ph_to_e164(value)
    if normalized and normalized.startswith("+639"):
        return normalized[3:]

    cleaned = _clean_phone_input(value)
    digits = re.sub(r"\D", "", cleaned)

    if digits.startswith("09") and len(digits) == 11:
        return digits[1:]
    if digits.startswith("9") and len(digits) == 10:
        return digits

    return ""
