"""
Layer 2: ATAAD vs Normal 单细胞对比 (GSE213740, 升主动脉壁)
- 9 个 10x 样本 (6 AD + 3 Normal) 读入、质检、整合、聚类、细胞类型注释
- 16 基因已知疾病模块打分, 比较 AD vs Normal 各细胞类型
- 逐细胞类型差异表达 (AD vs Normal)
输出: layer2_out/ (umap_condition.png, umap_module.png, composition.png,
                    celltype_stats.csv, de_top.csv, gse213740_processed.h5ad)
"""
import os, gzip, glob
import numpy as np
import pandas as pd
import scanpy as sc
from scipy.io import mmread
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats as sstats

INPUT_DIR = "D:/WorkBuddy/2026-11-05-13-29-03/data/GSE213740"
OUT = os.path.join(os.path.dirname(__file__), "layer2_out")
os.makedirs(OUT, exist_ok=True)

sc.settings.verbosity = 1
sc.settings.figure_figsize = (7, 6)

# ---- 1) 读 9 个 10x 样本 ----
samples = [
    ("GSM6593315_AD_replicate_1",   "AD", 1),
    ("GSM6593316_AD_replicate_2",   "AD", 2),
    ("GSM6593317_AD_replicate_3",   "AD", 3),
    ("GSM6593318_AD_replicate_4",   "AD", 4),
    ("GSM6593319_AD_replicate_5",   "AD", 5),
    ("GSM6593320_AD_replicate_6",   "AD", 6),
    ("GSM6593321_Normal_replicate_1","Normal", 1),
    ("GSM6593322_Normal_replicate_2","Normal", 2),
    ("GSM6593323_Normal_replicate_3","Normal", 3),
]

def read_sample(prefix):
    d = INPUT_DIR
    feat = pd.read_csv(gzip.open(f"{d}/{prefix}_features.tsv.gz","rt"), sep="\t", header=None,
                       names=["gene_id","gene_symbol","feature_type"])
    bc = pd.read_csv(gzip.open(f"{d}/{prefix}_barcodes.tsv.gz","rt"), sep="\t", header=None)[0]
    mat = mmread(gzip.open(f"{d}/{prefix}_matrix.mtx.gz","rt")).T.tocsr()
    ad = sc.AnnData(mat, obs=pd.DataFrame(index=bc.values), var=feat[["gene_id","gene_symbol"]])
    ad.var.index = feat["gene_symbol"].values  # 用 symbol 作 var index (去重保留首次)
    # 去重 symbol
    ad = ad[:, ~ad.var.index.duplicated()].copy()
    return ad

adatas = []
for prefix, cond, rep in samples:
    ad = read_sample(prefix)
    ad.obs["sample"] = prefix
    ad.obs["condition"] = cond
    ad.obs["replicate"] = rep
    adatas.append(ad)
    print(f"  {prefix}: {ad.shape[0]} cells x {ad.shape[1]} genes")

adata = sc.concat(adatas, join="inner", label="sample", index_unique=None)
print("concat shape:", adata.shape)
adata.obs_names_make_unique()
adata.obs["sample"] = adata.obs["sample"].astype("category")
adata.obs["condition"] = adata.obs["condition"].astype("category")

# ---- 2) 质检 + 归一化 ----
sc.pp.calculate_qc_metrics(adata, percent_top=None, log1p=False, inplace=True)
adata = adata[adata.obs["n_genes_by_counts"] > 200].copy()
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)
# 疾病模块打分在全基因表达上算 (避免 HVG 过滤掉部分疾病基因)
disease_genes = ["ENO1","MIF","COL6A3","LRP1","TP53","LOXL1","JAG1","MRC2",
                 "ALOX5","LTBP4","COMP","ACAN","FBN1","ACTA2","MYH11","ELN"]
var_symbols0 = set(adata.var.index)
present_dg = [g for g in disease_genes if g in var_symbols0]
print(f"disease module genes present (full expr): {len(present_dg)}/{len(disease_genes)}")
sc.tl.score_genes(adata, present_dg, score_name="disease_module")
adata.obs["disease_module"] = adata.obs["disease_module"].astype(float)
sc.pp.highly_variable_genes(adata, batch_key="sample", n_top_genes=3000)
adata.raw = adata
# 仅用 HVG 做后续降维
adata = adata[:, adata.var["highly_variable"]].copy()

# ---- 3) 降维 + 聚类 ----
sc.pp.scale(adata, max_value=10)
sc.tl.pca(adata, n_comps=30, svd_solver="irange" if False else "auto")
sc.pp.neighbors(adata, n_neighbors=15, n_pcs=30)
sc.tl.umap(adata, min_dist=0.3)
sc.tl.leiden(adata, resolution=0.6, key_added="leiden", flavor="igraph")

# ---- 4) 细胞类型注释 (canonical 血管标记) ----
markers = {
    "Vascular_SMC": ["ACTA2","TAGLN","MYH11","CNN1","RBP1"],
    "Endothelial":  ["PECAM1","VWF","CLDN5","FLT1","PLVAP"],
    "Fibroblast":   ["COL1A1","COL1A2","PDGFRA","DCN","LUM"],
    "Macrophage":   ["CD68","LYZ","CD163","MARCO","FCN1"],
    "T_cell":       ["CD3D","CD3E","IL7R","TRAC"],
    "B_cell":       ["CD79A","MS4A1","CD19"],
    "NK":           ["NKG7","GNLY","KLRF1"],
    "Pericyte":     ["PDGFRB","CSPG4","RGS5"],
    "Proliferating":["MKI67","TOP2A"],
}
# 每 cluster 平均表达每个 marker set 的 mean, 取最大者
var_symbols = set(adata.var.index)
score_mat = {}
for ct, genes in markers.items():
    present = [g for g in genes if g in var_symbols]
    if not present:
        continue
    # 用 raw log 表达
    expr = adata.raw[:, present].X
    mean_expr = np.asarray(expr.mean(axis=1)).ravel()  # 占位
# 改: 逐 cluster 计算
clusters = sorted(adata.obs["leiden"].unique())
ct_assign = {}
for cl in clusters:
    mask = (adata.obs["leiden"] == cl).values
    sub = adata.raw[mask]
    best_ct, best_val = "Unknown", -1
    for ct, genes in markers.items():
        present = [g for g in genes if g in var_symbols]
        if not present:
            continue
        m = np.asarray(sub[:, present].X.mean(axis=1)).ravel().mean()
        if m > best_val:
            best_ct, best_val = ct, m
    ct_assign[cl] = best_ct
    print(f"  cluster {cl}: {best_ct} (score={best_val:.2f})")
adata.obs["cell_type"] = adata.obs["leiden"].map(ct_assign).astype("category")

# ---- 6) AD vs Normal 各细胞类型模块打分比较 ----
rows = []
groups = adata.obs.groupby("cell_type")
for ct, idx in groups.groups.items():
    sub = adata[idx]
    ad_vals = sub.obs.loc[sub.obs["condition"]=="AD","disease_module"].values
    no_vals = sub.obs.loc[sub.obs["condition"]=="Normal","disease_module"].values
    if len(ad_vals)<3 or len(no_vals)<3:
        continue
    u, p = sstats.mannwhitneyu(ad_vals, no_vals, alternative="two-sided")
    rows.append({
        "cell_type": ct, "n_AD": len(ad_vals), "n_Normal": len(no_vals),
        "mean_AD": ad_vals.mean(), "mean_Normal": no_vals.mean(),
        "delta": ad_vals.mean()-no_vals.mean(),
        "mannwhitney_p": p,
    })
stats_df = pd.DataFrame(rows).sort_values("delta", ascending=False)
stats_df.to_csv(f"{OUT}/celltype_stats.csv", index=False)
print(stats_df.to_string())

# ---- 7) 逐细胞类型差异表达 (AD vs Normal, 全基因) ----
adata.obs["condition"] = adata.obs["condition"].cat.reorder_categories(["Normal","AD"])
de_rows = []
for ct in adata.obs["cell_type"].cat.categories:
    if ct == "Unknown":
        continue
    sub = adata[adata.obs["cell_type"] == ct]
    n_ad = int((sub.obs["condition"] == "AD").sum())
    n_no = int((sub.obs["condition"] == "Normal").sum())
    if n_ad < 10 or n_no < 10:
        print(f"  skip DE {ct}: n_AD={n_ad}, n_Normal={n_no}")
        continue
    sc.tl.rank_genes_groups(sub, groupby="condition", groups=["AD"],
                            reference="Normal", method="wilcoxon",
                            use_raw=True, key_added="de")
    key = sub.uns["de"]
    names = key["names"]["AD"]
    scores = key["scores"]["AD"]
    logfc = key["logfoldchanges"]["AD"]
    pvals = key["pvals"]["AD"]
    for i in range(min(15, len(names))):
        de_rows.append({"cell_type": ct, "gene": names[i],
                        "logfoldchange": logfc[i], "wilcoxon_score": scores[i],
                        "pval": pvals[i]})
de_df = pd.DataFrame(de_rows)
de_df.to_csv(f"{OUT}/de_top.csv", index=False)
print("DE top written:", de_df.shape)

# ---- 8) 图 ----
sc.pl.umap(adata, color="condition", title="GSE213740: ATAAD vs Normal",
           save=None, show=False, palette=["#4C78A8","#E45756"])
plt.savefig(f"{OUT}/umap_condition.png", dpi=150, bbox_inches="tight"); plt.close()

sc.pl.umap(adata, color="disease_module", cmap="RdBu_r",
           title="Disease module score (16 known genes)", vmax=0.4, vmin=-0.4,
           save=None, show=False)
plt.savefig(f"{OUT}/umap_module.png", dpi=150, bbox_inches="tight"); plt.close()

sc.pl.umap(adata, color="cell_type", title="Cell type annotation",
           save=None, show=False, legend_loc="on data" if False else "right margin")
plt.savefig(f"{OUT}/umap_celltype.png", dpi=150, bbox_inches="tight"); plt.close()

# 细胞类型组成 (按 condition)
comp = pd.crosstab(adata.obs["cell_type"], adata.obs["condition"], normalize="columns")*100
# 两个条件各为 100%，必须并列（grouped）而不是堆叠
comp.plot(kind="bar", stacked=False, figsize=(9,5), color=["#E45756","#4C78A8"])
plt.ylabel("% of cells per condition"); plt.title("Cell-type composition: ATAAD vs Normal")
plt.legend(title="condition", labels=["AD","Normal"])
plt.tight_layout(); plt.savefig(f"{OUT}/composition.png", dpi=150, bbox_inches="tight"); plt.close()

# 模块打分按细胞类型分组
order = stats_df.sort_values("delta")["cell_type"]
plt.figure(figsize=(8,5))
data_for_box = [adata.obs.loc[(adata.obs["cell_type"]==ct),"disease_module"].values for ct in order]
plt.boxplot(data_for_box, vert=True)   # 新版 matplotlib 已移除 boxplot 的 labels 参数
plt.xticks(range(1, len(order) + 1), order, rotation=45, ha="right")
plt.axhline(0, color="k", lw=0.8)
plt.ylabel("disease module score"); plt.title("Disease module by cell type (AD+Normal)")
plt.tight_layout(); plt.savefig(f"{OUT}/module_by_celltype.png", dpi=150, bbox_inches="tight"); plt.close()

# 轻量存盘: 去掉 X/raw (图与下游只需 embedding + obs + var), 避免撑爆磁盘
light = adata.copy()
light.X = None
light.raw = None
light.write(f"{OUT}/gse213740_processed.h5ad")
print("DONE -> layer2_out/ (light h5ad + csv + png)")
