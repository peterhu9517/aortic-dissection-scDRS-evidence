"""从 celltype_stats.csv 重画 Layer 2 细胞组成图（并列柱状，不再堆叠）。
原图 comp.plot(stacked=True) 把两个条件各 100% 叠在一起，纵轴虚高到 200%，属画法错误。
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56/scdrs_pipeline/layer2_out"
df = pd.read_csv(f"{OUT}/celltype_stats.csv").set_index("cell_type")

n_ad = df["n_AD"]
n_no = df["n_Normal"]
pct = pd.DataFrame({
    "AD": n_ad / n_ad.sum() * 100,
    "Normal": n_no / n_no.sum() * 100,
})

fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(pct))
w = 0.38
ax.bar(x - w/2, pct["Normal"], w, label="Normal", color="#4C78A8")
ax.bar(x + w/2, pct["AD"], w, label="AD (ATAAD)", color="#E45756")
ax.set_xticks(x)
ax.set_xticklabels(pct.index, rotation=45, ha="right")
ax.set_ylabel("% of cells within condition")
ax.set_title("Cell-type composition: ATAAD vs Normal (GSE213740)")
ax.legend(title="condition")
for i, (a, b) in enumerate(zip(pct["Normal"], pct["AD"])):
    ax.text(i - w/2, a + 0.6, f"{a:.1f}", ha="center", fontsize=8)
    ax.text(i + w/2, b + 0.6, f"{b:.1f}", ha="center", fontsize=8)
plt.tight_layout()
plt.savefig(f"{OUT}/composition.png", dpi=150)
plt.close()
print(pct.round(1).to_string())
print("saved ->", f"{OUT}/composition.png")
