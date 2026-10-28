import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from query_papers.cli import collect_queries, gather_queries_from_dir
from query_papers.constants import Config


def test_gather_from_dir(tmp_path):
    (tmp_path / "b.txt").write_text("query b", encoding="utf-8")
    (tmp_path / "a.txt").write_text("query a", encoding="utf-8")
    assert gather_queries_from_dir(tmp_path) == [("a", "query a"), ("b", "query b")]


def test_inline_queries():
    assert collect_queries(Config(queries=["x", "y"])) == [("query_1", "x"), ("query_2", "y")]
