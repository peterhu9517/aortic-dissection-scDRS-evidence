"""从 UCSC hg19 ensGene.txt.gz 生成 scDRS 所需的 gene_info_hg19.gz。

背景：scDRS 官方 storage 桶已删（原 gene_info_hg19.gz 是 133B 的 NoSuchBucket 死桩），
但 hgdownload.soe.ucsc.edu/goldenPath/hg19/database/ensGene.txt.gz 可达。
ensGene 的 name2 列就是 ENSG（无版本号），与 CELLxGENE 图谱 var_names 一致。

输出列：gene \t chrom(1..22/X/Y) \t start \t end  (hg19 / GRCh37 坐标)
"""
import gzip
import os

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56/scdrs_pipeline"
SRC = os.path.join(ROOT, "data", "ensGene.txt.gz")
DST = os.path.join(ROOT, "data", "gene_info_hg19.gz")

CANON = {f"chr{i}": str(i) for i in range(1, 23)}
CANON.update({"chrX": "X", "chrY": "Y", "chrM": "M"})

# gene -> (chrom, start, end)，同一基因多转录本取外显子整体最小/最大
best = {}
with gzip.open(SRC, "rt") as f:
    for line in f:
        p = line.rstrip("\n").split("\t")
        if len(p) < 13:
            continue
        chrom_raw, tx_start, tx_end, gene = p[2], p[4], p[5], p[12]
        if chrom_raw not in CANON:      # 过滤 chr1_gl000... 等 alt contig
            continue
        if not gene.startswith("ENSG"):
            continue
        chrom = CANON[chrom_raw]
        s, e = int(tx_start), int(tx_end)
        if gene in best:
            pc, ps, pe = best[gene]
            if pc != chrom:
                # 同一 ENSG 出现在多条染色体（PAR / alt）：只保留常染色体那条，
                # 且必须整条替换坐标，不能跨染色体取 min/max
                old_bad = pc in ("X", "Y", "M")
                new_bad = chrom in ("X", "Y", "M")
                if new_bad and not old_bad:
                    continue
                if old_bad and not new_bad:
                    best[gene] = (chrom, s, e)
                    continue
                continue
            s, e = min(s, ps), max(e, pe)
        best[gene] = (chrom, s, e)

with gzip.open(DST, "wt") as out:
    out.write("gene\tchrom\tstart\tend\n")
    for g, (c, s, e) in sorted(best.items()):
        out.write(f"{g}\t{c}\t{s}\t{e}\n")

print(f"wrote {DST}: {len(best)} ENSG genes (hg19)")
print("size:", os.path.getsize(DST), "bytes")
with gzip.open(DST, "rt") as f:
    for _ in range(4):
        print(" ", f.readline().rstrip())
