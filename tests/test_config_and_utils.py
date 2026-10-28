import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from query_papers.constants import ensure_output_dir, load_config


def test_valid_config(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('retmax = 10\nqueries = ["test"]', encoding="utf-8")
    cfg = load_config(path)
    assert cfg.retmax == 10
    assert cfg.queries == ["test"]


def test_invalid_config(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("retmax = -1", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(path)


def test_ensure_dir(tmp_path):
    assert ensure_output_dir(tmp_path / "new").is_dir()
