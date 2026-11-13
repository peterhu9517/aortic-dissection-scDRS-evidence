# Tri-level single-cell evidence chain for aortic dissection

Analysis code supporting the manuscript *"Genome-wide and single-cell evidence converge on macrophage inflammation in aortic dissection"* (submitted to *Genome Medicine*).

## Overview

This project builds a three-level evidence chain for aortic dissection / thoracic aortic disease:

- **Layer 1** — genetic susceptibility mapped onto the healthy human aortic single-cell atlas (scDRS).
- **Option 2** — GWAS → gene → scDRS enrichment of an AAD GWAS.
- **Layer 2** — cross-cohort validation of a 16-gene disease module across six GEO cohorts.

## Data sources (all public, de-identified)

| Source | Accession | Reference |
|--------|-----------|-----------|
| AAD GWAS summary statistics | OMIX007191-02 (NGDC/CNCB) | Du et al., *Genomics Proteomics Bioinformatics* 2025;23(5):qzaf039. doi:10.1093/gpbjnl/qzaf039 |
| Healthy arterial vasculature atlas (57,999 aortic cells) | CZ CELLxGENE Discover collection `8f17ac63-aaba-44b5-9b78-60f121da4c2f` | Zhao et al., *Cell Genomics* 2025;5(12):101034. doi:10.1016/j.xgen.2025.101034 |
| Six GEO cohorts | GSE213740, GSE155468, GSE224559, GSE226492, GSE254132, GSE222318 | cited individually in the manuscript reference list |

## Analysis scripts

- `01_prepare_data.py` — download / prepare the six GEO cohorts and the healthy-aorta atlas subset
- `build_aad_gs.py` — build the 16-gene disease module and the AAD GWAS gene score (Option 2)
- `run_layer1.py` — scDRS on the healthy-aorta atlas (Layer 1) and on the GWAS-derived gene set (Option 2)
- `compare_layers.py` — compare Layer 1 / Option 2 / Layer 2 evidence
- `run_layer2.py`, `run_layer2_multidataset.py` — cross-cohort disease-module scoring (Layer 2)
- `robustness_simple.py`, `robustness_negctrl.py` — Supplementary file 6 sensitivity analyses
- `build_genome_medicine.py`, `build_supplementary.py`, `patch_manuscript.py`, `patch_metadata.py` — manuscript assembly

Raw single-cell matrices and GWAS summary statistics are **not** committed (see `.gitignore`); download them from the accessions above.

## Requirements

See `requirements.txt`. Python 3.13; scDRS 1.0.2; Scanpy 1.12.5; AnnData 0.13.4.

## License

Code: **MIT**. Processed data (if shared): **CC-BY-4.0**.
