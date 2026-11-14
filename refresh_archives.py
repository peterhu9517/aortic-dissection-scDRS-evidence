"""Synchronise the code archive with the post-major-review revision.

1. Copy every analysis / manuscript-generation script into github_repo/.
2. Refresh README.md (final title, revision section, complete script list).
3. Rebuild Additional_file_4.zip (pipeline/ + helpers/ + manifest).
4. Rebuild github_repo/scidb_upload.zip (flat file list for ScienceDB).

The existing helpers/*.py entries are preserved by extracting them from the
old Additional_file_4.zip, because those helper scripts were generated inline
during the original packaging step and are no longer present on disk.
"""
import os, shutil, zipfile, io

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56"
PIPE = os.path.join(ROOT, "scdrs_pipeline")
REPO = os.path.join(ROOT, "github_repo")
AFDIR = os.path.join(ROOT, "output", "aortic_dissection_manuscript",
                     "submission_kit", "additional_files")
AF4 = os.path.join(AFDIR, "Additional_file_4.zip")
SCIDB_ZIP = os.path.join(REPO, "scidb_upload.zip")

TITLE = ("Genetic susceptibility to aortic dissection and related aortopathies "
         "localizes to vascular wall cells, whereas macrophage inflammation marks "
         "established aortic disease: a tri-level single-cell dissection")

# Archival wording must follow the manuscript: while the ScienceDB record is
# under review we must not claim a registered DOI. activate_doi.py flips the
# manuscript text, and a subsequent run of this script flips the archive too.
DOI = "10.57760/sciencedb.019x8"
M_MD = os.path.join(ROOT, "output", "aortic_dissection_manuscript", "stage3",
                    "Genome_Medicine_Full_Manuscript.md")
DOI_PENDING = "DOI activation pending" in open(M_MD, encoding="utf-8").read()
ARCHIVE_README = (
    "**Archival deposit:** ScienceDB record 019x8 (DOI activation pending). "
    "A versioned snapshot of the complete analysis code is supplied with the "
    "manuscript as Additional file 4."
    if DOI_PENDING else f"**Archived DOI:** {DOI} (ScienceDB)")
ARCHIVE_TXT = (
    "Archival deposit: ScienceDB record 019x8 (DOI activation pending); "
    "versioned code snapshot supplied as Additional file 4\n"
    if DOI_PENDING else f"Archived DOI: {DOI}\n")

# ------------------------------------------------------- 1. preserve helpers
old_helpers = {}
if os.path.exists(AF4):
    with zipfile.ZipFile(AF4) as z:
        for n in z.namelist():
            if n.startswith("helpers/") and n.endswith(".py"):
                old_helpers[n] = z.read(n)
print("preserved helper scripts:", len(old_helpers))

# ------------------------------------------------------- 2. copy scripts
# edsdk_patch.py is a one-off local-editor helper with a machine-specific
# file_id; it is not part of the reproducible analysis pipeline.
scripts = sorted(f for f in os.listdir(PIPE)
                 if f.endswith(".py") and f != "edsdk_patch.py")
for f in scripts:
    shutil.copy2(os.path.join(PIPE, f), os.path.join(REPO, f))
print("scripts copied to github_repo:", len(scripts))

# ------------------------------------------------------- 3. README
readme = f"""# Tri-level single-cell evidence chain for aortic dissection

Analysis code supporting the manuscript *"{TITLE}"* (submitted to *Genome Medicine*).

**Repository:** https://github.com/peterhu9517/aortic-dissection-scDRS-evidence
{ARCHIVE_README}
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
"""
open(os.path.join(REPO, "README.md"), "w", encoding="utf-8").write(readme)
print("README.md refreshed")

# ------------------------------------------------------- 4. Additional_file_4.zip
manifest = (
    "Additional file 4 — Analysis scripts\n"
    "====================================\n\n"
    f"Manuscript: {TITLE}\n\n"
    "pipeline/  : all Python scripts used for Layers 1/2, Option 2, robustness,\n"
    "             the post-review sample-level revision, figure redrawing and\n"
    "             manuscript/attachment generation.\n"
    "helpers/   : label-verification and figure helper scripts from the original\n"
    "             analysis round (retained for provenance).\n\n"
    "Primary inference is at the sample/donor level; cell-level P values are\n"
    "exploratory. See build_supplementary_v2.py and Additional file 6 for the\n"
    "eight pre-specified robustness / sensitivity analyses.\n\n"
    "Repository: https://github.com/peterhu9517/aortic-dissection-scDRS-evidence\n"
    + ARCHIVE_TXT
    + "Licence: MIT (code); CC-BY-4.0 (any shared processed data)\n"
)
with zipfile.ZipFile(AF4, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("README.txt", manifest)
    z.write(os.path.join(REPO, "LICENSE"), "LICENSE")
    z.write(os.path.join(REPO, "requirements.txt"), "requirements.txt")
    for f in scripts:
        z.write(os.path.join(PIPE, f), "pipeline/" + f)
    for n, blob in old_helpers.items():
        z.writestr(n, blob)
print("Additional_file_4.zip rebuilt:", len(scripts) + len(old_helpers) + 3, "entries")

# ------------------------------------------------------- 5. scidb_upload.zip
flat = ["README.md", "LICENSE", "requirements.txt", ".gitignore"]
flat += [f for f in sorted(os.listdir(REPO)) if f.endswith(".py")]
if os.path.exists(os.path.join(REPO, "scidb_cover.png")):
    flat.append("scidb_cover.png")
flat = list(dict.fromkeys(flat))
with zipfile.ZipFile(SCIDB_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
    for f in flat:
        z.write(os.path.join(REPO, f), f)
print("scidb_upload.zip rebuilt:", len(flat), "entries")

with zipfile.ZipFile(SCIDB_ZIP) as z:
    names = z.namelist()
for must in ["revision_analyses.py", "revision_sensitivity.py", "revision_figures.py",
             "build_supplementary_v2.py", "README.md", "LICENSE", "scidb_cover.png"]:
    print(f"  scidb contains {must}: {must in names}")
print("sizes: AF4", os.path.getsize(AF4), "| scidb", os.path.getsize(SCIDB_ZIP))
