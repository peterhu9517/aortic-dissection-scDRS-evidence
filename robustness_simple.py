"""Supplementary robustness analyses B-F (fast, dataframe / small-h5ad based).
Outputs JSON + CSV + figures into scdrs_pipeline/robustness_out/.
- B: leave-one-cohort-out consensus for macrophage upregulation
- C: bootstrap CI of Layer1-Option2 convergence Pearson r (+ leave-one-celltype-out)
- D: label permutation test for Layer2 disease_module (per cohort x cell type)
- E: sample-level comparison (aggregate to sample mean; mixed model where feasible)
- F: GSE222318 exclusion sensitivity
"""
import os, json, numpy as np, pandas as pd
import anndata as ad
from scipy import stats as sstats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56/scdrs_pipeline"
OUT  = os.path.join(ROOT, "robustness_out")
os.makedirs(OUT, exist_ok=True)

L2 = pd.read_csv(os.path.join(ROOT, "layer2_multidataset_out", "all_celltype_stats.csv"))
L1 = pd.read_csv(os.path.join(ROOT, "layer1_out", "celltype_summary.csv"))
O2 = pd.read_csv(os.path.join(ROOT, "option2_out", "celltype_summary.csv"))

results = {}

# ---------------------------------------------------------------- C: bootstrap r
m = L1[["cell_type", "mean_z"]].merge(O2[["cell_type", "mean_z"]], on="cell_type",
                                       suffixes=("_l1", "_o2"))
x, y = m.mean_z_l1.values, m.mean_z_o2.values
r_obs, p_obs = sstats.pearsonr(x, y)
B = 20000
rng = np.random.default_rng(20261112)
boot = np.empty(B)
idx = np.arange(len(x))
for b in range(B):
    s = rng.integers(0, len(x), len(x))
    if np.std(x[s]) == 0 or np.std(y[s]) == 0:
        boot[b] = np.nan
    else:
        boot[b] = np.corrcoef(x[s], y[s])[0, 1]
boot = boot[~np.isnan(boot)]
ci_low, ci_high = np.percentile(boot, [2.5, 97.5])
# leave-one-cell-type-out r
loo = {}
for i, ct in enumerate(m.cell_type):
    mask = idx != i
    loo[ct] = float(np.corrcoef(x[mask], y[mask])[0, 1])
results["convergence_r"] = {
    "n_cell_types": int(len(x)),
    "r_obs": float(r_obs), "p_obs": float(p_obs),
    "boot_B": int(B), "ci_95_low": float(ci_low), "ci_95_high": float(ci_high),
    "leave_one_celltype_out_r": loo,
}
plt.figure(figsize=(6, 4))
plt.hist(boot, bins=50, color="#3b6ea5", alpha=0.85)
plt.axvline(r_obs, color="#c0392b", lw=2, label=f"observed r={r_obs:.3f}")
plt.axvline(ci_low, color="#7f8c8d", ls="--", lw=1)
plt.axvline(ci_high, color="#7f8c8d", ls="--", lw=1, label=f"95% CI [{ci_low:.3f}, {ci_high:.3f}]")
plt.xlabel("Bootstrap Pearson r (Layer1 vs Option2, cell-type level)")
plt.ylabel("Frequency")
plt.title("Bootstrap distribution of convergence r")
plt.legend(fontsize=8)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "fig_bootstrap_r.png"), dpi=130)
plt.close()

# ---------------------------------------------------------------- B: leave-one-cohort-out (macrophage)
mac = L2[L2.cell_type == "Macrophage"].copy()
# cohorts with both arms
both = mac[(mac.n_Disease > 0) & (mac.n_Control > 0)].copy()
# direction = up if delta>0 and p<0.05 (two-sided); treat GSE222318 as direction-only
def is_up(r):
    if r.dataset == "GSE222318":
        return r.delta > 0  # direction only
    return (r.delta > 0) and (r.mannwhitney_p < 0.05)
both["up"] = both.apply(is_up, axis=1)
cohorts = list(both.dataset)
loo_rows = []
all_up = int(both["up"].sum()); n_all = len(both)
for drop in [None] + cohorts:
    sub = both if drop is None else both[both.dataset != drop]
    frac = sub["up"].sum() / len(sub) if len(sub) else np.nan
    mean_delta = sub[sub.dataset != "GSE222318"].delta.mean() if drop is None or (drop != "GSE222318") else sub[sub.dataset != "GSE222318"].delta.mean()
    loo_rows.append({
        "exclude_cohort": drop if drop else "NONE (all)",
        "n_cohorts": int(len(sub)),
        "n_up": int(sub["up"].sum()),
        "frac_up": float(frac),
        "mean_signed_delta_excl_GSE222318": float(sub[sub.dataset != "GSE222318"].delta.mean()),
    })
loo_df = pd.DataFrame(loo_rows)
loo_df.to_csv(os.path.join(OUT, "leave_one_cohort.csv"), index=False)
results["leave_one_cohort_macrophage"] = loo_df.to_dict(orient="records")

# ---------------------------------------------------------------- F: GSE222318 exclusion
excl = both[both.dataset != "GSE222318"]
results["gse222318_exclusion"] = {
    "with_GSE222318": {"n_cohorts": int(len(both)), "n_up": int(both["up"].sum()),
                        "frac_up": float(both["up"].sum()/len(both))},
    "without_GSE222318": {"n_cohorts": int(len(excl)), "n_up": int(excl["up"].sum()),
                           "frac_up": float(excl["up"].sum()/len(excl))},
}
plt.figure(figsize=(6, 4))
labels = ["All 5 cohorts", "Excl. GSE222318"]
fracs = [both["up"].sum()/len(both), excl["up"].sum()/len(excl)]
plt.bar(labels, fracs, color=["#3b6ea5", "#5dade2"])
for i, f in enumerate(fracs):
    plt.text(i, f + 0.01, f"{f:.2f}", ha="center", fontsize=10)
plt.ylim(0, 1.1); plt.ylabel("Fraction of cohorts with macrophage upregulation")
plt.title("GSE222318 exclusion sensitivity")
plt.tight_layout()
plt.savefig(os.path.join(OUT, "fig_gse222318_exclusion.png"), dpi=130)
plt.close()

# ---------------------------------------------------------------- D & E: permutation + sample-level
perm_rows, sample_rows = [], []
proc_dir = os.path.join(ROOT, "layer2_multidataset_out")
# GSE222318 has no per-cell processed.h5ad (curated-gene only) -> excluded
# from per-cell permutation / sample-level analyses.
files = {ds: os.path.join(proc_dir, f"{ds}_processed.h5ad")
         for ds in ["GSE213740", "GSE155468", "GSE226492", "GSE254132", "GSE224559"]}
NPERM = 1000
for ds, fp in files.items():
    a = ad.read_h5ad(fp)
    a.obs["condition"] = a.obs["condition"].astype(str)
    if (a.obs.condition == "Control").sum() == 0:
        continue
    cond = a.obs["condition"].values
    dm = a.obs["disease_module"].values.astype(float)
    for ct, g in a.obs.groupby("cell_type"):
        mask = a.obs.cell_type == ct
        yv = dm[mask]; cv = cond[mask]
        iD = cv == "Disease"; iC = cv == "Control"
        if iD.sum() < 5 or iC.sum() < 5:
            continue
        obs_diff = yv[iD].mean() - yv[iC].mean()
        # cell-level MWU (observed)
        u, pcell = sstats.mannwhitneyu(yv[iD], yv[iC], alternative="two-sided")
        # permutation
        rng2 = np.random.default_rng(hash((ds, ct)) & 0xFFFFFFFF)
        cv_np = cv.to_numpy().copy()  # numpy str array -> safe shuffle (no duplicates)
        perm_diff = np.empty(NPERM)
        for k in range(NPERM):
            rng2.shuffle(cv_np)
            pD = cv_np == "Disease"
            perm_diff[k] = yv[pD].mean() - yv[~pD].mean()
        perm_p = (np.sum(np.abs(perm_diff) >= np.abs(obs_diff)) + 1) / (NPERM + 1)
        perm_rows.append({"dataset": ds, "cell_type": ct,
                          "n_Disease": int(iD.sum()), "n_Control": int(iC.sum()),
                          "obs_delta": float(obs_diff), "cell_level_mwu_p": float(pcell),
                          "perm_p": float(perm_p), "n_perm": NPERM})
        # sample-level: aggregate to sample mean
        sub = a.obs.loc[mask, ["sample", "condition", "disease_module"]].copy()
        sm = sub.groupby(["sample", "condition"], observed=True)["disease_module"].mean()
        sD = sm[sm.index.get_level_values(1) == "Disease"].values
        sC = sm[sm.index.get_level_values(1) == "Control"].values
        if len(sD) >= 3 and len(sC) >= 3:
            us, psamp = sstats.mannwhitneyu(sD, sC, alternative="two-sided")
            # mixed model (cells ~ condition + random intercept sample)
            p_mm = None
            try:
                import warnings
                import statsmodels.formula.api as smf
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    dd = sub.rename(columns={"disease_module": "y", "condition": "cond"})
                    dd["cond"] = dd["cond"].map({"Disease": 1, "Control": 0})
                    mm = smf.mixedlm("y ~ cond", dd, groups=dd["sample"]).fit(reml=False)
                    p_mm = float(mm.pvalues.get("cond", np.nan))
            except Exception:
                p_mm = None
            cell_sig = "yes" if pcell < 0.05 else "no"
            samp_sig = "yes" if psamp < 0.05 else "no"
            agree = cell_sig == samp_sig
            sample_rows.append({"dataset": ds, "cell_type": ct,
                                "n_samples_D": int(len(sD)), "n_samples_C": int(len(sC)),
                                "cell_level_mwu_p": float(pcell), "sample_level_mwu_p": float(psamp),
                                "mixed_model_p_cond": p_mm,
                                "cell_sig": cell_sig, "sample_sig": samp_sig,
                                "agree": bool(agree)})
    a.file.close()

perm_df = pd.DataFrame(perm_rows)
sample_df = pd.DataFrame(sample_rows)
perm_df.to_csv(os.path.join(OUT, "permutation_test.csv"), index=False)
sample_df.to_csv(os.path.join(OUT, "sample_level.csv"), index=False)
results["permutation"] = perm_df[perm_df.cell_type == "Macrophage"].to_dict(orient="records")
results["sample_level_macrophage"] = sample_df[sample_df.cell_type == "Macrophage"].to_dict(orient="records")
results["sample_level_agreement_rate"] = float(sample_df["agree"].mean()) if len(sample_df) else None

# figure: permutation p vs cell-level p (macrophage)
fig, ax = plt.subplots(figsize=(6, 5))
mp = perm_df[perm_df.cell_type == "Macrophage"]
ax.scatter(-np.log10(mp.cell_level_mwu_p.clip(1e-300)), -np.log10(mp.perm_p.clip(1e-300)),
           s=70, color="#c0392b")
lim = max(-np.log10(mp[["cell_level_mwu_p", "perm_p"]].clip(1e-300).min().min()), 1)
ax.plot([0, lim], [0, lim], "k--", lw=1)
ax.set_xlabel("-log10 cell-level MWU p"); ax.set_ylabel("-log10 permutation p")
ax.set_title("Label-permutation vs cell-level test (Macrophage)")
ax.set_xlim(0, lim); ax.set_ylim(0, lim)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "fig_permutation.png"), dpi=130); plt.close()

with open(os.path.join(OUT, "robustness_simple.json"), "w") as f:
    json.dump(results, f, indent=2, default=str)

print("=== SUMMARY ===")
print(f"Convergence r = {r_obs:.3f} (95% CI [{ci_low:.3f}, {ci_high:.3f}]), p={p_obs:.2e}")
print(f"Leave-one-cohort (macrophage up fraction):")
print(loo_df.to_string(index=False))
print(f"\nGSE222318 exclusion: with={results['gse222318_exclusion']['with_GSE222318']}, "
      f"without={results['gse222318_exclusion']['without_GSE222318']}")
print(f"\nSample-level agreement rate: {results['sample_level_agreement_rate']}")
print("\nMacrophage permutation (cohort, delta, cell_p, perm_p):")
print(perm_df[perm_df.cell_type=='Macrophage'][['dataset','obs_delta','cell_level_mwu_p','perm_p']].to_string(index=False))
print("\nMacrophage sample-level (cell_p, sample_p, mixed_p, agree):")
print(sample_df[sample_df.cell_type=='Macrophage'][['dataset','cell_level_mwu_p','sample_level_mwu_p','mixed_model_p_cond','agree']].to_string(index=False))
print("\nDONE ->", OUT)
