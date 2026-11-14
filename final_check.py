"""Final consistency audit across the whole Genome Medicine submission kit."""
import os, re, zipfile, json
from docx import Document

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56"
ST = os.path.join(ROOT, "output", "aortic_dissection_manuscript", "stage3")
KIT = os.path.join(ROOT, "output", "aortic_dissection_manuscript", "submission_kit")
AF = os.path.join(KIT, "additional_files")
REPO = os.path.join(ROOT, "github_repo")

md = open(os.path.join(ST, "Genome_Medicine_Full_Manuscript.md"), encoding="utf-8").read()
docx = Document(os.path.join(ST, "Genome_Medicine_Full_Manuscript.docx"))
doc_text = "\n".join(p.text for p in docx.paragraphs)
for t in docx.tables:
    for r in t.rows:
        doc_text += "\n" + " | ".join(c.text for c in r.cells)
cl = Document(os.path.join(KIT, "stage3", "Cover_Letter_Genome_Medicine.docx"))
cl_text = "\n".join(p.text for p in cl.paragraphs)
af6 = Document(os.path.join(AF, "Additional_file_6.docx"))
af6_text = "\n".join(p.text for p in af6.paragraphs)
for t in af6.tables:
    for r in t.rows:
        af6_text += "\n" + " | ".join(c.text for c in r.cells)
dossier = open(os.path.join(KIT, "Submission_Dossier_Genome_Medicine.md"), encoding="utf-8").read()
guide = open(os.path.join(ROOT, "代码归档与注册指南.md"), encoding="utf-8").read()

TITLE = ("Genetic susceptibility to aortic dissection and related aortopathies "
         "localizes to vascular wall cells")
DOI = "10.57760/sciencedb.019x8"
GH = "https://github.com/peterhu9517/aortic-dissection-scDRS-evidence"
DOI_PENDING = "DOI activation pending" in md
ARCHIVE_WORD = "DOI activation pending" if DOI_PENDING else DOI
_dm = re.search(r"\b\d{1,2} [A-Z][a-z]+ 20\d{2}\b", cl_text)
SUBMIT_DATE = _dm.group(0) if _dm else "(date not found)"

print("=" * 74)
print("1. MAIN MANUSCRIPT (.md / .docx)")
print("=" * 74)
for name, text in [("md", md), ("docx", doc_text)]:
    print(f" [{name}]")
    for s in [TITLE, "0.0026", "8 of the 16 curated genes", "sample-level label permutation",
              "MIF, ALOX5, TP53, JAG1 and MRC2", "Table 4", "Additional file 6"]:
        print(f"   required {s[:48]!r}: {s in text}")
    for s in ["four of five cohorts", "2.3e-102", "P ≈ 0", "pre-registered",
              "unmasks it", "is driven by macrophage", "decades before any event",
              "This is the same gene panel used in Layer 1 and Option 2",
              "Graphical abstract\n\n"]:
        print(f"   stale    {s[:48]!r}: {s in text}")
print("   docx tables:", len(docx.tables), "| paragraphs:", len(docx.paragraphs))
print("   docx inline images:", sum(1 for _ in docx.element.body.iter(
    "{http://schemas.openxmlformats.org/drawingml/2006/main}blip")))

# reference integrity
body = md.split("# References")[0]


def expand(tok):
    out = set()
    for part in tok.strip("[]").split(","):
        part = part.strip()
        if "-" in part:
            a, b = [int(v) for v in part.split("-")]
            out.update(range(a, b + 1))
        elif part.isdigit():
            out.add(int(part))
    return out


cited = set()
for tok in re.findall(r"\[[0-9,\-\s]+\]", body):
    cited |= expand(tok)
refs = sorted({int(x) for x in re.findall(r"^\[(\d+)\]", md, re.M)})
print("   references listed:", len(refs), "range", min(refs), "-", max(refs))
print("   distinct cited numbers:", len(cited))
print("   orphan references:", [r for r in refs if r not in cited])
print("   cited but missing:", sorted(r for r in cited if r not in refs))

print()
print("=" * 74)
print("2. COVER LETTER")
print("=" * 74)
for s in [SUBMIT_DATE, "0.0026", ARCHIVE_WORD, GH, "0000-0002-8554-6138",
          "2024ZD0527001", "Kimi Pro3", "no competing interests",
          "in addition to the separate 57,999-cell healthy aorta atlas"]:
    print(f"   required {s[:52]!r}: {s in cl_text}")
for s in ["Internal checklist", "Before submitting", "12 November 2026",
          "four of the five", "2.3e-102", "[待补]", "[bracketed]"]:
    print(f"   stale    {s[:52]!r}: {s in cl_text}")

print()
print("=" * 74)
print("3. ADDITIONAL FILE 6")
print("=" * 74)
for s in ["Table S6", "Table S7", "eight pre-specified", "2,000", "0.0026",
          "sample labels", "ENSG00000240972", "hypothesis-generating"]:
    print(f"   required {s!r}: {s in af6_text}")
for s in ["six pre-registered", "permutation-supported", "4/5 case",
          "1,000 times", "confirming the cell-level"]:
    print(f"   stale    {s!r}: {s in af6_text}")
print("   tables:", len(af6.tables), "| S6 data rows:", len(af6.tables[5].rows) - 1)
print("   embedded figures:", sum(1 for _ in af6.element.body.iter(
    "{http://schemas.openxmlformats.org/drawingml/2006/main}blip")))

print()
print("=" * 74)
print("4. ADDITIONAL FILES ON DISK")
print("=" * 74)
expected = ["Additional_file_1.csv", "Additional_file_2.csv", "Additional_file_3.pdf",
            "Additional_file_4.zip", "Additional_file_5.csv", "Additional_file_6.docx"]
for f in expected:
    p = os.path.join(AF, f)
    print(f"   {f}: {'OK' if os.path.exists(p) else 'MISSING'} "
          f"{os.path.getsize(p)/1024:.0f} KB (<20MB: {os.path.getsize(p) < 20*1024*1024})")
with zipfile.ZipFile(os.path.join(AF, "Additional_file_4.zip")) as z:
    n = z.namelist()
for s in ["revision_analyses.py", "revision_sensitivity.py", "build_supplementary_v2.py"]:
    print(f"   AF4 contains {s}: {any(s in x for x in n)}")

print()
print("=" * 74)
print("5. DOSSIER / GUIDE / REPO")
print("=" * 74)
for s in [TITLE, ARCHIVE_WORD, GH, "0.0026", "Table S6", "Kimi Pro3"]:
    print(f"   dossier required {s[:42]!r}: {s in dossier}")
for s in ["[待补]", "four of five", "2.3e-102", "[Insert", "[DRAFT"]:
    print(f"   dossier stale    {s!r}: {s in dossier}")
for s in [ARCHIVE_WORD, GH, "MIT", "0000-0002-8554-6138"]:
    print(f"   guide required   {s!r}: {s in guide}")
py = [f for f in os.listdir(REPO) if f.endswith(".py")]
print("   github_repo .py files:", len(py))
print("   README final title:", TITLE[:45] in open(os.path.join(REPO, "README.md"),
                                                  encoding="utf-8").read())
with zipfile.ZipFile(os.path.join(REPO, "scidb_upload.zip")) as z:
    print("   scidb_upload.zip entries:", len(z.namelist()))
print()
print("=" * 74)
print("6. CROSS-FILE NUMBER CONSISTENCY")
print("=" * 74)
for label, text in [("md", md), ("docx", doc_text), ("cover", cl_text), ("AF6", af6_text)]:
    print(f"   {label:6s}  293,000: {'293,000' in text} | 57,999: {'57,999' in text} "
          f"| 39 annotated: {'39 annotated' in text} | r = 0.78: {'r = 0.78' in text} "
          f"| 8 of 16/8 of the 16: {('8 of 16' in text or '8 of the 16' in text)}")
print()
print("NOTE: ScienceDB currently holds the PRE-revision zip. The rebuilt "
      "scidb_upload.zip must replace it before submission so the DOI snapshot "
      "matches the final code.")
