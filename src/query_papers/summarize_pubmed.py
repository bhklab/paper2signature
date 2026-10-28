"""Parse PubMed XML into a reproducible, rule-based literature-screening table.

The text flags are candidate screening annotations, not verified gene signatures.
"""

from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Output columns
# ---------------------------------------------------------------------------

COLUMNS = [
    "PMID",
    "Year",
    "Cancer",
    "ICB_Target",
    "ICB_Drug",
    "Title",
    "Journal",
    "Journal_Abbrev",
    "Publication_Type",
    "DOI",
    "ICB_specific",
    "RNA_transcriptomic",
    "DNA_genomic",
    "Biomarker_signature",
    "Novelty",
    "Extracted_Signature",
    "Pan_cancer_novel_signature",
    "Response_resistance",
    "Review",
    "Potentially_eligible",
    "Abstract",
    "Retrieved_By",
    "Biomarker_Category",
    "Study_Focus",
    "ICB_Response_Evidence",
    "Manual_Review",
]


# ---------------------------------------------------------------------------
# Cancer classification patterns
# Specific and broad cancer labels can coexist.
# ---------------------------------------------------------------------------

CANCER_PATTERNS = {
    "Pan-cancer": [
        r"\bpan[- ]?cancer\b",
        r"across (?:multiple )?cancer types",
        r"multiple (?:cancer|tumou?r) types",
    ],
    "Triple-negative breast cancer": [
        r"triple[- ]negative breast cancer",
        r"\btnbc\b",
    ],
    "Breast cancer": [
        r"breast (?:cancer|carcinoma|neoplasm)",
    ],
    "Hepatocellular carcinoma": [
        r"hepatocellular carcinoma",
        r"\bhcc\b",
    ],
    "Liver cancer": [
        r"liver (?:cancer|carcinoma)",
    ],
    "Glioblastoma": [
        r"glioblastoma",
        r"\bgbm\b",
    ],
    "Glioma": [
        r"\bgliomas?\b",
    ],
    "Brain cancer": [
        r"brain (?:cancer|tumou?r|neoplasm)",
    ],
    "Urothelial carcinoma": [
        r"urothelial carcinoma",
    ],
    "Bladder cancer": [
        r"bladder (?:cancer|carcinoma)",
    ],
    "Pancreatic cancer": [
        r"pancreatic (?:cancer|carcinoma)",
    ],
    "Pancreatic ductal adenocarcinoma": [
        r"pancreatic ductal adenocarcinoma",
        r"\bpdac\b",
    ],
    "Non-small cell lung cancer": [
        r"non[- ]small cell lung cancer",
        r"\bnsclc\b",
    ],
    "Small cell lung cancer": [
        r"\bsmall cell lung cancer",
        r"\bsclc\b",
    ],
    "Lung cancer": [
        r"lung (?:cancer|carcinoma)",
    ],
    "Melanoma": [
        r"\bmelanoma\b",
    ],
    "Renal cell carcinoma": [
        r"renal cell carcinoma",
        r"\brcc\b",
    ],
    "Kidney cancer": [
        r"kidney cancer",
        r"renal cancer",
    ],
    "Colorectal cancer": [
        r"colorectal (?:cancer|carcinoma)",
        r"\bcrc\b",
    ],
    "Colon cancer": [
        r"colon (?:cancer|carcinoma)",
    ],
    "Rectal cancer": [
        r"rectal (?:cancer|carcinoma)",
    ],
    "Gastric cancer": [
        r"gastric (?:cancer|carcinoma)",
        r"stomach cancer",
    ],
    "Ovarian cancer": [
        r"ovarian (?:cancer|carcinoma)",
    ],
    "Prostate cancer": [
        r"prostat(?:e cancer|e carcinoma|ic cancer)",
    ],
    "Head and neck squamous cell carcinoma": [
        r"head and neck squamous cell carcinoma",
        r"\bhnscc\b",
    ],
    "Head and neck cancer": [
        r"head and neck cancer",
    ],
    "Oral squamous cell carcinoma": [
        r"oral squamous cell carcinoma",
        r"\boscc\b",
    ],
    "Diffuse large B-cell lymphoma": [
        r"diffuse large b[- ]cell lymphoma",
        r"\bdlbcl\b",
    ],
    "Lymphoma": [
        r"\blymphomas?\b",
    ],
    "Leukemia": [
        r"\bleuk(?:emia|aemia)\b",
    ],
    "Multiple myeloma": [
        r"multiple myeloma",
    ],
    "Esophageal cancer": [
        r"(?:esophageal|oesophageal) (?:cancer|carcinoma)",
    ],
    "Endometrial cancer": [
        r"endometrial (?:cancer|carcinoma)",
    ],
    "Cervical cancer": [
        r"cervical (?:cancer|carcinoma)",
    ],
    "Vulvar cancer": [
        r"vulvar (?:cancer|carcinoma)",
    ],
    "Anal cancer": [
        r"anal (?:cancer|carcinoma)",
    ],
    "Penile cancer": [
        r"penile (?:cancer|carcinoma|squamous cell carcinoma)",
    ],
    "Mesothelioma": [
        r"\bmesothelioma\b",
    ],
    "Soft tissue sarcoma": [
        r"soft tissue sarcoma",
        r"\bsts\b",
    ],
    "Sarcoma": [
        r"\bsarcomas?\b",
    ],
    "Thyroid cancer": [
        r"thyroid (?:cancer|carcinoma)",
    ],
    "Skin cancer": [
        r"skin cancer",
        r"cutaneous cancer",
    ],
}


# ---------------------------------------------------------------------------
# Immune checkpoint targets and drugs
# ---------------------------------------------------------------------------

TARGET_PATTERNS = {
    "PD-1": [
        r"\bpd[- ]?1\b",
        r"programmed cell death protein 1",
        r"programmed death 1 receptor",
    ],
    "PD-L1": [
        r"\bpd[- ]?l1\b",
        r"programmed death[- ]ligand 1",
    ],
    "CTLA-4": [
        r"\bctla[- ]?4\b",
    ],
    "LAG-3": [
        r"\blag[- ]?3\b",
    ],
    "TIGIT": [
        r"\btigit\b",
    ],
    "TIM-3": [
        r"\btim[- ]?3\b",
    ],
    "NKG2A": [
        r"\bnkg2a\b",
    ],
}

DRUGS = (
    "Nivolumab",
    "Pembrolizumab",
    "Atezolizumab",
    "Durvalumab",
    "Avelumab",
    "Ipilimumab",
    "Cemiplimab",
    "Dostarlimab",
    "Tremelimumab",
    "Relatlimab",
    "Toripalimab",
    "Sintilimab",
    "Tislelizumab",
    "Camrelizumab",
)


# ---------------------------------------------------------------------------
# Screening patterns
# ---------------------------------------------------------------------------

PAN_CANCER = CANCER_PATTERNS["Pan-cancer"]

ICB_TERMS = [
    r"immune checkpoint",
    r"checkpoint (?:blockade|inhibitor)",
    r"anti[- ]?(?:pd[- ]?1|pd[- ]?l1|ctla[- ]?4)",
    r"(?:pd[- ]?1|pd[- ]?l1|ctla[- ]?4) blockade",
]

RNA_TERMS = [
    r"\brna\b",
    r"rna[- ]?seq",
    r"transcriptom",
    r"gene expression",
    r"\bscrna",
]

DNA_TERMS = [
    r"\bdna\b",
    r"genom",
    r"mutat",
    r"copy number",
    r"methylation",
    r"whole[- ]exome",
    r"\bwes\b",
    r"whole[- ]genome",
    r"\bwgs\b",
    r"tumou?r mutational burden",
    r"\btmb\b",
]

BIOMARKER_TERMS = [
    r"biomarker",
    r"signature",
    r"predicti",
    r"predictor",
    r"classifier",
]

NOVELTY_TERMS = [
    r"\bnovel(?:ty)?\b",
    r"\bnew (?:biomarkers?|signatures?)\b",
    r"newly (?:identified|developed|discovered)",
    r"previously (?:unrecognized|unknown)",
    r"(?:emerging|candidate) (?:biomarkers?|signatures?)",
]

RESPONSE_TERMS = [
    r"\bresponse\b",
    r"\brespond",
    r"\bresistan",
    r"\bsensitiv",
    r"\boutcome",
    r"\bsurvival",
    r"\befficacy",
    r"\bbenefit",
]


# ---------------------------------------------------------------------------
# Additional MAR-40 screening patterns (candidate annotations only)
# ---------------------------------------------------------------------------

BIOMARKER_CATEGORY_PATTERNS = {
    "RNA expression": [
        r"gene expression (?:signatures?|classifiers?)",
        r"transcriptomic signatures?",
        r"rna[- ]?based signatures?",
        r"expression[- ]based signatures?",
        r"immune[- ]related (?:gene )?signatures?",
    ],
    "TMB": [r"tumou?r mutational burden", r"\btmb\b"],
    "Mutation-derived": [
        r"mutational signatures?",
        r"mutation[- ](?:based|derived) signatures?",
        r"mutational profiles?",
    ],
    "DNA methylation": [r"dna methylation", r"methylation signatures?"],
    "Copy number / instability": [
        r"copy[- ]number",
        r"aneuploidy",
        r"chromosomal instability",
    ],
    "MSI / MMR": [
        r"microsatellite instability",
        r"mismatch repair deficien",
        r"\bmsi[- ]?(?:high|h)?\b",
        r"\bdmmr\b",
    ],
    "DNA repair": [r"dna (?:damage )?repair", r"homologous recombination deficien"],
    "Neoantigen": [r"neoantigen"],
}

SIGNATURE_MODEL_TERMS = [
    r"\bsignatures?\b",
    r"\bclassifiers?\b",
    r"\bpredictive models?\b",
    r"\bpredictive scores?\b",
]

DEVELOPMENT_TERMS = [
    r"\bdevelop(?:ed|ing|ment)?\b",
    r"\bconstruct(?:ed|ion)?\b",
    r"\bderiv(?:ed|ation)\b",
    r"\bbuilt\b",
    r"\btrain(?:ed|ing)\b",
]

VALIDATION_TERMS = [
    r"\bvalidat(?:e|ed|ion)\b",
    r"\bexternal validation\b",
    r"\bindependent cohort\b",
]

# Pairing an ICB concept and an outcome in an abstract is only suggestive.
ICB_RESPONSE_EVIDENCE_TERMS = [
    (
        r"(?:immunotherapy|immune checkpoint(?: blockade| inhibitors?)?)"
        r".{0,65}(?:response|resistance|clinical benefit|predict)"
    ),
    (
        r"(?:response|resistance|clinical benefit|predict)"
        r".{0,65}(?:immunotherapy|immune checkpoint(?: blockade| inhibitors?)?)"
    ),
    (
        r"(?:anti[- ]?pd[- ]?1|anti[- ]?pd[- ]?l1|anti[- ]?ctla[- ]?4)"
        r".{0,65}(?:response|resistance|clinical benefit|predict)"
    ),
    (
        r"(?:response|resistance|clinical benefit|predict)"
        r".{0,65}(?:anti[- ]?pd[- ]?1|anti[- ]?pd[- ]?l1|anti[- ]?ctla[- ]?4)"
    ),
]


def classify_mar40_paper(
    text: str,
    *,
    icb_specific: bool,
    is_review: bool,
) -> dict[str, str | bool]:
    """Annotate abstract-level evidence; do not confirm a study's eligibility."""
    categories = [
        name
        for name, patterns in BIOMARKER_CATEGORY_PATTERNS.items()
        if contains_any(text, patterns)
    ]
    has_signature = contains_any(text, SIGNATURE_MODEL_TERMS)
    has_development = contains_any(text, DEVELOPMENT_TERMS)
    has_validation = contains_any(text, VALIDATION_TERMS)

    if is_review:
        study_focus = "Review"
    elif has_signature and has_development:
        study_focus = "Possible signature development"
    elif has_signature and has_validation:
        study_focus = "Possible signature validation"
    elif categories:
        study_focus = "Biomarker investigation"
    else:
        study_focus = "Unclear"

    if icb_specific and contains_any(text, ICB_RESPONSE_EVIDENCE_TERMS):
        evidence = "Possible direct ICB-response evidence"
    elif icb_specific:
        evidence = "ICB mentioned; response link unclear"
    else:
        evidence = "Unclear"

    return {
        "Biomarker_Category": "; ".join(categories) if categories else "Unclear",
        "Study_Focus": study_focus,
        "ICB_Response_Evidence": evidence,
        "Manual_Review": True,
    }


# ---------------------------------------------------------------------------
# Candidate signature phrase patterns
# These identify mentions of signatures, not actual gene lists.
# ---------------------------------------------------------------------------

SIGNATURE_PATTERNS = [
    r"\b\d+[- ]gene(?:[- ]based)?(?:\s+[\w-]+){0,4}\s+signature\b",
    r"\bpan[- ]?cancer(?:\s+[\w-]+){0,4}\s+signature\b",
    (
        r"\b(?:[\w-]+\s+){0,4}"
        r"(?:gene expression|transcriptomic|genomic|"
        r"immune[- ]related|immune|predictive|molecular|"
        r"biomarker|prognostic|tumou?r inflammation|"
        r"t[- ]cell inflammation|interferon[- ]?gamma|"
        r"response|resistance|immunotherapy)"
        r"\s+signature\b"
    ),
    r"\bcheckpoint(?:\s+[\w-]+){0,3}\s+signature\b",
]


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------


def get_text(element: ET.Element | None) -> str:
    """Collect text, including inline markup, from an XML element."""
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


def contains_any(text: str, patterns: list[str]) -> bool:
    """Check whether any case-insensitive pattern matches."""
    return any(
        re.search(pattern, text, re.IGNORECASE) is not None for pattern in patterns
    )


def _matched_labels(
    text: str,
    patterns: dict[str, list[str]],
) -> str:
    """Return matching labels as a semicolon-separated string."""
    return "; ".join(
        label for label, terms in patterns.items() if contains_any(text, terms)
    )


# ---------------------------------------------------------------------------
# Cancer and ICB extraction
# ---------------------------------------------------------------------------


def extract_cancer_type(text: str) -> str:
    """Identify cancer types mentioned in title or abstract."""
    return _matched_labels(text, CANCER_PATTERNS)


def extract_icb_targets(text: str) -> str:
    """Identify immune checkpoint targets."""
    return _matched_labels(text, TARGET_PATTERNS)


def extract_icb_drugs(text: str) -> str:
    """Identify named immune checkpoint inhibitor drugs."""
    return "; ".join(
        drug
        for drug in DRUGS
        if re.search(
            rf"\b{re.escape(drug)}\b",
            text,
            re.IGNORECASE,
        )
    )


def extract_signature_phrases(text: str) -> str:
    """Extract candidate named signature phrases.

    These are text mentions and require manual verification.
    They are not extracted gene lists.
    """
    found: dict[str, str] = {}

    for pattern in SIGNATURE_PATTERNS:
        for match in re.finditer(
            pattern,
            text,
            re.IGNORECASE,
        ):
            phrase = " ".join(match.group(0).split())

            if phrase and len(phrase) <= 180:
                found.setdefault(
                    phrase.casefold(),
                    phrase,
                )

    return "; ".join(found.values())


# ---------------------------------------------------------------------------
# PubMed metadata extraction
# ---------------------------------------------------------------------------


def _year(article: ET.Element) -> str:
    """Extract publication year using available PubMed fields."""
    for path in (
        "Journal/JournalIssue/PubDate/Year",
        "ArticleDate/Year",
    ):
        value = article.findtext(
            path,
            default="",
        ).strip()

        if re.fullmatch(r"\d{4}", value):
            return value

    medline_date = article.findtext(
        "Journal/JournalIssue/PubDate/MedlineDate",
        default="",
    )

    match = re.search(
        r"\b(?:19|20)\d{2}\b",
        medline_date,
    )

    return match.group(0) if match else ""


def _abstract(article: ET.Element) -> str:
    """Extract complete abstract, including section labels."""
    parts: list[str] = []

    for node in article.findall("Abstract/AbstractText"):
        value = get_text(node)

        if value:
            label = node.attrib.get("Label", "").strip()

            parts.append(f"{label}: {value}" if label else value)

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Process one PubMed article
# ---------------------------------------------------------------------------


def _article_row(
    pubmed_article: ET.Element,
) -> dict | None:
    """Convert a PubMed article into a screening record."""

    citation = pubmed_article.find("MedlineCitation")

    article = citation.find("Article") if citation is not None else None

    if citation is None or article is None:
        return None

    # Basic publication information
    title = get_text(article.find("ArticleTitle"))
    abstract = _abstract(article)
    screening_text = f"{title} {abstract}"

    publication_type = "; ".join(
        get_text(node)
        for node in article.findall("PublicationTypeList/PublicationType")
        if get_text(node)
    )

    doi = next(
        (
            get_text(node)
            for node in pubmed_article.findall("PubmedData/ArticleIdList/ArticleId")
            if node.get("IdType", "").lower() == "doi"
        ),
        "",
    )

    # Cancer and immunotherapy annotations
    cancer = extract_cancer_type(screening_text)
    icb_targets = extract_icb_targets(screening_text)
    icb_drugs = extract_icb_drugs(screening_text)

    icb_specific = (
        contains_any(screening_text, ICB_TERMS) or bool(icb_targets) or bool(icb_drugs)
    )

    # Molecular modality annotations
    rna_transcriptomic = contains_any(
        screening_text,
        RNA_TERMS,
    )

    dna_genomic = contains_any(
        screening_text,
        DNA_TERMS,
    )

    # Biomarker and novelty annotations
    biomarker_signature = contains_any(
        screening_text,
        BIOMARKER_TERMS,
    )

    novelty = contains_any(
        screening_text,
        NOVELTY_TERMS,
    )

    response_resistance = contains_any(
        screening_text,
        RESPONSE_TERMS,
    )

    extracted_signature = extract_signature_phrases(screening_text)

    is_pan_cancer = contains_any(
        screening_text,
        PAN_CANCER,
    )

    pan_cancer_novel_signature = is_pan_cancer and novelty and bool(extracted_signature)

    # Publication type
    is_review = any(
        item.strip().casefold() == "review" for item in publication_type.split(";")
    )

    # Preliminary screening eligibility
    # Keyword-based only; manual review is required.
    potentially_eligible = (
        icb_specific
        and biomarker_signature
        and response_resistance
        and (rna_transcriptomic or dna_genomic)
    )

    mar40_screening = classify_mar40_paper(
        screening_text,
        icb_specific=icb_specific,
        is_review=is_review,
    )

    return {
        "PMID": citation.findtext(
            "PMID",
            default="",
        ).strip(),
        "Year": _year(article),
        "Cancer": cancer,
        "ICB_Target": icb_targets,
        "ICB_Drug": icb_drugs,
        "Title": title,
        "Journal": article.findtext(
            "Journal/Title",
            default="",
        ),
        "Journal_Abbrev": citation.findtext(
            "MedlineJournalInfo/MedlineTA",
            default="",
        ),
        "Publication_Type": publication_type,
        "DOI": doi,
        "ICB_specific": icb_specific,
        "RNA_transcriptomic": rna_transcriptomic,
        "DNA_genomic": dna_genomic,
        "Biomarker_signature": biomarker_signature,
        "Novelty": novelty,
        "Extracted_Signature": extracted_signature,
        "Pan_cancer_novel_signature": pan_cancer_novel_signature,
        "Response_resistance": response_resistance,
        "Review": is_review,
        "Potentially_eligible": potentially_eligible,
        "Abstract": abstract,
        "Retrieved_By": "Unknown",
        **mar40_screening,
    }


# ---------------------------------------------------------------------------
# Parse complete PubMed XML
# ---------------------------------------------------------------------------


def parse_pubmed_xml(
    xml_file: str | Path,
) -> pd.DataFrame:
    """Parse standard PubMed XML into a paper-level screening table.

    Each PubmedArticle becomes one row. Missing metadata fields are empty;
    screening fields may contain Unclear. Empty results retain all columns.
    """

    root = ET.parse(xml_file).getroot()

    rows = []

    for node in root.findall(".//PubmedArticle"):
        row = _article_row(node)

        if row is not None:
            rows.append(row)

    df = pd.DataFrame(rows, columns=COLUMNS)

    # Source query is provenance only; it does not confirm signature modality.
    source_query = {
        "results_001_query_1.xml": "RNA",
        "results_002_query_2.xml": "DNA",
        "results_003_query_3.xml": "RNA+DNA",
    }.get(Path(xml_file).name, "Unknown")
    df["Retrieved_By"] = source_query
    return df


# ---------------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------------


def main(
    argv: list[str] | None = None,
) -> int:
    """Summarize a PubMed XML file and save a screening CSV."""

    parser = argparse.ArgumentParser(
        description=(
            "Screen standard PubMed XML for candidate "
            "immunotherapy-related gene signatures."
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the input PubMed XML file.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output CSV path (default: next to input XML).",
    )

    args = parser.parse_args(argv)

    if not args.input.is_file():
        parser.error(f"Input XML file not found: {args.input}")

    output_file = (
        args.output
        if args.output is not None
        else args.input.with_name(f"{args.input.stem}_summary.csv")
    )

    try:
        df = parse_pubmed_xml(args.input)

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        df.to_csv(
            output_file,
            index=False,
            encoding="utf-8-sig",
        )

    except (OSError, ET.ParseError) as exc:
        parser.exit(
            1,
            f"ERROR: {exc}\n",
        )

    # Console summary
    print(f"Publications parsed: {len(df)}")

    screening_columns = (
        "ICB_specific",
        "RNA_transcriptomic",
        "DNA_genomic",
        "Biomarker_signature",
        "Novelty",
        "Pan_cancer_novel_signature",
        "Review",
        "Potentially_eligible",
    )

    for column in screening_columns:
        print(f"{column}: {int(df[column].sum())}")

    print(f"Screening CSV saved: {output_file}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
