import re
import yaml


def check_required_clauses(text: str, rules: dict) -> list:
    """
    Verifica se le clausole obbligatorie sono presenti nel testo.
    Restituisce lista di clausole mancanti.
    """
    required = rules.get("required_clauses", [])
    missing = []

    for clause in required:
        name = clause["name"]
        keywords = clause["keywords"]
        found = any(
            re.search(re.escape(kw), text, re.IGNORECASE)
            for kw in keywords
        )
        if not found:
            missing.append(name)

    return missing


def score_clause(clause_text: str, risk_rules: list) -> list:
    """
    Applica le regole di scoring a un blocco di testo.
    Restituisce lista di match con score e commento.
    """
    findings = []

    for rule in risk_rules:
        pattern = rule.get("pattern", "")
        score = rule.get("score", "YELLOW")
        comment = rule.get("comment", "")

        if re.search(pattern, clause_text, re.IGNORECASE):
            findings.append({
                "pattern": pattern,
                "score": score,
                "comment": comment,
                "excerpt": extract_excerpt(clause_text, pattern),
            })

    return findings


def extract_excerpt(text: str, pattern: str, context: int = 100) -> str:
    """Estrae un breve estratto attorno al pattern trovato."""
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return ""
    start = max(0, match.start() - context)
    end = min(len(text), match.end() + context)
    excerpt = text[start:end].strip()
    return f"...{excerpt}..."


def analyze(full_text: str, clauses: dict, rules: dict) -> dict:
    """
    Analisi completa del contratto:
    - clausole mancanti
    - scoring R/Y/G per ogni categoria
    """
    risk_rules = rules.get("risk_rules", {})
    results = {}

    # Clausole mancanti
    results["missing_clauses"] = check_required_clauses(full_text, rules)

    # Scoring per categoria
    results["findings"] = {}

    for category, category_rules in risk_rules.items():
        # Cerca nel testo completo per ogni categoria
        findings = score_clause(full_text, category_rules)
        if findings:
            results["findings"][category] = findings

    # Score globale del contratto
    all_scores = [
        f["score"]
        for cat_findings in results["findings"].values()
        for f in cat_findings
    ]

    if "RED" in all_scores:
        results["overall_score"] = "RED"
    elif "YELLOW" in all_scores:
        results["overall_score"] = "YELLOW"
    elif "GREEN" in all_scores:
        results["overall_score"] = "GREEN"
    else:
        results["overall_score"] = "UNKNOWN"

    return results