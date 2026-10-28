import io
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from query_papers.query_pubmed import query_pubmed, write_pubmed_results


class ByteContext(io.BytesIO):
    pass


def test_query_pubmed_with_mocks(tmp_path):
    with (
        patch("query_papers.query_pubmed.Entrez.esearch", return_value=ByteContext()),
        patch("query_papers.query_pubmed.Entrez.read", return_value={"Count": "5", "IdList": ["1", "2"]}),
        patch("query_papers.query_pubmed.Entrez.efetch", return_value=ByteContext(b"<PubmedArticleSet/>")),
    ):
        count, xml = query_pubmed("test", 2, "test@example.org")
    assert count == 5
    path = tmp_path / "articles.xml"
    write_pubmed_results(xml, path)
    assert path.read_bytes() == b"<PubmedArticleSet/>"
