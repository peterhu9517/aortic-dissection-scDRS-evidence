"""第二条（GWAS -> 单细胞映射）：MAGMA-free AAD GWAS -> 加权基因集 -> scDRS -> 细胞类型富集。

为什么不需要 MAGMA / 1000G LD：scDRS 的 score_cell 只需要「基因列表 + 权重」，
MAGMA 只在 sumstats -> 基因分数那一步用（需要 LD 面板做基因级检验）。
本脚本用本地 AAD sumstats + UCSC hg19 ensGene 坐标，自己完成 SNP -> 基因窗口映射，
得到 MAGMA-free 的近似基因分数，直接喂给 scDRS。

方法学（务必如实说明）：
  * 每个基因取 gene body +/- 50 kb 窗口内的所有 SNP；
  * 基因分数 = max(-log10 P) - log10(n_SNP_in_window)
    （Bonferroni 式校正，消除「基因越长 / SNP 越多 -> 峰值越容易大」的偏倚）；
  * 取分数最高的 TOP_N 基因构成疾病基因集，权重 = 1 + 2 * 组内百分位（1~3）；
  * scDRS 打分时用 500 组表达量匹配的 control gene set 做标准化（scDRS 自带）。
  * 局限：未做 LD 校正、未做 MAGMA 的多元回归，属「方向性、探索性」结果；
    论文级无偏映射仍应在本机用 00~03 标准脚本跑 MAGMA + 1000G EUR。

输入（全部本地）：
  OMIX007191-02.sumstats        AAD GWAS, hg19, 9,797,427 SNP
  data/gene_info_hg19.gz        由 make_gene_info.py 从 UCSC ensGene 生成
  D:/aao_subset_backup.h5ad     健康主动脉 57,999 细胞（Layer 1 的子集）
输出 option2_out/:
  gene_scores.csv               全部基因的 GWAS 派生分数（可复核）
  AAD.gs                        scDRS 格式加权基因集
  full_score.csv                57,999 细胞逐细胞打分
  celltype_summary.csv          细胞类型富集（Welch t + FDR）
  celltype_bar.png / umap_z.png

用法：
  python3 build_aad_gs.py --validate        # 只校验输入
  python3 build_aad_gs.py --debug 2000      # 2k 细胞快速验证全流程
  python3 build_aad_gs.py                  # 全量
"""
import os
import sys
import gzip
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import scanpy as sc

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56/scdrs_pipeline"
SUMMARY = "C:/Users/胡行健/Downloads/OMIX007191-02.sumstats"
GENEINFO = os.path.join(ROOT, "data", "gene_info_hg19.gz")
H5AD = "D:/aao_subset_backup.h5ad"
OUT = os.path.join(ROOT, "option2_out")
os.makedirs(OUT, exist_ok=True)
WINDOW = 50000
TRAIT = "AAD"


def load_gene_info(path):
    genes = {}
    with gzip.open(path, "rt") as f:
        for i, line in enumerate(f):
            if i == 0 and line.lower().startswith("gene"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 4:
                continue
            genes[p[0]] = (p[1], int(p[2]), int(p[3]))
    if len(genes) < 1000:
        raise RuntimeError("gene_info 为空/损坏：%s（若是 133B 的 NoSuchBucket 死桩，先跑 make_gene_info.py）" % path)
    return genes


def map_snps_to_genes(summary, genes, atlas_genes, window=WINDOW):
    """返回 DataFrame[gene, chrom, adj_score, max_neglog10p, n_snp]。"""
    df = pd.read_csv(summary, sep="\t", usecols=["CHR", "BP", "P"])
    df["nlp"] = -np.log10(df["P"].clip(lower=1e-300))
    df["CHR"] = df["CHR"].astype(str)

    # 只保留图谱里存在的基因（scDRS 打分必须用图谱 var_names）
    by_chr = {}
    for g, (c, s, e) in genes.items():
        if g in atlas_genes:
            by_chr.setdefault(c, []).append((s - window, e + window, g))

    rows = []
    for chrom, glist in by_chr.items():
        sub = df[df["CHR"] == chrom]
        if sub.empty:
            continue
        sub = sub.sort_values("BP")
        bp = sub["BP"].to_numpy()
        nlp = sub["nlp"].to_numpy()
        starts = np.array([x[0] for x in glist])
        ends = np.array([x[1] for x in glist])
        lo = np.searchsorted(bp, starts, side="left")
        hi = np.searchsorted(bp, ends, side="right")
        for (s, e, g), a, b in zip(glist, lo, hi):
            n = int(b - a)
            if n < 1:
                continue
            mx = float(nlp[a:b].max())
            # Bonferroni 式校正：扣掉窗口内 SNP 数带来的多重检验膨胀
            adj = mx - np.log10(n)
            rows.append((g, chrom, adj, mx, n))
        print(f"  chr{chrom}: {len(glist)} genes, {len(sub):,} SNPs")

    res = pd.DataFrame(rows, columns=["gene", "chrom", "adj_score", "max_neglog10p", "n_snp"])
    res = res.sort_values("adj_score", ascending=False).reset_index(drop=True)
    del df
    return res


def select_and_write_gs(res, top_n, out_gs):
    sel = res.head(top_n).copy()
    # 权重 1~3，随 GWAS 信号单调；全部为正，符合 scDRS gene_weight 约定
    pct = (len(sel) - 1 - np.arange(len(sel))) / max(len(sel) - 1, 1)
    sel["weight"] = 1 + 2 * pct
    sel.to_csv(os.path.join(OUT, "selected_genes.csv"), index=False)
    parts = ["%s:%.4f" % (g, w) for g, w in zip(sel["gene"], sel["weight"])]
    with open(out_gs, "w") as f:
        f.write("TRAIT\tGENESET\n")
        f.write("%s\t%s\n" % (TRAIT, ",".join(parts)))
    print("wrote %s : %d genes, weight range %.2f-%.2f" %
          (out_gs, len(sel), sel["weight"].min(), sel["weight"].max()))
    print(sel.head(12)[["gene", "chrom", "adj_score", "max_neglog10p", "n_snp", "weight"]].to_string(index=False))
    return sel


def score_cells(sel, h5ad, debug_n, n_ctrl):
    import scdrs
    from scdrs.method import score_cell

    sub = sc.read_h5ad(h5ad)
    if sub.raw is not None:
        sub.raw = None          # 关键：留着 .raw 会让 adata[:, genes] 触发 732MB 额外分配并崩
    if debug_n:
        sub = sub[:debug_n].copy()
    print("cells=%d  genes=%d  disease_genes=%d  n_ctrl=%d" %
          (sub.n_obs, sub.n_vars, len(sel), n_ctrl))

    scdrs.pp.preprocess(sub)
    if sub.raw is not None:
        sub.raw = None
    df = score_cell(sub, sel["gene"].tolist(),
                    gene_weight=sel["weight"].to_numpy(),
                    n_ctrl=n_ctrl, verbose=True)
    print("score_cell done, columns:", list(df.columns))
    return sub, df


def enrichment(sub, df, out_csv, bar_png, umap_png):
    from scipy import stats as sstats
    ct = sub.obs["author_cell_type"].values
    z = df["zscore"].values
    rows = []
    for c in pd.unique(ct):
        a, b = z[ct == c], z[ct != c]
        t, p = sstats.ttest_ind(a, b, equal_var=False)
        rows.append((c, len(a), float(a.mean()), float(a.std(ddof=1)), float(t), float(p)))
    g = pd.DataFrame(rows, columns=["cell_type", "n", "mean_z", "std_z", "t", "p"])
    # 极小 debug 子集里某类可能只有 1 个细胞 -> Welch t 为 NaN，按 p=1 处理
    g["p"] = g["p"].fillna(1.0).clip(0.0, 1.0)
    g["fdr"] = sstats.false_discovery_control(g["p"].values)
    g = g.sort_values("mean_z", ascending=False).reset_index(drop=True)
    g.to_csv(out_csv, index=False)
    print("\n=== Option 2: AAD GWAS-derived gene set, per-cell-type enrichment ===\n",
          g.to_string(index=False))

    plt.figure(figsize=(8, 5))
    err = g["std_z"] / np.sqrt(g["n"])
    plt.bar(range(len(g)), g["mean_z"], yerr=err, capsize=4, color="#3b6ea5")
    plt.xticks(range(len(g)), g["cell_type"], rotation=45, ha="right")
    plt.ylabel("mean scDRS z-score (AAD GWAS-derived weighted gene set)")
    plt.title("Option 2 (MAGMA-free): AAD GWAS enrichment across aortic cell types")
    plt.tight_layout(); plt.savefig(bar_png, dpi=140); plt.close()

    um = sub.obsm["X_umap"]
    plt.figure(figsize=(7, 6))
    sc1 = plt.scatter(um[:, 0], um[:, 1], c=z, cmap="RdBu_r", s=2, vmin=-3, vmax=3)
    plt.colorbar(sc1, label="scDRS z-score")
    plt.title("UMAP overlay: AAD GWAS-derived score")
    plt.axis("off"); plt.tight_layout(); plt.savefig(umap_png, dpi=140); plt.close()
    print("saved", bar_png, umap_png)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--debug", type=int, default=0, help="只用前 N 个细胞快速验证")
    ap.add_argument("--top", type=int, default=1000, help="疾病基因集大小")
    ap.add_argument("--n_ctrl", type=int, default=500)
    ap.add_argument("--reuse", action="store_true", help="复用已算好的 gene_scores.csv，跳过 SNP 映射")
    args = ap.parse_args()

    gi = load_gene_info(GENEINFO)
    print("[validate] gene_info OK: %d ENSG genes (hg19)" % len(gi))
    ad = sc.read_h5ad(H5AD, backed="r")
    atlas_genes = set(ad.var_names)
    n_obs, n_vars = ad.n_obs, ad.n_vars
    ad.file.close()
    print("[validate] atlas: %d cells x %d genes" % (n_obs, n_vars))
    s = pd.read_csv(SUMMARY, sep="\t", usecols=["CHR", "BP", "P"])
    print("[validate] sumstats: %d SNPs, CHR %d-%d, P<5e-8=%d" %
          (len(s), s.CHR.min(), s.CHR.max(), int((s.P < 5e-8).sum())))
    del s
    if args.validate:
        print("[validate] 输入齐备，可运行：python3 build_aad_gs.py")
        sys.exit(0)

    score_csv = os.path.join(OUT, "gene_scores.csv")
    if args.reuse and os.path.exists(score_csv):
        res = pd.read_csv(score_csv)
        print("=== reused gene_scores.csv (%d genes) ===" % len(res))
    else:
        print("=== SNP -> gene window mapping (+/- %d kb) ===" % (WINDOW // 1000))
        res = map_snps_to_genes(SUMMARY, gi, atlas_genes)
        res.to_csv(score_csv, index=False)
    print("scored genes: %d (adj_score range %.2f - %.2f)" %
          (len(res), res.adj_score.min(), res.adj_score.max()))
    print("\ntop 15 GWAS-derived genes:\n", res.head(15).to_string(index=False))

    sel = select_and_write_gs(res, args.top, os.path.join(OUT, TRAIT + ".gs"))
    sub, df = score_cells(sel, H5AD, args.debug, args.n_ctrl)
    df.to_csv(os.path.join(OUT, "full_score.csv"), index=False)
    enrichment(sub, df,
               os.path.join(OUT, "celltype_summary.csv"),
               os.path.join(OUT, "celltype_bar.png"),
               os.path.join(OUT, "umap_z.png"))
    print("ALL DONE ->", OUT)
