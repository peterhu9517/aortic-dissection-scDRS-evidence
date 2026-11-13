"""
Layer 2 (multi-dataset): 主动脉夹层/动脉瘤 scRNA-seq 跨数据集整合对比
- 6 个 GEO 子集统一管线: QC -> normalize -> 16 基因疾病模块打分 -> HVG -> PCA/UMAP/leiden
  -> 血管标记细胞类型注释 -> 各细胞类型 疾病 vs 对照 模块打分比对 (Mann-Whitney)
- 数据集: GSE213740(ATAAD), GSE155468(ATAA), GSE224559(人夹层分层),
          GSE226492(AD+AA+MF+对照), GSE254132(ATAD+正常), GSE222318(STAAD 时间特异)
- GSE222318 用分块稀疏读取 (125k 细胞 / 9GB, 不爆内存)
- 输出: layer2_multidataset_out/ (各数据集 celltype_stats.csv + 图 + 跨数据集 all_celltype_stats.csv + 热力图)
"""
import os, glob, gzip
import numpy as np
import pandas as pd
import scanpy as sc
from scipy.io import mmread
import scipy.sparse as sp
from scipy import stats as sstats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(__file__)
OUT = os.path.join(BASE, "layer2_multidataset_out")
os.makedirs(OUT, exist_ok=True)
sc.settings.verbosity = 1
sc.settings.figdir = OUT

DISEASE_GENES = ["ENO1","MIF","COL6A3","LRP1","TP53","LOXL1","JAG1","MRC2",
                 "ALOX5","LTBP4","COMP","ACAN","FBN1","ACTA2","MYH11","ELN"]
MARKERS = {
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
SUBSAMPLE_CAP = 40000  # 每数据集用于聚类/注释的细胞上限 (模块打分统计也在该子集上)

# ----------------------------------------------------------------------------
# 加载器
# ----------------------------------------------------------------------------
def load_10x(sample_dir, condition, subtype, dataset, prefix=None):
    """10x mtx: 带 GSM 前缀 (GSE213740/224559/226492) 或无前缀 (GSE254132 嵌套)"""
    if prefix:
        bc = f"{sample_dir}/{prefix}_barcodes.tsv.gz"
        ft = f"{sample_dir}/{prefix}_features.tsv.gz"
        mx = f"{sample_dir}/{prefix}_matrix.mtx.gz"
    else:
        bc = sorted(glob.glob(f"{sample_dir}/*barcodes.tsv.gz"))[0]
        ft = sorted(glob.glob(f"{sample_dir}/*features.tsv.gz"))[0]
        mx = sorted(glob.glob(f"{sample_dir}/*matrix.mtx.gz"))[0]
    feat = pd.read_csv(gzip.open(ft,"rt"), sep="\t", header=None,
                       names=["gid","symbol","ftype"])
    barcodes = pd.read_csv(gzip.open(bc,"rt"), sep="\t", header=None)[0]
    mat = mmread(gzip.open(mx,"rt")).T.tocsr()
    ad = sc.AnnData(mat, obs=pd.DataFrame(index=barcodes.values),
                    var=feat[["gid","symbol"]])
    ad.var.index = feat["symbol"].values
    ad = ad[:, ~ad.var.index.duplicated()].copy()
    ad.obs["condition"] = condition
    ad.obs["disease_subtype"] = subtype
    ad.obs["dataset"] = dataset
    return ad

def read_gse155468_txt(path, condition, subtype, dataset):
    """GSE155468: 单 .txt.gz, 基因(行)x细胞(列), 首列基因名, 首行 barcode 表头"""
    df = pd.read_csv(path, sep="\t", index_col=0)
    ad = sc.AnnData(sp.csr_matrix(df.values.T.astype("float32")))
    ad.var_names = df.index.astype(str).values
    ad.obs_names = [str(c) for c in df.columns]
    ad.obs["condition"] = condition
    ad.obs["disease_subtype"] = subtype
    ad.obs["dataset"] = dataset
    return ad

def read_gse222318(counts_path, meta_path):
    """GSE222318: 计数矩阵 基因(行)x细胞(列), 125k cells / 36k genes.
    为避开解析 45 亿个值, 仅读取 16 疾病基因 + 全部血管标记基因 (~50 行).
    对所有行用 split(',',1)[0] 廉价取基因名判断, 仅对命中的关键行完整解析。"""
    print("  [GSE222318] 仅读取关键基因行 (疾病基因 + 血管标记) ...")
    curated = list(dict.fromkeys(list(DISEASE_GENES) +
                                 [g for gs in MARKERS.values() for g in gs]))
    curated_set = set(curated)
    gene_pos = {g: i for i, g in enumerate(curated)}
    meta = pd.read_csv(meta_path, index_col=0)
    meta.index = [str(i) for i in meta.index]
    rows = np.zeros((len(curated), 0), dtype=np.float32)
    cols = []
    n_read = 0
    with gzip.open(counts_path, "rt") as fh:
        header = fh.readline().rstrip("\n").split(",")
        cols = [str(c).strip('"') for c in header[1:]]
        n_cells = len(cols)
        rows = np.zeros((len(curated), n_cells), dtype=np.float32)
        for line in fh:
            gname = line.split(",", 1)[0].strip('"')
            if gname in curated_set:
                parts = line.rstrip("\n").split(",")
                rows[gene_pos[gname]] = np.array([p.strip('"') for p in parts[1:]], dtype=np.float32)
                n_read += 1
    print(f"  [GSE222318] 关键基因命中 {n_read}/{len(curated)}, {n_cells} cells")
    ad = sc.AnnData(sp.csr_matrix(rows.T))      # cells x curated_genes
    ad.var_names = curated
    ad.obs_names = cols
    # 用 barcode 对齐 metadata (Group1=夹层/对照, Group2=急/亚急/慢性)
    m = meta.reindex(cols)
    ad.obs["condition"] = m["Group1"].map(
        {"Aortic dissection": "Disease", "Normal": "Control"}).astype("object")
    ad.obs["disease_subtype"] = m["Group2"].astype("object")
    ad.obs["dataset"] = "GSE222318"
    keep = ad.obs["condition"].notna().values
    ad = ad[keep].copy()
    print(f"  [GSE222318] {ad.shape[0]} cells (有分组标签) | "
          f"Disease={int((ad.obs.condition=='Disease').sum())} "
          f"Control={int((ad.obs.condition=='Control').sum())}")
    return ad

def analyze_gse222318(name, lst):
    """GSE222318 专用分析: 因 metadata 无自带细胞类型, 用标记基因打分标注; 不做全基因聚类 (数据量过大).
    输出与其它数据集同 schema 的 celltype_stats.csv, 便于汇总比对."""
    ad = lst[0]
    print("\n===== GSE222318 (curated-gene / marker-assigned) =====")
    sc.pp.normalize_total(ad, target_sum=1e4)
    sc.pp.log1p(ad)
    present_dg = [g for g in DISEASE_GENES if g in set(ad.var_names)]
    print(f"  disease module genes present: {len(present_dg)}/{len(DISEASE_GENES)}")
    sc.tl.score_genes(ad, present_dg, score_name="disease_module")
    ad.obs["disease_module"] = ad.obs["disease_module"].astype(float)
    # 细胞类型标注: 每细胞取 marker 集合均值最高者
    var_sym = set(ad.var_names)
    ct_scores = {}
    for ct, genes in MARKERS.items():
        present = [g for g in genes if g in var_sym]
        if present:
            ct_scores[ct] = np.asarray(ad[:, present].X.mean(axis=1)).ravel()
    ct_names = list(ct_scores.keys())
    ct_mat = np.vstack([ct_scores[ct] for ct in ct_names]).T
    ad.obs["cell_type"] = np.array(ct_names)[ct_mat.argmax(axis=1)]
    # 各细胞类型: 夹层 vs 对照 模块打分比较
    rows = []
    for ct in ct_names:
        sub = ad[ad.obs.cell_type == ct]
        dis = sub.obs.disease_module[sub.obs.condition == "Disease"].values
        con = sub.obs.disease_module[sub.obs.condition == "Control"].values
        if len(dis) < 3 or len(con) < 3:
            rows.append({"cell_type": ct, "n_Disease": len(dis), "n_Control": len(con),
                         "mean_Disease": np.nan, "mean_Control": np.nan,
                         "delta": np.nan, "mannwhitney_p": np.nan})
            continue
        u, p = sstats.mannwhitneyu(dis, con, alternative="two-sided")
        rows.append({"cell_type": ct, "n_Disease": len(dis), "n_Control": len(con),
                     "mean_Disease": dis.mean(), "mean_Control": con.mean(),
                     "delta": dis.mean() - con.mean(), "mannwhitney_p": p})
    stats_df = pd.DataFrame(rows).sort_values("delta", ascending=False)
    stats_df.insert(0, "dataset", "GSE222318")
    stats_df.to_csv(f"{OUT}/GSE222318_celltype_stats.csv", index=False)
    print(stats_df.to_string())
    # 图: 组成 + delta 条形
    comp = pd.crosstab(ad.obs["cell_type"], ad.obs["condition"],
                       normalize="columns") * 100
    comp.plot(kind="barh", figsize=(8, 5), color=["#4C78A8", "#E45756"])
    plt.xlabel("% of cells per condition"); plt.title("GSE222318: composition")
    plt.legend(title="condition"); plt.tight_layout()
    plt.savefig(f"{OUT}/GSE222318_composition.png", dpi=150, bbox_inches="tight"); plt.close()
    s = stats_df.dropna(subset=["delta"]).sort_values("delta")
    plt.figure(figsize=(8, 5))
    colors = ["#E45756" if v > 0 else "#4C78A8" for v in s["delta"]]
    plt.barh(s["cell_type"], s["delta"], color=colors)
    plt.axvline(0, color="k", lw=0.8)
    plt.xlabel("delta (Disease - Control) disease-module score")
    plt.title("GSE222318: cell-type disease-module delta")
    plt.tight_layout()
    plt.savefig(f"{OUT}/GSE222318_delta.png", dpi=150, bbox_inches="tight"); plt.close()
    # 时间维度 (急/亚急/慢性, 仅夹层细胞)
    dis_sub = ad[ad.obs.condition == "Disease"]
    if dis_sub.obs["disease_subtype"].nunique() > 1:
        piv = dis_sub.obs.groupby(["disease_subtype", "cell_type"])["disease_module"].mean().unstack()
        print("\n  [GSE222318] 夹层细胞内 疾病模块打分 (按时间分期 x 细胞类型):")
        print(piv.round(3).to_string())
    print(f"  -> GSE222318 done")
    return stats_df

def cond_subtype(name, dataset):
    n = name.upper()
    if dataset == "GSE213740":
        return ("Control","Control") if "NORMAL" in n else ("Disease","ATAAD")
    if dataset == "GSE155468":
        return ("Control","Control") if "CON" in n else ("Disease","ATAA")
    if dataset == "GSE224559":
        if "INTIMA" in n: return ("Disease","AD_intima")
        if "ADVENTITIA" in n: return ("Disease","AD_adventitia")
        return ("Disease","AD")
    if dataset == "GSE226492":
        if "CON" in n: return ("Control","Control")
        if "AD" in n: return ("Disease","AD")
        if "AA" in n: return ("Disease","AA")
        if "MF" in n: return ("Disease","MF")
        return ("Disease","other")
    if dataset == "GSE254132":
        return ("Control","Normal_aorta") if ("NA" in n and "ATAD" not in n) else ("Disease","ATAD")
    return ("Disease","")

# ----------------------------------------------------------------------------
# 单数据集分析
# ----------------------------------------------------------------------------
def analyze_dataset(name, adata_list, has_control=True):
    print(f"\n===== {name} =====")
    if not adata_list:
        print("  (无样本, 跳过)"); return None
    adata = sc.concat(adata_list, join="outer", label="sample", index_unique=None)
    adata.obs_names_make_unique()
    print(f"  concat: {adata.shape[0]} cells x {adata.shape[1]} genes, "
          f"samples={adata.obs['sample'].nunique()}")
    # 子集抽样 (控制内存/时间)
    if adata.n_obs > SUBSAMPLE_CAP:
        rng = np.random.default_rng(0)
        idx = rng.choice(adata.obs_names, size=SUBSAMPLE_CAP, replace=False)
        adata = adata[idx].copy()
        print(f"  抽样至 {adata.n_obs} cells")
    # QC + 归一化
    sc.pp.calculate_qc_metrics(adata, percent_top=None, log1p=False, inplace=True)
    adata = adata[adata.obs["n_genes_by_counts"] > 200].copy()
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    # 16 基因疾病模块打分 (全基因表达, 避免 HVG 过滤掉疾病基因)
    var0 = set(adata.var.index)
    present_dg = [g for g in DISEASE_GENES if g in var0]
    print(f"  disease module genes present: {len(present_dg)}/{len(DISEASE_GENES)}")
    if present_dg:
        sc.tl.score_genes(adata, present_dg, score_name="disease_module")
        adata.obs["disease_module"] = adata.obs["disease_module"].astype(float)
    else:
        adata.obs["disease_module"] = 0.0
        print("  WARNING: 0 disease-module genes present -> disease_module set to 0")
    # HVG + PCA + UMAP + leiden
    sc.pp.highly_variable_genes(adata, batch_key="sample", n_top_genes=2000)
    adata.raw = adata
    adata = adata[:, adata.var["highly_variable"]].copy()
    sc.pp.scale(adata, max_value=10)
    sc.tl.pca(adata, n_comps=30, svd_solver="auto")
    sc.pp.neighbors(adata, n_neighbors=15, n_pcs=30)
    sc.tl.umap(adata, min_dist=0.3)
    sc.tl.leiden(adata, resolution=0.6, key_added="leiden", flavor="igraph")
    # 细胞类型注释 (canonical 血管标记, 逐 cluster 取最高分)
    var_sym = set(adata.var.index)
    clusters = sorted(adata.obs["leiden"].unique())
    ct_assign = {}
    for cl in clusters:
        mask = (adata.obs["leiden"] == cl).values
        sub = adata.raw[mask]
        best_ct, best_val = "Unknown", -1
        for ct, genes in MARKERS.items():
            present = [g for g in genes if g in var_sym]
            if not present: continue
            m = float(np.asarray(sub[:, present].X.mean(axis=1)).ravel().mean())
            if m > best_val:
                best_ct, best_val = ct, m
        ct_assign[cl] = best_ct
        print(f"    cluster {cl}: {best_ct} (score={best_val:.2f})")
    adata.obs["cell_type"] = adata.obs["leiden"].map(ct_assign).astype("category")
    # 各细胞类型 疾病 vs 对照 模块打分比较
    rows = []
    for ct, idx in adata.obs.groupby("cell_type").groups.items():
        sub = adata[idx]
        dis = sub.obs.loc[sub.obs["condition"]=="Disease","disease_module"].values
        con = sub.obs.loc[sub.obs["condition"]=="Control","disease_module"].values
        if len(dis) < 3 or len(con) < 3:
            n_dis, n_con = len(dis), len(con)
            rows.append({"cell_type":ct,"n_Disease":n_dis,"n_Control":n_con,
                         "mean_Disease":np.nan if n_dis==0 else dis.mean(),
                         "mean_Control":np.nan if n_con==0 else con.mean(),
                         "delta":np.nan,"mannwhitney_p":np.nan})
            continue
        u, p = sstats.mannwhitneyu(dis, con, alternative="two-sided")
        rows.append({"cell_type":ct,"n_Disease":len(dis),"n_Control":len(con),
                     "mean_Disease":dis.mean(),"mean_Control":con.mean(),
                     "delta":dis.mean()-con.mean(),"mannwhitney_p":p})
    stats_df = pd.DataFrame(rows).sort_values("delta", ascending=False)
    stats_df.insert(0, "dataset", name)
    stats_df.to_csv(f"{OUT}/{name}_celltype_stats.csv", index=False)
    print(stats_df.to_string())
    # 图
    sc.pl.umap(adata, color="condition", title=f"{name}: condition",
               save=f"_{name}_umap_condition.png", show=False)
    sc.pl.umap(adata, color="disease_module", cmap="RdBu_r", vmax=0.4, vmin=-0.4,
               title=f"{name}: disease module", save=f"_{name}_umap_module.png", show=False)
    sc.pl.umap(adata, color="cell_type", title=f"{name}: cell types",
               save=f"_{name}_umap_celltype.png", show=False, legend_loc="right margin")
    # 组成
    comp = pd.crosstab(adata.obs["cell_type"], adata.obs["condition"],
                       normalize="columns")*100
    comp.plot(kind="bar", stacked=False, figsize=(9,5),
              color=["#4C78A8","#E45756"])
    plt.ylabel("% of cells per condition"); plt.title(f"{name}: composition")
    plt.legend(title="condition"); plt.tight_layout()
    plt.savefig(f"{OUT}/{name}_composition.png", dpi=150, bbox_inches="tight"); plt.close()
    # 轻量存盘
    light = adata.copy(); light.X = None; light.raw = None
    light.write(f"{OUT}/{name}_processed.h5ad")
    print(f"  -> {name} done")
    return stats_df

# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------
def run_or_skip(name, loader, analyzer=None):
    """断点续跑: 已生成 stats 则直接读盘跳过 (含加载+聚类); 否则加载并分析"""
    cp = f"{OUT}/{name}_celltype_stats.csv"
    if os.path.exists(cp):
        print(f"\n===== {name} ===== (checkpoint: 读取已存 stats, 跳过)")
        df = pd.read_csv(cp)
        return df
    lst = loader()
    df = (analyzer or analyze_dataset)(name, lst) if analyzer else analyze_dataset(name, lst)
    return df

def main():
    all_stats = []

    # ---- GSE213740 (旧目录, 10x 前缀) ----
    def load_gse213740():
        d = "D:/WorkBuddy/2026-11-05-13-29-03/data/GSE213740"
        lst = []
        if os.path.isdir(d):
            for bc in glob.glob(f"{d}/*barcodes.tsv.gz"):
                prefix = os.path.basename(bc).replace("_barcodes.tsv.gz","")
                c, st = cond_subtype(prefix, "GSE213740")
                a = load_10x(d, c, st, "GSE213740", prefix=prefix)
                a.obs["sample"] = prefix
                lst.append(a)
        return lst
    df = run_or_skip("GSE213740", load_gse213740)
    if df is not None: all_stats.append(df)

    # ---- GSE155468 (根目录 .txt.gz, Con/TAA) ----
    def load_gse155468():
        lst = []
        for f in glob.glob("D:/GSE_AD_subsets/GSM*_Con*.txt.gz") + \
               glob.glob("D:/GSE_AD_subsets/GSM*_TAA*.txt.gz"):
            base = os.path.basename(f).replace(".txt.gz","")
            c, st = cond_subtype(base, "GSE155468")
            a = read_gse155468_txt(f, c, st, "GSE155468")
            a.obs["sample"] = base
            lst.append(a)
        return lst
    df = run_or_skip("GSE155468", load_gse155468)
    if df is not None: all_stats.append(df)

    # ---- GSE224559 (10x, 只取人夹层; 排除 mouse) ----
    def load_gse224559():
        lst = []
        for bc in glob.glob("D:/GSE_AD_subsets/GSE224559/*barcodes.tsv.gz"):
            prefix = os.path.basename(bc).replace("_barcodes.tsv.gz","")
            if "mouse" in prefix.lower(): continue
            c, st = cond_subtype(prefix, "GSE224559")
            a = load_10x("D:/GSE_AD_subsets/GSE224559", c, st, "GSE224559", prefix=prefix)
            a.obs["sample"] = prefix
            lst.append(a)
        return lst
    df = run_or_skip("GSE224559", load_gse224559)
    if df is not None: all_stats.append(df)

    # ---- GSE226492 (10x, Con/AA/AD/MF) ----
    def load_gse226492():
        lst = []
        for bc in glob.glob("D:/GSE_AD_subsets/GSE226492/*barcodes.tsv.gz"):
            prefix = os.path.basename(bc).replace("_barcodes.tsv.gz","")
            c, st = cond_subtype(prefix, "GSE226492")
            a = load_10x("D:/GSE_AD_subsets/GSE226492", c, st, "GSE226492", prefix=prefix)
            a.obs["sample"] = prefix
            lst.append(a)
        return lst
    df = run_or_skip("GSE226492", load_gse226492)
    if df is not None: all_stats.append(df)

    # ---- GSE254132 (嵌套 tar -> 无前缀 10x, ATAD/NA) ----
    def load_gse254132():
        lst = []
        for mx in glob.glob("D:/GSE_AD_subsets/GSE254132/*/*/matrix.mtx.gz"):
            sdir = os.path.dirname(mx)
            outer = os.path.basename(os.path.dirname(sdir))   # GSM8033727_ATAD1
            c, st = cond_subtype(outer, "GSE254132")
            a = load_10x(sdir, c, st, "GSE254132")
            a.obs["sample"] = outer
            lst.append(a)
        return lst
    df = run_or_skip("GSE254132", load_gse254132)
    if df is not None: all_stats.append(df)

    # ---- GSE222318 (csv 对, metadata Group1=夹层/对照) ----
    def load_gse222318():
        a = read_gse222318(
            "D:/迅雷下载/GSE222318_Raw_gene_counts_matrix.csv.gz",
            "D:/迅雷下载/GSE222318_Cell_metadata.csv.gz")
        a.obs["sample"] = "GSE222318"
        return [a]
    df = run_or_skip("GSE222318", load_gse222318, analyzer=analyze_gse222318)
    if df is not None: all_stats.append(df)

    # ---- 汇总跨数据集对比表 ----
    if all_stats:
        big = pd.concat(all_stats, ignore_index=True)
        big.to_csv(f"{OUT}/all_celltype_stats.csv", index=False)
        # 热力图: delta (疾病-对照 模块打分) across datasets x cell types
        piv = big.pivot(index="cell_type", columns="dataset", values="delta")
        plt.figure(figsize=(10, 8))
        im = plt.imshow(piv.values, aspect="auto", cmap="RdBu_r", vmin=-0.4, vmax=0.4)
        plt.colorbar(im, label="delta (Disease - Control) module score")
        plt.yticks(range(len(piv.index)), piv.index, rotation=0)
        plt.xticks(range(len(piv.columns)), piv.columns, rotation=45, ha="right")
        plt.title("Cross-dataset: disease-module delta per cell type")
        plt.tight_layout()
        plt.savefig(f"{OUT}/cross_dataset_delta_heatmap.png", dpi=150, bbox_inches="tight")
        plt.close()
        # Macrophage / wall cell 聚焦总结
        focus = ["Macrophage","Vascular_SMC","Endothelial","Fibroblast","Pericyte"]
        print("\n========== 跨数据集聚焦 (Macrophage / wall cell) ==========")
        print(big[big["cell_type"].isin(focus)][
            ["dataset","cell_type","n_Disease","n_Control","delta","mannwhitney_p"]
        ].to_string(index=False))
        print(f"\nDONE -> {OUT}/")

if __name__ == "__main__":
    main()
