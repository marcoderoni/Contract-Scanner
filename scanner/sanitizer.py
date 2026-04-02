# Copyright (c) 2026 Marco De Roni. All rights reserved.
# Licensed under the MIT License — see LICENSE file for details.

import re

# Try to import presidio — fall back to regex if not available
try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()
    PRESIDIO_AVAILABLE = True
except Exception:
    PRESIDIO_AVAILABLE = False


def sanitize(text: str) -> tuple:
    """
    Detects and replaces PII entities in contract text.
    Uses presidio if available, falls back to regex.
    Returns (sanitized_text, mapping) where mapping allows de-sanitization.
    """
    if PRESIDIO_AVAILABLE:
        return _sanitize_presidio(text)
    else:
        return _sanitize_regex(text)


def _sanitize_presidio(text: str) -> tuple:
    """ML-based PII detection using Microsoft Presidio."""
    mapping = {}
    counter = {}

    results = analyzer.analyze(
        text=text,
        language="en",
        entities=[
            "PERSON",
            "ORG",
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "IBAN_CODE",
            "CREDIT_CARD",
            "DATE_TIME",
            "LOCATION",
            "URL",
        ]
    )

    # Sort by position descending to avoid index shift
    results = sorted(results, key=lambda x: x.start, reverse=True)

    sanitized = text
    for result in results:
        original = text[result.start:result.end]
        entity_type = result.entity_type

        if entity_type not in counter:
            counter[entity_type] = 0
        counter[entity_type] += 1
        placeholder = f"[{entity_type}_{counter[entity_type]}]"

        mapping[placeholder] = original
        sanitized = sanitized[:result.start] + placeholder + sanitized[result.end:]

    return sanitized, mapping


def _sanitize_regex(text: str) -> tuple:
    """Lightweight regex-based sanitization — fallback if presidio unavailable."""
    mapping = {}
    sanitized = text

    # Email addresses
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    for i, email in enumerate(set(emails)):
        placeholder = f"[EMAIL_{i+1}]"
        mapping[placeholder] = email
        sanitized = sanitized.replace(email, placeholder)

    # Phone numbers
    phones = re.findall(r'\+?[\d\s\-\(\)]{10,20}', text)
    for i, phone in enumerate(set(phones)):
        placeholder = f"[PHONE_{i+1}]"
        mapping[placeholder] = phone.strip()
        sanitized = sanitized.replace(phone, placeholder)

    # IBAN
    ibans = re.findall(r'\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b', text)
    for i, iban in enumerate(set(ibans)):
        placeholder = f"[IBAN_{i+1}]"
        mapping[placeholder] = iban
        sanitized = sanitized.replace(iban, placeholder)

    return sanitized, mapping


def desanitize(text: str, mapping: dict) -> str:
    """Restores original PII values from mapping."""
    result = text
    for placeholder, original in mapping.items():
        result = result.replace(placeholder, original)
    return result