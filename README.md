# paper2signature

A reproducible pipeline for literature-based discovery, extraction, and curation of biological gene signatures.

**paper2signature** provides a collaborative framework for querying scientific publications, identifying relevant molecular signatures, and supporting LLM-assisted information extraction and standardization.

The project aims to improve reproducibility, streamline literature mining, and facilitate the integration of curated signatures into downstream computational and translational research.

## Overview

The pipeline is designed to support:

- **Literature discovery:** Retrieval of relevant scientific publications.
- **Signature identification:** Screening for molecular signatures and biomarkers across data modalities.
- **Information extraction:** Structured extraction of signature definitions, associated biological features, and supporting evidence.
- **Data harmonization:** Standardization of extracted information for downstream analyses.

The framework is intended to support diverse research applications, including immuno-oncology and biomarker discovery. PubMed querying and preliminary rule-based screening are currently available; LLM-assisted extraction and full-text verification are planned extensions.

## Getting Started

Install [Pixi](https://pixi.sh/) and, from the repository root, run:

```bash
pixi install
```

Review `inputs/config.toml` to set your PubMed query terms, NCBI email address, and publication date range. Then run:

```bash
pixi run python main.py --config inputs/config.toml
```

To run the available quality checks:

```bash
pixi run lint
pixi run test
```

## Acknowledgments

This project builds upon the original paper-query workflow developed at the **BHK Lab**: [bhklab/query_papers](https://github.com/bhklab/query_papers).

The current repository extends this foundation through improved code organization, reproducible environment management using Pixi, and support for downstream signature extraction and validation workflows.
