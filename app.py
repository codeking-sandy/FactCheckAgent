import os
import re
import json
import time
from typing import List, Dict, Any

import requests
import streamlit as st
import pandas as pd
from pypdf import PdfReader
from dotenv import load_dotenv
from groq import Groq


load_dotenv()

st.set_page_config(
    page_title="Fact-Check Agent",
    page_icon="✅",
    layout="wide",
)

st.markdown("""
<style>
.main-title {
    font-size: 2.7rem;
    font-weight: 900;
    margin-bottom: 0.2rem;
}
.subtitle {
    font-size: 1.08rem;
    color: #888;
    margin-bottom: 1.5rem;
}
.claim-card {
    padding: 1.2rem;
    border-radius: 16px;
    border: 1px solid #333;
    margin-bottom: 0.9rem;
    background: rgba(255,255,255,0.02);
}
.verified { border-left: 8px solid #22c55e; }
.inaccurate { border-left: 8px solid #f59e0b; }
.false { border-left: 8px solid #ef4444; }

.badge {
    padding: 0.22rem 0.6rem;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.85rem;
}
.badge-verified {
    background: rgba(34,197,94,0.18);
    color: #22c55e;
}
.badge-inaccurate {
    background: rgba(245,158,11,0.18);
    color: #f59e0b;
}
.badge-false {
    background: rgba(239,68,68,0.18);
    color: #ef4444;
}
</style>
""", unsafe_allow_html=True)


FACTCHECK_SYSTEM_PROMPT = """
You are a strict fact-checking analyst.

Verify the claim ONLY using the provided web evidence.
Do not use outside knowledge.
Do not guess.

Use exactly one status:
- Verified: evidence clearly supports the claim.
- Inaccurate: evidence is related but the claim has an outdated/wrong number, date, ranking, amount, or misleading detail.
- False: evidence contradicts the claim, or there is no reliable evidence supporting it.

Return ONLY valid JSON in this exact schema:
{
  "status": "Verified | Inaccurate | False",
  "reason": "short explanation based only on evidence",
  "correct_fact": "correct fact if evidence provides it, otherwise unable to determine",
  "confidence": 0.0
}
"""


def get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def pdf_to_text(uploaded_file) -> str:
    reader = PdfReader(uploaded_file)
    return "\n".join([(page.extract_text() or "") for page in reader.pages])


def split_sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 25]


def looks_like_claim(sentence: str) -> bool:
    patterns = [
        r"\b\d{4}\b",
        r"\b\d+(\.\d+)?\s?%",
        r"\$\s?\d+",
        r"₹\s?\d+|Rs\.?\s?\d+|INR\s?\d+",
        r"\b\d+(\.\d+)?\s?(million|billion|trillion|crore|lakh|bn|mn)\b",
        r"\b(first|largest|smallest|fastest|most|least|leading|number one|No\. 1)\b",
        r"\b(increased|decreased|grew|declined|reached|launched|founded|acquired|reported|revenue|population|users)\b",
        r"\b(capital|located|released|delivered|founded|launched)\b",
    ]
    return any(re.search(p, sentence, re.IGNORECASE) for p in patterns)


def extract_claims(text: str, max_claims: int) -> List[str]:
    claims = []
    seen = set()

    for sentence in split_sentences(text):
        if looks_like_claim(sentence):
            cleaned = sentence.strip(" -•\t")
            key = cleaned.lower()

            if key not in seen:
                claims.append(cleaned)
                seen.add(key)

        if len(claims) >= max_claims:
            break

    return claims


def tavily_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    api_key = get_env("TAVILY_API_KEY")

    if not api_key:
        st.warning("TAVILY_API_KEY missing.")
        return []

    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "advanced",
                "include_answer": True,
                "include_raw_content": False,
                "max_results": max_results,
            },
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

        results = []

        if data.get("answer"):
            results.append({
                "title": "Tavily Answer",
                "url": "",
                "content": data.get("answer", ""),
            })

        for item in data.get("results", []):
            results.append({
                "title": item.get("title", "Untitled"),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
            })

        return results[:max_results]

    except Exception as exc:
        st.warning(f"Tavily search failed: {exc}")
        return []


def clean_json(raw: str) -> Dict[str, Any]:
    raw = raw.strip()
    raw = re.sub(r"^```json", "", raw)
    raw = re.sub(r"^```", "", raw)
    raw = re.sub(r"```$", "", raw)

    start = raw.find("{")
    end = raw.rfind("}")

    if start != -1 and end != -1:
        raw = raw[start:end + 1]

    return json.loads(raw)


def verify_with_groq(claim: str, evidence: List[Dict[str, str]]) -> Dict[str, Any]:
    api_key = get_env("GROQ_API_KEY")

    if not api_key:
        return {
            "status": "False",
            "reason": "GROQ_API_KEY missing. AI verification could not run.",
            "correct_fact": "Add GROQ_API_KEY in .env or Streamlit Secrets.",
            "confidence": 0.10,
        }

    if not evidence:
        return {
            "status": "False",
            "reason": "No live web evidence found for this claim.",
            "correct_fact": "Unable to verify from live web.",
            "confidence": 0.30,
        }

    evidence_text = "\n\n".join([
        f"Source {idx + 1}\nTitle: {e.get('title')}\nURL: {e.get('url')}\nContent: {e.get('content')}"
        for idx, e in enumerate(evidence)
    ])

    user_prompt = f"""
Claim:
{claim}

Web evidence:
{evidence_text[:12000]}
"""

    try:
        client = Groq(api_key=api_key)

        completion = client.chat.completions.create(
            model=get_env("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=[
                {"role": "system", "content": FACTCHECK_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )

        raw = completion.choices[0].message.content
        result = clean_json(raw)

        if result.get("status") not in {"Verified", "Inaccurate", "False"}:
            result["status"] = "False"

        result["confidence"] = float(result.get("confidence", 0.5))

        return result

    except Exception as exc:
        return {
            "status": "False",
            "reason": f"Groq verification failed: {exc}",
            "correct_fact": "Retry or check GROQ_API_KEY / model availability.",
            "confidence": 0.10,
        }


def status_class(status: str) -> str:
    return {
        "Verified": "verified",
        "Inaccurate": "inaccurate",
        "False": "false",
    }.get(status, "false")


def badge_class(status: str) -> str:
    return {
        "Verified": "badge-verified",
        "Inaccurate": "badge-inaccurate",
        "False": "badge-false",
    }.get(status, "badge-false")


def render_sources(evidence: List[Dict[str, str]]):
    if not evidence:
        st.caption("No web evidence found.")
        return

    with st.expander("View web evidence"):
        for idx, source in enumerate(evidence, start=1):
            title = source.get("title") or "Source"
            url = source.get("url")
            content = source.get("content") or ""

            st.markdown(f"**Source {idx}:**")

            if url:
                st.markdown(f"[{title}]({url})")
            else:
                st.markdown(title)

            st.caption(content[:700])


def main():
    st.markdown('<div class="main-title">Fact-Check Agent</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Upload a PDF. The app extracts factual claims, searches live web evidence, and uses AI verification to classify them.</div>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Settings")
        max_claims = st.slider("Maximum claims to verify", 3, 20, 8)
        search_results = st.slider("Web sources per claim", 3, 8, 5)

        st.divider()
        st.markdown("### API Status")
        st.write("Tavily:", "✅" if get_env("TAVILY_API_KEY") else "❌")
        st.write("Groq:", "✅" if get_env("GROQ_API_KEY") else "❌")

    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_pdf is None:
        st.info("Upload a PDF to start automated fact-checking.")
        st.markdown("""
        **This app checks:**
        - Statistics and percentages
        - Dates and launches
        - Market size and revenue figures
        - Financial or technical numbers
        - Ranking or superlative claims
        """)
        return

    if st.button("Run Fact Check", type="primary", use_container_width=True):
        with st.spinner("Reading PDF..."):
            pdf_text = pdf_to_text(uploaded_pdf)

        if not pdf_text.strip():
            st.error("No readable text found. Scanned PDFs are not supported.")
            return

        with st.spinner("Extracting fact-checkable claims..."):
            claims = extract_claims(pdf_text, max_claims)

        if not claims:
            st.warning("No strong fact-checkable claims found.")
            return

        rows = []
        progress = st.progress(0)

        st.subheader("Fact-check Report")

        for idx, claim in enumerate(claims):
            with st.spinner(f"Checking claim {idx + 1}/{len(claims)}..."):
                evidence = tavily_search(claim, search_results)
                verdict = verify_with_groq(claim, evidence)

                top_sources = "; ".join([
                    e.get("url", "") for e in evidence if e.get("url")
                ][:3])

                rows.append({
                    "claim": claim,
                    "status": verdict.get("status", "False"),
                    "reason": verdict.get("reason", ""),
                    "correct_fact": verdict.get("correct_fact", ""),
                    "confidence": verdict.get("confidence", 0),
                    "sources": top_sources,
                    "evidence": evidence,
                })

                progress.progress((idx + 1) / len(claims))
                time.sleep(0.2)

        df = pd.DataFrame([
            {k: v for k, v in row.items() if k != "evidence"}
            for row in rows
        ])

        st.success(f"Processed {len(rows)} claims successfully.")

        c1, c2, c3 = st.columns(3)
        c1.metric("Verified", int((df["status"] == "Verified").sum()))
        c2.metric("Inaccurate", int((df["status"] == "Inaccurate").sum()))
        c3.metric("False", int((df["status"] == "False").sum()))

        st.download_button(
            "Download CSV Report",
            df.to_csv(index=False).encode("utf-8"),
            file_name="fact_check_report.csv",
            mime="text/csv",
            use_container_width=True,
        )

        for i, row in enumerate(rows, start=1):
            klass = status_class(row["status"])
            badge = badge_class(row["status"])

            st.markdown(
                f"""
                <div class="claim-card {klass}">
                    <b>Claim {i}</b><br>
                    <span>{row['claim']}</span><br><br>
                    <span class="badge {badge}">{row['status']}</span>
                    &nbsp; <b>Confidence:</b> {row['confidence']}<br><br>
                    <b>Reason:</b> {row['reason']}<br>
                    <b>Correct Fact:</b> {row['correct_fact']}
                </div>
                """,
                unsafe_allow_html=True,
            )

            render_sources(row["evidence"])


if __name__ == "__main__":
    main()