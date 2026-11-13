# 01_prepare_data.py
# 从 113,304 细胞健康多动脉主集切出「主动脉专属子集」（原始计数），供 scDRS 使用。
import os
import anndata as ad

SRC = r"D:/迅雷下载/473452ed-3b89-466a-9610-14eb36cbd12c.h5ad"
OUT_DIR = "./data"
OUT = os.path.join(OUT_DIR, "aorta_subset_raw.h5ad")

# 主动脉相关节段（来自 obs["tissue"] 实际取值）
AORTA_LABELS = [
    "ascending aorta",   # 升主动脉 14,731
    "arch of aorta",     # 主动脉弓   16,497
    "descending aorta",  # 降主动脉   16,581
    "bulb of aorta",     # 主动脉球部  7,336
    "abdominal aorta",    # 腹主动脉    2,854
]

os.makedirs(OUT_DIR, exist_ok=True)

print(">> loading", SRC)
a = ad.read_h5ad(SRC)
print("   full shape:", a.shape, "| has .raw:", a.raw is not None)

# 取原始计数矩阵（scDRS 需要 raw count）
raw = a.raw.to_adata()
print("   raw shape:", raw.shape)

# 主动脉细胞 mask（在 raw 的 obs 上）
mask = raw.obs["tissue"].isin(AORTA_LABELS)
sub = raw[mask].copy()
print(">> aorta subset cells:", sub.shape[0])

# 保留对下游有用的注释列
keep = ["author_cell_type", "cell_type", "tissue", "donor_id", "disease"]
keep = [c for c in keep if c in sub.obs.columns]
sub.obs = sub.obs[keep].copy()

sub.write(OUT)
print(">> saved", OUT, "shape", sub.shape)
print(">> cell_type counts:\n", sub.obs["author_cell_type"].value_counts())
