# Tri-level single-cell evidence chain for aortic dissection

Analysis code supporting the manuscript *"Genetic susceptibility to aortic dissection and related aortopathies localizes to vascular wall cells, whereas macrophage inflammation marks established aortic disease: a tri-level single-cell dissection"* (submitted to *Genome Medicine*).

**Repository:** https://github.com/peterhu9517/aortic-dissection-scDRS-evidence
**Archived DOI:**&#8203; 10.57760/sciencedb.019x8 (ScienceDB)
**Licence:** MIT (code); CC-BY-4.0 for any shared processed data.

## Overview

- **Layer 1** — genetic susceptibility mapped onto the healthy human aortic single-cell atlas (scDRS, 16 curated aortic-disease genes).
- **Option 2** — GWAS → gene → scDRS using a MAGMA-free variant-to-gene framework on the same 57,999 cells.
- **Layer 2** — cross-cohort validation of the same 16-gene module across six public GEO aortic disease cohorts.

> **Interpretation after revision.** Layer 1 and Option 2 are *not* independent: 8 of the 16 curated genes (50%) also appear in the GWAS-weighted set, and both use the same cells. Their correlation (r = 0.78, bootstrap 95% CI 0.29–0.96) is directional support only. In Layer 2, **sample/donor-level inference is primary**; cell-level Mann–Whitney U P values are exploratory because cells are not independent biological replicates. The macrophage-associated signal is hypothesis-generating.

## Data sources (all public, de-identified)

| Source | Accession | Reference |
|--------|-----------|-----------|
| AAD GWAS summary statistics | OMIX007191-02 (NGDC/CNCB), 9,797,427 variants, GRCh37/hg19 | Du et al., *Genomics Proteomics Bioinformatics* 2025;23(5):qzaf039. doi:10.1093/gpbjnl/qzaf039 |
| Healthy arterial vasculature atlas (57,999 aortic cells) | CZ CELLxGENE Discover collection `8f17ac63-aaba-44b5-9b78-60f121da4c2f`, dataset `473452ed-3b89-466a-9610-14eb36cbd12c` | Zhao et al., *Cell Genomics* 2025;5(12):101034. doi:10.1016/j.xgen.2025.101034 |
| Six GEO cohorts | GSE213740, GSE155468, GSE224559, GSE226492, GSE254132, GSE222318 | cited individually in the manuscript reference list |

Raw single-cell matrices and GWAS summary statistics are **not** committed (see `.gitignore`); download them from the accessions above.

## Core analysis scripts

| Script | Purpose |
|---|---|
| `01_prepare_data.py`, `run_prep.py`, `run_probe.py` | data preparation / probing |
| `build_aad_gs.py` | 16-gene curated module and GWAS-weighted gene score (Option 2) |
| `run_layer1.py`, `02_run_scdrs.py`, `03_collect_results.py` | scDRS on the healthy-aorta atlas (Layer 1 / Option 2) |
| `compare_layers.py` | compare the cell-type z-score vectors |
| `run_layer2.py`, `run_layer2_multidataset.py` | cross-cohort disease-module scoring (Layer 2) |
| `fix_composition.py`, `make_gene_info.py` | composition and gene-annotation helpers |
| `robustness_simple.py`, `robustness_negctrl.py` | original robustness / expression-matched negative-control analyses |

## Post-review revision scripts (sample-level primary inference)

| Script | Purpose |
|---|---|
| `revision_analyses.py` | gene-set overlap (8/16), sample-level means + 95% CI, Welch tests, mixed-effects models, 2,000 **sample-level** label permutations, sample-level forest plot |
| `revision_sensitivity.py` | 11-gene reduced-panel re-scoring from the original count matrices (removes MIF, ALOX5, TP53, JAG1, MRC2) |
| `revision_figures.py` | redraws the four main figures / graphical abstract with GSE222318 on a separate scale and toned-down wording |
| `build_supplementary_v2.py` | **authoritative** Additional file 6: 8 pre-specified analyses, Tables S1–S7, Figures S1–S6 |
| `build_supplementary.py` | superseded first version of Additional file 6 (retained for provenance) |
| `swap_docx_figures.py` | replace the four embedded figures in the final manuscript .docx |
| `sync_docx_revision.py`, `patch_docx_review.py` | synchronise revised markdown text / tables into the manuscript .docx |
| `build_cover_letter.py`, `update_dossier.py` | rebuild the cover letter .docx and the submission dossier |
| `build_genome_medicine.py`, `patch_manuscript.py`, `patch_metadata.py` | original manuscript assembly and metadata backfill |
| `final_check.py`, `bundle_patch.py`, `bundle_build.py` | final consistency audit, last-mile wording fixes and submission-bundle manifest |

## Reproducing the primary result

```bash
python revision_analyses.py          # -> revision_out/donor_primary_table.csv,
                                     #    sample_level_permutation.csv, gene_set_overlap.csv
python revision_sensitivity.py       # -> revision_out/sensitivity_full/sensitivity_results.csv
python revision_figures.py           # -> revision_out/figures/*.png
python build_supplementary_v2.py     # -> Additional_file_6.docx
```

The reduced-panel sensitivity re-loads the original 10x/txt count matrices because the
processed lightweight `.h5ad` objects have `X = None`.

## Requirements

See `requirements.txt`. Python 3.13; scDRS 1.0.2; Scanpy 1.12.5; AnnData 0.13.4;
statsmodels (MixedLM); python-docx and Matplotlib for manuscript/figure generation.

## Licence

Code: **MIT**. Processed data (if shared): **CC-BY-4.0**.
