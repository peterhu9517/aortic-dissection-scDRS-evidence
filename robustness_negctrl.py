"""Supplementary robustness A: negative-control gene-set scoring.
Memory-safe scDRS-equivalent on the 3.1 GB sparse healthy-aorta atlas:
  - X is already log-normalized (verified: nonzero values ~0.3-3.8)
  - per-gene standardization across cells
  - 500 expression-matched control gene sets (scDRS-style rank-window sampling)
  - per-cell z = (set_score - mean(control_scores)) / std(control_scores)
  - per-cell-type Welch t vs all-other cells + BH FDR
Runs the SAME pipeline on (i) the 16-gene AAD disease set (positive control,
   should reproduce Layer 1 SMC/Fibroblast enrichment) and (ii) a 16-gene
   expression-matched null set (should show ~0 enrichment).
"""
import os, json, numpy as np, pandas as pd, scipy.sparse as sp
import anndata as ad
from scipy import stats as sstats
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56/scdrs_pipeline"
ATLAS = "D:/aao_subset_backup.h5ad"
GENELIST = os.path.join(ROOT, "aad_geneset.txt")
OUT = os.path.join(ROOT, "robustness_out")
os.makedirs(OUT, exist_ok=True)

N_CTRL = 500
WINDOW = 50          # rank window for expression-matched control sampling
N_CHUNK = 4000       # cells per chunk for sparse passes
rng = np.random.default_rng(20261113)

print("opening atlas (backed, sparse) ...", flush=True)
a = ad.read_h5ad(ATLAS, backed="r")
genes = np.array(a.var.index)
ncells, ngenes = a.shape
print(f"  atlas {ncells} cells x {ngenes} genes; X sparse={sp.issparse(a.X)}", flush=True)

# ---- step 1: per-gene mean & std across cells (chunked, sparse) ----------
gene_sum = np.zeros(ngenes, dtype=np.float64)
gene_sumsq = np.zeros(ngenes, dtype=np.float64)
gene_nnz = np.zeros(ngenes, dtype=np.float64)
for s in range(0, ncells, N_CHUNK):
    e = min(s + N_CHUNK, ncells)
    X = a[s:e].X
    if sp.issparse(X):
        X = X.toarray()
    gene_sum += X.sum(0)
    gene_sumsq += (X ** 2).sum(0)
    gene_nnz += (X > 0).sum(0)
gene_mean = gene_sum / ncells
gene_var = gene_sumsq / ncells - gene_mean ** 2
gene_std = np.sqrt(np.clip(gene_var, 1e-12, None))
rank_order = np.argsort(gene_mean)          # ascending mean-expression rank
rank_of = np.empty(ngenes, dtype=int); rank_of[rank_order] = np.arange(ngenes)
print("  per-gene stats done", flush=True)

# ---- step 2: AAD set + null set + control sets ---------------------------
aad_ids = [l.strip() for l in open(GENELIST) if l.strip()]
aad_idx = [np.where(genes == g)[0][0] for g in aad_ids if g in set(genes)]
missing = [g for g in aad_ids if g not in set(genes)]
print(f"  AAD set: {len(aad_idx)}/{len(aad_ids)} genes matched; missing={missing}", flush=True)

def matched_null(seed_offset):
    """16 genes whose mean-expression rank matches the AAD genes one-to-one."""
    r = np.random.default_rng(20261113 + seed_offset)
    out = []
    for g in aad_idx:
        rk = rank_of[g]
        lo, hi = max(0, rk - WINDOW), min(ngenes - 1, rk + WINDOW)
        cand = rank_order[lo:hi + 1]
        cand = cand[cand != g]
        out.append(int(r.choice(cand)))
    return out

null_idx = matched_null(1)
print(f"  null set: {len(null_idx)} genes; sample IDs {[genes[i] for i in null_idx[:4]]}...", flush=True)

# 500 control sets, each 16 genes matched to the AAD set's expression profile
control_sets = []
for c in range(N_CTRL):
    r = np.random.default_rng(7000 + c)
    cs = []
    for g in aad_idx:
        rk = rank_of[g]
        lo, hi = max(0, rk - WINDOW), min(ngenes - 1, rk + WINDOW)
        cand = rank_order[lo:hi + 1]; cand = cand[cand != g]
        cs.append(int(r.choice(cand)))
    control_sets.append(cs)
ctrl_idx_flat = sorted(set(i for cs in control_sets for i in cs))
print(f"  {N_CTRL} control sets built; unique control genes={len(ctrl_idx_flat)}", flush=True)

# ---- step 3: standardize needed gene columns and score --------------------
def standardize_columns(idx_list):
    """Return dense 58k x len(idx) gene-z matrix for the requested genes."""
    idx = np.array(idx_list)
    X = a[:, idx].X
    if sp.issparse(X):
        X = X.toarray()
    X = X.astype(np.float64)
    m = gene_mean[idx]; sd = gene_std[idx]
    return (X - m) / sd

# AAD + null set scores
z_aad = standardize_columns(aad_idx)
z_null = standardize_columns(null_idx)
aad_score = z_aad.mean(1)
null_score = z_null.mean(1)
print("  AAD/null set scores computed", flush=True)

# control scores in batches (bound peak memory: slice only each batch's genes)
ctrl_score = np.empty((ncells, N_CTRL), dtype=np.float64)
BATCH = 25
for b0 in range(0, N_CTRL, BATCH):
    b1 = min(b0 + BATCH, N_CTRL)
    batch_sets = control_sets[b0:b1]
    ugenes = sorted(set(g for cs in batch_sets for g in cs))
    z_u = standardize_columns(ugenes)
    pos = {g: j for j, g in enumerate(ugenes)}
    for k, cs in enumerate(batch_sets):
        cols = np.array([pos[g] for g in cs])
        ctrl_score[:, b0 + k] = z_u[:, cols].mean(1)
print("  control scores computed", flush=True)

def scdrs_z(set_score):
    mu = ctrl_score.mean(1); sd = ctrl_score.std(1)
    return (set_score - mu) / np.clip(sd, 1e-9, None)

z_aad_cells = scdrs_z(aad_score)
z_null_cells = scdrs_z(null_score)

# ---- step 4: per-cell-type Welch t + FDR ---------------------------------
ct = a.obs["author_cell_type"].values

def celltype_enrichment(zcells):
    rows = []
    for c in np.unique(ct):
        z = zcells[ct == c]; rest = zcells[ct != c]
        t, p = sstats.ttest_ind(z, rest, equal_var=False)
        rows.append((c, int((ct == c).sum()), float(z.mean()), float(z.std(ddof=1)), float(t), float(p)))
    g = pd.DataFrame(rows, columns=["cell_type", "n", "mean_z", "std_z", "t", "p"])
    g["fdr"] = sstats.false_discovery_control(g["p"].values)
    return g.sort_values("mean_z", ascending=False).reset_index(drop=True)

res_aad = celltype_enrichment(z_aad_cells)
res_null = celltype_enrichment(z_null_cells)
res_aad.to_csv(os.path.join(OUT, "negctrl_AAD_enrichment.csv"), index=False)
res_null.to_csv(os.path.join(OUT, "negctrl_NULL_enrichment.csv"), index=False)
print("\n=== AAD set (positive control) ===")
print(res_aad.to_string(index=False))
print("\n=== NULL set (negative control) ===")
print(res_null.to_string(index=False))

# ---- step 5: figures ----------------------------------------------------
def plot(g, title, fname):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    err = g["std_z"] / np.sqrt(g["n"])
    colors = ["#c0392b" if x > 0 else "#2e86c1" for x in g["mean_z"]]
    ax.bar(range(len(g)), g["mean_z"], yerr=err, capsize=4, color=colors)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(range(len(g))); ax.set_xticklabels(g["cell_type"], rotation=45, ha="right")
    ax.set_ylabel("mean scDRS-equivalent z"); ax.set_title(title)
    plt.tight_layout(); plt.savefig(os.path.join(OUT, fname), dpi=130); plt.close()
plot(res_aad, "Negative-control check: AAD disease gene set (should enrich SMC/Fibroblast)",
     "fig_negctrl_AAD.png")
plot(res_null, "Negative-control check: expression-matched null gene set (should be ~0)",
     "fig_negctrl_NULL.png")

# combined
fig, ax = plt.subplots(figsize=(7.5, 4.5))
xpos = np.arange(len(res_aad)); w = 0.4
ax.bar(xpos - w/2, res_aad["mean_z"], w, yerr=res_aad["std_z"]/np.sqrt(res_aad["n"]),
       label="AAD disease set", color="#c0392b")
ax.bar(xpos + w/2, res_null["mean_z"], w, yerr=res_null["std_z"]/np.sqrt(res_null["n"]),
       label="Null set", color="#7f8c8d")
ax.axhline(0, color="k", lw=0.8); ax.set_xticks(xpos)
ax.set_xticklabels(res_aad["cell_type"], rotation=45, ha="right")
ax.set_ylabel("mean z"); ax.legend(); ax.set_title("Negative-control gene-set comparison")
plt.tight_layout(); plt.savefig(os.path.join(OUT, "fig_negctrl_compare.png"), dpi=130); plt.close()

a.file.close()
out = {
    "n_ctrl": N_CTRL, "window": WINDOW,
    "aad_n_matched": len(aad_idx), "aad_missing": missing,
    "null_n": len(null_idx),
    "aad_max_abs_mean_z": float(res_aad["mean_z"].abs().max()),
    "null_max_abs_mean_z": float(res_null["mean_z"].abs().max()),
    "aad_n_significant_fdr": int((res_aad["fdr"] < 0.05).sum()),
    "null_n_significant_fdr": int((res_null["fdr"] < 0.05).sum()),
}
with open(os.path.join(OUT, "negctrl_summary.json"), "w") as f:
    json.dump(out, f, indent=2)
print("\nSUMMARY:", json.dumps(out, indent=2))
print("DONE ->", OUT)
