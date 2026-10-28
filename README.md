# paper2signature

A reproducible pipeline for literature-based discovery, extraction, and curation of biological gene signatures.

**paper2signature** provides a collaborative framework for querying scientific publications, identifying potentially relevant biological signatures, and preparing structured evidence for downstream curation and LLM-assisted extraction. The project aims to improve reproducibility, streamline literature mining, and facilitate integration of curated signatures into computational analyses.

> **Project status:** PubMed retrieval and rule-based, abstract-level screening are available. LLM-assisted extraction, full-text signature verification, and comprehensive retrieval across large result sets are planned extensions; they are not performed by the commands below.

## Overview

The initial use case is the **MAR-40 immuno-oncology literature search**, focused on RNA-based, DNA-based, and integrated RNA + DNA signatures associated with response or resistance to immune checkpoint blockade (ICB).

| Search | Focus |
| --- | --- |
| Query 1 | RNA / transcriptomic signatures |
| Query 2 | DNA / genomic signatures and biomarkers, including tumor mutational burden (TMB) and mutation-derived signatures |
| Query 3 | Integrated RNA + DNA signatures |

The search covers all cancer types, including pan-cancer studies, and emphasizes PD-1, PD-L1, and CTLA-4 inhibition. The publication period is controlled in the configuration file; the current pilot may be restricted to a single year.

## Objectives

- Run reproducible PubMed searches from version-controlled query definitions.
- Retain publication metadata, titles, abstracts, and search-level records.
- Flag candidate RNA, DNA, and integrated signatures for scientific review.
- Distinguish broad genomic biomarkers (such as TMB) from multifeature signatures during curation.
- Support future LLM-assisted extraction, standardization, and validation of signature definitions.

## Repository structure

```text
paper2signature/
├── main.py                         # Command-line entry point
├── pixi.toml                       # Environment and task definitions
├── pixi.lock                       # Reproducible dependency lockfile
├── inputs/
│   ├── config.toml                 # PubMed queries and Entrez settings
│   └── example/                    # Example query files (if present)
├── src/
│   └── query_papers/
│       ├── cli.py                   # Query orchestration and run metadata
│       ├── constants.py             # Configuration loading and validation
│       ├── query_pubmed.py          # PubMed search and XML retrieval
│       └── summarize_pubmed.py      # Rule-based publication screening
├── tests/                           # Automated tests
└── outputs/                         # Generated results (typically git-ignored)
```

> The Python package directory is currently named `query_papers` for compatibility with the existing codebase, even though the repository is named `paper2signature`.

## Requirements

- [Pixi](https://pixi.sh/) installed and available from the terminal.
- Internet access to query NCBI PubMed.
- A valid email address for NCBI Entrez requests.

Python dependencies are managed by Pixi; a separate manual installation of Python packages is not required.

## Quick start

From the repository root:

```bash
# Install/synchronize the locked environment
pixi install

# Review configuration before running a search
# Edit inputs/config.toml to set email, dates, retmax, and queries

# Run the configured PubMed searches
pixi run python main.py --config inputs/config.toml
```

For a small pilot, use `retmax = 10`. The date window is specified separately:

```toml
retmax = 10
date_start = "2022/01/01"
date_end = "2022/12/31"
```

For the intended broader MAR-40 scope, the end date can be changed to `2026/10/28`. **Increasing the date window does not guarantee complete retrieval**: `retmax` currently limits the number of returned records per query. Full-coverage retrieval requires batching or pagination and validation against PubMed match counts.

## Screen retrieved publications

Each search creates a timestamped folder under `outputs/` containing PubMed XML results, a query-level `summary.csv`, and `run_metadata.json`.

Use the actual run folder generated on your machine:

```bash
pixi run python src/query_papers/summarize_pubmed.py \
  --input outputs/<RUN_FOLDER>/results_001_query_1.xml

pixi run python src/query_papers/summarize_pubmed.py \
  --input outputs/<RUN_FOLDER>/results_002_query_2.xml

pixi run python src/query_papers/summarize_pubmed.py \
  --input outputs/<RUN_FOLDER>/results_003_query_3.xml
```

By default, each command writes a CSV beside its input XML file, such as `results_001_query_1_summary.csv`.

The publication-level screening table includes bibliographic fields, cancer and ICB annotations, RNA/DNA keyword flags, candidate signature phrases, and preliminary eligibility indicators. The updated screening script also records query provenance, biomarker category, study focus, ICB response evidence, and manual-review status.

## Interpretation and quality control

**All automated screening labels are preliminary.** A keyword match does not establish that a paper developed a new signature, that both RNA and DNA were integrated into one model, or that a biomarker predicts clinical response to ICB.

In particular:

- `RNA_transcriptomic` and `DNA_genomic` indicate text-based signals, not verified signature modalities.
- `Novelty` indicates novelty-related wording; genuine novelty must be checked against prior literature.
- TMB, MSI, and single-gene mutations can be relevant biomarkers without being multifeature signatures.
- General survival or prognostic associations do not necessarily demonstrate treatment-specific predictive value.
- Reviews and ambiguous publications require appropriate review before inclusion in a curated signature catalogue.

Cross-query deduplication by PMID and full-text verification are recommended before downstream analysis.

## Development checks

```bash
pixi run lint
pixi run test
```

To check the screening script's Python syntax:

```bash
pixi run python -m py_compile src/query_papers/summarize_pubmed.py
```

Existing automated tests may not cover every literature-screening classification. Additional tests should be added as screening rules evolve.

## Planned extensions

- Complete, batched PubMed retrieval across the full publication window.
- Deduplicated master paper catalogue with query provenance.
- Evidence-based separation of signature development, validation, and single-biomarker studies.
- LLM-assisted extraction of signature names, features/genes, cohorts, endpoints, and validation evidence.
- Human-reviewed, standardized signature records for downstream analysis.

## Acknowledgments

This project builds upon the original paper-query workflow developed at the **BHK Lab**: [bhklab/query_papers](https://github.com/bhklab/query_papers).

The current repository extends this foundation through improved code organization, reproducible environment management using Pixi, and integration with downstream signature extraction and validation workflows.
