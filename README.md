# paper2signature

A reproducible pipeline for literature-based discovery, extraction, and curation of biological gene signatures.

**paper2signature** provides a collaborative framework for querying scientific publications, identifying relevant molecular signatures, and preparing structured information for downstream curation and LLM-assisted extraction. It aims to support reproducible literature mining and downstream computational and translational research.

## Overview

The framework supports literature discovery, preliminary signature screening, and structured publication-level outputs across molecular data modalities. Current functionality includes **PubMed search and XML retrieval** and **rule-based screening of titles and abstracts**. Comprehensive retrieval of large search result sets, full-text signature verification, and LLM-assisted extraction are future extensions.

## Getting started

Install [Pixi](https://pixi.sh/) and, from the repository root, prepare the environment:

```bash
pixi install
```

Edit `inputs/config.toml` to set your NCBI Entrez email, PubMed queries, publication date range, and `retmax` (maximum records retrieved per query).

## Usage

### 1. Search PubMed

```bash
pixi run python main.py --config inputs/config.toml
```

This creates a timestamped directory under `outputs/` with PubMed XML files, a search-level `summary.csv`, and `run_metadata.json`.

### 2. Extract publication CSVs

In **Git Bash**, identify the newest output folder:

```bash
RUN_DIR=$(find outputs -mindepth 1 -maxdepth 1 -type d | sort | tail -n 1)
echo "$RUN_DIR"
```

Then convert every XML file in that folder to a screening CSV using the existing script:

```bash
for xml in "$RUN_DIR"/results_*.xml; do
    [ -f "$xml" ] || continue
    pixi run python src/query_papers/summarize_pubmed.py --input "$xml"
done
```

Each `results_*.xml` produces a corresponding `results_*_summary.csv` in the same directory. These contain publication metadata and preliminary screening annotations. **The current workflow does not automatically create a deduplicated master catalogue.**

### 3. Validate the project

```bash
pixi run lint
pixi run test
```

## Notes

- Screening labels are keyword-based candidates, **not confirmed molecular signatures or verified ICB-response predictors**.
- `retmax` limits the number of records downloaded per query; the returned PubMed match count may be much larger.
- Generated `outputs/` files are normally excluded from Git version control.
- The Python module is currently named `query_papers` for compatibility with the existing implementation.

## Acknowledgments

This project builds upon the paper-query workflow developed at the **BHK Lab**: [bhklab/query_papers](https://github.com/bhklab/query_papers).

The current repository extends this foundation through improved code organization, reproducible environment management with Pixi, and preparation for downstream signature extraction and validation workflows.
