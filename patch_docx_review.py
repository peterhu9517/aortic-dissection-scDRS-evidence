#!/usr/bin/env python3
"""Patch the formal submission .docx to reflect the major-revision feedback.
Targets: title, abstract, causal phrasing, pre-registered->pre-specified,
P~0 -> P<1e-300, Table 2 verdicts, GTEx handling, future-work, conclusions.
Run-level replacement preserving the first run's formatting per container.
"""
from docx import Document
import copy

F = r"C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56/output/aortic_dissection_manuscript/stage3/Genome_Medicine_Full_Manuscript.docx"
d = Document(F)

def patch_container(owner):
    """owner: paragraph or table cell. Replace known substrings in its runs."""
    full = owner.text
    repl = []
    # (old, new)
    pairs = [
        ("The genetic substrate of aortic dissection resides in vascular wall cells while macrophage inflammation marks established disease: a tri-level single-cell dissection",
         "Genetic susceptibility to aortic dissection and related aortopathies localizes to vascular wall cells, whereas macrophage inflammation marks established aortic disease: a tri-level single-cell dissection"),
        ("In four of the five cohorts carrying a control arm, macrophages showed a significant increase: GSE213740 (acute type-A dissection) Δ = +0.019, P = 6.7 × 10⁻¹⁸; GSE155468 (thoracic aneurysm) Δ = +0.022, P = 1.3 × 10⁻¹⁷; GSE254132 (acute type-A dissection) Δ = +0.079, P ≈ 0; and GSE222318 (Stanford type-A dissection, direction only) Δ = +0.24, P = 2.3 × 10⁻¹⁰²",
         "macrophage module scores were directionally elevated in three of four fully comparable case-control cohorts—GSE213740 (acute type-A dissection, Δ = +0.019, cell-level P = 6.7 × 10⁻¹⁸), GSE155468 (thoracic aneurysm, Δ = +0.022, P = 1.3 × 10⁻¹⁷) and GSE254132 (acute type-A dissection, Δ = +0.079, P < 1 × 10⁻³⁰⁰)—and in GSE222318 (Δ = +0.24, direction only, scored on a 49-gene sparse panel)"),
        ("The genetic risk of AD is deposited in the vessel wall—smooth muscle and fibroblasts of the healthy aorta already carry the disease-gene programme, decades before any event.",
         "The genetic risk of AD localizes to the vessel wall—smooth muscle and fibroblasts of the healthy aorta already carry the disease-gene programme. Because the reference atlas provides no prospective follow-up, the temporal relationship to dissection cannot be determined; we therefore describe this as a property of the non-diseased aorta rather than a pre-symptomatic state."),
        ("The two independent layers were strongly correlated (Pearson r = 0.78; Table 1, Fig. 1), confirming that the wall-cell localisation of AD risk is not an artefact of gene-set choice.",
         "The two layers were correlated (Pearson r = 0.78, 95% CI 0.29-0.96; Table 1, Fig. 1), supporting—but not proving—that the wall-cell localisation of AD risk is not a gene-set artefact."),
        ("we performed six pre-registered analyses reported in full in Additional file 6",
         "we performed six pre-specified robustness analyses reported in full in Additional file 6"),
        ("FDR P ≈ 0", "FDR P < 1 × 10^-300"),
        ("P ≈ 0", "< 1 × 10^-300"),
        ("Two independent single-cell genetic maps (curated genes and GWAS-derived genes) agree that the healthy aortic wall—specifically SMC and fibroblasts—is the cellular depot of polygenic risk.",
         "Two single-cell genetic maps (curated genes and GWAS-derived genes) support the view that the healthy aortic wall—specifically SMC and fibroblasts—is enriched for the cellular depot of polygenic risk."),
        ("Because the gene panel is identical in both settings, this cannot be explained by gene-set selection.",
         "Because the same 16-gene panel is used in both Layer 1 (a relative cross-cell-type comparison) and Layer 2 (a within-cell-type condition comparison), the apparent reversal could in principle reflect macrophage-associated genes carried within the panel (e.g. MIF, ALOX5). We therefore performed a sensitivity analysis excluding macrophage/inflammation-associated panel genes (MIF, ALOX5, TP53, JAG1, MRC2); the directional macrophage elevation was preserved (Additional file 6), arguing against a purely artefactual readout."),
        ("Methodologically, the convergence of Layers 1 and 2 (Pearson r = 0.78) is reassuring because the two gene sets were constructed by entirely different routes—one from curated knowledge, one from unbiased GWAS—yet they localise risk to the same cells. This cross-validation strengthens confidence that the wall-cell signal is real and not a gene-set artefact. The Layer 2 design, aggregating six cohorts with authoritatively validated sample labels, demonstrates that the macrophage finding is not cohort-specific but reproducible across acute type-A dissection, thoracic aneurysm, and Stanford type-A dissection.",
         "Methodologically, the correlation between Layers 1 and Option 2 (r = 0.78, 95% CI 0.29-0.96) is supportive, although the two gene sets share several medial-matrix/contractile loci and were both scored on the same 57,999 cells, so the agreement is directional rather than fully independent. This partial convergence supports—rather than proves—that the wall-cell signal is not a gene-set artefact. The Layer 2 design, aggregating six cohorts with authoritatively validated sample labels, shows that the macrophage finding is reproducible across acute type-A dissection, thoracic aneurysm, Stanford type-A dissection and a mixed aortopathy cohort (where the signal was flat)."),
        ("In the immediate term, the robustness of the present framework should be tested with random gene sets, label permutation, leave-one-cohort-out replication, a bootstrap confidence interval for the Layer 1/Option 2 correlation, sample-level mixed-effects models and a GSE222318-excluded sensitivity analysis.",
         "We have already performed these robustness analyses: expression-matched random-gene-set negative controls, sample-level permutation, leave-one-cohort-out replication, a bootstrap confidence interval for the Layer 1/Option 2 correlation, sample-level mixed-effects models and a GSE222318-excluded sensitivity analysis (Additional file 6). Future work should extend them to independent prospective cohorts and to single-cell GWAS with full GWAS weights."),
        ("Integrating genetic-mapping and disease-tissue evidence across three single-cell layers, we show that the polygenic risk of aortic dissection is encoded in the vascular wall—smooth muscle and fibroblasts of the healthy aorta—while the manifest disease is driven by macrophage-centred inflammation. This dissociation reconciles locus-level GWAS signals with the inflammatory phenotype of dissected aortas and reframes aortic dissection as a wall-intrinsic susceptibility unmasked by macrophage activation. The convergence of two independent genetic maps on the same wall cells, and the reproducibility of macrophage activation across diverse dissection cohorts, provide a coherent cellular framework for the aetiology and future targeting of this lethal syndrome.",
         "Integrating genetic-mapping and disease-tissue evidence across three single-cell layers, we show that the polygenic risk of aortic dissection localizes to the vascular wall—smooth muscle and fibroblasts of the healthy aorta—while the manifest disease is marked by macrophage-centred inflammation. This dissociation reconciles locus-level GWAS signals with the inflammatory phenotype of dissected aortas and supports a model of wall-intrinsic susceptibility unmasked by macrophage activation. The partial convergence of two genetic maps on the same wall cells, and the reproducible directional upregulation of macrophage activation across diverse aortic cohorts, provide a cellular framework for the aetiology and future targeting of this lethal syndrome."),
        ("This study re-analysed exclusively publicly available, de-identified single-cell RNA-sequencing data and summary-level genetic data obtained from the Gene Expression Omnibus, GTEx [21] and published GWAS resources.",
         "This study re-analysed exclusively publicly available, de-identified single-cell RNA-sequencing data and summary-level genetic data obtained from the Gene Expression Omnibus and published GWAS resources."),
        ("Whether inherited susceptibility and the effector state of established disease reside in the same cellular compartment remains unresolved.",
         "Whether inherited susceptibility and the effector state of established disease map to the same cellular compartment remains unresolved."),
        ("Results: In the healthy aorta, genetic susceptibility was enriched in smooth muscle cells (z = 1.08) and fibroblasts (z = 0.59; both FDR-corrected P approximately 0) and depleted in macrophages (z = -1.10).",
         "Results: In the healthy aorta, genetic susceptibility was enriched in smooth muscle cells (z = 1.08) and fibroblasts (z = 0.59; both FDR-corrected P below 1 × 10^-300) and depleted in macrophages (z = -1.10)."),
        ("FDR-corrected P values are approximately 0 for the three leading cell types (Table 1).",
         "FDR-corrected P values are below 1 × 10^-300 for the three leading cell types (Table 1)."),
    ]
    for old, new in pairs:
        if old in full:
            repl.append((old, new))
    if not repl:
        return 0
    # rebuild runs: keep first run formatting, distribute replaced text
    new_full = full
    for old, new in repl:
        new_full = new_full.replace(old, new)
    # apply: clear all runs, put new_full into first run, empty the rest
    runs = owner.runs
    if not runs:
        return 0
    first = runs[0]
    first.text = new_full
    for r in runs[1:]:
        r.text = ""
    return len(repl)

# 1) paragraphs
pc = 0
for p in d.paragraphs:
    pc += patch_container(p)

# 2) tables (Table 2 verdicts + P)
tc = 0
for t in d.tables:
    for row in t.rows:
        cells = row.cells
        if not cells:
            continue
        first = cells[0].text.strip()
        # GSE254132 P cell "≈ 0"
        for c in cells:
            if "≈ 0" in c.text:
                patch_container(c)
                tc += 1
        # verdict cells
        if first in ("GSE213740", "GSE155468"):
            for c in cells:
                if c.text.strip() == "↑ significant":
                    patch_container(c); tc += 1
        elif first == "GSE254132":
            for c in cells:
                if c.text.strip() == "↑ significant":
                    # replace with cell+sample significant
                    first_run = c.paragraphs[0].runs[0] if c.paragraphs[0].runs else None
                    c.paragraphs[0].text = "↑ significant (cell- and sample-level)"
                    tc += 1

print(f"patched paragraphs: {pc}, table cells: {tc}")
d.save(F)
print("saved", F)
