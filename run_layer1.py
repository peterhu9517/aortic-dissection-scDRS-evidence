"""Layer 1 (Plan E): 用"已知主动脉疾病相关基因集"在健康主动脉单细胞图谱上
做 scDRS 细胞级打分，并下钻到细胞类型关联 + UMAP 叠加。

依赖：scdrs（已装）、scanpy、matplotlib。
用法：
  python3 run_layer1.py            # 全量 57,999 细胞
  python3 run_layer1.py 2000      # 仅前 2000 细胞（debug）
"""
import os, sys, scanpy as sc, pandas as pd, numpy as np
import scdrs
from scdrs.method import score_cell, downstream_group_analysis
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56/scdrs_pipeline"
SUB   = os.path.join(ROOT, "aao_subset.h5ad")
GENELIST = os.path.join(ROOT, "aad_geneset.txt")
OUT   = os.path.join(ROOT, "layer1_out")
os.makedirs(OUT, exist_ok=True)

n = int(sys.argv[1]) if len(sys.argv) > 1 else None
sub = sc.read_h5ad(SUB)
# 关键修复：去掉 .raw 槽位。scDRS 在 score_cell 内做 adata[:, gene_list]
# 切片时，若 adata.raw 存在，anndata 会同步对完整 raw 矩阵做子集，
# 触发一次 ~700MB 的临时分配，在内存压力下直接 _ArrayMemoryError 崩溃。
sub.raw = None
if n:
    sub = sub[:n].copy()
    sub.raw = None
genes = [l.strip() for l in open(GENELIST) if l.strip()]
print("n_cells=%d  n_genes=%d  genes=%s" % (sub.shape[0], len(genes), genes))

# 1) scDRS 预处理（建 control 基因池）
scdrs.pp.preprocess(sub)
sub.raw = None  # 再次防御性清除，避免 score_cell 切片 raw 触发大分配

# 2) 细胞级打分（已知疾病基因集作为 disease gene set）
df = score_cell(sub, genes, n_ctrl=500, verbose=True)
df.to_csv(os.path.join(OUT, "full_score.csv"))
print("df_full_score shape:", df.shape, "cols:", list(df.columns))

# 3) 细胞类型水平关联
#    注：scDRS 自带 downstream_group_analysis 调用 gearys_c，其中 np.float_
#    在 NumPy 2.x 已被移除，会崩溃。Layer 1 只需"各细胞类型 vs 其余"的
#    富集检验，这里用 scipy 自实现（Welch t + FDR），不依赖坏掉的下游函数。
summary = pd.DataFrame({'zscore': df['zscore'].values,
                        'cell_type': sub.obs['author_cell_type'].values},
                       index=sub.obs.index)
from scipy import stats as sstats
rows = []
for ct in summary['cell_type'].unique():
    z = summary.loc[summary.cell_type == ct, 'zscore'].values
    rest = summary.loc[summary.cell_type != ct, 'zscore'].values
    t, p = sstats.ttest_ind(z, rest, equal_var=False)
    rows.append((ct, len(z), float(z.mean()), float(z.std(ddof=1)), float(t), float(p)))
g = pd.DataFrame(rows, columns=['cell_type', 'n', 'mean_z', 'std_z', 't', 'p'])
g['fdr'] = sstats.false_discovery_control(g['p'].values)
g = g.sort_values('mean_z', ascending=False).reset_index(drop=True)
print("\n=== per-cell-type AAD disease-gene set enrichment ===\n", g.to_string())
g.to_csv(os.path.join(OUT, "celltype_summary.csv"))

plt.figure(figsize=(8, 5))
err = g['std_z'] / np.sqrt(g['n'])
plt.bar(range(len(g)), g['mean_z'], yerr=err, capsize=4, color='#3b6ea5')
plt.xticks(range(len(g)), g['cell_type'], rotation=45, ha='right')
plt.ylabel('mean scDRS z-score (AAD known-disease-gene set)')
plt.title('Layer 1: AAD disease-gene enrichment across aortic cell types')
plt.tight_layout()
plt.savefig(os.path.join(OUT, "celltype_bar.png"), dpi=130)
print("saved celltype_bar.png")

# 5) UMAP 叠加打分
umap = sub.obsm['X_umap']
z = df['zscore'].values
plt.figure(figsize=(7, 6))
sc1 = plt.scatter(umap[:, 0], umap[:, 1], c=z, cmap='RdBu_r', s=2, vmin=-3, vmax=3)
plt.colorbar(sc1, label='scDRS z-score')
plt.title('UMAP overlay: AAD disease-gene set score')
plt.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(OUT, "umap_z.png"), dpi=130)
print("saved umap_z.png")
print("ALL DONE")
