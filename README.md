# paper2signature

A reproducible workflow for finding scientific publications and identifying candidate molecular signatures.

**paper2signature** helps researchers search PubMed, save publication records, and create CSV tables for reviewing potential biological signatures and biomarkers. It is designed for collaborative research and future LLM-assisted extraction and curation.

> **What works today?** PubMed searches, XML downloads, and preliminary title/abstract screening. Automated full-text verification, comprehensive retrieval of every search match, and LLM-assisted signature extraction are not yet part of this workflow.

## Quick start

### 1. Get the repository and set up Pixi

Install [Pixi](https://pixi.sh/) if you do not already have it.

Clone the repository from its current GitHub location, then open a terminal in the project folder. For example:

```bash
git clone https://github.com/RibaA/paper2signature.git
cd paper2signature
pixi install
```

If you already downloaded or cloned the project, just open a terminal in that folder and run `pixi install`.

### 2. Set up your PubMed search

Open **`inputs/config.toml`** in a text editor (such as VS Code). Check these settings:

```toml
email = "your.email@institution.org"
retmax = 10
date_start = "2022/01/01"
date_end = "2022/12/31"
```

- **`email`**: Your contact email for NCBI Entrez requests.
- **`retmax`**: Maximum number of publication records to retrieve *per query* in the current implementation. Start with `10` for a trial run.
- **`date_start` / `date_end`**: Publication date range.
- **`queries`**: The PubMed searches defined later in the same configuration file.

Save the file before running the search.

### 3. Search PubMed

In the project folder, run:

```bash
pixi run python main.py --config inputs/config.toml
```

A new timestamped folder will appear under **`outputs/`**, containing files such as:

```text
outputs/
└── <RUN_ID>/
    ├── results_*.xml          # PubMed records for each query 
    ├── summary.csv            # Search-level summary
    ├── run_metadata.json      # Run information
    └── results_*_summary.csv  # Extracted publication data
```

If one query fails, check `summary.csv` for its status and error.

### 4. Convert the XML records to CSV

You do not need another Python script. The existing **`summarize_pubmed.py`** handles this step.

**For Git Bash (Windows) or a Bash terminal**, run:

```bash
RUN_DIR=$(find outputs -mindepth 1 -maxdepth 1 -type d | sort | tail -n 1)
echo "$RUN_DIR"

for xml in "$RUN_DIR"/results_*.xml; do
    pixi run python src/query_papers/summarize_pubmed.py --input "$xml"
done
```

This processes every `results_*.xml` file in the selected run and creates a CSV beside each XML.

### 5. Review your results

Open the CSV files in Excel or your preferred data-analysis software:

| File | What it contains |
| --- | --- |
| `summary.csv` | Number of PubMed matches, downloaded-record counts, and query status. |
| `results_*_summary.csv` | One row per retrieved paper, including title, abstract, PMID, and preliminary screening annotations. |
| `run_metadata.json` | Settings and metadata for the search run. |

**Important:** Screening labels are based on text patterns and are **not confirmed signature findings**. 

## Check that the project is working

Run these commands from the project folder:

```bash
pixi run lint
pixi run test
pixi run python main.py --help
```

## Acknowledgments

This project builds on the original paper-query workflow from the **BHK Lab**: [bhklab/query_papers](https://github.com/bhklab/query_papers).

The repository extends that foundation with reproducible environment management using Pixi and a workflow intended to support downstream signature extraction and curation.
