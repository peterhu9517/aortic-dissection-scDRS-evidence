# -*- coding: utf-8 -*-
"""Build a submission-ready Genome Medicine full manuscript from the existing draft.

Outputs:
  output/aortic_dissection_manuscript/stage3/Genome_Medicine_Full_Manuscript.docx
  output/aortic_dissection_manuscript/stage3/Genome_Medicine_Full_Manuscript.md
  output/aortic_dissection_manuscript/submission_kit/additional_files/Additional_file_1..5.*
"""
import os
import re
import sys
import glob
import shutil
import zipfile
from copy import deepcopy

import pandas as pd
from PIL import Image, ImageDraw
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56"
MANUSCRIPT_DIR = os.path.join(ROOT, "output", "aortic_dissection_manuscript")
SRC = os.path.join(MANUSCRIPT_DIR, "stage3", "aortic_dissection_manuscript.docx")
OUT_DOCX = os.path.join(MANUSCRIPT_DIR, "stage3", "Genome_Medicine_Full_Manuscript.docx")
OUT_MD = os.path.join(MANUSCRIPT_DIR, "stage3", "Genome_Medicine_Full_Manuscript.md")
AF_DIR = os.path.join(MANUSCRIPT_DIR, "submission_kit", "additional_files")
LAYER2 = os.path.join(ROOT, "scdrs_pipeline", "layer2_multidataset_out")
PIPE = os.path.join(ROOT, "scdrs_pipeline")
EXTRA = "D:/GSE_AD_subsets"

# --------------------------------------------------------------------------
# 1. Additional files (real, verifiable artefacts only)
# --------------------------------------------------------------------------
def build_additional_files():
    os.makedirs(AF_DIR, exist_ok=True)

    # AF1 / AF2: verified analysis outputs
    shutil.copyfile(os.path.join(LAYER2, "all_celltype_stats.csv"),
                    os.path.join(AF_DIR, "Additional_file_1.csv"))
    shutil.copyfile(os.path.join(LAYER2, "authoritative_sample_map.csv"),
                    os.path.join(AF_DIR, "Additional_file_2.csv"))

    # AF3: one supplementary figure per page, labelled S1 ... Sn
    datasets = ["GSE213740", "GSE155468", "GSE224559", "GSE226492", "GSE254132", "GSE222318"]
    plots = []
    for ds in datasets:
        plots += [
            (ds, "composition", os.path.join(LAYER2, f"{ds}_composition.png")),
            (ds, "UMAP: cell type", os.path.join(LAYER2, f"umap_{ds}_umap_celltype.png")),
            (ds, "UMAP: condition", os.path.join(LAYER2, f"umap_{ds}_umap_condition.png")),
            (ds, "UMAP: module score", os.path.join(LAYER2, f"umap_{ds}_umap_module.png")),
        ]
    extra_plots = [
        ("GSE222318", "module-score delta", os.path.join(LAYER2, "GSE222318_delta.png")),
    ]
    plots += extra_plots
    plots = [(a, b, c) for a, b, c in plots if os.path.exists(c)]

    pages = []
    for i, (ds, kind, path) in enumerate(plots, 1):
        im = Image.open(path).convert("RGB")
        canvas = Image.new("RGB", (im.width, im.height + 40), "white")
        canvas.paste(im, (0, 40))
        draw = ImageDraw.Draw(canvas)
        draw.text((12, 12), f"Supplementary Figure S{i} | {ds} | {kind}", fill="black")
        pages.append(canvas)
    af3 = os.path.join(AF_DIR, "Additional_file_3.pdf")
    pages[0].save(af3, "PDF", resolution=150.0, save_all=True, append_images=pages[1:])

    # AF4: reproducible scripts
    scripts = sorted(glob.glob(os.path.join(PIPE, "*.py")))
    for name in ["verify_labels.py", "make_figures.py", "make_fig4.py", "inspect_matrix.py"]:
        p = os.path.join(EXTRA, name)
        if os.path.exists(p):
            scripts.append(p)
    af4 = os.path.join(AF_DIR, "Additional_file_4.zip")
    with zipfile.ZipFile(af4, "w", zipfile.ZIP_DEFLATED) as z:
        for s in scripts:
            folder = "helpers" if s.startswith("D:/") else "pipeline"
            z.write(s, folder + "/" + os.path.basename(s))

    # AF5: cohort-level analysis / QC summary derived only from generated outputs
    st = pd.read_csv(os.path.join(LAYER2, "all_celltype_stats.csv"))
    mp = pd.read_csv(os.path.join(LAYER2, "authoritative_sample_map.csv"))
    rows = []
    for ds, g in st.groupby("dataset", sort=False):
        mac = g[g.cell_type == "Macrophage"]
        rows.append({
            "dataset": ds,
            "n_samples_in_official_GEO_map": int((mp.dataset == ds).sum()),
            "n_disease_samples": int(((mp.dataset == ds) &
                                      (mp.authoritative_condition == "Disease")).sum()),
            "n_control_samples": int(((mp.dataset == ds) &
                                      (mp.authoritative_condition == "Control")).sum()),
            "n_cell_types_tested": int(g.cell_type.nunique()),
            "n_disease_cells_summed_over_cell_types": int(g.n_Disease.fillna(0).sum()),
            "n_control_cells_summed_over_cell_types": int(g.n_Control.fillna(0).sum()),
            "mean_delta_all_cell_types": round(float(g.delta.mean()), 6),
            "min_delta": round(float(g.delta.min()), 6),
            "max_delta": round(float(g.delta.max()), 6),
            "n_cell_types_P_lt_0.05": int((g.mannwhitney_p < 0.05).sum()),
            "macrophage_delta": (round(float(mac.delta.iloc[0]), 6) if len(mac) else ""),
            "macrophage_mannwhitney_p": (
                f"{float(mac.mannwhitney_p.iloc[0]):.3g}"
                if len(mac) and pd.notna(mac.mannwhitney_p.iloc[0]) else ""),
            "note": ("No human control arm; excluded from case-control comparison"
                     if ds == "GSE224559" else
                     "Labels from the source study's Group1 annotation, not the 39-sample GEO "
                     "map; curated 49-gene sparse scoring, delta magnitude not comparable"
                     if ds == "GSE222318" else ""),
        })
    pd.DataFrame(rows).to_csv(os.path.join(AF_DIR, "Additional_file_5.csv"), index=False)

    print("[AF] pages in Additional file 3:", len(pages))
    for f in sorted(os.listdir(AF_DIR)):
        p = os.path.join(AF_DIR, f)
        print(f"  {f}: {os.path.getsize(p)/1024/1024:.2f} MB")
    return len(pages)


# --------------------------------------------------------------------------
# 2. Manuscript assembly helpers
# --------------------------------------------------------------------------
def clean_template(el):
    """Remove section properties and bookmarks so a paragraph can be reused."""
    el = deepcopy(el)
    pPr = el.find(qn("w:pPr"))
    if pPr is not None:
        for tag in ("w:sectPr",):
            for node in pPr.findall(qn(tag)):
                pPr.remove(node)
    for tag in ("w:bookmarkStart", "w:bookmarkEnd", "w:hyperlink"):
        for node in el.findall(qn(tag)):
            el.remove(node)
    if pPr is not None:
        for node in pPr.findall(qn("w:numPr")):
            pPr.remove(node)
    return el


def set_runs(el, parts):
    """parts: list of (text, bold). Keeps the first run's formatting."""
    runs = el.findall(qn("w:r"))
    r_tpl = deepcopy(runs[0]) if runs else None
    for r in runs:
        el.remove(r)
    for text, bold in parts:
        if r_tpl is not None:
            r = deepcopy(r_tpl)
            for t in r.findall(qn("w:t")):
                r.remove(t)
            for br in r.findall(qn("w:br")):
                r.remove(br)
            for tab in r.findall(qn("w:tab")):
                r.remove(tab)
        else:
            r = OxmlElement("w:r")
        t = OxmlElement("w:t")
        t.set(qn("xml:space"), "preserve")
        t.text = text
        r.append(t)
        if bold:
            rPr = r.find(qn("w:rPr"))
            if rPr is None:
                rPr = OxmlElement("w:rPr")
                r.insert(0, rPr)
            if rPr.find(qn("w:b")) is None:
                rPr.insert(0, OxmlElement("w:b"))
        el.append(r)


def main():
    n_pages = build_additional_files()

    d = Document(SRC)
    body = d.element.body
    orig = list(body)

    def P(i):
        return Paragraph(orig[i], d)

    # Reusable paragraph templates (from the original document, preserving its fonts)
    TPL_BODY = clean_template(orig[29])   # justified SimSun 12 pt
    TPL_H1 = clean_template(orig[28])     # Heading 1
    TPL_H2 = clean_template(orig[33])     # Heading 2

    def mk(tpl, text, bold=False, center=False, italic=False):
        el = clean_template(tpl)
        set_runs(el, [(text, bold)])
        p = Paragraph(el, d)
        if center:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if italic:
            for r in p.runs:
                r.italic = True
        return el

    def replace(i, text, bold=False, center=False):
        set_runs(orig[i], [(text, bold)])
        p = P(i)
        if center:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return orig[i]

    def insert_many(anchor, elements):
        cur = anchor
        for el in elements:
            cur.addnext(el)
            cur = el
        return cur

    # --- 2.1 Title page -----------------------------------------------------
    replace(2, "¹ Department of Cardiovascular Surgery, Union Hospital, Tongji Medical College, "
               "Huazhong University of Science and Technology, 1277 Jiefang Avenue, Wuhan, "
               "Hubei 430000, China; ³ Hubei Provincial Cardiovascular Surgery Quality Control "
               "Center, 1277 Jiefang Avenue, Wuhan, Hubei 430000, China.")
    replace(3, "Corresponding author: HU Xingjian, Department of Cardiovascular Surgery, "
               "Union Hospital, Tongji Medical College, Huazhong University of Science and "
               "Technology, 1277 Jiefang Avenue, Wuhan, Hubei 430000, China. "
               "Email: peterhu9517@hust.edu.cn. ORCID: [TO BE COMPLETED].")

    # --- 2.2 Structured abstract (<=350 words) -----------------------------
    abstract = [
        ("Background: ",
         "Aortic dissection (AD) is a highly heritable, life-threatening aortic syndrome, "
         "but genome-wide association study (GWAS) loci identify genes and tissues rather than "
         "the cell types in which risk acts. Whether inherited susceptibility and the effector "
         "state of established disease reside in the same cellular compartment remains unresolved."),
        ("Methods: ",
         "We applied single-cell disease-relevance scoring (scDRS) with 16 established "
         "aortic-disease genes to 57,999 cells from the healthy human aorta, and independently "
         "reconstructed a GWAS-weighted gene set through a MAGMA-free variant-to-gene framework "
         "applied to the same cells; concordance was quantified by Pearson correlation of "
         "cell-type z-scores. We then validated the disease axis across six public aortic "
         "single-cell cohorts (39 annotated samples plus one 124,901-cell cohort, approximately "
         "293,000 cells in total), scoring the same 16-gene aortic-disease module and comparing "
         "diseased versus control cells within each cell type using the Mann-Whitney U test. "
         "Disease/control labels were verified against official GEO series-matrix files or the "
         "source study's own annotation."),
        ("Results: ",
         "In the healthy aorta, genetic susceptibility was enriched in smooth muscle cells "
         "(z = 1.08) and fibroblasts (z = 0.59; both FDR-corrected P approximately 0) and "
         "depleted in macrophages (z = -1.10). GWAS-derived scores reproduced this map (smooth "
         "muscle z = 0.39; fibroblasts z = 0.32) and correlated with the known-gene layer "
         "(r = 0.78). In established disease, the macrophage module score was elevated in four "
         "of five cohorts with a control arm (GSE213740: delta = +0.019, P = 6.7e-18; "
         "GSE155468: +0.022, P = 1.3e-17; GSE254132: +0.079, P approximately 0; GSE222318: "
         "+0.24, P = 2.3e-102), whereas wall-cell signatures were inconsistent in direction. "
         "GSE224559 lacked a human control arm and was excluded from case-control comparisons; "
         "GSE222318 effect sizes are interpretable in direction only."),
        ("Conclusions: ",
         "Inherited AD risk is encoded in the vascular wall, while manifest disease is "
         "characterised by macrophage-centred inflammation. This dissociation reconciles "
         "locus-level genetic signals with the inflammatory phenotype of dissected aortas and "
         "provides a cell-type-resolved, reproducible framework for other heritable vascular "
         "diseases. Functional validation in independent prospective cohorts is required."),
    ]
    set_runs(orig[5], [(abstract[0][0], True), (abstract[0][1], False)])
    rest = []
    for label, txt in abstract[1:]:
        el = clean_template(TPL_BODY)
        set_runs(el, [(label, True), (txt, False)])
        rest.append(el)
    insert_many(orig[5], rest)

    # --- 2.3 Remove the table of contents (fake page numbers) --------------
    for i in range(7, 26):
        el = orig[i]
        if el.getparent() is not None:
            el.getparent().remove(el)

    # --- 2.4 Graphical abstract label in the front matter ------------------
    replace(27, "Graphical abstract", center=True)

    # --- 2.5 Section headings (Genome Medicine wording, no numbering) ------
    headings = {
        28: "Background",
        32: "Methods",
        33: "Data sources",
        36: "Layer 1: known-gene scDRS on the healthy aorta",
        38: "Option 2: GWAS-derived scDRS",
        40: "Layer 2: cross-cohort disease-module scoring",
        42: "Statistics",
        44: "Results",
        45: "Layers 1 and Option 2 converge on the vascular wall",
        53: "Layer 2: macrophage activation is the consistent signal of established disease",
        61: "Synthesis: genetic substrate versus inflammatory effector",
        66: "Discussion",
        70: "Limitations",
        72: "Implications and future directions",
        74: "Conclusions",
        76: "References",
    }
    for i, text in headings.items():
        replace(i, text)

    # --- 2.6 Methods: make the analyses reproducible ----------------------
    replace(34, "The healthy-aorta reference comprised 57,999 cells from published human "
                "aortic single-cell atlases, uniformly processed and annotated into eight cell "
                "types: smooth muscle, fibroblast, microvasculature, endothelial (two states), "
                "macrophage, lymphocyte, and an uncharacterised cluster. [TO BE COMPLETED: "
                "citation, repository and accession/URL of the original healthy aortic atlas.] "
                "GWAS summary statistics for aortic aneurysm and dissection were obtained as "
                "OMIX007191-02 (9,797,427 variants; genome build GRCh37/hg19); gene coordinates "
                "were taken from the UCSC ensGene annotation for hg19. [TO BE COMPLETED: full "
                "dataset citation and persistent URL.]")
    insert_many(orig[35], [
        mk(TPL_BODY, "Sample-level disease/control labels were verified against official GEO "
                     "series-matrix files (Additional file 2); cohort-level cell counts, "
                     "label counts and analysis summaries are provided in Additional file 5.")
    ])

    replace(39, "Independently of the curated gene set, we built a GWAS-gene score using a "
                "MAGMA-free variant-to-gene framework. For every gene present in the atlas, all "
                "variants within the gene body plus/minus 50 kb were identified from the hg19 "
                "summary statistics and a gene score was computed as the maximum "
                "-log10(P) minus log10(number of variants in the window), a Bonferroni-style "
                "correction for gene length and variant density. Top-ranked genes formed a "
                "weighted set (weights 1-3 by within-set percentile), which was supplied to the "
                "identical scDRS machinery on the same 57,999 cells using 500 "
                "expression-matched control gene sets. The two cell-type z-score vectors were "
                "compared by Pearson correlation. This positional approximation does not model "
                "linkage disequilibrium or the multivariate regression used by MAGMA and is "
                "therefore treated as an exploratory, directional confirmation rather than a "
                "formal gene-based association test.")

    replace(41, "Each dataset was processed through a unified pipeline: quality control, "
                "log-normalisation (target sum 1 x 10^4), identification of highly variable "
                "genes, PCA, UMAP visualisation and Leiden clustering; cells were assigned to "
                "vascular cell types using canonical marker genes (SMC: ACTA2/MYH11; "
                "fibroblast: COL1A1; endothelial: PECAM1/CLDN5; macrophage: CD68/LYZ; "
                "T/NK/B lymphocytes by canonical markers). For every cell we computed a "
                "16-gene aortic-disease module score (ENO1, MIF, COL6A3, LRP1, TP53, LOXL1, "
                "JAG1, MRC2, ALOX5, LTBP4, COMP, ACAN, FBN1, ACTA2, MYH11, ELN). This is the "
                "same gene panel used in Layer 1 and Option 2, here represented by HGNC symbols "
                "because the disease cohorts deposit symbol-indexed matrices; the healthy atlas "
                "uses the corresponding Ensembl identifiers. Within each cell type we compared "
                "the module score between diseased and control cells using the Mann-Whitney U "
                "test, reporting the mean difference (delta) and P value (Additional file 1). "
                "Per-cohort UMAP, composition and module-score plots are shown in Additional "
                "file 3. GSE222318, whose 9 GB dense matrix exceeded available memory, was "
                "scored in sparse form on a curated 49-gene panel comprising the module genes "
                "and canonical marker genes; its delta magnitudes are therefore on a different "
                "scale and are used for direction only.")

    replace(43, "Per-cell-type enrichment in Layers 1 and Option 2 was assessed with a Welch "
                "two-sample t test comparing the scDRS z-scores of cells in a given cell type "
                "with all other cells, followed by Benjamini-Hochberg false-discovery-rate (FDR) "
                "correction across cell types. Layer 2 deltas were tested with the two-sided "
                "Mann-Whitney U test. Convergence between the two genetic layers was quantified "
                "by Pearson correlation of cell-type z-score vectors. All tests were performed "
                "at the cell level; no sample-level aggregation or mixed-effects model was "
                "applied, and P values are reported per test without a pooled cross-cohort FDR "
                "hierarchy (see Limitations).")

    insert_many(orig[43], [
        mk(TPL_H2, "Software and reproducibility"),
        mk(TPL_BODY, "Analyses were performed under Python 3.13 on Microsoft Windows with "
                     "scDRS 1.0.2, Scanpy 1.12.5, AnnData 0.13.4 and SciPy, pandas, NumPy and "
                     "Matplotlib. All code used for Layer 1, Option 2, the six-cohort Layer 2 "
                     "pipeline, official label verification and figure generation is archived "
                     "as Additional file 4."),
        mk(TPL_H2, "Use of large language models"),
        mk(TPL_BODY, "During preparation of this manuscript, [TO BE COMPLETED: generative AI "
                     "tool name and version] was used for language editing and for assistance "
                     "with code debugging. All generated text and code were checked and "
                     "verified by the authors, who take full responsibility for the accuracy "
                     "and integrity of the analyses, results and conclusions. No large language "
                     "model is listed as an author."),
    ])

    # --- 2.7 Table titles / legends (<=15 words / <=300 words) ------------
    replace(48, "Table 1. Cell-type scDRS z-scores in the healthy aorta", center=True)
    insert_many(orig[48], [
        mk(TPL_BODY, "Per-cell-type mean scDRS z-scores from Layer 1 (16 known aortic-disease "
                     "genes, Ensembl identifiers) and Option 2 (GWAS-derived weighted gene set) "
                     "in 57,999 healthy aortic cells. Positive z indicates enrichment of the "
                     "disease-gene programme relative to expression-matched control gene sets; "
                     "FDR-corrected P values are approximately 0 for smooth muscle, fibroblast "
                     "and macrophage in Layer 1. Pearson correlation between the two z-score "
                     "vectors: r = 0.78.", center=True)
    ])
    replace(55, "Table 2. Macrophage module score across aortic cohorts", center=True)
    insert_many(orig[55], [
        mk(TPL_BODY, "Mean difference (delta) in the 16-gene aortic-disease module score "
                     "between diseased and control macrophages within each cohort, with "
                     "two-sided Mann-Whitney U P values. GSE224559 is omitted because it has no "
                     "human control arm. *GSE222318 was scored on a curated 49-gene sparse "
                     "panel; its magnitude is not comparable to the other cohorts and is "
                     "interpreted by direction only. Complete statistics for every cell type "
                     "are provided in Additional file 1.", center=True)
    ])

    # --- 2.8 Figure captions: short in-text labels, full legends at end ----
    replace(52, "Fig. 1", center=True)
    replace(59, "Fig. 2", center=True)
    replace(65, "Fig. 3", center=True)
    replace(54, P(54).text + " Complete dataset-by-cell-type statistics are provided in "
                            "Additional file 1.")

    # --- 2.9 Discussion: explain the directional reversal -----------------
    insert_many(orig[67], [
        mk(TPL_BODY, "A potential concern is the apparent reversal of the macrophage signal: "
                     "the same 16-gene panel is depleted in macrophages of the healthy aorta "
                     "(z = -1.10) yet shows the largest and most reproducible disease-associated "
                     "increase in macrophages of dissected and aneurysmal tissue. Because the "
                     "gene panel is identical in both settings, this cannot be explained by "
                     "gene-set selection. The two readouts estimate different quantities. scDRS "
                     "in healthy tissue is a relative, expression-matched comparison between "
                     "cell types at baseline: it localises where a constitutively expressed "
                     "susceptibility programme is most active. The Layer 2 module score is an "
                     "absolute, state-dependent comparison within a cell type between "
                     "conditions: it measures how strongly that programme is induced once "
                     "disease is established. A macrophage can therefore be relatively depleted "
                     "for a wall-matrix/contractile programme at rest and still mount the "
                     "largest inducible response when the wall fails. We interpret the wall-cell "
                     "signal as inherited susceptibility and the macrophage signal as an "
                     "effector response, rather than as two competing localisations of a single "
                     "disease process. This interpretation is a testable hypothesis; it does "
                     "not establish a causal sequence.")
    ])

    # --- 2.10 Limitations and future work: honest disclosure ---------------
    replace(71, P(71).text + " (vii) All comparisons were performed at the cell level, so "
                             "cells are not independent biological replicates and the reported "
                             "P values may be anti-conservative; sample-level aggregation, "
                             "mixed-effects models and a pooled cross-cohort FDR hierarchy "
                             "were not applied. (viii) Negative-control gene sets, label "
                             "permutation tests, leave-one-cohort-out validation, a bootstrap "
                             "confidence interval for r = 0.78 and a sensitivity analysis "
                             "excluding GSE222318 have not yet been performed. These analyses "
                             "are planned before definitive mechanistic claims are made.")
    replace(73, P(73).text + " In the immediate term, the robustness of the present framework "
                             "should be tested with random gene sets, label permutation, "
                             "leave-one-cohort-out replication, a bootstrap confidence interval "
                             "for the Layer 1/Option 2 correlation, sample-level mixed-effects "
                             "models and a GSE222318-excluded sensitivity analysis.")

    # --- 2.11 List of abbreviations ---------------------------------------
    abbr_els = [
        mk(TPL_H1, "List of abbreviations"),
        mk(TPL_BODY, "AD - aortic dissection; ATAA - ascending thoracic aortic aneurysm; "
                     "ATAD - acute type A aortic dissection; FDR - false discovery rate; "
                     "GEO - Gene Expression Omnibus; GTEx - Genotype-Tissue Expression; "
                     "GWAS - genome-wide association study; HGNC - HUGO Gene Nomenclature "
                     "Committee; HVG - highly variable gene; PCA - principal component "
                     "analysis; QC - quality control; scDRS - single-cell disease relevance "
                     "score; scRNA-seq - single-cell RNA sequencing; SMC - smooth muscle "
                     "cell; TAA - thoracic aortic aneurysm; UMAP - Uniform Manifold "
                     "Approximation and Projection."),
    ]

    # --- 2.12 Declarations (all eight sub-sections) ------------------------
    declarations = [
        ("Ethics approval and consent to participate",
         "This study re-analysed exclusively publicly available, de-identified single-cell "
         "RNA-sequencing data and summary-level genetic data obtained from the Gene Expression "
         "Omnibus, GTEx and published GWAS resources. No new human participants, human tissue "
         "or animal experiments were involved. Ethics approval and informed consent for the "
         "original data collections were obtained by the respective source studies and are "
         "reported in their publications. [TO BE COMPLETED: name of the approving ethics "
         "committee and reference number, or the formal institutional waiver statement.]"),
        ("Consent for publication", "Not applicable."),
        ("Availability of data and materials",
         "The datasets supporting the conclusions of this article are available in the NCBI "
         "Gene Expression Omnibus repository under accession numbers GSE213740, GSE155468, "
         "GSE224559, GSE226492, GSE254132 and GSE222318; each is formally cited with its "
         "accession number in the reference list. GWAS summary statistics were obtained from "
         "[TO BE COMPLETED: repository, OMIX007191-02 persistent link and full citation; "
         "genome build GRCh37/hg19]; the healthy aortic single-cell reference comprised "
         "57,999 aortic cells subset from [TO BE COMPLETED: original atlas citation, "
         "repository and accession/URL]. The derived cross-dataset statistics, verified "
         "sample-to-condition map, supplementary figures, analysis scripts and cohort-level "
         "QC summary are included in this article as Additional files 1-5. Project name: "
         "[TO BE COMPLETED]; project home page: [TO BE COMPLETED: GitHub repository URL]; "
         "archived version: [TO BE COMPLETED: Zenodo DOI]; operating system: Microsoft "
         "Windows; programming language: Python 3.13; other requirements: scDRS 1.0.2, "
         "Scanpy 1.12.5, AnnData 0.13.4, SciPy, pandas, NumPy, Matplotlib; licence: "
         "[TO BE COMPLETED]; any restrictions to use by non-academics: [TO BE COMPLETED]."),
        ("Competing interests",
         "[TO BE COMPLETED: if none, use: \"The authors declare that they have no competing "
         "interests.\" Otherwise list all financial and non-financial competing interests "
         "using author initials.]"),
        ("Funding",
         "[TO BE COMPLETED: all funders and grant numbers, and the role of each funder in "
         "study design, data collection, analysis, interpretation and manuscript preparation, "
         "or a statement that funders had no such role.]"),
        ("Authors' contributions",
         "[DRAFT - TO BE CONFIRMED by all authors; use initials.] SW, FL and YW performed "
         "data curation and computational analyses; ND and XH conceived and supervised the "
         "study; XH drafted the manuscript; all authors interpreted the results, critically "
         "revised the manuscript and read and approved the final version."),
        ("Acknowledgements",
         "[TO BE COMPLETED: acknowledgements, or \"Not applicable.\" Obtain permission from "
         "everyone acknowledged.]"),
        ("Authors' information", "Not applicable."),
    ]
    decl_els = [mk(TPL_H1, "Declarations")]
    for h, txt in declarations:
        decl_els.append(mk(TPL_H2, h))
        decl_els.append(mk(TPL_BODY, txt))
    insert_many(orig[75], abbr_els + decl_els)

    # --- 2.13 Figure legends (after References) ----------------------------
    legends = [
        ("Fig. 1", "Genetic risk converges on vascular wall cells across two independent gene sets",
         "Paired bar chart of per-cell-type scDRS z-scores in 57,999 healthy human aortic "
         "cells, computed with 16 established aortic-disease genes (Layer 1, Ensembl "
         "identifiers) and with an independent GWAS-weighted gene set reconstructed through "
         "a MAGMA-free variant-to-gene framework (Option 2). Positive z indicates enrichment "
         "of the disease-gene programme relative to expression-matched control gene sets. "
         "Both layers peak in smooth muscle and fibroblasts and are depleted in immune "
         "populations, with macrophages most negative in Layer 1. Pearson correlation "
         "between the two cell-type z-score vectors: r = 0.78. FDR-corrected P values are "
         "approximately 0 for the three leading cell types (Table 1). Bar colour denotes "
         "the gene-set source; the dashed line marks z = 0."),
        ("Fig. 2", "Macrophage module elevation is reproducible across aortic cohorts",
         "Heatmap of mean disease-minus-control differences (delta) in the 16-gene "
         "aortic-disease module score, computed within each annotated cell type for six GEO "
         "cohorts. Warmer colours denote higher scores in diseased cells. Macrophages are "
         "positive in four of the five cohorts with a control arm; GSE224559 has no human "
         "control arm and is shown for completeness only. GSE222318 was scored on a curated "
         "49-gene panel in sparse form, so its delta magnitudes are not on the same scale as "
         "the other cohorts and are interpreted by direction only. Exact cell counts, means "
         "and Mann-Whitney U P values for every dataset x cell type are given in Additional "
         "file 1; official sample labels are documented in Additional file 2."),
        ("Fig. 3", "Two-compartment model of aortic dissection risk and manifestation",
         "Schematic of the dissociation between inherited susceptibility and effector "
         "response. Left: in the healthy aorta, the 16-gene aortic-disease programme is "
         "enriched in smooth muscle cells and fibroblasts and depleted in macrophages. "
         "Right: in established dissection and aneurysm tissue, macrophages show the most "
         "reproducible transcriptional up-regulation, whereas wall-cell programmes vary "
         "with disease phase, anatomical segment and aetiology. The model is interpretative "
         "rather than mechanistic; causal direction has not been established."),
        ("Graphical abstract", "Tri-level single-cell evidence chain in aortic dissection",
         "Layer 1 (known aortic-disease genes) and Option 2 (GWAS-derived genes) "
         "independently converge on vascular wall cells of the healthy aorta (Pearson "
         "r = 0.78), whereas Layer 2, spanning six independent cohorts, identifies "
         "macrophage inflammation as the reproducible effector of established disease. "
         "The resulting dissociation places the genetic substrate in smooth muscle cells "
         "and fibroblasts, while the manifest disease state is dominated by "
         "macrophage-centred inflammation."),
    ]
    leg_els = [mk(TPL_H1, "Figure legends")]
    for tag, title, legend in legends:
        leg_els.append(mk(TPL_BODY, f"{tag}. {title}", bold=True))
        leg_els.append(mk(TPL_BODY, legend))

    # --- 2.14 Additional files list ---------------------------------------
    af_items = [
        ("Additional file 1: ", "Cross-dataset cell-type statistics. File format: .csv. "
         "Complete dataset x cell-type table (42 rows) of diseased and control cell counts, "
         "means, deltas and Mann-Whitney U P values for the 16-gene module score."),
        ("Additional file 2: ", "Authoritative GEO sample-to-condition map. File format: "
         ".csv. All 39 annotated samples with GEO accession and title, inferred condition, "
         "official condition from series-matrix files and concordance flag."),
        ("Additional file 3: ", "Supplementary figures. File format: .pdf. "
         f"{n_pages} one-page supplementary figures: per-cohort UMAP overlays (cell type, "
         "condition, module score), composition bar plots and the GSE222318 delta plot, "
         "ordered by dataset."),
        ("Additional file 4: ", "Analysis scripts. File format: .zip. Python scripts for "
         "Layer 1, Option 2, the six-cohort Layer 2 pipeline, official label verification "
         "and figure generation."),
        ("Additional file 5: ", "Per-cohort analysis and QC summary. File format: .csv. "
         "Cohort-level cell counts per condition, number of cell types tested, module-score "
         "delta ranges, number of nominal associations and macrophage statistics derived "
         "from the processed objects."),
    ]
    af_els = [mk(TPL_H1, "Additional files")]
    for head, txt in af_items:
        el = clean_template(TPL_BODY)
        set_runs(el, [(head, True), (txt, False)])
        af_els.append(el)
    af_els.append(mk(TPL_BODY, "All additional files are cited individually in the main text. "
                               "Each file is smaller than the 20 MB limit for Genome Medicine."))
    insert_many(orig[106], leg_els + af_els)

    d.save(OUT_DOCX)

    # --- 2.16 Plain-text Markdown companion -------------------------------
    dd = Document(OUT_DOCX)
    lines = []
    for el in list(dd.element.body):
        if el.tag == qn("w:p"):
            p = Paragraph(el, dd)
            t = p.text.strip()
            if not t:
                if p._p.findall(".//" + qn("w:drawing")):
                    lines.append("[Figure image — see Figure legends]")
                continue
            style = p.style.name
            if style == "Heading 1":
                lines.append("\n## " + t + "\n")
            elif style == "Heading 2":
                lines.append("\n### " + t + "\n")
            elif t.startswith("Table 1.") or t.startswith("Table 2."):
                lines.append("\n**" + t + "**\n")
            elif re.match(r"^(Fig\. \d|Graphical abstract)\. ", t) and p.runs and p.runs[0].bold:
                lines.append("\n**" + t + "**\n")
            else:
                lines.append(t + "\n")
        elif el.tag == qn("w:tbl"):
            tb = Table(el, dd)
            rows = ["| " + " | ".join(c.text.replace("\n", " ") for c in r.cells) + " |"
                    for r in tb.rows]
            rows.insert(1, "| " + " | ".join(["---"] * len(tb.columns)) + " |")
            lines.append("\n".join(rows) + "\n")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # --- 2.17 Audit --------------------------------------------------------
    final = Document(OUT_DOCX)
    paras = [p.text for p in final.paragraphs]
    full = "\n".join(paras)
    abstract_words = len(" ".join(x[0] + x[1] for x in abstract).split())
    print("\n[AUDIT]")
    print("  structured abstract words:", abstract_words)
    print("  total manuscript words:", len(full.split()))
    print("  paragraphs:", len(final.paragraphs), "tables:", len(final.tables),
          "images:", len(final.inline_shapes))
    print("  placeholders:", full.count("[TO BE COMPLETED"),
          "+ DRAFT:", full.count("[DRAFT"))
    print("  section headings:", [p.text for p in final.paragraphs
                                  if p.style.name == "Heading 1"])
    print("  files:")
    for f in [OUT_DOCX, OUT_MD]:
        print("   ", f, os.path.getsize(f))


if __name__ == "__main__":
    main()
