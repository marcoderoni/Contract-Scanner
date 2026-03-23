import os
import sys
from colorama import Fore, Style, init
from scanner.extractor import extract_text, split_into_clauses
from scanner.metadata import load_rules, extract_metadata
from scanner.analyzer import analyze
from scanner.reporter import generate_report

init(autoreset=True)

RULES_PATH = "config/rules.yaml"
CONTRACTS_DIR = "contracts"
OUTPUT_DIR = "output"


def check_rules_file():
    if not os.path.exists(RULES_PATH):
        print(Fore.RED + f"\n❌ File regole non trovato: {RULES_PATH}")
        print(Fore.YELLOW + "   Copia config/rules.example.yaml → config/rules.yaml e personalizzalo.")
        sys.exit(1)


def scan_contract(path: str, rules: dict) -> dict:
    name = os.path.basename(path)
    print(Fore.CYAN + f"\n📄 Scanning: {name}")

    # 1. Estrai testo
    print("   → Estrazione testo...")
    text = extract_text(path)
    clauses = split_into_clauses(text)
    print(f"   → {len(clauses)} sezioni rilevate")

    # 2. Metadati
    print("   → Estrazione metadati...")
    metadata = extract_metadata(text, rules)

    # 3. Analisi R/Y/G
    print("   → Analisi clausole...")
    analysis = analyze(text, clauses, rules)

    # 4. Report
    print("   → Generazione report Word...")
    report_path = generate_report(name, metadata, analysis, OUTPUT_DIR)

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
    check_rules_file()
    rules = load_rules(RULES_PATH)

    # Trova tutti i contratti nella cartella contracts/
    contracts = [
        os.path.join(CONTRACTS_DIR, f)
        for f in os.listdir(CONTRACTS_DIR)
        if f.lower().endswith((".pdf", ".docx"))
    ]

    if not contracts:
        print(Fore.YELLOW + f"\n⚠️  Nessun contratto trovato in '{CONTRACTS_DIR}/'")
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