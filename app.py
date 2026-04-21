# Copyright (c) 2026 Marco De Roni. All rights reserved.
# Licensed under the MIT License — see LICENSE file for details.

import streamlit as st
import os
import tempfile
import yaml
import warnings
warnings.filterwarnings("ignore")
from scanner.extractor import extract_text, split_into_clauses
from scanner.metadata import load_rules, extract_metadata
from scanner.analyzer import analyze
from scanner.reporter import generate_report

# Disable presidio at startup to avoid blocking
os.environ["PRESIDIO_DISABLE_CACHE"] = "1"



st.set_page_config(
    page_title="Contract Scanner",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Contract Scanner")
st.caption("AI-powered contract review — R/Y/G risk scoring, missing clause detection and metadata extraction")

# ── Sidebar ──
with st.sidebar:
    st.header("⚙️ Configuration")

    rules_file = st.file_uploader("Upload rules.yaml (optional)", type=["yaml", "yml"])
    if rules_file:
        rules = yaml.safe_load(rules_file)
        st.success("✅ Custom rules loaded")
    else:
        default_path = "config/rules.yaml"
        if os.path.exists(default_path):
            rules = load_rules(default_path)
            st.info("Using default config/rules.yaml")
        else:
            rules = None
            st.warning("No rules file found")

    sanitize_pii = st.checkbox("🔒 Enable PII sanitization", value=True)

# ── Main ──
uploaded_file = st.file_uploader(
    "Upload contract (PDF or DOCX)",
    type=["pdf", "docx"]
)

if uploaded_file and rules:
    if st.button("▶ Analyse Contract", type="primary"):

        with st.spinner("Analysing contract..."):

            # Save to temp file
            suffix = ".pdf" if uploaded_file.name.endswith(".pdf") else ".docx"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name

            # Extract text
            text = extract_text(tmp_path)
            clauses = split_into_clauses(text)

            # PII sanitization
            pii_mapping = {}
            if sanitize_pii:
                try:
                    from scanner.sanitizer import sanitize
                    text, pii_mapping = sanitize(text)
                    st.info(f"🔒 PII sanitized: {len(pii_mapping)} entities redacted")
                except Exception as e:
                    st.warning(f"PII sanitization skipped: {e}")

            # Analyse
            metadata = extract_metadata(text, rules)
            analysis = analyze(text, clauses, rules)

            # Build PII summary
            pii_summary = {"total_entities": len(pii_mapping), "breakdown": {}}
            for placeholder in pii_mapping.keys():
                entity_type = placeholder.split("_")[0].replace("[", "")
                pii_summary["breakdown"][entity_type] = pii_summary["breakdown"].get(entity_type, 0) + 1

            os.unlink(tmp_path)

        # ── Results ──
        overall = analysis.get("overall_score", "UNKNOWN")
        color_map = {"RED": "🔴", "YELLOW": "🟡", "GREEN": "🟢"}
        st.subheader(f"{color_map.get(overall, '⚪')} Overall Risk: {overall}")

        tab1, tab2, tab3, tab4 = st.tabs(["📊 Metadata", "⚠️ Missing Clauses", "🔍 Risk Findings", "📄 Clause Extracts"])

        with tab1:
            st.subheader("Contract Metadata")
            meta_fields = {
                "parties": "Parties",
                "effective_date": "Effective Date",
                "governing_law": "Governing Law",
                "jurisdiction": "Jurisdiction",
                "notice_period": "Notice Period",
                "duration": "Duration",
                "auto_renewal": "Auto-Renewal",
            }
            for key, label in meta_fields.items():
                value = metadata.get(key, "Not detected")
                st.write(f"**{label}:** {value}")

        with tab2:
            st.subheader("Missing Clauses")
            missing = analysis.get("missing_clauses", [])
            if missing:
                for clause in missing:
                    st.error(f"⚠️ {clause} — not found in document")
            else:
                st.success("✅ All required clauses detected")

        with tab3:
            st.subheader("Risk Findings")
            findings = analysis.get("findings", {})
            if not findings:
                st.info("No risk patterns detected.")
            else:
                for category, items in findings.items():
                    st.write(f"**{category.replace('_', ' ').title()}**")
                    for item in items:
                        score = item["score"]
                        conf = item.get("confidence", "")
                        comment = item["comment"]
                        if score == "RED":
                            st.error(f"🔴 {comment} [{conf} confidence]")
                        elif score == "YELLOW":
                            st.warning(f"🟡 {comment} [{conf} confidence]")
                        else:
                            st.success(f"🟢 {comment} [{conf} confidence]")
                        if item.get("excerpt"):
                            st.caption(item["excerpt"])

        with tab4:
            st.subheader("Clause Extracts")
            found_extracts = analysis.get("found_extracts", {})
            if found_extracts:
                for clause_name, extract in found_extracts.items():
                    with st.expander(clause_name):
                        st.write(extract)
            else:
                st.info("No clause extracts available.")

        # ── Download ──
        st.subheader("📥 Download Report")
        output_dir = tempfile.mkdtemp()
        report_path = generate_report(
            uploaded_file.name, metadata, analysis, output_dir, pii_summary=pii_summary
        )
        with open(report_path, "rb") as f:
            st.download_button(
                "📝 Download Word Report",
                f,
                file_name=f"report_{uploaded_file.name}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

elif not rules:
    st.warning("⚠️ No rules file found. Ensure config/rules.yaml exists.")
else:
    st.info("👆 Upload a contract to begin analysis.")