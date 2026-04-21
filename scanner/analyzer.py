# Copyright (c) 2026 Marco De Roni. All rights reserved.
# Licensed under the MIT License — see LICENSE file for details.

import re


def check_required_clauses(text: str, rules: dict) -> tuple:
    """Verifica clausole obbligatorie e estrae il testo dove trovate."""
    required = rules.get("required_clauses", [])
    missing = []
    found_extracts = {}

    for clause in required:
        name = clause["name"]
        keywords = clause["keywords"]
        found = False
        for kw in keywords:
            if re.search(re.escape(kw), text, re.IGNORECASE):
                found = True
                if name not in found_extracts:
                    extract = extract_clause_text(text, kw)
                    if extract:
                        found_extracts[name] = extract
                break
        if not found:
            missing.append(name)

    return missing, found_extracts


def extract_excerpt(text: str, pattern: str, context: int = 100) -> str:
    """Estrae un breve estratto attorno al pattern trovato."""
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return ""
    start = max(0, match.start() - context)
    end = min(len(text), match.end() + context)
    excerpt = text[start:end].strip()
    return f"...{excerpt}..."


def extract_clause_text(text: str, keyword: str, context: int = 500) -> str:
    """
    Extracts the surrounding text around a keyword match.
    Tries to capture the full clause by looking for sentence boundaries.
    """
    match = re.search(re.escape(keyword), text, re.IGNORECASE)
    if not match:
        return ""

    start = max(0, match.start() - context)
    end = min(len(text), match.end() + context)
    excerpt = text[start:end].strip()

    # Trim to sentence boundaries
    first_cap = re.search(r'[A-Z]', excerpt)
    if first_cap and first_cap.start() < 100:
        excerpt = excerpt[first_cap.start():]

    last_period = excerpt.rfind(".")
    if last_period > len(excerpt) // 2:
        excerpt = excerpt[:last_period + 1]

    return excerpt.strip()


def confidence_score(pattern: str, text: str) -> str:
    """
    Assigns confidence score based on how clearly the pattern matches.
    - HIGH: exact phrase match, multiple occurrences
    - MEDIUM: single match found
    - LOW: partial or weak match
    """
    matches = re.findall(pattern, text, re.IGNORECASE)
    count = len(matches)
    if count >= 3:
        return "HIGH"
    elif count >= 1:
        return "MEDIUM"
    else:
        return "LOW"


def score_clause(clause_text: str, risk_rules: list) -> list:
    """Applica le regole di scoring a un blocco di testo."""
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
                "confidence": confidence_score(pattern, clause_text),
                "excerpt": extract_excerpt(clause_text, pattern),
            })

    return findings


def analyze(full_text: str, clauses: dict, rules: dict) -> dict:
    """Analisi completa: clausole mancanti + scoring R/Y/G + confidence."""
    risk_rules = rules.get("risk_rules", {})
    results = {}

    results["missing_clauses"], results["found_extracts"] = check_required_clauses(full_text, rules)
    results["findings"] = {}

    for category, category_rules in risk_rules.items():
        findings = score_clause(full_text, category_rules)
        if findings:
            results["findings"][category] = findings

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