# -*- coding: utf-8 -*-
"""
Gene-set circularity sensitivity (reviewer point 2).

Re-runs the SAME Layer-2 pipeline as run_layer2_multidataset.py but with the
16-gene curated panel replaced by an 11-gene panel that removes the five
macrophage/inflammation-associated genes MIF, ALOX5, TP53, JAG1, MRC2.

Clustering / cell-type annotation are unaffected (they depend on HVG+PCA, not
on the disease-module score), so the resulting macrophage deltas are directly
comparable with the original analysis.

Writes into revision_out/sensitivity_full/ (never touches layer2_multidataset_out).
"""
import os, sys, glob, warnings, traceback
import numpy as np
import pandas as pd
import scanpy as sc
warnings.filterwarnings("ignore")

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56/scdrs_pipeline"
sys.path.insert(0, ROOT)
import run_layer2_multidataset as M

EXCLUDE = {"MIF", "ALOX5", "TP53", "JAG1", "MRC2"}
FULL = list(M.DISEASE_GENES)
REDUCED = [g for g in FULL if g not in EXCLUDE]
print("FULL panel (%d):" % len(FULL), FULL)
print("REDUCED panel (%d):" % len(REDUCED), REDUCED)

M.DISEASE_GENES = REDUCED
SOUT = os.path.join(ROOT, "revision_out", "sensitivity_full")
os.makedirs(SOUT, exist_ok=True)
M.OUT = SOUT
M.sc.settings.figdir = SOUT
M.sc.settings.verbosity = 1


def load_gse254132():
    lst = []
    for mx in glob.glob("D:/GSE_AD_subsets/GSE254132/*/*/matrix.mtx.gz"):
        sdir = os.path.dirname(mx)
        outer = os.path.basename(os.path.dirname(sdir))
        c, st = M.cond_subtype(outer, "GSE254132")
        a = M.load_10x(sdir, c, st, "GSE254132")
        a.obs["sample"] = outer
        lst.append(a)
    return lst


def load_gse226492():
    lst = []
    for bc in glob.glob("D:/GSE_AD_subsets/GSE226492/*barcodes.tsv.gz"):
        prefix = os.path.basename(bc).replace("_barcodes.tsv.gz", "")
        c, st = M.cond_subtype(prefix, "GSE226492")
        a = M.load_10x("D:/GSE_AD_subsets/GSE226492", c, st, "GSE226492", prefix=prefix)
        a.obs["sample"] = prefix
        lst.append(a)
    return lst


def load_gse155468():
    lst = []
    for f in glob.glob("D:/GSE_AD_subsets/GSM*_Con*.txt.gz") + \
             glob.glob("D:/GSE_AD_subsets/GSM*_TAA*.txt.gz"):
        base = os.path.basename(f).replace(".txt.gz", "")
        c, st = M.cond_subtype(base, "GSE155468")
        a = M.read_gse155468_txt(f, c, st, "GSE155468")
        a.obs["sample"] = base
        lst.append(a)
    return lst


def load_gse213740():
    d = "D:/WorkBuddy/2026-11-05-13-29-03/data/GSE213740"
    lst = []
    if os.path.isdir(d):
        for bc in glob.glob(f"{d}/*barcodes.tsv.gz"):
            prefix = os.path.basename(bc).replace("_barcodes.tsv.gz", "")
            c, st = M.cond_subtype(prefix, "GSE213740")
            a = M.load_10x(d, c, st, "GSE213740", prefix=prefix)
            a.obs["sample"] = prefix
            lst.append(a)
    return lst


JOBS = [
    ("GSE254132", load_gse254132),
    ("GSE226492", load_gse226492),
    ("GSE155468", load_gse155468),
    ("GSE213740", load_gse213740),
]

# Original (16-gene) macrophage deltas for comparison
ORIG = pd.read_csv(os.path.join(ROOT, "layer2_multidataset_out", "all_celltype_stats.csv"))
orig_mac = ORIG[ORIG.cell_type == "Macrophage"].set_index("dataset")

rows = []
for name, loader in JOBS:
    print("\n############ SENSITIVITY:", name, "############", flush=True)
    try:
        lst = loader()
        print("  loaded %d samples" % len(lst), flush=True)
        df = M.analyze_dataset(name, lst)
        if df is None:
            print("  analyze_dataset returned None", flush=True)
            continue
        mac = df[df.cell_type == "Macrophage"]
        if len(mac) == 0:
            print("  WARNING: no Macrophage rows", flush=True)
            continue
        r = mac.iloc[0]
        o = orig_mac.loc[name] if name in orig_mac.index else None
        row = {
            "dataset": name,
            "n_panel_genes": len(REDUCED),
            "delta_cell_reduced": float(r["delta"]),
            "p_cell_reduced": float(r["mannwhitney_p"]),
            "delta_cell_full16": float(o["delta"]) if o is not None else np.nan,
            "p_cell_full16": float(o["mannwhitney_p"]) if o is not None else np.nan,
            "direction_preserved": bool(np.sign(float(r["delta"])) == np.sign(float(o["delta"]))) if o is not None else None,
        }
        rows.append(row)
        print("  RESULT reduced delta=%+.4f (p=%.2g) vs full delta=%+.4f  direction_preserved=%s"
              % (row["delta_cell_reduced"], row["p_cell_reduced"],
                 row["delta_cell_full16"], row["direction_preserved"]), flush=True)
        pd.DataFrame(rows).to_csv(os.path.join(SOUT, "sensitivity_results.csv"), index=False)
    except Exception as e:
        print("  FAILED:", repr(e), flush=True)
        traceback.print_exc()

out = pd.DataFrame(rows)
out.to_csv(os.path.join(SOUT, "sensitivity_results.csv"), index=False)
print("\nDONE. Results ->", os.path.join(SOUT, "sensitivity_results.csv"), flush=True)
print(out.to_string(index=False), flush=True)
