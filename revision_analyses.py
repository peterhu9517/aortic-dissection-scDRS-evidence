# -*- coding: utf-8 -*-
"""
Revision analyses (reviewer major-revision, points 1-3, 8).

Runs on the four processed GEO h5ad files that carry a human control arm:
  (1) Gene-set overlap: curated 16-gene panel vs Option-2 GWAS-weighted set.
  (2) Donor/sample-level PRIMARY table: sample means, 95% CI, Welch t on
      sample means, and a mixed-effects model (random intercept for sample).
  (3) Sample-level label permutation (the correct unit; old AF6 used cells).
  (4) MIF/ALOX5/TP53/JAG1/MRC2-excluded sensitivity: re-score each dataset
      with Scanpy score_genes on the remaining 11 genes, recompute macrophage
      delta at cell and sample level.

Outputs -> revision_out/  (CSV, JSON, PNG)
"""
import os, json, warnings
import numpy as np
import pandas as pd
import scanpy as sc
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56/scdrs_pipeline"
L2   = os.path.join(ROOT, "layer2_multidataset_out")
OUT  = os.path.join(ROOT, "revision_out")
os.makedirs(OUT, exist_ok=True)

DATASETS = ["GSE213740", "GSE155468", "GSE226492", "GSE254132"]
LABELS = {
    "GSE213740": "Acute type-A dissection",
    "GSE155468": "Thoracic ascending aneurysm",
    "GSE226492": "Mixed (AAA/AD/Marfan)",
    "GSE254132": "Acute type-A dissection",
}
NPERM = 2000
SEED = 20261113

# ---------------------------------------------------------------- panel
sym = {}
for line in open(os.path.join(ROOT, "aad_geneset_symbols.txt"), encoding="utf-8"):
    parts = line.strip().split("\t")
    if len(parts) == 2:
        sym[parts[0]] = parts[1]
CURATED_ENSG = set(sym.keys())
CURATED_SYM  = [sym[k] for k in sym]
EXCLUDE = {"MIF", "ALOX5", "TP53", "JAG1", "MRC2"}
REDUCED = [g for g in CURATED_SYM if g not in EXCLUDE]

res = {"panel": {}, "overlap": {}, "donor_primary": [], "sample_perm": [],
       "sensitivity": [], "notes": []}

# ---------------------------------------------------------------- (1) overlap
gs_lines = [l for l in open(os.path.join(ROOT, "option2_out", "AAD.gs"), encoding="utf-8").read().split("\n") if l.strip()]
gs_payload = gs_lines[1].split("\t")[-1]
gwas_items = [x for x in gs_payload.split(",") if ":" in x]
gwas_ensg = {x.split(":")[0] for x in gwas_items}
overlap = sorted(CURATED_ENSG & gwas_ensg)
res["panel"] = {
    "n_curated": len(CURATED_ENSG),
    "curated_symbols": CURATED_SYM,
    "excluded_macrophage_inflammation": sorted(EXCLUDE),
    "n_reduced": len(REDUCED),
    "reduced_symbols": REDUCED,
}
res["overlap"] = {
    "n_gwas_weighted_genes": len(gwas_ensg),
    "n_overlap": len(overlap),
    "overlap_ensg": overlap,
    "overlap_symbols": [sym.get(e, "?") for e in overlap],
    "pct_of_curated_overlapping": round(100.0 * len(overlap) / len(CURATED_ENSG), 1),
}
print("(1) Gene-set overlap: %d/%d curated genes also in GWAS-weighted set: %s"
      % (len(overlap), len(CURATED_ENSG), res["overlap"]["overlap_symbols"]))


def ci95(v):
    v = np.asarray(v, float)
    n = len(v)
    if n < 2:
        return (float(np.nan), float(np.nan))
    se = v.std(ddof=1) / np.sqrt(n)
    h = stats.t.ppf(0.975, n - 1) * se
    return (float(v.mean() - h), float(v.mean() + h))


def mixedlm_p(sub):
    """cells ~ condition + (1|sample); returns p for condition."""
    try:
        import statsmodels.formula.api as smf
        dd = sub[["sample", "condition", "y"]].copy()
        dd["cond"] = (dd["condition"] == "Disease").astype(int)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = smf.mixedlm("y ~ cond", dd, groups=dd["sample"]).fit(reml=False)
        return float(m.pvalues.get("cond", np.nan)), float(m.params.get("cond", np.nan))
    except Exception as e:
        res["notes"].append("mixedlm failed: %s" % str(e)[:120])
        return None, None


# ---------------------------------------------------------------- per dataset
for ds in DATASETS:
    f = os.path.join(L2, ds + "_processed.h5ad")
    ad = sc.read_h5ad(f)
    # Scanpy 1.12.5 score_genes cannot take a sparse .X (np.nanmean returns None)
    import scipy.sparse as _sp
    if _sp.issparse(ad.X):
        ad.X = ad.X.toarray()
    obs = ad.obs.copy()
    obs["y"] = obs["disease_module"].astype(float)
    mac = obs[obs["cell_type"] == "Macrophage"].copy()

    # --- (2) donor/sample-level primary table
    sm = mac.groupby(["sample", "condition"], observed=True)["y"].mean().reset_index()
    sD = sm.loc[sm.condition == "Disease", "y"].values
    sC = sm.loc[sm.condition == "Control", "y"].values
    loD, hiD = ci95(sD); loC, hiC = ci95(sC)
    delta_s = float(sD.mean() - sC.mean())
    # delta CI via Welch approximation on sample means
    se_d = np.sqrt(sD.var(ddof=1)/len(sD) + sC.var(ddof=1)/len(sC)) if len(sD) > 1 and len(sC) > 1 else np.nan
    dfw = (sD.var(ddof=1)/len(sD) + sC.var(ddof=1)/len(sC))**2 / (
        (sD.var(ddof=1)/len(sD))**2/(len(sD)-1) + (sC.var(ddof=1)/len(sC))**2/(len(sC)-1)
    ) if len(sD) > 1 and len(sC) > 1 else np.nan
    h_d = stats.t.ppf(0.975, dfw) * se_d if np.isfinite(dfw) else np.nan
    t_p = float(stats.ttest_ind(sD, sC, equal_var=False).pvalue) if len(sD) > 1 and len(sC) > 1 else None
    mw_p = float(stats.mannwhitneyu(sD, sC, alternative="two-sided").pvalue) if len(sD) > 2 and len(sC) > 2 else None
    mm_p, mm_beta = mixedlm_p(mac)
    cellD = mac.loc[mac.condition == "Disease", "y"].values
    cellC = mac.loc[mac.condition == "Control", "y"].values
    cell_p = float(stats.mannwhitneyu(cellD, cellC, alternative="two-sided").pvalue)

    row = {
        "dataset": ds, "phenotype": LABELS[ds],
        "n_samples_D": int(len(sD)), "n_samples_C": int(len(sC)),
        "n_cells_D": int(len(cellD)), "n_cells_C": int(len(cellC)),
        "mean_D": float(sD.mean()), "ci_D": [loD, hiD],
        "mean_C": float(sC.mean()), "ci_C": [loC, hiC],
        "delta_sample": delta_s, "delta_sample_ci": [float(delta_s-h_d), float(delta_s+h_d)],
        "welch_p_sample": t_p, "mwu_p_sample": mw_p,
        "mixedlm_p_cond": mm_p, "mixedlm_beta_cond": mm_beta,
        "delta_cell": float(cellD.mean()-cellC.mean()), "mwu_p_cell": cell_p,
    }
    res["donor_primary"].append(row)
    print("(2) %-11s nD=%d nC=%d  sample delta=%+.4f  Welch p=%.3g  mixedlm p=%s beta=%s  cell p=%.2g"
          % (ds, len(sD), len(sC), delta_s, t_p if t_p else float("nan"),
             ("%.3g" % mm_p) if mm_p else "NA",
             ("%+.4f" % mm_beta) if mm_beta else "NA", cell_p))
    # diagnostic: per-sample macrophage means (why sample-level can disagree with cell-level)
    _diag = sm.copy()
    _diag["y"] = _diag["y"].round(4)
    print("      per-sample means:", ", ".join("%s/%s=%.4f" % (r["sample"], r["condition"][:1], r["y"])
          for _, r in _diag.iterrows()))

    # --- (3) sample-level label permutation (permute sample labels, keep nD/nC)
    labels = sm["condition"].to_numpy().copy()
    vals = sm["y"].to_numpy().astype(float)
    obs_delta = vals[labels == "Disease"].mean() - vals[labels == "Control"].mean()
    rng = np.random.default_rng(SEED + DATASETS.index(ds))
    perm = np.empty(NPERM)
    for k in range(NPERM):
        rng.shuffle(labels)
        perm[k] = vals[labels == "Disease"].mean() - vals[labels == "Control"].mean()
    p_perm = float((np.sum(np.abs(perm) >= np.abs(obs_delta)) + 1) / (NPERM + 1))
    res["sample_perm"].append({
        "dataset": ds, "unit": "sample", "n_perm": NPERM,
        "observed_delta_sample_means": float(obs_delta),
        "perm_p_two_sided": p_perm,
        "perm_null_sd": float(perm.std(ddof=1)),
    })
    print("(3) %-11s sample-level permutation p=%.4f (n_perm=%d)" % (ds, p_perm, NPERM))

    # --- (4) re-score with the 11-gene reduced panel
    # NOTE: processed h5ad files are "light" (X=None), so this requires the
    # original 10x matrices; handled by revision_sensitivity.py instead.
    # Kept as an optional hook in case a full matrix is present.
    if ad.X is not None:
        try:
            present = [g for g in REDUCED if g in set(ad.var_names)]
            sc.tl.score_genes(ad, present, score_name="module_reduced", random_state=0)
            obs2 = ad.obs.copy()
            obs2["y"] = obs2["module_reduced"].astype(float)
            mac2 = obs2[obs2["cell_type"] == "Macrophage"].copy()
            rD = mac2.loc[mac2.condition == "Disease", "y"].values
            rC = mac2.loc[mac2.condition == "Control", "y"].values
            red_cell_delta = float(rD.mean() - rC.mean())
            red_cell_p = float(stats.mannwhitneyu(rD, rC, alternative="two-sided").pvalue)
            sm2 = mac2.groupby(["sample", "condition"], observed=True)["y"].mean().reset_index()
            rSD = sm2.loc[sm2.condition == "Disease", "y"].values
            rSC = sm2.loc[sm2.condition == "Control", "y"].values
            red_samp_delta = float(rSD.mean() - rSC.mean())
            red_samp_p = float(stats.ttest_ind(rSD, rSC, equal_var=False).pvalue) if len(rSD) > 1 and len(rSC) > 1 else None
            res["sensitivity"].append({
                "dataset": ds, "n_panel_genes_used": len(present),
                "delta_cell_full": row["delta_cell"], "delta_cell_reduced": red_cell_delta,
                "p_cell_reduced": red_cell_p,
                "delta_sample_reduced": red_samp_delta, "p_sample_reduced": red_samp_p,
                "direction_preserved": bool(np.sign(red_cell_delta) == np.sign(row["delta_cell"])),
            })
            print("(4) %-11s reduced(%d genes) cell delta=%+.4f (p=%.2g)  direction preserved=%s"
                  % (ds, len(present), red_cell_delta, red_cell_p,
                     np.sign(red_cell_delta) == np.sign(row["delta_cell"])))
        except Exception as e:
            res["notes"].append("%s reduced-panel scoring failed: %s" % (ds, str(e)[:140]))
    else:
        res["notes"].append("%s: processed h5ad has X=None; reduced-panel score deferred to revision_sensitivity.py" % ds)

# ---------------------------------------------------------------- save tables
dp = pd.DataFrame([{
    "Dataset": r["dataset"], "Phenotype": r["phenotype"],
    "n samples (D/C)": "%d/%d" % (r["n_samples_D"], r["n_samples_C"]),
    "Mean D (95% CI)": "%.4f (%.4f-%.4f)" % (r["mean_D"], r["ci_D"][0], r["ci_D"][1]),
    "Mean C (95% CI)": "%.4f (%.4f-%.4f)" % (r["mean_C"], r["ci_C"][0], r["ci_C"][1]),
    "Δ sample (95% CI)": "%+.4f (%+.4f-%+.4f)" % (r["delta_sample"], r["delta_sample_ci"][0], r["delta_sample_ci"][1]),
    "Welch p (sample)": "%.3g" % r["welch_p_sample"] if r["welch_p_sample"] else "NA",
    "Mixed-model p (cond)": "%.3g" % r["mixedlm_p_cond"] if r["mixedlm_p_cond"] else "NA",
    "Cell-level MWU p (exploratory)": "%.3g" % r["mwu_p_cell"],
} for r in res["donor_primary"]])
dp.to_csv(os.path.join(OUT, "donor_primary_table.csv"), index=False)

sp = pd.DataFrame(res["sample_perm"])
sp.to_csv(os.path.join(OUT, "sample_level_permutation.csv"), index=False)

se = pd.DataFrame(res["sensitivity"])
se.to_csv(os.path.join(OUT, "panel_sensitivity.csv"), index=False)

ov = pd.DataFrame({
    "ENSG": res["overlap"]["overlap_ensg"],
    "Symbol": res["overlap"]["overlap_symbols"],
    "In curated 16-gene panel": "yes",
    "In Option-2 GWAS-weighted set": "yes",
})
ov.to_csv(os.path.join(OUT, "gene_set_overlap.csv"), index=False)

with open(os.path.join(OUT, "revision_summary.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)

# ---------------------------------------------------------------- figures
# Fig R1: sample-level forest plot (primary evidence)
fig, ax = plt.subplots(figsize=(8, 4.2))
ys = np.arange(len(res["donor_primary"]))
for i, r in enumerate(res["donor_primary"]):
    lo, hi = r["delta_sample_ci"]
    ax.plot([lo, hi], [i, i], "o-", color="#1f4e79", lw=2, markersize=5)
    ax.annotate("p(mixed)=%s" % (("%.2g" % r["mixedlm_p_cond"]) if r["mixedlm_p_cond"] else "NA"),
                (hi, i), textcoords="offset points", xytext=(6, -3), fontsize=8, color="#555")
ax.axvline(0, color="grey", ls="--", lw=1)
ax.set_yticks(ys); ax.set_yticklabels([r["dataset"] for r in res["donor_primary"]])
ax.set_xlabel("Δ macrophage module score (sample means, 95% CI)")
ax.set_title("Sample-level primary analysis — macrophage module (disease minus control)")
ax.set_xlim(left=min(r["delta_sample_ci"][0] for r in res["donor_primary"]) - 0.02,
            right=max(r["delta_sample_ci"][1] for r in res["donor_primary"]) + 0.10)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "fig_sample_level_forest.png"), dpi=160); plt.close()

# Fig R2: full vs reduced panel macrophage delta (only if sensitivity was computed)
if res["sensitivity"]:
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    x = np.arange(len(res["sensitivity"])); w = 0.36
    ax.bar(x - w/2, [r["delta_cell_full"] for r in res["sensitivity"]], w, label="16-gene full panel", color="#c0392b")
    ax.bar(x + w/2, [r["delta_cell_reduced"] for r in res["sensitivity"]], w, label="11-gene panel (MIF/ALOX5/TP53/JAG1/MRC2 removed)", color="#2c7fb8")
    ax.axhline(0, color="grey", ls="--", lw=1)
    ax.set_xticks(x); ax.set_xticklabels([r["dataset"] for r in res["sensitivity"]], rotation=20, ha="right")
    ax.set_ylabel("Δ macrophage module score (disease minus control)")
    ax.set_title("Gene-set circularity sensitivity: removing macrophage/inflammation genes")
    ax.legend(fontsize=8); plt.tight_layout()
    plt.savefig(os.path.join(OUT, "fig_panel_sensitivity.png"), dpi=160); plt.close()

print("\nDONE ->", OUT)
print("overlap: %d/%d (%.1f%%)" % (res["overlap"]["n_overlap"], res["panel"]["n_curated"],
                                   res["overlap"]["pct_of_curated_overlapping"]))
