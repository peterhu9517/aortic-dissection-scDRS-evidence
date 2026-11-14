"""探测 scdrs.score_cell 的返回结构与下游接口（小样本）。"""
import os, sys, scanpy as sc
import scdrs
from scdrs.method import score_cell

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56/scdrs_pipeline"
SUB  = os.path.join(ROOT, "aao_subset.h5ad")
GENELIST = os.path.join(ROOT, "aad_geneset.txt")

sub = sc.read_h5ad(SUB)
n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
if n:
    sub = sub[:n].copy()
genes = [l.strip() for l in open(GENELIST) if l.strip()]
print("n_cells=%d  n_genes=%d" % (sub.shape[0], len(genes)))

print("running scdrs.pp.preprocess ...")
scdrs.pp.preprocess(sub)
print("preprocess done; SCDRS_PARAM keys:", list(sub.uns['SCDRS_PARAM'].keys())[:8])

df = score_cell(sub, genes, n_ctrl=500, verbose=True)
print("RETURN TYPE:", type(df))
print("df shape:", df.shape)
print("df columns:", list(df.columns))
import pandas as pd
pd.set_option('display.width', 220); pd.set_option('display.max_columns', 30)
print(df.head(3).to_string())
