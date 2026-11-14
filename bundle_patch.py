"""Pre-bundle fixes found in the final cross-check.

1) Remove the IRB-exemption sentence (user asked earlier: "IRB豁免暂时不要").
2) Remove the residual GSE222318 cell-level P from Additional file 5.
3) Add exploratory / direction-only caveats to the AF1, AF3 and AF5 descriptions.
4) Annotate the GSE222318 delta plot and rebuild Additional file 3 (22 pages).
"""
import os, shutil
import pandas as pd
from PIL import Image, ImageDraw
from docx import Document

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56"
ST = os.path.join(ROOT, "output", "aortic_dissection_manuscript", "stage3")
KIT = os.path.join(ROOT, "output", "aortic_dissection_manuscript", "submission_kit")
AF = os.path.join(KIT, "additional_files")
L2 = os.path.join(ROOT, "scdrs_pipeline", "layer2_multidataset_out")
FIG = os.path.join(ROOT, "scdrs_pipeline", "revision_out", "figures")

MD = os.path.join(ST, "Genome_Medicine_Full_Manuscript.md")
DOCX = os.path.join(ST, "Genome_Medicine_Full_Manuscript.docx")
DOSSIER = os.path.join(KIT, "Submission_Dossier_Genome_Medicine.md")
AF5 = os.path.join(AF, "Additional_file_5.csv")
AF3 = os.path.join(AF, "Additional_file_3.pdf")

ETH_OLD = ("Because this work is a secondary analysis of publicly available, "
           "de-identified datasets, no new ethics approval was sought; "
           "the study qualifies for exemption from additional ethical review "
           "under the exemption provisions for de-identified public data.")
ETH_NEW = ("Because this work is a secondary analysis of publicly available, "
           "de-identified datasets, no new ethics approval was sought.")

AF1_OLD = ("Additional file 1: Cross-dataset cell-type statistics. File format: .csv. "
           "Complete dataset x cell-type table (42 rows) of diseased and control cell "
           "counts, means, deltas and Mann-Whitney U P values for the 16-gene module score.")
AF1_NEW = AF1_OLD + (" All P values are cell-level and exploratory; GSE222318 values "
                     "are direction-only and are not used for inference.")

AF3_OLD = ("Additional file 3: Supplementary figures. File format: .pdf. 22 one-page "
           "supplementary figures: per-cohort UMAP overlays (cell type, condition, "
           "module score), composition bar plots and the GSE222318 delta plot, "
           "ordered by dataset.")
AF3_NEW = AF3_OLD + (" The GSE222318 delta plot is drawn on its own scale (curated "
                     "49-gene sparse panel) and is interpreted by direction only.")

AF5_OLD = ("Additional file 5: Per-cohort analysis and QC summary. File format: .csv. "
           "Cohort-level cell counts per condition, number of cell types tested, "
           "module-score delta ranges, number of nominal associations and macrophage "
           "statistics derived from the processed objects.")
AF5_NEW = AF5_OLD + (" Cell-level P values are exploratory; the GSE222318 P value is "
                     "not reported and is not used for inference.")

# Same strings live inside the dossier's §4.4 table cells (without the "Additional file N: " prefix).
DOSSIER_MAP = {
    "Complete dataset x cell-type table (42 rows) of diseased and control cell counts, means, deltas and Mann-Whitney U P values for the 16-gene module score.":
        "Complete dataset x cell-type table (42 rows) of diseased and control cell counts, means, deltas and Mann-Whitney U P values for the 16-gene module score. All P values are cell-level and exploratory; GSE222318 values are direction-only and are not used for inference.",
    "22 one-page supplementary figures: per-cohort UMAP overlays (cell type, condition, module score), composition bar plots and the GSE222318 delta plot, ordered by dataset.":
        "22 one-page supplementary figures: per-cohort UMAP overlays (cell type, condition, module score), composition bar plots and the GSE222318 delta plot, ordered by dataset. The GSE222318 delta plot is drawn on its own scale (curated 49-gene sparse panel) and is interpreted by direction only.",
    "Cohort-level cell counts per condition, number of cell types tested, module-score delta ranges, number of nominal associations and macrophage statistics derived from the processed objects.":
        "Cohort-level cell counts per condition, number of cell types tested, module-score delta ranges, number of nominal associations and macrophage statistics derived from the processed objects. Cell-level P values are exploratory; the GSE222318 P value is not reported and is not used for inference.",
}

REPL = [(ETH_OLD, ETH_NEW), (AF1_OLD, AF1_NEW), (AF3_OLD, AF3_NEW), (AF5_OLD, AF5_NEW)]


def patch_text_file(path, mapping, label):
    s = open(path, encoding="utf-8").read()
    hits = []
    for old, new in mapping:
        # Idempotence: when the new text is an extension of the old one and is
        # already present, the patch was applied in an earlier run. Appending
        # again would duplicate the caveat sentence.
        if old in new and new in s and old in s:
            hits.append("already applied")
            continue
        n = s.count(old)
        hits.append(n)
        s = s.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(s)
    print(f"  {label}: replacements per pattern = {hits}")


def set_text(p, text):
    """Replace paragraph text while keeping its style."""
    if not p.runs:
        p.add_run(text)
        return
    p.runs[0].text = text
    for r in p.runs[1:]:
        r.text = ""


def patch_docx():
    d = Document(DOCX)
    n = 0
    for p in d.paragraphs:
        t = p.text
        for old, new in REPL:
            if old in t:
                set_text(p, t.replace(old, new))
                n += 1
                break
    try:
        d.save(DOCX)
    except PermissionError:
        tmp = DOCX + ".tmp.docx"
        d.save(tmp)
        os.replace(tmp, DOCX)
    print(f"  manuscript docx: {n} paragraphs patched")
    return n


def patch_af5():
    df = pd.read_csv(AF5, dtype=str, keep_default_na=False)
    m = df["dataset"] == "GSE222318"
    print(f"  AF5 GSE222318 P before: {df.loc[m, 'macrophage_mannwhitney_p'].tolist()}")
    df.loc[m, "macrophage_mannwhitney_p"] = "not reported"
    df.loc[m, "note"] = (df.loc[m, "note"] + "; cell-level P values are exploratory "
                         "only and not used for inference")
    df.to_csv(AF5, index=False)
    print("  AF5 GSE222318 P after:  not reported")


def rebuild_af3():
    datasets = ["GSE213740", "GSE155468", "GSE224559", "GSE226492",
                "GSE254132", "GSE222318"]
    plots = []
    for ds in datasets:
        plots += [
            (ds, "composition", os.path.join(L2, f"{ds}_composition.png")),
            (ds, "UMAP: cell type", os.path.join(L2, f"umap_{ds}_umap_celltype.png")),
            (ds, "UMAP: condition", os.path.join(L2, f"umap_{ds}_umap_condition.png")),
            (ds, "UMAP: module score", os.path.join(L2, f"umap_{ds}_umap_module.png")),
        ]
    # Annotated replacement for the last page.
    src = os.path.join(L2, "GSE222318_delta.png")
    ann = os.path.join(FIG, "GSE222318_delta_annotated.png")
    im = Image.open(src).convert("RGB")
    canvas = Image.new("RGB", (im.width, im.height + 62), "white")
    canvas.paste(im, (0, 0))
    dr = ImageDraw.Draw(canvas)
    dr.text((12, im.height + 8),
            "GSE222318: curated 49-gene sparse panel; delta magnitudes are NOT comparable",
            fill="black")
    dr.text((12, im.height + 28),
            "to the other cohorts. Direction only; no P value is used for inference.",
            fill="black")
    canvas.save(ann)
    plots += [("GSE222318", "module-score delta", ann)]
    plots = [x for x in plots if os.path.exists(x[2])]

    pages = []
    for i, (ds, kind, path) in enumerate(plots, 1):
        pg = Image.open(path).convert("RGB")
        cv = Image.new("RGB", (pg.width, pg.height + 40), "white")
        cv.paste(pg, (0, 40))
        ImageDraw.Draw(cv).text((12, 12),
                                f"Supplementary Figure S{i} | {ds} | {kind}",
                                fill="black")
        pages.append(cv)
    pages[0].save(AF3, "PDF", resolution=150.0, save_all=True,
                  append_images=pages[1:])
    print(f"  AF3 rebuilt: {len(pages)} pages, {os.path.getsize(AF3)/1024:.0f} KB; "
          f"last page annotated")


print("PATCH 1/4  manuscript .md")
patch_text_file(MD, REPL, "manuscript md")
print("PATCH 2/4  manuscript .docx (applied via the live local editor; skipped here)")
print("PATCH 3/4  dossier .md")
dmap = [(ETH_OLD, ETH_NEW)] + list(DOSSIER_MAP.items())
patch_text_file(DOSSIER, dmap, "dossier md")
print("PATCH 4/4  Additional file 5 + Additional file 3")
patch_af5()
rebuild_af3()
print("DONE")
