import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from query_papers.summarize_pubmed import parse_pubmed_xml


def test_screening_output_columns(tmp_path):
    path = tmp_path / "results_002_query_2.xml"
    path.write_text("""<PubmedArticleSet><PubmedArticle>
    <MedlineCitation><PMID>12</PMID><Article>
    <ArticleTitle>Mutational signature predicts response to anti-PD-1</ArticleTitle>
    <Abstract><AbstractText>A genomic classifier was developed and validated.</AbstractText></Abstract>
    <Journal><Title>Test</Title><JournalIssue><PubDate><Year>2022</Year></PubDate></JournalIssue></Journal>
    </Article></MedlineCitation></PubmedArticle></PubmedArticleSet>""", encoding="utf-8")
    df = parse_pubmed_xml(path)
    assert len(df) == 1
    assert df.loc[0, "PMID"] == "12"
    assert df.loc[0, "Retrieved_By"] == "DNA"
    assert "Biomarker_Category" in df.columns
    assert "Manual_Review" in df.columns
