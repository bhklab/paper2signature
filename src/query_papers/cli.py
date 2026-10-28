"""Command-line runner for configured PubMed literature searches."""
from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from .constants import (
    DEFAULT_CONFIG_PATH,
    OUTPUTS_DIR,
    Config,
    ensure_output_dir,
    load_config,
)
from .query_pubmed import query_pubmed, write_pubmed_results


@dataclass
class QueryResult:
    name: str
    query: str
    count: int | None
    status: str
    error: str = ""
    output_file: str = ""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PubMed searches from TOML")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--demo", action="store_true", help="Use sample .txt queries")
    return parser.parse_args(argv)


def gather_queries_from_dir(dirpath: str | Path | None) -> list[tuple[str, str]]:
    if not dirpath:
        return []
    folder = Path(dirpath)
    if not folder.is_dir():
        return []
    result = []
    for path in sorted(folder.glob("*.txt")):
        query = path.read_text(encoding="utf-8").strip()
        if query:
            result.append((path.stem, query))
    return result


def collect_queries(config: Config, demo: bool = False) -> list[tuple[str, str]]:
    if demo:
        return gather_queries_from_dir("inputs/example/queries")
    if config.queries is not None:
        return [(f"query_{i}", q.strip()) for i, q in enumerate(config.queries, 1) if q.strip()]
    return gather_queries_from_dir(config.queries_dir)


def create_run_directory(base: Path = OUTPUTS_DIR) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S_%fZ")
    return ensure_output_dir(base / stamp)


def run_queries(queries: list[tuple[str, str]], config: Config, output_dir: Path) -> list[QueryResult]:
    rows = []
    for index, (name, query) in enumerate(queries, start=1):
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
        filename = f"results_{index:03d}_{safe}.xml"
        try:
            count, xml = query_pubmed(
                query, retmax=config.retmax, email=config.email,
                date_start=config.date_start, date_end=config.date_end,
            )
            if xml:
                write_pubmed_results(xml, output_dir / filename)
            else:
                filename = ""
            rows.append(QueryResult(name, query, count, "success", output_file=filename))
        except Exception as exc:  # noqa: BLE001
            rows.append(QueryResult(name, query, None, "failed", error=str(exc)))
    return rows


def write_summary(rows: list[QueryResult], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "count", "status", "query", "output_file", "error"])
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)


def write_run_metadata(rows: list[QueryResult], path: Path, args: argparse.Namespace, config: Config) -> None:
    metadata = {
        "generated_utc": datetime.now(UTC).isoformat(),
        "config": args.config,
        "demo": args.demo,
        "retmax": config.retmax,
        "date_start": config.date_start,
        "date_end": config.date_end,
        "results": [asdict(row) for row in rows],
    }
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = load_config(args.config)
    queries = collect_queries(config, demo=args.demo)
    if not queries:
        print("No PubMed queries found. Check inputs/config.toml or demo query files.")
        return 1
    folder = create_run_directory()
    rows = run_queries(queries, config, folder)
    write_summary(rows, folder / "summary.csv")
    write_run_metadata(rows, folder / "run_metadata.json", args, config)
    print(f"Results saved under {folder}")
    for row in rows:
        print(f"{row.name}: {row.status}; PubMed matches: {row.count}; {row.error}")
    return 1 if any(row.status == "failed" for row in rows) else 0
