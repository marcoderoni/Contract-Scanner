# Copyright (c) 2026 Marco De Roni. All rights reserved.
# Licensed under the MIT License — see LICENSE file for details.

import os
import sys
import argparse
from colorama import Fore, Style, init
from scanner.extractor import extract_text, split_into_clauses
from scanner.metadata import load_rules, extract_metadata
from scanner.analyzer import analyze
from scanner.reporter import generate_report

init(autoreset=True)

RULES_PATH = "config/rules.yaml"
CONTRACTS_DIR = "contracts"
OUTPUT_DIR = "output"


def parse_args():
    parser = argparse.ArgumentParser(description="Contract Scanner — rule-based contract review")
    parser.add_argument("--rules", type=str, help="Path to rules YAML file")
    parser.add_argument("--contracts", type=str, help="Path to contracts folder")
    parser.add_argument("--output", type=str, help="Path to output folder")
    parser.add_argument("--format", choices=["docx", "pdf", "both"], default="docx", help="Output format")
    return parser.parse_args()


def check_rules_file(path: str):
    if not os.path.exists(path):
        print(Fore.RED + f"\n❌ File regole non trovato: {path}")
        print(Fore.YELLOW + "   Copia config/rules.example.yaml → config/rules.yaml e personalizzalo.")
        sys.exit(1)


def scan_contract(path: str, rules: dict) -> dict:
    name = os.path.basename(path)
    print(Fore.CYAN + f"\n📄 Scanning: {name}")

    print("   → Estrazione testo...")
    text = extract_text(path)
    clauses = split_into_clauses(text)
    print(f"   → {len(clauses)} sezioni rilevate")

    # Sanitize PII
    pii_mapping = {}
    try:
        from scanner.sanitizer import sanitize
        text, pii_mapping = sanitize(text)
        print(f"   → PII sanitizzato: {len(pii_mapping)} entità redatte")
    except Exception as e:
        print(f"   → PII sanitization skipped: {e}")

    print("   → Estrazione metadati...")
    metadata = extract_metadata(text, rules)

    print("   → Analisi clausole...")
    analysis = analyze(text, clauses, rules)

    # Build PII summary
    pii_summary = {"total_entities": len(pii_mapping), "breakdown": {}}
    for placeholder in pii_mapping.keys():
        entity_type = placeholder.split("_")[0].replace("[", "")
        pii_summary["breakdown"][entity_type] = pii_summary["breakdown"].get(entity_type, 0) + 1

    print("   → Generazione report Word...")
    report_path = generate_report(name, metadata, analysis, OUTPUT_DIR, pii_summary=pii_summary)

    # Audit log
    try:
        from scanner.audit import log_analysis
        log_analysis(
            contract_name=name,
            overall_score=analysis.get("overall_score", "UNKNOWN"),
            missing_clauses=analysis.get("missing_clauses", []),
            metadata=metadata
        )
    except Exception as e:
        print(f"   ⚠️  Audit log skipped: {e}")

    return {
        "name": name,
        "metadata": metadata,
        "analysis": analysis,
        "report": report_path,
    }


def print_summary(results: list):
    print(Fore.WHITE + Style.BRIGHT + "\n" + "="*60)
    print(Fore.WHITE + Style.BRIGHT + "  SCAN SUMMARY")
    print("="*60)

    for r in results:
        overall = r["analysis"]["overall_score"]
        color = {
            "RED": Fore.RED,
            "YELLOW": Fore.YELLOW,
            "GREEN": Fore.GREEN,
        }.get(overall, Fore.WHITE)

        emoji = {"RED": "🔴", "YELLOW": "🟡", "GREEN": "🟢"}.get(overall, "⚪")
        print(f"\n{emoji} {color}{r['name']}{Style.RESET_ALL}")
        print(f"   Overall:  {color}{overall}{Style.RESET_ALL}")

        missing = r["analysis"].get("missing_clauses", [])
        if missing:
            print(f"   Missing:  {Fore.RED}{', '.join(missing)}{Style.RESET_ALL}")

        meta = r["metadata"]
        if meta.get("governing_law"):
            print(f"   Law:      {meta['governing_law']}")
        if meta.get("effective_date"):
            print(f"   Date:     {meta['effective_date']}")
        if meta.get("notice_period"):
            print(f"   Notice:   {meta['notice_period']}")

        print(f"   Report:   {r['report']}")

    print("\n" + "="*60)
    print(Fore.GREEN + f"✅ {len(results)} contratto/i analizzato/i. Report in: {OUTPUT_DIR}/")


def main():
    args = parse_args()

    rules_path = args.rules or RULES_PATH
    contracts_dir = args.contracts or CONTRACTS_DIR
    output_dir = args.output or OUTPUT_DIR

    check_rules_file(rules_path)
    rules = load_rules(rules_path)

    contracts = [
        os.path.join(contracts_dir, f)
        for f in os.listdir(contracts_dir)
        if f.lower().endswith((".pdf", ".docx"))
    ]

    if not contracts:
        print(Fore.YELLOW + f"\n⚠️  Nessun contratto trovato in '{contracts_dir}/'")
        print("   Metti uno o più file PDF o DOCX nella cartella contracts/ e riprova.")
        return

    print(Fore.WHITE + Style.BRIGHT + f"\n=== Contract Scanner | {len(contracts)} file trovati ===")

    results = []
    for path in contracts:
        try:
            result = scan_contract(path, rules)
            results.append(result)
        except Exception as e:
            print(Fore.RED + f"   ❌ Errore su {path}: {e}")

    if results:
        print_summary(results)


if __name__ == "__main__":
    main()