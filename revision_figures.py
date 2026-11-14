# -*- coding: utf-8 -*-
"""Redraw all four manuscript figures for the major revision.

Fixes:
  Fig.1 - overlapping title, "converges" -> "enriched", partial-overlap note.
  Fig.2 - GSE222318 (different scale) split into its own panel with its own
          colour scale; GSE224559 (no human control) removed; shared colour
          limits widened so nothing is clipped; cell-type labels harmonised.
  Fig.3 - causal wording removed.
  Graphical abstract - "independent convergence / replicated / 4 of 5
          cohorts / before any dissection" replaced with the revised,
          sample-level, hypothesis-generating wording; 39 samples kept.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56/scdrs_pipeline"
OUT = os.path.join(ROOT, "revision_out", "figures")
os.makedirs(OUT, exist_ok=True)

NAVY = "#1f4e79"
ORANGE = "#d95f02"
INK = "#12263a"
GREY = "#5b6b7c"
PALE = "#eef3f8"

# ---------------------------------------------------------------- Fig. 1
l1 = pd.read_csv(os.path.join(ROOT, "layer1_out", "celltype_summary.csv"))
o2 = pd.read_csv(os.path.join(ROOT, "option2_out", "celltype_summary.csv"))
order = ["Smooth Muscle", "Fibroblast", "Microvasculature", "Uncharacterized",
         "Lymphocyte", "Macrophage", "Endothelial2", "Endothelial1"]
lab = ["Vascular SMC", "Fibroblast", "Microvasculature", "Uncharacterised",
       "Lymphocyte", "Macrophage", "Endothelial 2", "Endothelial 1"]
z1 = [float(l1.loc[l1.cell_type == c, "mean_z"].iloc[0]) for c in order]
z2 = [float(o2.loc[o2.cell_type == c, "mean_z"].iloc[0]) for c in order]

fig, ax = plt.subplots(figsize=(11, 5.6))
x = np.arange(len(order)); w = 0.38
ax.bar(x - w/2, z1, w, color=NAVY, label="Layer 1 · 16 curated genes")
ax.bar(x + w/2, z2, w, color=ORANGE, label="Option 2 · GWAS-weighted genes")
ax.axhline(0, color=GREY, lw=1)
ax.set_xticks(x); ax.set_xticklabels(lab, rotation=32, ha="right", fontsize=10)
ax.set_ylabel("scDRS z-score (per cell type)", fontsize=11)
ax.set_title("Genetic susceptibility is enriched in vascular wall cells across\ntwo partially overlapping gene sets",
             fontsize=14, weight="bold", color=INK, pad=14)
ax.text(0.99, 0.96, "r = 0.78 (bootstrap 95% CI 0.29–0.96)\n8 of 16 genes shared — directional support only",
        transform=ax.transAxes, ha="right", va="top", fontsize=9.5, color=GREY,
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#cbd5e1"))
ax.legend(frameon=False, fontsize=10, loc="lower left")
ax.set_ylim(-1.9, 1.35)
for s in ["top", "right"]: ax.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "fig1.png"), dpi=170); plt.close()

# ---------------------------------------------------------------- Fig. 2
big = pd.read_csv(os.path.join(ROOT, "layer2_multidataset_out", "all_celltype_stats.csv"))
MAIN = ["GSE213740", "GSE155468", "GSE226492", "GSE254132"]
SPECIAL = "GSE222318"
rename = {"Vascular_SMC": "Vascular SMC", "B_cell": "B cell", "T_cell": "T cell",
          "NK": "NK", "Macrophage": "Macrophage", "Fibroblast": "Fibroblast",
          "Endothelial": "Endothelial", "Pericyte": "Pericyte",
          "Proliferating": "Proliferating"}
ct_order = ["Macrophage", "Vascular SMC", "Fibroblast", "Endothelial", "Pericyte",
            "T cell", "B cell", "NK", "Proliferating"]

def pivot_for(datasets):
    sub = big[big.dataset.isin(datasets)].copy()
    sub["cell_type"] = sub["cell_type"].map(lambda c: rename.get(c, c))
    return sub.pivot(index="cell_type", columns="dataset", values="delta").reindex(
        index=[c for c in ct_order if c in set(sub.cell_type)],
        columns=[d for d in datasets if d in set(sub.dataset)])

pm = pivot_for(MAIN)
ps = pivot_for([SPECIAL])
lim = float(np.nanmax(np.abs(pm.values))) * 1.05
lim2 = float(np.nanmax(np.abs(ps.values))) * 1.05

fig = plt.figure(figsize=(12.5, 8.0))
gs = fig.add_gridspec(1, 2, width_ratios=[4.2, 1.55], wspace=0.42)
ax = fig.add_subplot(gs[0, 0]); ax2 = fig.add_subplot(gs[0, 1])
im = ax.imshow(pm.values, aspect="auto", cmap="RdBu_r", vmin=-lim, vmax=lim)
ax.set_yticks(range(len(pm.index))); ax.set_yticklabels(pm.index, fontsize=10)
ax.set_xticks(range(len(pm.columns))); ax.set_xticklabels(pm.columns, rotation=0, ha="center", fontsize=9.5)
ax.set_title("Four fully comparable case–control cohorts\n(16-gene module; shared colour scale)",
             fontsize=11.5, weight="bold", color=INK)
for i in range(pm.shape[0]):
    for j in range(pm.shape[1]):
        v = pm.values[i, j]
        if np.isfinite(v):
            ax.text(j, i, "%+.2f" % v, ha="center", va="center", fontsize=7.5,
                    color="white" if abs(v) > lim*0.62 else INK)
plt.colorbar(im, ax=ax, label="Δ module score (Disease − Control)", shrink=0.82)
im2 = ax2.imshow(ps.values, aspect="auto", cmap="RdBu_r", vmin=-lim2, vmax=lim2)
ax2.set_yticks(range(len(ps.index))); ax2.set_yticklabels(ps.index, fontsize=8)
ax2.yaxis.tick_right()
ax2.set_xticks([0]); ax2.set_xticklabels(["GSE222318"], rotation=0, ha="center", fontsize=9.5)
ax2.set_title("Direction only\n49-gene sparse panel\n(separate scale)", fontsize=10, weight="bold", color=ORANGE)
for i in range(ps.shape[0]):
    v = ps.values[i, 0]
    if np.isfinite(v):
        ax2.text(0, i, "%+.2f" % v, ha="center", va="center", fontsize=7.5,
                 color="white" if abs(v) > lim2*0.62 else INK)
fig.suptitle("Cell-level disease-module differences across aortic cohorts (exploratory)",
             fontsize=14, weight="bold", color=INK, y=0.99)
fig.text(0.5, 0.125,
         "Note: small deltas (+0.02 to +0.08) can carry extremely small cell-level nominal P values; "
         "cells are not independent replicates, so sample-level inference (Table 4) is primary.",
         ha="center", va="center", fontsize=9.0, color=ORANGE, weight="bold")
fig.text(0.5, 0.055,
         "GSE224559 has no human control arm (N/A, omitted). Cell-level tests are exploratory; "
         "primary inference is sample-level (Table 4). Cell-type labels harmonised with Table 1.",
         ha="center", fontsize=8.5, color=GREY)
# tight_layout is unreliable for this mixed gridspec + colorbar layout; reserve
# the footer explicitly so the two notes never collide with the x tick labels.
gs.update(left=0.105, right=0.965, top=0.88, bottom=0.18)
plt.savefig(os.path.join(OUT, "fig2.png"), dpi=170, bbox_inches="tight"); plt.close()

# ---------------------------------------------------------------- Fig. 3
fig, ax = plt.subplots(figsize=(10.5, 4.6))
ax.set_xlim(0, 10); ax.set_ylim(0, 4.4); ax.axis("off")
ax.add_patch(FancyBboxPatch((0.2, 0.7), 3.9, 3.0, boxstyle="round,pad=0.12",
                            fc=PALE, ec=NAVY, lw=1.6))
ax.add_patch(FancyBboxPatch((5.9, 0.7), 3.9, 3.0, boxstyle="round,pad=0.12",
                            fc="#fdf1e7", ec=ORANGE, lw=1.6))
ax.text(2.15, 3.30, "HEALTHY AORTA", ha="center", fontsize=12.5, weight="bold", color=NAVY)
ax.text(7.85, 3.30, "ESTABLISHED AORTIC DISEASE", ha="center", fontsize=12.5, weight="bold", color=ORANGE)
ax.text(2.15, 2.75, "Genetic susceptibility enriched\nin SMC and fibroblasts", ha="center", fontsize=10.5, color=INK)
ax.text(2.15, 1.85, "Supported by expression-matched\nnegative-control gene sets", ha="center", fontsize=9.5, color=GREY)
ax.text(2.15, 1.05, "WALL-CELL ENRICHMENT", ha="center", fontsize=10, weight="bold", color=NAVY)
ax.text(7.85, 2.75, "Directional macrophage module\nsignal at the cell level (3/4 cohorts)", ha="center", fontsize=10.5, color=INK)
ax.text(7.85, 1.85, "Sample-level models significant\nin 1/4 cohorts — exploratory", ha="center", fontsize=9.5, color=GREY)
ax.text(7.85, 1.05, "MACROPHAGE-ASSOCIATED SIGNAL", ha="center", fontsize=10, weight="bold", color=ORANGE)
ax.annotate("", xy=(5.75, 2.2), xytext=(4.25, 2.2),
            arrowprops=dict(arrowstyle="->", lw=2, color=GREY))
ax.text(5.0, 2.55, "association", ha="center", fontsize=9.5, color=GREY)
ax.text(5.0, 1.85, "not causation", ha="center", fontsize=9.5, color=GREY)
ax.text(5.0, 0.28, "Two-compartment working hypothesis — testable, not a causal sequence",
        ha="center", fontsize=10, style="italic", color=GREY)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "fig3.png"), dpi=170); plt.close()

# ---------------------------------------------------------------- Graphical abstract
fig = plt.figure(figsize=(13.5, 6.2))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
ax.text(50, 96, "TRI-LEVEL SINGLE-CELL EVIDENCE CHAIN", ha="center", fontsize=16, weight="bold", color=NAVY)
ax.text(50, 92.0, "Aortic dissection and related aortopathies: wall-cell enrichment of inherited susceptibility; "
                  "exploratory macrophage signal in established disease",
        ha="center", va="center", fontsize=9, color=GREY)

boxes = [(3, 46, 30, 39, NAVY, PALE), (35, 46, 30, 39, "#3b6ea5", "#f0f5fb"),
         (67, 46, 30, 39, ORANGE, "#fdf1e7")]
for x, y, w, h, ec, fc in boxes:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6",
                                fc=fc, ec=ec, lw=1.8))

def line(x, y, t, size=8.6, color=INK, weight="normal"):
    ax.text(x, y, t, ha="center", va="center", fontsize=size, color=color, weight=weight)

def button(x, y, t, fc, size=9):
    ax.text(x, y, t, ha="center", va="center", fontsize=size, weight="bold", color="white",
            linespacing=1.35, bbox=dict(boxstyle="round,pad=0.45", fc=fc, ec=fc))

# LAYER 1
line(18, 81.5, "LAYER 1", 12, NAVY, "bold")
line(18, 77.6, "Healthy human aorta", 9.5)
line(18, 73.8, "57,999 cells · 8 cell types", 8.4, GREY)
line(18, 70.8, "16 curated aortic-disease genes", 8.4, GREY)
line(18, 66.8, "SMC  z = +1.08")
line(18, 63.8, "Fibroblast  z = +0.59")
line(18, 60.8, "Macrophage  z = −1.10")
button(18, 51.5, "GENETIC RISK ENRICHED\nIN WALL CELLS", NAVY, 9.2)

# OPTION 2
line(50, 81.5, "OPTION 2", 12, "#3b6ea5", "bold")
line(50, 77.6, "GWAS → gene → scDRS", 9.5)
line(50, 73.8, "Same 57,999 healthy-aorta cells", 8.4, GREY)
line(50, 70.8, "GWAS-weighted gene set", 8.4, GREY)
line(50, 66.8, "SMC +0.39 · Fibroblast +0.32")
line(50, 63.8, "r = 0.78 (95% CI 0.29–0.96)")
line(50, 60.8, "8/16 genes shared: partial convergence", 8.4)
button(50, 51.5, "DIRECTIONAL SUPPORT\n(not independent replication)", "#3b6ea5", 8.6)

# LAYER 2
line(82, 81.5, "LAYER 2", 12, ORANGE, "bold")
line(82, 77.6, "Established aortic disease", 9.5)
line(82, 73.8, "6 GEO cohorts · ~293,000 cells", 8.4, GREY)
line(82, 70.8, "39 samples + one 124,901-cell cohort", 8.4, GREY)
line(82, 66.8, "Cell level: macrophage ↑ in 3/4 cohorts")
line(82, 63.8, "Sample level: significant in 1/4")
line(82, 60.8, "GSE254132 (mixed-effects model)", 8.4)
button(82, 51.5, "EXPLORATORY\nMACROPHAGE SIGNAL", ORANGE, 9)

ax.text(50, 41, "ASSOCIATION, NOT A CAUSAL SEQUENCE", ha="center", va="center",
        fontsize=9.5, style="italic", color=GREY)
ax.add_patch(FancyBboxPatch((3, 12), 45, 24, boxstyle="round,pad=0.5", fc=NAVY, ec=NAVY))
ax.add_patch(FancyBboxPatch((52, 12), 45, 24, boxstyle="round,pad=0.5", fc=ORANGE, ec=ORANGE))
ax.text(25.5, 30, "WALL-CELL ENRICHMENT", ha="center", va="center", fontsize=11, weight="bold", color="white")
ax.text(25.5, 24.8, "Healthy aortic wall: SMC + fibroblasts", ha="center", va="center", fontsize=9, color="white")
ax.text(25.5, 22.0, "Supported by negative-control gene sets", ha="center", va="center", fontsize=9, color="white")
ax.text(25.5, 16.5, "robust, correlative", ha="center", va="center", fontsize=8.5, color="#cfe0f0", style="italic")
ax.text(74.5, 30, "MACROPHAGE-ASSOCIATED SIGNAL", ha="center", va="center", fontsize=11, weight="bold", color="white")
ax.text(74.5, 24.8, "Established disease: cell-level direction in 3/4", ha="center", va="center", fontsize=9, color="white")
ax.text(74.5, 22.0, "Not robust to sample-level inference in most cohorts", ha="center", va="center", fontsize=9, color="white")
ax.text(74.5, 16.5, "hypothesis-generating", ha="center", va="center", fontsize=8.5, color="#fde3cf", style="italic")
ax.text(50, 6, "Curated aortic-disease genes · GWAS summary statistics · public GEO cohorts · "
               "8 pre-specified robustness / sensitivity analyses (Additional file 6)",
        ha="center", va="center", fontsize=8, color=GREY)
ax.text(50, 2.8, "scDRS = single-cell disease-relevance scoring; SMC = smooth muscle cell; "
                 "GEO = Gene Expression Omnibus; GWAS = genome-wide association study",
        ha="center", fontsize=7.5, color=GREY)
plt.savefig(os.path.join(OUT, "graphical_abstract.png"), dpi=170, bbox_inches="tight"); plt.close()

print("figures written to", OUT)
for f in ["fig1.png", "fig2.png", "fig3.png", "graphical_abstract.png"]:
    print(" ", f, os.path.getsize(os.path.join(OUT, f)), "bytes")
