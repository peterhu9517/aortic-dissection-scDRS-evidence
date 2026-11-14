"""Rebuild the final Genome Medicine cover-letter .docx from the revised
markdown source. Inline **bold** markers are converted to bold runs; no
internal checklist or placeholder text is carried over."""
import os, re
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56"
KIT = os.path.join(ROOT, "output", "aortic_dissection_manuscript", "submission_kit")
SRC = os.path.join(KIT, "Cover_Letter_Genome_Medicine.md")
OUT = os.path.join(KIT, "stage3", "Cover_Letter_Genome_Medicine.docx")

lines = open(SRC, encoding="utf-8").read().split("\n")
_m = re.search(r"\b\d{1,2} [A-Z][a-z]+ 20\d{2}\b", "\n".join(lines))
SUBMIT_DATE = _m.group(0) if _m else "(date missing)"

doc = Document()
normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(10.5)
for section in doc.sections:
    section.top_margin = section.bottom_margin = 914400  # 1 inch

BOLD = re.compile(r"(\*\*[^*]+\*\*)")


def add_rich(p, text, size=10.5):
    for chunk in BOLD.split(text):
        if not chunk:
            continue
        if chunk.startswith("**") and chunk.endswith("**"):
            r = p.add_run(chunk[2:-2])
            r.bold = True
        else:
            r = p.add_run(chunk)
        r.font.size = Pt(size)


for raw in lines:
    line = raw.rstrip()
    if not line.strip():
        continue
    if line.startswith("# "):
        h = doc.add_paragraph()
        r = h.add_run(line[2:].strip())
        r.bold = True
        r.font.size = Pt(14)
        r.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)
        h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        continue
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    add_rich(p, line)

doc.save(OUT)
print("saved:", OUT)

# ------------------------------------------------------------------ verify
chk = Document(OUT)
text = "\n".join(p.text for p in chk.paragraphs)
must_have = [
    SUBMIT_DATE,
    "0000-0002-8554-6138",
    "localized polygenic susceptibility to vascular wall cells",
    "0.0026",
    "in addition to the separate 57,999-cell healthy aorta atlas",
    "no competing interests",
    "2024ZD0527001",
    "Kimi Pro3",
]
must_not = [
    "Internal checklist",
    "Before submitting",
    "bracketed",
    "12 November 2026",
    "four of the five",
    "2.3e-102",
    "[待补]",
    "TO BE COMPLETED",
]
for s in must_have:
    print(f"  required  {s!r}: {s in text}")
for s in must_not:
    print(f"  forbidden {s!r}: {s in text}")
print("  archival  verifiable (pending or activated DOI):",
      ("DOI activation pending" in text) or ("10.57760/sciencedb.019x8" in text))
print("paragraphs:", len(chk.paragraphs))
