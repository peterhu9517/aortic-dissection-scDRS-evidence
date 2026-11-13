"""对比 Layer 1（已知疾病基因集）与 Option 2（AAD GWAS 派生加权基因集）
在同一 57,999 细胞健康主动脉图谱上的细胞类型富集结果。
两条独立的基因来源若收敛，说明「壁/基质细胞富集」不是基因集选择的偶然产物。
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats as sstats

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56/scdrs_pipeline"
OUT = os.path.join(ROOT, "comparison_out")
os.makedirs(OUT, exist_ok=True)

l1 = pd.read_csv(os.path.join(ROOT, "layer1_out", "celltype_summary.csv"))
o2 = pd.read_csv(os.path.join(ROOT, "option2_out", "celltype_summary.csv"))
print("layer1 cols:", list(l1.columns))
print("option2 cols:", list(o2.columns))

m = l1[["cell_type", "mean_z"]].rename(columns={"mean_z": "z_known_genes"}).merge(
    o2[["cell_type", "mean_z", "fdr"]].rename(columns={"mean_z": "z_gwas", "fdr": "fdr_gwas"}),
    on="cell_type", how="inner")
m = m.sort_values("z_gwas", ascending=False).reset_index(drop=True)
m.to_csv(os.path.join(OUT, "layer1_vs_option2.csv"), index=False)

r_p, p_p = sstats.pearsonr(m.z_known_genes, m.z_gwas)
r_s, p_s = sstats.spearmanr(m.z_known_genes, m.z_gwas)
print("\n", m.round(3).to_string(index=False))
print("\nPearson  r=%.3f (p=%.2g)   Spearman rho=%.3f (p=%.2g)" % (r_p, p_p, r_s, p_s))

x = np.arange(len(m)); w = 0.38
fig, ax = plt.subplots(figsize=(9, 5))
ax.bar(x - w/2, m.z_known_genes, w, label="Layer 1: 16 known disease genes", color="#6A9F58")
ax.bar(x + w/2, m.z_gwas, w, label="Option 2: AAD GWAS top-1000 weighted genes", color="#3B6EA5")
ax.set_xticks(x); ax.set_xticklabels(m.cell_type, rotation=35, ha="right")
ax.axhline(0, color="k", lw=0.8)
ax.set_ylabel("mean scDRS z-score (same 57,999 aortic cells)")
ax.set_title("Two independent gene anchors converge on wall/matrix cells\n"
             "Pearson r=%.2f, Spearman rho=%.2f" % (r_p, r_s))
ax.legend(fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "layer1_vs_option2.png"), dpi=150)
plt.close()
print("saved ->", OUT)
