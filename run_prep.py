"""Layer 1 (Plan E): 预处理健康多动脉图谱，切出主动脉子集并归一化；
   将"已知主动脉疾病相关基因"由 symbol 映射为 h5ad 的 ENSG，
   写出 gene_list 供 scdrs.score_cell 使用。"""
import os, scanpy as sc

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56/scdrs_pipeline"
H5  = "D:/迅雷下载/473452ed-3b89-466a-9610-14eb36cbd12c.h5ad"
SUB = os.path.join(ROOT, "aao_subset.h5ad")
GENELIST = os.path.join(ROOT, "aad_geneset.txt")

# 1) 切主动脉子集（多动脉健康图谱含 9 个动脉段，取主动脉相关 5 段）
aorta_tissues = ['ascending aorta', 'arch of aorta', 'descending aorta',
                 'bulb of aorta', 'abdominal aorta']

if not os.path.exists(SUB):
    print("Reading full 113k h5ad ...")
    ad = sc.read_h5ad(H5)
    print("full shape:", ad.shape)
    sub = ad[ad.obs['tissue'].isin(aorta_tissues)].copy()
    print("aorta subset raw shape:", sub.shape)
    sc.pp.normalize_total(sub, target_sum=1e4)
    sc.pp.log1p(sub)
    sub.write_h5ad(SUB)
else:
    sub = sc.read_h5ad(SUB)

print("subset shape:", sub.shape)
print("cell types:", sub.obs['author_cell_type'].value_counts().to_dict())
print("has umap obsm:", 'X_umap' in sub.obsm)

# 2) 已知主动脉疾病相关基因 (symbol) -> ENSG
# 来源：ENO1-MIF 代谢免疫轴(Adv Sci 2026)；Horjus 2026 cTWAS 因果基因节选；
#       ALOX5(铁死亡)；LTBP4/COMP/ACAN(ECM 血浆投影)；FBN1/ACTA2/MYH11/ELN(壁结构)
known = ['ENO1','MIF','COL6A3','LRP1','TP53','LOXL1','JAG1','MRC2',
         'ALOX5','LTBP4','COMP','ACAN','FBN1','ACTA2','MYH11','ELN']
sym2ensg = {}
for s, e in zip(sub.var['feature_name'].astype(str), sub.var_names.astype(str)):
    if s not in sym2ensg:          # 取每个 symbol 首个 ENSG
        sym2ensg[s] = e
mapped = [sym2ensg[s] for s in known if s in sym2ensg]
missing = [s for s in known if s not in sym2ensg]
print("mapped %d/%d genes; missing: %s" % (len(mapped), len(known), missing))
print("ENSG list:", mapped)

with open(GENELIST, 'w') as f:
    f.write("\n".join(mapped))
print("wrote", GENELIST)
