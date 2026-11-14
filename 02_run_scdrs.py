# 02_run_scdrs.py
# scDRS 主流程驱动：compute-gs -> compute-score -> perform-downstream
# 注意：本 sumstats 经已知 SNP 判定为 **hg19**，故使用 gene_info_hg19.gz
import os
import glob
import subprocess

DATA = "./data"
H5AD = os.path.join(DATA, "aorta_subset_raw.h5ad")
SUMSTATS = r"C:/Users/胡行健/Downloads/OMIX007191-02.sumstats"
GENE_INFO = os.path.join(DATA, "gene_info_hg19.gz")   # <-- 已判定为 hg19
OUT_GS = os.path.join(DATA, "gs_out")
OUT_SCORE = os.path.join(DATA, "scdrs_score")
OUT_DOWN = os.path.join(DATA, "downstream")

for p in (OUT_GS, OUT_SCORE, OUT_DOWN):
    os.makedirs(p, exist_ok=True)

assert os.path.exists(H5AD), f"缺少 {H5AD}，请先跑 01_prepare_data.py"
assert os.path.exists(GENE_INFO), f"缺少 {GENE_INFO}，请跑 00_setup_env.sh"

# 1) 计算基因级分数（MAGMA）
cmd_gs = [
    "scdrs", "compute-gs",
    "--out-dir", OUT_GS,
    "--h5ad-file", H5AD,
    "--gs-path", SUMSTATS,
    "--gs-format", "sumstats",
    "--gene-info", GENE_INFO,
    "--n-max-bulk", "2000",
    "--flag-filter-data", "True",
    "--flag-raw-count", "True",
]

# 2) 计算逐细胞分数
cmd_score = [
    "scdrs", "compute-score",
    "--h5ad-file", H5AD,
    "--gs-dir", OUT_GS,
    "--h5ad-scdrs-dir", OUT_SCORE,
    "--out-dir", OUT_SCORE,
    "--n-cell", "1000",
    "--flag-raw-count", "True",
]

# 3) 下游分析（细胞类型关联 + UMAP/散点/小提琴）
#    scored h5ad 由 compute-score 产出，文件名含 .scdrs. ，用 glob 定位
cands = glob.glob(os.path.join(OUT_SCORE, "*.h5ad"))
scored = [c for c in cands if "scdrs" in os.path.basename(c)]
if not scored:
    raise SystemExit(f"未找到 scored h5ad，请检查 compute-score 是否成功：{cands}")
scored = scored[0]
print(">> scored h5ad:", scored)

cmd_down = [
    "scdrs", "perform-downstream",
    "--h5ad-file", scored,
    "--out-dir", OUT_DOWN,
    "--task", "all",
]

for name, cmd in [("compute-gs", cmd_gs), ("compute-score", cmd_score), ("perform-downstream", cmd_down)]:
    print(f"\n========== {name} ==========")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

print("\n>> 完成。下游结果在", OUT_DOWN)
