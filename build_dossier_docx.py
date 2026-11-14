"""Regenerate the Word version of the submission dossier from the refreshed
markdown so the two copies no longer disagree. The dossier is an internal
planning memo, not a file submitted to the journal."""
import os, re
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56"
KIT = os.path.join(ROOT, "output", "aortic_dissection_manuscript", "submission_kit")
SRC = os.path.join(KIT, "Submission_Dossier_Genome_Medicine.md")
OUT = os.path.join(KIT, "stage3", "Submission_Dossier_Genome_Medicine.docx")

lines = open(SRC, encoding="utf-8").read().split("\n")
doc = Document()
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(9.5)
BOLD = re.compile(r"(\*\*[^*]+\*\*)")


def rich(p, text, size=9.5, italic=False):
    for chunk in BOLD.split(text):
        if not chunk:
            continue
        if chunk.startswith("**") and chunk.endswith("**"):
            r = p.add_run(chunk[2:-2])
            r.bold = True
        else:
            r = p.add_run(chunk)
        r.italic = italic
        r.font.size = Pt(size)


i = 0
while i < len(lines):
    line = lines[i].rstrip()
    if not line.strip() or line.strip() == "---":
        i += 1
        continue
    # markdown table
    if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s\-|:]+\|$", lines[i + 1].strip()):
        rows = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            if not all(re.fullmatch(r"[-: ]+", c or "-") for c in cells):
                rows.append(cells)
            i += 1
        ncol = max(len(r) for r in rows)
        t = doc.add_table(rows=0, cols=ncol)
        try:
            t.style = "Light Grid Accent 1"
        except Exception:
            t.style = "Table Grid"
        for ri, cells in enumerate(rows):
            cr = t.add_row().cells
            for j in range(ncol):
                txt = cells[j] if j < len(cells) else ""
                rich(cr[j].paragraphs[0], txt, size=8.2)
                if ri == 0:
                    for r_ in cr[j].paragraphs[0].runs:
                        r_.bold = True
        doc.add_paragraph()
        continue
    if line.startswith("### "):
        h = doc.add_heading(line[4:], level=2)
    elif line.startswith("## "):
        h = doc.add_heading(line[3:], level=1)
    elif line.startswith("# "):
        h = doc.add_heading(line[2:], level=0)
    elif line.startswith("> "):
        p = doc.add_paragraph()
        rich(p, line[2:], size=9, italic=True)
    elif line.startswith("- "):
        p = doc.add_paragraph(style="List Bullet")
        rich(p, line[2:])
    else:
        p = doc.add_paragraph()
        rich(p, line)
    i += 1

doc.save(OUT)
print("saved:", OUT)
chk = Document(OUT)
t = "\n".join(p.text for p in chk.paragraphs)
for tb in chk.tables:
    t += "\n" + "\n".join(" | ".join(c.text for c in r.cells) for r in tb.rows)
print("paragraphs:", len(chk.paragraphs), "tables:", len(chk.tables))
for s in ["10.57760/sciencedb.019x8", "0000-0002-8554-6138", "0.0026",
          "Kimi Pro3", "Table S6"]:
    print(f"  required {s!r}: {s in t}")
for s in ["[待补]", "four of five", "2.3e-102", "[Insert"]:
    print(f"  stale    {s!r}: {s in t}")
