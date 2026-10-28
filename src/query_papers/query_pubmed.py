"""Fetch PubMed search results through NCBI Entrez."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from Bio import Entrez


def query_pubmed(
    query: str,
    retmax: int,
    email: str,
    date_start: str | None = None,
    date_end: str | None = None,
) -> tuple[int, bytes | str]:
    """Return total matching PubMed records and XML for up to retmax papers.

    Important: count is TOTAL matches, not XML article count.
    """
    if not email:
        raise ValueError("Provide an Entrez email via config.toml or ENTREZ_EMAIL")
    if retmax <= 0:
        raise ValueError("retmax must be positive")
    Entrez.email = email
    kwargs: dict[str, Any] = {
        "db": "pubmed", "term": query, "retmax": retmax
    }
    if date_start or date_end:
        kwargs.update(
            mindate=date_start or "1800",
            maxdate=date_end or "3000",
            datetype="pdat",
        )
    with Entrez.esearch(**kwargs) as handle:
        results = Entrez.read(handle)
    if not isinstance(results, dict) or "Count" not in results or "IdList" not in results:
        raise ValueError("Unexpected PubMed ESearch results")
    total_count = int(results["Count"])
    ids = list(results["IdList"])
    if not ids:
        return total_count, b""
    with Entrez.efetch(db="pubmed", id=",".join(ids), retmode="xml") as handle:
        xml = handle.read()
    return total_count, xml


def write_pubmed_results(xml_content: bytes | str, filepath: str | Path) -> None:
    """Write PubMed XML to disk, propagating failures to the caller."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = xml_content.encode("utf-8") if isinstance(xml_content, str) else xml_content
    path.write_bytes(data)
