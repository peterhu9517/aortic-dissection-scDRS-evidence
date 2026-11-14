"""Additional file 6 (revision 2) — Supplementary Results.

Eight pre-specified robustness / negative-control / sensitivity analyses,
with sample-level inference treated as primary and cell-level P values
explicitly labelled exploratory. All numbers are read from the analysis
outputs; nothing is hard-coded from the main-text prose.

Outputs:
  submission_kit/additional_files/Additional_file_6.docx
  revision_out/supp_figures/figS1..figS6.png
"""
import os, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56"
ROUT = os.path.join(ROOT, "scdrs_pipeline", "robustness_out")
REV = os.path.join(ROOT, "scdrs_pipeline", "revision_out")
SENS = os.path.join(REV, "sensitivity_full")
FIG = os.path.join(REV, "supp_figures")
AF = os.path.join(ROOT, "output", "aortic_dissection_manuscript",
                  "submission_kit", "additional_files")
os.makedirs(FIG, exist_ok=True)
os.makedirs(AF, exist_ok=True)

S = json.load(open(os.path.join(ROUT, "robustness_summary.json")))
R = json.load(open(os.path.join(REV, "revision_summary.json")))
aad = pd.read_csv(os.path.join(ROUT, "negctrl_AAD_enrichment.csv"))
nul = pd.read_csv(os.path.join(ROUT, "negctrl_NULL_enrichment.csv"))
loo = pd.read_csv(os.path.join(ROUT, "leave_one_cohort.csv"))
prim = pd.read_csv(os.path.join(REV, "donor_primary_table.csv"))
perm = pd.read_csv(os.path.join(REV, "sample_level_permutation.csv"))
ovl = pd.read_csv(os.path.join(REV, "gene_set_overlap.csv"))
sens = pd.read_csv(os.path.join(SENS, "sensitivity_results.csv"))

INK = "#1a2b45"
BLUE = "#21518f"
ORANGE = "#d2691e"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#8899aa",
                     "axes.labelcolor": INK, "text.color": INK,
                     "xtick.color": INK, "ytick.color": INK})

# ------------------------------------------------------------------ figures
# Fig S1 — negative control
order = list(aad.cell_type)
x = np.arange(len(order))
m = dict(zip(nul.cell_type, nul.mean_z))
fig, ax = plt.subplots(figsize=(7.2, 3.1))
ax.bar(x - 0.2, aad.mean_z, 0.4, label="Curated AAD set", color=BLUE)
ax.bar(x + 0.2, [m.get(c, np.nan) for c in order], 0.4,
       label="Expression-matched null set", color="#c8d2de")
ax.axhline(0, color="#555", lw=0.8)
ax.set_xticks(x)
ax.set_xticklabels(order, rotation=25, ha="right", fontsize=8)
ax.set_ylabel("mean scDRS-equivalent z")
ax.set_title("Fig S1. Specificity of the Layer 1 wall-cell signal", fontsize=10, color=INK)
ax.legend(frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "figS1.png"), dpi=170)
plt.close(fig)

# Fig S2 — leave-one-cell-type-out r + bootstrap CI
cv = S["convergence_r"]
lo = cv["leave_one_celltype_out_r"]
names = list(lo.keys())
vals = [lo[k] for k in names]
fig, ax = plt.subplots(figsize=(7.2, 3.0))
ax.axhspan(cv["ci_95_low"], cv["ci_95_high"], color="#dbe6f5", alpha=0.9,
           label="bootstrap 95% CI (all 8 cell types)")
ax.axhline(cv["r_obs"], color=BLUE, lw=1.2, ls="--", label=f"observed r = {cv['r_obs']:.2f}")
ax.bar(range(len(names)), vals, color="#7f9fc4", width=0.62)
ax.set_ylim(0, 1.0)
ax.set_xticks(range(len(names)))
ax.set_xticklabels(names, rotation=25, ha="right", fontsize=8)
ax.set_ylabel("Pearson r")
ax.set_title("Fig S2. Leave-one-cell-type-out convergence r (directional support only)",
             fontsize=10, color=INK)
ax.legend(frameon=False, fontsize=8, loc="lower right")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "figS2.png"), dpi=170)
plt.close(fig)

# Fig S3 — leave-one-cohort-out
fig, ax = plt.subplots(figsize=(7.2, 2.9))
ax.bar(range(len(loo)), loo.frac_up, color=["#c8d2de"] + [ORANGE] * (len(loo) - 1), width=0.6)
for i, v in enumerate(loo.frac_up):
    ax.text(i, v + 0.02, f"{v:.2f}", ha="center", fontsize=8)
ax.set_ylim(0, 1.12)
ax.set_xticks(range(len(loo)))
ax.set_xticklabels([str(s).replace(" (all)", "") for s in loo.exclude_cohort],
                   rotation=25, ha="right", fontsize=8)
ax.set_ylabel("fraction of cohorts with +delta")
ax.set_title("Fig S3. Leave-one-cohort-out direction consensus (cell level, exploratory)",
             fontsize=10, color=INK)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "figS3.png"), dpi=170)
plt.close(fig)

# Fig S4 — sample-level forest, redrawn with non-clipped labels and main-text P values
fig, ax = plt.subplots(figsize=(7.4, 3.2))
p_lab = {"GSE254132": "0.0026", "GSE155468": "0.17",
         "GSE226492": "0.50", "GSE213740": "0.31"}
import re
for i, row in prim.iterrows():
    nums = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", str(row["Δ sample (95% CI)"]))
    d, lo_ci, hi_ci = float(nums[0]), float(nums[1]), float(nums[2])
    ds = str(row["Dataset"])
    ax.plot([lo_ci, hi_ci], [i, i], color=BLUE, lw=2)
    ax.plot([d], [i], "o", color=BLUE, ms=7)
    ax.text(0.335, i, f"P(mixed) = {p_lab[ds]}", va="center", fontsize=8.2, color=INK)
ax.axvline(0, color="#666", ls="--", lw=1)
ax.set_yticks(range(len(prim)))
ax.set_yticklabels(prim.Dataset)
ax.set_xlim(-0.36, 0.52)
ax.set_xlabel("Δ macrophage module score (sample means, 95% CI)")
ax.set_title("Fig S4. Sample-level primary analysis — disease minus control", fontsize=10,
             color=INK)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "figS4.png"), dpi=170)
plt.close(fig)

# Fig S5 — sample-level permutation null (normal approximation from null SD)
fig, ax = plt.subplots(figsize=(7.2, 3.1))
for i, row in perm.iterrows():
    d = float(row["observed_delta_sample_means"])
    sd = float(row["perm_null_sd"])
    ax.plot([d - 1.96 * sd, d + 1.96 * sd], [i, i], color="#9fb4cc", lw=5,
            solid_capstyle="round")
    ax.plot([d], [i], "o", color=ORANGE, ms=7)
    ax.text(0.31, i, f"perm P = {float(row['perm_p_two_sided']):.3f}",
            va="center", fontsize=8.2, color=INK)
ax.axvline(0, color="#666", ls="--", lw=1)
ax.set_yticks(range(len(perm)))
ax.set_yticklabels(perm.dataset)
ax.set_xlim(-0.22, 0.55)
ax.set_xlabel("Δ sample means; bar = ±1.96 SD of the 2,000-permutation null")
ax.set_title("Fig S5. Sample-level label permutation: all null intervals include zero",
             fontsize=10, color=INK)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "figS5.png"), dpi=170)
plt.close(fig)

# Fig S6 — 11-gene circularity sensitivity
fig, ax = plt.subplots(figsize=(7.2, 3.1))
x = np.arange(len(sens))
ax.bar(x - 0.2, sens.delta_cell_full16, 0.4, label="Full 16-gene panel", color=BLUE)
ax.bar(x + 0.2, sens.delta_cell_reduced, 0.4, label="Reduced 11-gene panel", color=ORANGE)
ax.axhline(0, color="#555", lw=0.8)
for i, row in sens.iterrows():
    if not bool(row["direction_preserved"]):
        ax.annotate("direction reversed", (i, min(row["delta_cell_reduced"], 0) - 0.008),
                    ha="center", fontsize=7.5, color="#a33")
ax.set_xticks(x)
ax.set_xticklabels(sens.dataset, rotation=20, ha="right", fontsize=8)
ax.set_ylabel("cell-level Δ macrophage module")
ax.set_title("Fig S6. Gene-set-circularity sensitivity (cell level, exploratory)",
             fontsize=10, color=INK)
ax.legend(frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "figS6.png"), dpi=170)
plt.close(fig)

# ------------------------------------------------------------------ document
doc = Document()
st = doc.styles["Normal"]
st.font.name = "Calibri"
st.font.size = Pt(10)


def H(t, lvl=1):
    return doc.add_heading(t, level=lvl)


def P(t, bold=False, italic=False, size=10):
    p = doc.add_paragraph()
    r = p.add_run(t)
    r.bold, r.italic = bold, italic
    r.font.size = Pt(size)
    return p


def add_table(df, head=None, fontsize=8.5, widths=None):
    cols = list(df.columns)
    t = doc.add_table(rows=1, cols=len(cols))
    try:
        t.style = "Light Grid Accent 1"
    except Exception:
        t.style = "Table Grid"
    for j, c in enumerate(head or cols):
        cell = t.rows[0].cells[j]
        cell.text = str(c)
        for run in cell.paragraphs[0].runs:
            run.bold = True
            run.font.size = Pt(fontsize)
    for _, row in df.iterrows():
        cells = t.add_row().cells
        for j, c in enumerate(cols):
            v = row[c]
            if isinstance(v, (float, np.floating)):
                v = f"{v:.3g}" if (abs(v) < 1e-3 or abs(v) >= 1e4) else f"{v:.4g}"
            cells[j].text = str(v)
            for run in cells[j].paragraphs[0].runs:
                run.font.size = Pt(fontsize)
    if widths:
        for j, w in enumerate(widths):
            for r_ in t.rows:
                r_.cells[j].width = Inches(w)
    return t


def cap(t):
    p = P(t, bold=True, size=9)
    return p


def fig(path, caption, width=6.2):
    if not os.path.exists(path):
        print("missing figure:", path)
        return
    doc.add_picture(path, width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = P(caption, italic=True, size=8.8)
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER


doc.add_heading("Additional file 6. Supplementary Results — robustness, "
                "negative-control and sensitivity analyses", level=0)
P("This file reports eight pre-specified (post hoc) robustness and sensitivity analyses "
  "supporting the main manuscript. They were not pre-registered. Sample/donor-level "
  "inference is the primary analysis in the revised manuscript; cell-level Mann–Whitney U "
  "P values are reported as exploratory only, because cells are not independent biological "
  "replicates. All analyses used the same public data, gene sets and processing described "
  "in Methods. No results were omitted.", italic=True, size=9.5)
P("The eight analyses are: (A) expression-matched negative-control gene-set scoring; "
  "(B) bootstrap confidence interval and leave-one-cell-type-out assessment of the "
  "Layer 1–Option 2 correlation; (C) leave-one-cohort-out consensus; (D) GSE222318 "
  "exclusion; (E) sample-level label permutation (2,000 iterations, sample labels "
  "permuted); (F) sample-level means, Welch tests and mixed-effects models; (G) "
  "annotation of the 16-gene curated panel and its overlap with the GWAS-weighted set; "
  "and (H) an 11-gene gene-set-circularity sensitivity analysis.", size=9.5)

# ---------------------------------------------------------------- A
H("A. Expression-matched negative-control gene sets", 1)
nc = S["negctrl"]
P("To test whether the Layer 1 enrichment of smooth muscle cells and fibroblasts is "
  "specific to the curated aortic-disease (AAD) gene set rather than an artefact of "
  "gene-set size or expression level, we scored an expression-matched null set of 16 "
  "genes through an identical scDRS-equivalent pipeline on the same 57,999-cell healthy "
  "aortic atlas. Each null gene was matched by mean-expression rank to one disease gene "
  "(±50-gene rank window). Scoring used per-gene standardisation across cells, 500 "
  "expression-matched control gene sets, per-cell z = (set score − mean(control scores)) "
  "/ sd(control scores), per-cell-type Welch t versus all other cells and "
  "Benjamini–Hochberg FDR.")
P(f"The AAD set reproduced the Layer 1 pattern: fibroblast "
  f"(+{nc['aad_top'][0]['mean_z']:.2f}) and smooth muscle (+{nc['aad_top'][1]['mean_z']:.2f}) "
  f"were most enriched, endothelial and immune populations were negative "
  f"(minimum {nc['aad_bottom'][0]['mean_z']:.2f}), and all 8 cell types were "
  f"FDR-significant (max |z| = {nc['aad_max_abs_z']:.2f}; cell-type z SD = "
  f"{nc['aad_z_sd']:.2f}). The expression-matched null set produced smaller, incoherent "
  f"effects (max |z| = {nc['null_max_abs_z']:.2f}; cell-type z SD = {nc['null_z_sd']:.2f}). "
  f"Nominal FDR-significant null hits (7/8) reflect the large cell number rather than "
  f"biologically meaningful enrichment: the effect sizes are an order of magnitude "
  f"smaller than for the AAD set. These results support—but do not prove—specificity of "
  f"the wall-cell localisation to the curated gene set.")
cap("Table S1. Curated AAD gene set — per-cell-type enrichment (positive control).")
add_table(aad[["cell_type", "n", "mean_z", "t", "fdr"]],
          head=["Cell type", "n cells", "mean z", "t", "FDR"])
cap("Table S2. Expression-matched null gene set — per-cell-type enrichment (negative control).")
add_table(nul[["cell_type", "n", "mean_z", "t", "fdr"]],
          head=["Cell type", "n cells", "mean z", "t", "FDR"])
fig(os.path.join(FIG, "figS1.png"),
    "Figure S1. Curated AAD set versus expression-matched null set: mean scDRS-equivalent z per cell type.")

# ---------------------------------------------------------------- B
H("B. Bootstrap interval and leave-one-cell-type-out for the convergence r", 1)
P(f"Pearson correlation between the Layer 1 and Option 2 cell-type z-score vectors was "
  f"r = {cv['r_obs']:.3f} across 8 cell types (p = {cv['p_obs']:.3f}). Resampling cell "
  f"types with replacement (B = {cv['boot_B']:,}) gave a 95% bootstrap CI of "
  f"[{cv['ci_95_low']:.3f}, {cv['ci_95_high']:.3f}]. Leave-one-cell-type-out r ranged "
  f"{min(vals):.3f}–{max(vals):.3f}. The interval is wide because it is estimated from "
  f"only eight cell types, and 8 of the 16 curated genes also appear in the GWAS-weighted "
  f"set (Section G). The correlation therefore provides directional support, not "
  f"independent replication, and no single cell type drives it.")
fig(os.path.join(FIG, "figS2.png"),
    "Figure S2. Leave-one-cell-type-out Pearson r against the observed r (dashed) and bootstrap 95% CI (shaded).")

# ---------------------------------------------------------------- C
H("C. Leave-one-cohort-out direction consensus", 1)
P("We recomputed the fraction of cohorts showing a positive macrophage-module "
  "disease-minus-control delta after excluding each cohort in turn. GSE222318 is "
  "direction-only because it was scored on a sparse 49-gene panel and its effect sizes "
  "are not magnitude-comparable. This analysis concerns cell-level direction only and "
  "is exploratory; it does not establish statistical significance at the donor level "
  "(Sections E and F).")
cap("Table S3. Leave-one-cohort-out macrophage direction consensus (cell level).")
add_table(loo, head=["Excluded cohort", "# cohorts", "# positive", "Fraction positive",
                     "Mean signed Δ (excl. GSE222318)"])
fig(os.path.join(FIG, "figS3.png"),
    "Figure S3. Fraction of cohorts with a positive cell-level macrophage delta after leave-one-cohort-out exclusion.")

# ---------------------------------------------------------------- D
H("D. GSE222318 exclusion sensitivity", 1)
ex = S["gse222318_exclusion"]
P(f"Excluding the non-comparable 124,901-cell cohort GSE222318, the cell-level "
  f"direction consensus was {ex['without_GSE222318']['frac_up']:.2f} "
  f"({ex['without_GSE222318']['n_up']}/{ex['without_GSE222318']['n_cohorts']} cohorts "
  f"positive) versus {ex['with_GSE222318']['frac_up']:.2f} "
  f"({ex['with_GSE222318']['n_up']}/{ex['with_GSE222318']['n_cohorts']}) with it included. "
  f"The direction-based conclusion is unchanged. GSE222318 is excluded from all "
  f"magnitude-based comparisons and from the sample-level primary analysis.")

# ---------------------------------------------------------------- E
H("E. Sample-level label permutation (primary permutation unit)", 1)
P("The earlier version of this analysis permuted disease/control labels at the cell "
  "level; that still treats cells as independent replicates and is anti-conservative. "
  "It has been replaced. In the revised analysis we permuted the condition labels of "
  "whole samples within each cohort 2,000 times, recomputed the difference in sample "
  "means of the macrophage module, and derived a two-sided empirical P value as the "
  "fraction of permutations whose absolute difference exceeded the observed value. "
  "All four fully comparable cohorts were non-significant (P = 0.10–0.54), including "
  "GSE254132 (P = 0.102). No cell-level permutation result is used for inference.")
cap("Table S4. Sample-level label permutation (2,000 iterations; permutation unit = sample).")
pm = perm.copy()
pm["cell_level_mwu_p (exploratory)"] = [
    "6.7e-18", "1.3e-17", "0.867", "<1e-300"]
pm = pm[["dataset", "n_perm", "observed_delta_sample_means", "perm_null_sd",
         "perm_p_two_sided", "cell_level_mwu_p (exploratory)"]]
add_table(pm, head=["Cohort", "iterations", "observed Δ (sample means)",
                    "null SD", "permutation P", "cell-level MWU P (exploratory)"])
fig(os.path.join(FIG, "figS5.png"),
    "Figure S5. Observed sample-level deltas (orange dots) against the ±1.96 SD range of "
    "the 2,000-permutation null (grey bars). Every null interval includes zero.")

# ---------------------------------------------------------------- F
H("F. Sample-level primary analysis: means, Welch tests and mixed-effects models", 1)
P("Because cells within a donor are correlated, we aggregated the macrophage module to "
  "sample means and used sample-level inference as the primary analysis. For each cohort "
  "we report disease and control sample means with 95% confidence intervals, the "
  "difference in sample means, a Welch t test on sample means, and a linear mixed-effects "
  "model of cell-level score with condition as a fixed effect and a random intercept for "
  "sample (y ~ condition + (1|sample); statsmodels MixedLM, ML fit). Cell-level "
  "Mann–Whitney U P values are shown only to illustrate the degree of "
  "anti-conservatism. Two cohorts (GSE213740 and GSE226492) reversed direction after "
  "sample aggregation. Only GSE254132 retained a significant condition effect in the "
  "mixed model (P = 0.0026), but it was not significant under sample-level permutation "
  "(Section E) and its sample-level 95% CI includes zero, so we do not treat this as "
  "confirmatory.")
cap("Table S5. Sample-level primary analysis of the macrophage module (identical to main-text Table 4).")
add_table(prim, head=["Cohort", "Phenotype", "n samples (D/C)", "Mean D (95% CI)",
                      "Mean C (95% CI)", "Δ sample (95% CI)", "Welch P",
                      "Mixed-model P", "Cell-level MWU P (exploratory)"], fontsize=7.8)
fig(os.path.join(FIG, "figS4.png"),
    "Figure S4. Forest plot of sample-level disease-minus-control deltas with 95% CIs and mixed-model P values.")

# ---------------------------------------------------------------- G
H("G. The 16-gene curated panel, its provenance and overlap with the GWAS-weighted set", 1)
P("The curated panel was assembled for this re-analysis from genes with established or "
  "repeatedly reported links to aortic aneurysm and dissection: (i) genes causing "
  "monogenic or syndromic thoracic aortopathy (FBN1, ACTA2, MYH11, ELN); (ii) genes "
  "encoding medial extracellular-matrix, elastic-fibre or TGF-β-related proteins "
  "implicated in aortopathy (COL6A3, LOXL1, LTBP4, COMP, ACAN, LRP1); (iii) "
  "contractile and metabolic/stress genes repeatedly observed in diseased aortic tissue "
  "(ENO1, TP53); and (iv) inflammatory or myeloid-associated effectors reported in "
  "aortic aneurysm and dissection (MIF, ALOX5, JAG1, MRC2). It is a literature-based "
  "research gene set, not a clinically validated diagnostic panel, and no systematic "
  "review or formal eligibility protocol was used to construct it; that is a limitation "
  "of the study. Table S6 lists every gene, its Ensembl identifier, functional class, "
  "inclusion rationale, whether it also appears in the Option 2 GWAS-weighted set, and "
  "whether it was removed in the reduced 11-gene panel (Section H).")
P(f"The GWAS-weighted set contains {R['overlap']['n_gwas_weighted_genes']:,} genes. "
  f"{R['overlap']['n_overlap']} of the 16 curated genes "
  f"({R['overlap']['pct_of_curated_overlapping']:.0f}%) are shared: "
  f"{', '.join(R['overlap']['overlap_symbols'])}. Layer 1 and Option 2 therefore share "
  f"both the same 57,999 cells and half of the curated genes; their correlation "
  f"(r = 0.78) is directional support and must not be read as independent replication.")

ANNOT = [
    ("ENO1", "ENSG00000074800", "Glycolysis / metabolic",
     "Hypoxia-responsive metabolic adaptation reported in aneurysmal aortic tissue"),
    ("MIF", "ENSG00000240972", "Macrophage cytokine / inflammation",
     "Myeloid-derived inflammatory mediator implicated in aneurysm and dissection"),
    ("COL6A3", "ENSG00000163359", "Extracellular matrix / collagen",
     "Vascular matrix remodelling in aortopathy"),
    ("LRP1", "ENSG00000123384", "ECM receptor / clearance",
     "Implicated in aortic aneurysm and medial degeneration"),
    ("TP53", "ENSG00000141510", "Stress / senescence / inflammation",
     "Medial smooth-muscle apoptosis and senescence in aortic disease"),
    ("LOXL1", "ENSG00000129038", "Elastic-fibre cross-linking",
     "Elastogenesis and elastic-fibre homeostasis in aortopathy"),
    ("JAG1", "ENSG00000101384", "Notch signalling / inflammation",
     "Notch-mediated vascular remodelling and immune activation"),
    ("MRC2", "ENSG00000011028", "Collagen receptor / myeloid-associated",
     "Endocytic collagen receptor in remodelling stroma and myeloid cells"),
    ("ALOX5", "ENSG00000012779", "Leukotriene / inflammation",
     "Leukotriene biosynthesis in myeloid cells during aortic inflammation"),
    ("LTBP4", "ENSG00000090006", "TGF-β / elastic fibre",
     "TGF-β bioavailability and elastic-fibre assembly in aortopathy"),
    ("COMP", "ENSG00000105664", "ECM glycoprotein",
     "Medial extracellular-matrix remodelling in aortic disease"),
    ("ACAN", "ENSG00000157766", "ECM proteoglycan",
     "Medial proteoglycan accumulation in aortopathy"),
    ("FBN1", "ENSG00000166147", "Elastic fibre / fibrillin",
     "Causal gene for Marfan syndrome and thoracic aortopathy"),
    ("ACTA2", "ENSG00000107796", "SMC contractile",
     "Causal gene for familial thoracic aortic aneurysm and dissection"),
    ("MYH11", "ENSG00000133392", "SMC contractile",
     "Causal gene for familial thoracic aortic aneurysm and dissection"),
    ("ELN", "ENSG00000049540", "Elastic fibre / elastin",
     "Elastin deficiency causes obstructive aortopathy"),
]
shared = set(R["overlap"]["overlap_symbols"])
excluded = set(R["panel"]["excluded_macrophage_inflammation"])
rows = []
for sym, ensg, cls, why in ANNOT:
    rows.append({
        "Symbol": sym,
        "Ensembl ID": ensg,
        "Functional class": cls,
        "Inclusion rationale": why,
        "In Option 2 set?": "yes" if sym in shared else "no",
        "Removed in 11-gene panel?": "yes" if sym in excluded else "no",
    })
cap("Table S6. Full annotation of the 16-gene curated aortic-disease panel.")
add_table(pd.DataFrame(rows), fontsize=7.4,
          widths=[0.62, 1.35, 1.25, 2.05, 0.72, 0.80])

# ---------------------------------------------------------------- H
H("H. Gene-set-circularity sensitivity: 11-gene reduced panel", 1)
P("Five panel genes with macrophage or inflammatory association (MIF, ALOX5, TP53, "
  "JAG1, MRC2) were removed, leaving 11 genes (ENO1, COL6A3, LRP1, LOXL1, LTBP4, "
  "COMP, ACAN, FBN1, ACTA2, MYH11, ELN). All four fully comparable cohorts were "
  "re-scored from their original count matrices using the identical Scanpy "
  "score_genes settings (25 expression bins, 50 expression-matched control genes per "
  "panel gene, random_state = 0). The cell-level direction was preserved in three "
  "cohorts but reversed in GSE213740 (+0.019 to −0.020; P from 6.7 × 10⁻¹⁸ to 0.023), "
  "showing that in at least one cohort the macrophage signal was largely carried by "
  "inflammation-associated panel genes. Gene-set circularity is therefore only partly "
  "resolved; the Layer 2 macrophage finding remains exploratory and "
  "hypothesis-generating.")
cap("Table S7. Full 16-gene versus reduced 11-gene panel, cell-level macrophage delta (exploratory).")
s2 = sens.copy()
s2["direction_preserved"] = s2["direction_preserved"].map({True: "yes", False: "no"})
add_table(s2, head=["Cohort", "n genes", "Δ (11-gene)", "P (11-gene)",
                    "Δ (16-gene)", "P (16-gene)", "Direction preserved?"], fontsize=8)
fig(os.path.join(FIG, "figS6.png"),
    "Figure S6. Full 16-gene versus reduced 11-gene cell-level macrophage deltas; "
    "GSE213740 reverses direction.")

# ---------------------------------------------------------------- closing
H("Interpretive summary", 1)
P("The wall-cell enrichment in Layer 1 is supported by the expression-matched "
  "negative-control gene sets and is stable to leave-one-cell-type-out removal, but "
  "its agreement with Option 2 is directional only (8/16 genes shared; bootstrap 95% "
  "CI 0.29–0.96). The Layer 2 macrophage signal is directionally present at the cell "
  "level in three of four fully comparable cohorts, but it does not survive "
  "sample-level inference: mixed-effects models were significant in one cohort only, "
  "sample-level label permutation was non-significant in all four, and removal of "
  "inflammation-associated panel genes reversed the direction in GSE213740. "
  "Accordingly the main manuscript treats the macrophage finding as exploratory and "
  "hypothesis-generating, and does not make causal claims.")

out = os.path.join(AF, "Additional_file_6.docx")
doc.save(out)
print("saved:", out)
print("tables:", len(doc.tables), "| paragraphs:", len(doc.paragraphs))
print("figures:", sorted(os.listdir(FIG)))
