# 03_collect_results.py
# 汇总 scDRS 下游结果 -> 细胞类型关联图 + UMAP 叠加 + Top 表
import os
import glob
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import scanpy as sc

DATA = "./data"
DOWN = os.path.join(DATA, "downstream")
RESULTS = "./results"
os.makedirs(RESULTS, exist_ok=True)

# ---------- 1) 细胞类型关联条形图 ----------
assoc_files = glob.glob(os.path.join(DOWN, "*cell_type_assoc*"))
if not assoc_files:
    raise SystemExit(f"未找到 cell_type_assoc 文件，请先跑 02_run_scdrs.py（{DOWN}）")
df = pd.read_csv(assoc_files[0], sep=None, engine="python")
print(">> assoc columns:", list(df.columns))
print(df.sort_values("z_score", ascending=False).head(10).to_string(index=False))

# 兼容不同列名
ct_col = "cell_type"
z_col = "z_score" if "z_score" in df else "z"
p_col = "pval" if "pval" in df else "p_value"

d = df.copy().sort_values(z_col, ascending=True)
fig, ax = plt.subplots(figsize=(8, max(3, 0.4 * len(d))))
colors = ["#c0392b" if p < 0.05 else "#95a5a6" for p in d[p_col]]
ax.barh(d[ct_col].astype(str), d[z_col], color=colors)
ax.set_xlabel("scDRS z-score (AAD genetic risk enrichment)")
ax.set_title("Layer 1: AAD GWAS enrichment across healthy aortic cell types")
ax.axvline(0, color="k", lw=0.8)
fig.tight_layout()
fig.savefig(os.path.join(RESULTS, "fig1_celltype_assoc.png"), dpi=150)
print(">> saved results/fig1_celltype_assoc.png")

# ---------- 2) UMAP 叠加 scDRS 分数 ----------
score_h5 = [f for f in glob.glob(os.path.join(DATA, "scdrs_score", "*.h5ad")) if "scdrs" in os.path.basename(f)]
if score_h5:
    a = sc.read_h5ad(score_h5[0])
    # scDRS 把分数写进 obs（列名含 scdrs_score）
    score_col = [c for c in a.obs.columns if "scdrs" in c and "score" in c]
    if score_col and "X_umap" in a.obsm:
        sc.pl.umap(a, color=score_col[0], show=False,
                   save="_layer1_score.png", cmap="Reds")
        print(">> saved figures/umap_layer1_score.png (scanpy 默认输出到 ./figures)")
    else:
        print(">> 未找到 UMAP 或分数列，跳过 UMAP 图；可用 perform-downstream 的 umap.pdf")
else:
    print(">> 未找到 scored h5ad，跳过 UMAP 图")

print("\n>> Top 正向富集细胞类型（z>0）:")
print(d.sort_values(z_col, ascending=False).head(5)[[ct_col, z_col, p_col]].to_string(index=False))
