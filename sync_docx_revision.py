# -*- coding: utf-8 -*-
"""Sync the revised Genome Medicine .md into the submission .docx.

Keeps the existing docx layout / embedded figures / references intact:
  - replaces the text of the paragraphs that were rewritten,
  - inserts the two new result paragraphs,
  - inserts Table 2 (cohort composition) and Table 4 (sample-level primary),
  - renumbers the existing macrophage table to Table 3 and updates its P cell.
"""
import os, shutil
from docx import Document
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56"
STAGE = os.path.join(ROOT, "output", "aortic_dissection_manuscript", "stage3")
MD = os.path.join(STAGE, "Genome_Medicine_Full_Manuscript.md")
DOCX = os.path.join(STAGE, "Genome_Medicine_Full_Manuscript.docx")

BAK = DOCX.replace(".docx", ".pre-revision-bak.docx")
if not os.path.exists(BAK):
    shutil.copy2(DOCX, BAK)
lines = open(MD, encoding="utf-8").read().split("\n")
doc = Document(DOCX)
paras = list(doc.paragraphs)


def md_line(prefix):
    for l in lines:
        s = l.strip()
        if s.startswith(prefix):
            return s
        if s.startswith("## " + prefix):
            return s[3:].strip()
    raise KeyError("md line not found: " + prefix)


def md_table(prefix):
    i = next(k for k, l in enumerate(lines) if l.startswith(prefix))
    j = i + 1
    # skip caption / footnote lines before the markdown table itself
    while j < len(lines) and not lines[j].startswith("|"):
        j += 1
    rows = []
    while j < len(lines) and lines[j].startswith("|"):
        cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
        if not all(set(c) <= set("-: ") for c in cells):
            rows.append(cells)
        j += 1
    return rows


def set_text(p, t):
    if p.runs:
        p.runs[0].text = t
        for r in p.runs[1:]:
            r.text = ""
    else:
        p.add_run(t)


def new_para_before(ref, text, bold=False):
    el = OxmlElement("w:p")
    ref._p.addprevious(el)
    p = Paragraph(el, ref._parent)
    p.add_run(text).bold = bold
    return p


def new_table_before(ref, rows):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    try:
        t.style = doc.tables[0].style
    except Exception:
        pass
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.cell(i, j)
            cell.text = val
            if i == 0:
                for p in cell.paragraphs:
                    for r in p.runs:
                        r.bold = True
    el = t._tbl
    el.getparent().remove(el)
    ref._p.addprevious(el)
    return t


# ---------------------------------------------------------------- 1) text sync
MAP = {
    6:  "Methods: We applied",
    7:  "Results: In the healthy aorta",
    8:  "Conclusions: Inherited AD risk",
    23: "Separately from the curated gene set",
    25: "Each dataset was processed through a unified single-cell pipeline",
    27: "Per-cell-type enrichment in Layers 1 and Option 2",
    28: "Robustness and negative-control analyses.",
    34: "Layers 1 and Option 2 show partial convergence",
    35: "In the healthy aorta, scDRS with known",
    36: "Option 2, constructed from GWAS summary statistics",
    42: "Layer 2: macrophage module scores in established aortic disease",
    43: "Table 2 summarises the composition",
    44: "Table 3. Macrophage module score across aortic cohorts",
    45: "Mean difference (delta) in the 16-gene",
    50: "Synthesis: a two-compartment working hypothesis",
    51: "The three layers together motivate",
    56: "The central observation of this study",
    57: "A potential concern is the apparent reversal",
    58: "Biologically, the dissociation is intuitive",
    59: "Methodologically, the correlation between Layers 1 and Option 2",
    61: "Several caveats temper the interpretation.",
    63: "The wall-intrinsic / macrophage-associated hypothesis",
    65: "Integrating genetic-mapping and disease-tissue evidence",
    119: "Fig. 1. Genetic risk is enriched",
    120: "Paired bar chart of per-cell-type scDRS z-scores",
    121: "Fig. 2. Cell-level macrophage module differences",
    122: "Heatmap of mean disease-minus-control differences",
    124: "Schematic of the hypothesised dissociation",
    126: "Layer 1 (16 curated aortic-disease genes)",
    133: "Additional file 6: Supplementary Results",
}
for idx, prefix in MAP.items():
    set_text(paras[idx], md_line(prefix))
print("text paragraphs synced:", len(MAP))

# ---------------------------------------------------------------- 2) new paragraphs
# Insert, in order, immediately before the existing "Table 3" title paragraph [44].
ref = paras[44]
new_para_before(ref, md_line("At the cell level (exploratory)"))
new_para_before(ref, md_line("Because cells from the same donor"))

# Table 2 (cohort composition): title, table, footnote
new_para_before(ref, md_line("Table 2. Composition of the six aortic disease cohorts"), bold=True)
t2 = new_table_before(ref, md_table("Table 2. Composition of the six aortic disease cohorts"))
new_para_before(ref, md_line("Cell counts are after quality control"))
print("inserted Table 2 with", len(t2.rows), "rows")

# ---------------------------------------------------------------- 3) Table 4 (sample level)
# Insert before the "Fig. 2" placeholder paragraph [48], i.e. after the existing table.
ref2 = paras[48]
new_para_before(ref2, md_line("Table 4. Sample-level primary analysis"), bold=True)
new_para_before(ref2, md_line("Sample means were computed before comparing conditions"))
t4 = new_table_before(ref2, md_table("Table 4. Sample-level primary analysis"))
print("inserted Table 4 with", len(t4.rows), "rows")

# ---------------------------------------------------------------- 4) existing table fixes
for t in doc.tables:
    for row in t.rows:
        c = [x.text.strip() for x in row.cells]
        if c and c[0] == "GSE222318":
            for cell in row.cells:
                if "2.3" in cell.text and "10" in cell.text:
                    set_text(cell.paragraphs[0], "not reported*")
                    print("updated GSE222318 P cell ->", cell.text)

doc.save(DOCX)
print("saved:", DOCX)
print("tables now:", len(doc.tables), "| paragraphs:", len(doc.paragraphs))
