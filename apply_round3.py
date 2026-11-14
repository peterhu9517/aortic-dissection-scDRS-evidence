"""Round-3 response to the post-revision reviewer read-out.

What this script changes (all mirrored between the markdown sources and the
submission Word files):

 1. Discussion: new paragraph interpreting why GSE213740 reverses direction
    after removal of the five inflammation-associated panel genes.
 2. Methods Layers 1 and 2: explicit pointers to Additional file 6
    Sections G/H and Table S6, and a statement that the circularity analysis
    was pre-specified.
 3. Fig. 2 legend: GSE224559 is now "omitted" (the redrawn heatmap dropped
    that column), plus a note that small deltas can carry tiny cell-level
    nominal P values while sample-level inference is primary.
 4. Data availability / cover letter: stop asserting a registered permanent
    DOI.  Use the verifiable GitHub repository + the versioned code snapshot
    supplied as Additional file 4; ScienceDB is described as a deposit whose
    DOI is pending activation.
 5. Cover letter: "localized polygenic susceptibility to vascular wall cells".
 6. Dossier / registration guide / repository README: status and action notes.
"""
import os
from docx import Document
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56"
ST = os.path.join(ROOT, "output", "aortic_dissection_manuscript", "stage3")
KIT = os.path.join(ROOT, "output", "aortic_dissection_manuscript", "submission_kit")
REPO = os.path.join(ROOT, "github_repo")

MD_M = os.path.join(ST, "Genome_Medicine_Full_Manuscript.md")
DOC_M = os.path.join(ST, "Genome_Medicine_Full_Manuscript.docx")
MD_C = os.path.join(KIT, "Cover_Letter_Genome_Medicine.md")
MD_D = os.path.join(KIT, "Submission_Dossier_Genome_Medicine.md")
MD_G = os.path.join(ROOT, "代码归档与注册指南.md")
MD_R = os.path.join(REPO, "README.md")

# ------------------------------------------------------------------ new text
NEW_DISC = (
    "The reversal in GSE213740 merits a separate interpretation. This cohort "
    "consists of acute type-A dissection tissue, in which a macrophage-rich "
    "inflammatory infiltrate is a prominent feature [25,26]. Removing MIF, "
    "ALOX5, TP53, JAG1 and MRC2 abolished the apparent disease-associated "
    "increase and reversed its sign, which is consistent with the cell-level "
    "macrophage signal in this cohort being carried largely by inflammation- "
    "and activation-associated transcripts rather than by the matrix, "
    "contractile and mechanosensing genes that dominate the wall-cell "
    "programme (FBN1, ELN, ACTA2, MYH11, COMP, ACAN). The full 16-gene panel "
    "therefore mixes at least two biologically distinct processes—a "
    "constitutive wall-matrix programme and an inducible inflammatory "
    "response—and a single module score cannot separate them; an "
    "acute-dissection-specific reversal is a plausible consequence of that "
    "mixture. We emphasise that this is an interpretation, not a demonstrated "
    "mechanism: the available data cannot distinguish a genuine inflammatory "
    "contribution from differences in macrophage subtype composition, "
    "dissociation stress or ambient-RNA contamination between acute surgical "
    "specimens and comparator tissue, and the finding is cell-level and "
    "exploratory. Testing it will require macrophage-subtype-resolved, "
    "inflammation-adjusted scoring in prospectively collected paired specimens."
)

L1_OLD = ("Cell types with positive z-scores are enriched for the "
          "disease-gene programme; negative scores indicate depletion.")
L1_NEW = (L1_OLD + " The provenance, functional class and inclusion rationale "
          "for each of these 16 genes are documented individually in Additional "
          "file 6 (Section G, Table S6); because five carry macrophage or "
          "inflammatory associations that could generate a circular macrophage "
          "signal, a reduced-panel sensitivity analysis excluding them was "
          "pre-specified and is reported in Additional file 6 (Section H).")

L2_OLD = ("The 16 genes, their Ensembl identifiers, functional class and "
          "inclusion rationale are listed individually in Additional file 6 "
          "(Table S6).")
L2_NEW = ("The 16 genes, their Ensembl identifiers, functional class and "
          "inclusion rationale are listed individually in Additional file 6 "
          "(Section G, Table S6). Because five panel genes (MIF, ALOX5, TP53, "
          "JAG1, MRC2) have macrophage or inflammatory associations and could "
          "therefore generate a circular macrophage signal, we pre-specified a "
          "reduced 11-gene panel sensitivity analysis for every cohort "
          "(Additional file 6, Section H; see also Robustness and "
          "negative-control analyses).")

DOI_FIELD_OLD = "archived version: 10.57760/sciencedb.019x8;"
DOI_FIELD_NEW = ("archived version: a versioned snapshot of the complete "
                 "analysis code is supplied as Additional file 4, and the "
                 "repository is additionally deposited in ScienceDB (record "
                 "019x8; DOI activation pending);")

FIG2_OLD = ("GSE224559 has no human control arm and is shown for completeness "
            "only (N/A in the case-control colour scale).")
FIG2_NEW = ("GSE224559 has no human control arm and is omitted from the "
            "heatmap (N/A).")
FIG2_TAIL_OLD = "official sample labels are documented in Additional file 2."
FIG2_TAIL_NEW = (FIG2_TAIL_OLD + " Although the macrophage deltas in the four "
                 "comparable cohorts are small in magnitude (+0.02 to +0.08), "
                 "their cell-level nominal P values are extremely small; these "
                 "P values are anti-conservative because cells are not "
                 "independent biological replicates, and sample-level "
                 "inference (Table 4) is primary.")

CL_OLD1 = "enriched polygenic susceptibility in vascular wall cells"
CL_NEW1 = "localized polygenic susceptibility to vascular wall cells"
CL_OLD2 = " and is archived with a permanent DOI (10.57760/sciencedb.019x8)."
CL_NEW2 = ("; a versioned snapshot of the complete analysis code is supplied "
           "as Additional file 4, and the repository has been deposited in "
           "ScienceDB (record 019x8; DOI activation pending and to be supplied "
           "before publication).")

PAIRS_M = [(L1_OLD, L1_NEW), (L2_OLD, L2_NEW),
           (DOI_FIELD_OLD, DOI_FIELD_NEW), (FIG2_OLD, FIG2_NEW),
           (FIG2_TAIL_OLD, FIG2_TAIL_NEW)]
PAIRS_C = [(CL_OLD1, CL_NEW1), (CL_OLD2, CL_NEW2)]
PAIRS_D = [(DOI_FIELD_OLD, DOI_FIELD_NEW)]


def patch_file(path, pairs, label, expect_min=1):
    s = open(path, encoding="utf-8").read()
    orig = s
    for old, new in pairs:
        n = s.count(old)
        if n == 0:
            if new in s:
                print(f"  {label}: already applied -> {old[:45]}...")
                continue
            if expect_min > 0:
                raise RuntimeError(f"{label}: missing anchor: {old[:70]!r}")
            print(f"  {label}: optional anchor not present -> {old[:45]}...")
            continue
        if n < expect_min:
            raise RuntimeError(f"{label}: expected >= {expect_min} hits, got {n}: {old[:70]!r}")
        if new in s:
            print(f"  {label}: already applied -> {old[:45]}...")
            continue
        s = s.replace(old, new)
        print(f"  {label}: replaced {n} x {old[:45]}...")
    if s != orig:
        open(path, "w", encoding="utf-8", newline="").write(s)
    return s


def set_text(p, t):
    if p.runs:
        p.runs[0].text = t
        for r in p.runs[1:]:
            r.text = ""
    else:
        p.add_run(t)


def repl_para(doc, old, new, label, expect=1):
    hits = [p for p in doc.paragraphs if old in p.text]
    if len(hits) != expect:
        raise RuntimeError(f"docx {label}: expected {expect} hits, got {len(hits)} "
                           f"for {old[:70]!r}")
    for p in hits:
        set_text(p, p.text.replace(old, new))
    print(f"  docx: replaced {len(hits)} x {label}")


def insert_after(ref, text):
    el = OxmlElement("w:p")
    ref._p.addnext(el)
    np = Paragraph(el, ref._parent)
    np.style = ref.style
    np.add_run(text)
    return np


print("PATCH 1/6  manuscript .md")
s = open(MD_M, encoding="utf-8").read()
patch_file(MD_M, PAIRS_M, "manuscript.md")
if NEW_DISC not in s:
    lines = open(MD_M, encoding="utf-8").read().split("\n")
    anchor = next(i for i, l in enumerate(lines)
                  if l.startswith("Biologically, the dissociation is intuitive."))
    lines.insert(anchor, NEW_DISC)
    open(MD_M, "w", encoding="utf-8", newline="").write("\n".join(lines))
    print(f"  manuscript.md: inserted new Discussion paragraph at line {anchor+1}")
else:
    print("  manuscript.md: Discussion paragraph already present")

print("PATCH 2/6  cover letter .md")
patch_file(MD_C, PAIRS_C, "cover_letter.md")

print("PATCH 3/6  dossier / guide / README")
patch_file(MD_D, PAIRS_D, "dossier.md", expect_min=2)
patch_file(MD_G, [(DOI_FIELD_OLD, DOI_FIELD_NEW)], "guide.md", expect_min=0)
patch_file(MD_R, [("**Archived DOI:** 10.57760/sciencedb.019x8 (ScienceDB)",
                   "**Archival deposit:** ScienceDB record 019x8 (DOI activation "
                   "pending). A versioned snapshot of the complete analysis code "
                   "is supplied with the manuscript as Additional file 4.")],
           "README.md")

print("PATCH 4/6  manuscript .docx")
d = Document(DOC_M)
for old, new in PAIRS_M:
    repl_para(d, old, new, old[:42])
if NEW_DISC not in "\n".join(p.text for p in d.paragraphs):
    ref = next(p for p in d.paragraphs
               if p.text.startswith("A potential concern is the apparent reversal"))
    insert_after(ref, NEW_DISC)
    print("  docx: inserted new Discussion paragraph")
else:
    print("  docx: Discussion paragraph already present")
d.save(DOC_M)
print("  saved", os.path.basename(DOC_M))

print("PATCH 5/6  dossier status / action notes")
s = open(MD_D, encoding="utf-8").read()
s = s.replace(
    "| GitHub + 归档 DOI | ✅ https://github.com/peterhu9517/aortic-dissection-scDRS-evidence ；10.57760/sciencedb.019x8 |",
    "| GitHub + 代码归档 | ✅ https://github.com/peterhu9517/aortic-dissection-scDRS-evidence ；版本快照随稿作为 Additional file 4 提交；ScienceDB 记录 019x8 的 DOI 待激活 |")
s = s.replace(
    "**仍需你本人处理的三项（投稿阻断项已标红）**",
    "**仍需你本人处理的三项**")
s = s.replace(
    "**在 DOI 可解析之前不要投稿**，否则 `archived version:` 会被编辑部核验出来。",
    "**本轮已把投稿文件改为不依赖该 DOI**：正文与投稿信改以 GitHub 仓库 + 随稿 "
    "Additional file 4 版本快照作为可核验归档，ScienceDB 仅注明「DOI 待激活」。"
    "因此稿件可以在不写未注册 DOI 的前提下投稿；待 DOI 真正激活后，运行 "
    "`scdrs_pipeline/activate_doi.py` 可一键把正式 DOI 回填到全部投稿文件。")
s = s.replace(
    "| Suggested reviewers | 4 类真实人选（§5），在系统中填机构邮箱/ORCID |",
    "| Suggested reviewers | 4 类真实人选（§5）；投稿系统中必须填可独立核验的"
    "机构邮箱与 ORCID，编辑部会逐一查验，禁止使用虚构或未核实的身份信息 |")
note = ("\n> **投稿信日期**：当前为 `13 November 2026`（即本日）。若实际点击 Submit "
        "的日期不是今天，请把投稿信中的日期改为真实提交日期——不要用未来日期，"
        "也不要为了「避免未来日期」改成已过去的年份。\n")
if "投稿信日期**：当前为" not in s:
    k = s.find("## ")
    s = s[:k] + note + "\n" + s[k:]
    print("  dossier: inserted cover-letter date note")
open(MD_D, "w", encoding="utf-8", newline="").write(s)

print("PATCH 6/6  guide status rows")
s = open(MD_G, encoding="utf-8").read()
s = s.replace(
    "| 归档 DOI | `10.57760/sciencedb.019x8`（ScienceDB；Zenodo 国内不可达，故改用此路径） | ⚠️ 已回填正文，**但 2026-11-13 实测未注册** |",
    "| 归档 DOI | `10.57760/sciencedb.019x8`（ScienceDB；Zenodo 国内不可达，故改用此路径） | ⚠️ 2026-11-13 实测未注册；**已从投稿文件移除「已注册」声称**，待激活后回填 |")
s = s.replace(
    "- `archived version: 10.57760/sciencedb.019x8`",
    "- `archived version:` 字段目前写的是 GitHub + Additional file 4 版本快照 + "
    "ScienceDB 记录 019x8（DOI 待激活）；激活后运行 `scdrs_pipeline/activate_doi.py` 回填")
tail = ("\n## DOI 激活后的一键回填\n\n"
        "当 `https://doi.org/10.57760/sciencedb.019x8` 能正常解析后，运行：\n\n"
        "```bash\n"
        "cd scdrs_pipeline && python activate_doi.py\n"
        "```\n\n"
        "该脚本会先复核 DataCite 记录是否真实存在，再把正文、投稿信、投稿备忘、"
        "注册指南、README 中的「DOI activation pending」表述统一换回正式 DOI，"
        "并重建 Word 成品与投稿汇总报告。\n")
if "## DOI 激活后的一键回填" not in s:
    s = s.rstrip() + "\n" + tail
    print("  guide: appended DOI re-activation section")
open(MD_G, "w", encoding="utf-8", newline="").write(s)

print("\nDONE round-3 text patches")
