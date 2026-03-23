import re
import yaml


def load_rules(rules_path: str) -> dict:
    """Carica le regole dal file YAML."""
    with open(rules_path, "r") as f:
        return yaml.safe_load(f)


def extract_metadata(text: str, rules: dict) -> dict:
    """Estrae metadati chiave dal testo del contratto."""
    meta = rules.get("metadata", {})
    result = {}

    # --- Parti ---
    for kw in meta.get("parties_keywords", []):
        match = re.search(
            rf"{re.escape(kw)}\s+([A-Z][^\n]{{5,80}})",
            text, re.IGNORECASE
        )
        if match:
            result["parties"] = match.group(1).strip()
            break

    # --- Data effettiva ---
    for kw in meta.get("date_keywords", []):
        match = re.search(
            rf"{re.escape(kw)}\s+([A-Z][a-z]{{2,8}}\s+\d{{1,2}},?\s+\d{{4}}|\d{{1,2}}[/\-\.]\d{{1,2}}[/\-\.]\d{{2,4}})",
            text, re.IGNORECASE
        )
        if match:
            result["effective_date"] = match.group(1).strip()
            break

    # --- Governing law ---
    for kw in meta.get("governing_law_keywords", []):
        match = re.search(
            rf"{re.escape(kw)}\s+(?:the\s+)?(?:laws?\s+of\s+)?([A-Z][a-zA-Z\s]{{3,40}})",
            text, re.IGNORECASE
        )
        if match:
            result["governing_law"] = match.group(1).strip()
            break

    # --- Jurisdiction ---
    for kw in meta.get("jurisdiction_keywords", []):
        match = re.search(
            rf"{re.escape(kw)}\s+(?:of\s+)?([A-Z][a-zA-Z\s]{{3,40}})",
            text, re.IGNORECASE
        )
        if match:
            result["jurisdiction"] = match.group(1).strip()
            break

    # --- Notice period ---
    match = re.search(
        r"(\d+)\s+(?:business\s+)?days['\s]*\s*(?:prior\s+)?(?:written\s+)?notice",
        text, re.IGNORECASE
    )
    if match:
        result["notice_period"] = f"{match.group(1)} days"

    # --- Durata ---
    for kw in meta.get("duration_keywords", []):
        match = re.search(
            rf"{re.escape(kw)}\s+(?:of\s+)?(\d+\s+(?:months?|years?)|one year|two years|three years)",
            text, re.IGNORECASE
        )
        if match:
            result["duration"] = match.group(1).strip()
            break

    # --- Auto-renewal ---
    for kw in meta.get("renewal_keywords", []):
        if re.search(re.escape(kw), text, re.IGNORECASE):
            result["auto_renewal"] = "Yes — auto-renewal clause detected"
            break
    if "auto_renewal" not in result:
        result["auto_renewal"] = "Not detected"

    return result