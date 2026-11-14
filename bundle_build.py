"""Collect every Genome Medicine submission artefact into ONE folder,
produce an itemised manifest, and run a full final audit over the copies.
"""
import os, re, io, json, shutil, zipfile, hashlib, datetime
import pandas as pd
from PIL import Image
from docx import Document
from docx.shared import Pt

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56"
ST = os.path.join(ROOT, "output", "aortic_dissection_manuscript", "stage3")
KIT = os.path.join(ROOT, "output", "aortic_dissection_manuscript", "submission_kit")
K3 = os.path.join(KIT, "stage3")
AF = os.path.join(KIT, "additional_files")
REPO = os.path.join(ROOT, "github_repo")
FIG = os.path.join(ROOT, "scdrs_pipeline", "revision_out", "figures")
BUNDLE = os.path.join(ROOT, "Submission_Final_Genome_Medicine")
INTERNAL = os.path.join(BUNDLE, "_非上传_内部参考")
FIGDIR = os.path.join(BUNDLE, "figures_可选单独上传")

DOI = "10.57760/sciencedb.019x8"
GH = "https://github.com/peterhu9517/aortic-dissection-scDRS-evidence"
ORCID = "0000-0002-8554-6138"
TITLE = ("Genetic susceptibility to aortic dissection and related aortopathies "
         "localizes to vascular wall cells")

# Dynamic state: the cover-letter date must equal the real submission day, and
# the archival wording depends on whether ScienceDB has approved the record.
_cl_src = open(os.path.join(KIT, "Cover_Letter_Genome_Medicine.md"),
               encoding="utf-8").read()
_dm = re.search(r"\b\d{1,2} [A-Z][a-z]+ 20\d{2}\b", _cl_src)
SUBMIT_DATE = _dm.group(0) if _dm else (
    f"{datetime.date.today().day} {datetime.date.today().strftime('%B %Y')}")
DOI_PENDING = ("DOI activation pending" in
               open(os.path.join(ST, "Genome_Medicine_Full_Manuscript.md"),
                    encoding="utf-8").read())

UPLOAD = [
    ("Genome_Medicine_Full_Manuscript.docx", ST,  "Manuscript（主文，含 4 表 4 图）"),
    ("Cover_Letter_Genome_Medicine.docx",   K3,  "Cover letter（投稿信）"),
    ("Additional_file_1.csv",               AF,  "Additional file 1（跨队列细胞类型统计）"),
    ("Additional_file_2.csv",               AF,  "Additional file 2（GEO 样本-分组对照表）"),
    ("Additional_file_3.pdf",               AF,  "Additional file 3（22 页补充图）"),
    ("Additional_file_4.zip",               AF,  "Additional file 4（分析脚本）"),
    ("Additional_file_5.csv",               AF,  "Additional file 5（队列级 QC 汇总）"),
    ("Additional_file_6.docx",              AF,  "Additional file 6（Supplementary Results）"),
]
INTERNAL_FILES = [
    ("Genome_Medicine_Full_Manuscript.md", ST,   "正文 Markdown 源，便于逐字比对"),
    ("Cover_Letter_Genome_Medicine.md",   KIT,  "投稿信 Markdown 源"),
    ("Submission_Dossier_Genome_Medicine.docx", K3, "投稿备忘（Word）"),
    ("Submission_Dossier_Genome_Medicine.md", KIT, "投稿备忘（Markdown 源）"),
    ("代码归档与注册指南.md",              ROOT, "GitHub / ScienceDB / licence 操作指南"),
]
FIGURE_FILES = [
    ("Figure_1.png", "fig1.png"),
    ("Figure_2.png", "fig2.png"),
    ("Figure_3.png", "fig3.png"),
    ("Graphical_abstract.png", "graphical_abstract.png"),
]

R = []   # (section, label, ok, detail)


def ck(section, label, ok, detail=""):
    R.append((section, label, bool(ok), detail))


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def human(n):
    return f"{n/1024:.0f} KB" if n < 1024 * 1024 else f"{n/1024/1024:.2f} MB"


# ---------------------------------------------------------------- 1. bundle
os.makedirs(INTERNAL, exist_ok=True)
os.makedirs(FIGDIR, exist_ok=True)
copied = []
for name, src_dir, _ in UPLOAD:
    src, dst = os.path.join(src_dir, name), os.path.join(BUNDLE, name)
    shutil.copyfile(src, dst)
    copied.append((name, src, dst, "上传"))
for name, src_dir, _ in INTERNAL_FILES:
    src, dst = os.path.join(src_dir, name), os.path.join(INTERNAL, name)
    shutil.copyfile(src, dst)
    copied.append((name, src, dst, "内部"))
for name, srcname in FIGURE_FILES:
    src, dst = os.path.join(FIG, srcname), os.path.join(FIGDIR, name)
    shutil.copyfile(src, dst)
    copied.append((name, src, dst, "图"))

for name, src, dst, _ in copied:
    ck("A 文件完整性", f"{name} 与源文件字节一致", sha(src) == sha(dst),
       human(os.path.getsize(dst)))

# ---------------------------------------------------------------- 2. loaders
md = open(os.path.join(ST, "Genome_Medicine_Full_Manuscript.md"), encoding="utf-8").read()
doc = Document(os.path.join(BUNDLE, "Genome_Medicine_Full_Manuscript.docx"))
doc_text = "\n".join(p.text for p in doc.paragraphs)
for t in doc.tables:
    for row in t.rows:
        doc_text += "\n" + " | ".join(c.text for c in row.cells)
cl = Document(os.path.join(BUNDLE, "Cover_Letter_Genome_Medicine.docx"))
cl_text = "\n".join(p.text for p in cl.paragraphs)
af6 = Document(os.path.join(BUNDLE, "Additional_file_6.docx"))
af6_text = "\n".join(p.text for p in af6.paragraphs)
for t in af6.tables:
    for row in t.rows:
        af6_text += "\n" + " | ".join(c.text for c in row.cells)
dossier = open(os.path.join(INTERNAL, "Submission_Dossier_Genome_Medicine.md"),
               encoding="utf-8").read()
guide = open(os.path.join(INTERNAL, "代码归档与注册指南.md"), encoding="utf-8").read()

ALL_TEXT = {"正文 md": md, "正文 docx": doc_text, "投稿信": cl_text,
            "AF6": af6_text, "投稿备忘": dossier}

# ---------------------------------------------------------------- 3. A: files
for name, _, _, _ in copied[:8]:
    p = os.path.join(BUNDLE, name)
    ok = os.path.exists(p) and 0 < os.path.getsize(p) < 20 * 1024 * 1024
    ck("A 文件完整性", f"{name} 存在且 <20 MB", ok, human(os.path.getsize(p)))
stray = [f for f in os.listdir(BUNDLE)
         if os.path.isfile(os.path.join(BUNDLE, f)) and
         re.search(r"bak|v2|tmp|~\$|\.pre-", f, re.I)]
ck("A 文件完整性", "主目录无备份/旧版/临时文件混入", not stray, str(stray))

with zipfile.ZipFile(os.path.join(BUNDLE, "Additional_file_4.zip")) as z:
    af4 = z.namelist()
ck("A 文件完整性", "Additional_file_4.zip 可正常解压", len(af4) > 0,
   f"{len(af4)} 项")
pdf = open(os.path.join(BUNDLE, "Additional_file_3.pdf"), "rb").read()
npages = int(re.findall(rb"/Count\s+(\d+)", pdf)[0])
ck("A 文件完整性", "Additional_file_3.pdf 页数", npages == 22, f"{npages} 页")
for f in ["Genome_Medicine_Full_Manuscript.docx", "Cover_Letter_Genome_Medicine.docx",
          "Additional_file_6.docx"]:
    try:
        Document(os.path.join(BUNDLE, f))
        ck("A 文件完整性", f"{f} 可被 Word 解析", True)
    except Exception as e:
        ck("A 文件完整性", f"{f} 可被 Word 解析", False, str(e))

# embedded figures vs source PNGs
blips = list(doc.element.body.iter(
    "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"))
ck("B 正文", "正文内嵌图片数量", len(blips) == 4, f"{len(blips)} 张")
with zipfile.ZipFile(os.path.join(BUNDLE, "Genome_Medicine_Full_Manuscript.docx")) as z:
    media = [n for n in z.namelist() if n.startswith("word/media/")]
    sizes = []
    for n in media:
        try:
            im = Image.open(io.BytesIO(z.read(n)))
            sizes.append(im.size)
        except Exception:
            pass
src_sizes = []
for _, s in FIGURE_FILES:
    src_sizes.append(Image.open(os.path.join(FIG, s)).size)
ck("B 正文", "内嵌图与重画图分辨率一致",
   sorted(sizes) == sorted(src_sizes), f"docx {sorted(sizes)} / 源 {sorted(src_sizes)}")

# ---------------------------------------------------------------- 4. B: manuscript
DECL_HEADS = ["Ethics approval and consent to participate", "Consent for publication",
              "Availability of data and materials", "Competing interests", "Funding",
              "Authors' contributions", "Acknowledgements", "Authors' information"]
for label, text in [("正文 md", md), ("正文 docx", doc_text)]:
    ck("B 正文", f"{label}：标题为修订版", TITLE in text)
    if label == "正文 md":
        n_decl = len(re.findall(r"^## ", text.split("# Declarations")[1]
                                .split("# References")[0], re.M))
        ck("B 正文", f"{label}：Declarations 8 节齐全", n_decl == 8,
           f"{n_decl} 个二级标题")
    else:
        hit = [h for h in DECL_HEADS if h in text]
        ck("B 正文", f"{label}：Declarations 8 节齐全", len(hit) == 8,
           f"{len(hit)}/8 个小节标题")
    ck("B 正文", f"{label}：Additional files 6 条且逐文件引用",
       len(re.findall(r"^Additional file \d:", text, re.M)) == 6 and
       all(f"Additional file {i}" in text for i in range(1, 7)))
    ck("B 正文", f"{label}：IRB 豁免句已删除", "qualifies for exemption" not in text)
    for s in ["0.0026", "8 of the 16 curated genes", "sample-level label permutation",
              "MIF, ALOX5, TP53, JAG1 and MRC2", "not used for inference"]:
        ck("B 正文", f"{label}：含关键结果 {s[:34]}", s in text)
    for s in ["Section G, Table S6", "Section H",
              "acute-dissection-specific reversal", "omitted from the heatmap"]:
        ck("B 正文", f"{label}：第三轮修订 {s[:32]}", s in text)
    ck("B 正文", f"{label}：代码归档表述可核验",
       "Additional file 4" in text and
       ("DOI activation pending" in text or DOI in text))

tnums = [int(x) for x in re.findall(r"^Table (\d)\.", md, re.M)]
ck("B 正文", "表编号顺序 Table 1→4", tnums == [1, 2, 3, 4], str(tnums))
ck("B 正文", "缩写表存在", "# List of abbreviations" in md)

# figure titles and legends
sec = md.split("# Figure legends")[1].split("# Additional files")[0]
blocks = [b for b in re.split(r"(?=^(?:Fig\. \d+\.|Graphical abstract\.))",
                              sec, flags=re.M) if b.strip()]
leg_info = []
for b in blocks:
    lines = [x.strip() for x in b.strip().split("\n") if x.strip()]
    m = re.match(r"^(?:Fig\. \d+\.|Graphical abstract\.)\s*(.*)", lines[0])
    ttl = m.group(1) if m else lines[0]
    leg = " ".join(lines[1:])
    leg_info.append((ttl, len(ttl.split()), len(leg.split())))
ck("B 正文", "4 条图题/图例齐全", len(leg_info) == 4, str(len(leg_info)))
ck("B 正文", "图题均 ≤15 词", all(n <= 15 for _, n, _ in leg_info),
   str([n for _, n, _ in leg_info]))
ck("B 正文", "图例均 ≤300 词", all(n <= 300 for _, _, n in leg_info),
   str([n for _, _, n in leg_info]))

# references (expand ranges such as [1-4])
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


body = md.split("# References")[0]
cited = set()
for tok in re.findall(r"\[[0-9,\-\s]+\]", body):
    cited |= expand(tok)
refs = sorted({int(x) for x in re.findall(r"^\[(\d+)\]", md, re.M)})
ck("B 正文", "参考文献 32 条且全部被引用",
   len(refs) == 32 and not [r for r in refs if r not in cited] and
   not [r for r in cited if r not in refs],
   f"列出 {len(refs)} 条，引用 {len(cited)} 条，孤儿 {[r for r in refs if r not in cited]}")

# cross-file numbers
for label, text in [("正文 md", md), ("正文 docx", doc_text), ("投稿信", cl_text)]:
    ck("C 数字一致性", f"{label}：293,000 / 57,999 / 0.0026 / r = 0.78",
       all(s in text for s in ["293,000", "57,999", "0.0026", "r = 0.78"]) if label != "投稿信"
       else all(s in text for s in ["293,000", "57,999", "0.0026"]),
       "")

# stale wording / placeholders
STALE = ["P ≈ 0", "six pre-registered", "four of the five", "four of five cohorts",
         "2.3e-102", "unmasks it", "decades before any event",
         "This is the same gene panel used in Layer 1 and Option 2",
         "qualifies for exemption", "Internal checklist", "Before submitting",
         "12 November 2026", "[待补]", "[Insert", "TO BE COMPLETED", "[bracketed]",
         "[DRAFT", "Graphical abstract\n\n"]
for label, text in ALL_TEXT.items():
    hits = [s for s in STALE if s in text]
    ck("D 旧口径与占位符", f"{label}：无旧表述/占位符", not hits, ", ".join(hits))

# ---------------------------------------------------------------- 5. C: cover letter
for s in [SUBMIT_DATE, ORCID,
          "localized polygenic susceptibility to vascular wall cells", GH,
          "2024ZD0527001", "Kimi Pro3", "no competing interests",
          "in addition to the separate 57,999-cell healthy aorta atlas"]:
    ck("E 投稿信", f"含 {s[:44]}", s in cl_text)
ck("E 投稿信", "代码归档表述可核验（pending 或已激活 DOI）",
   (("Additional file 4" in cl_text) and ("DOI activation pending" in cl_text))
   or (DOI in cl_text))

# ------------------------------------------------- 5b. round-3 reviewer read-out
abs_txt = md.split("\nAbstract\n")[1].split("\nKeywords:")[0] if "\nAbstract\n" in md else md[:6000]
ck("I 第三轮复核意见", "摘要无 four-of-five / 4/5 旧表述",
   "four of five" not in abs_txt and "4/5" not in abs_txt)
ck("I 第三轮复核意见", "摘要明确样本级主推断与探索性结论",
   "primary inference is at the sample level" in abs_txt and "exploratory" in abs_txt)
ck("I 第三轮复核意见", "Discussion 含 GSE213740 反转的生物学解读",
   "acute-dissection-specific reversal" in md and "inflammatory infiltrate" in md)
ck("I 第三轮复核意见", "Methods 引用 AF6 Section G/H",
   "Section G, Table S6" in md and "Section H" in md)
ck("I 第三轮复核意见", "Fig.2 图注与新图一致（GSE224559 已剔除）",
   "omitted from the heatmap" in md and "shown for completeness only" not in md)
ck("I 第三轮复核意见", "Fig.2 图注含小效应量 / 样本级主推断说明",
   "small in magnitude (+0.02 to +0.08)" in md)
ck("I 第三轮复核意见", "投稿信改用 localized ... to 措辞",
   "localized polygenic susceptibility to vascular wall cells" in cl_text)
ck("I 第三轮复核意见", "投稿信日期为提交当日、备忘含提交日提示",
   SUBMIT_DATE in cl_text and "投稿信日期" in dossier)
ck("I 第三轮复核意见", "备忘写明推荐审稿人需可核验邮箱与 ORCID",
   "禁止使用虚构" in dossier)
ck("I 第三轮复核意见", "未激活 DOI 不以「已注册」形式出现在需上传文件中",
   ("DOI activation pending" in doc_text and "DOI activation pending" in cl_text)
   or (DOI in doc_text and DOI in cl_text))

# ---------------------------------------------------------------- 6. D: AF6
for s in ["Table S6", "Table S7", "eight pre-specified", "2,000", "0.0026",
          "sample labels", "ENSG00000240972", "reversed in GSE213740",
          "MIF, ALOX5, TP53, JAG1, MRC2"]:
    ck("F AF6", f"含 {s[:40]}", s in af6_text)
ck("F AF6", "明确声明八项分析未预注册（not pre-registered）",
   "not pre-registered" in af6_text)
ck("F AF6", "7 表 6 图", len(af6.tables) == 7 and
   sum(1 for _ in af6.element.body.iter(
       "{http://schemas.openxmlformats.org/drawingml/2006/main}blip")) == 6,
   f"{len(af6.tables)} 表")
ck("F AF6", "Table S6 为 16 基因", len(af6.tables[5].rows) - 1 == 16,
   f"{len(af6.tables[5].rows)-1} 行")
for s in ["six pre-registered", "permutation-supported", "1,000 times",
          "confirming the cell-level"]:
    ck("F AF6", f"无旧表述 {s}", s not in af6_text)

# ---------------------------------------------------------------- 7. E: data files
d1 = pd.read_csv(os.path.join(BUNDLE, "Additional_file_1.csv"))
d2 = pd.read_csv(os.path.join(BUNDLE, "Additional_file_2.csv"))
d5 = pd.read_csv(os.path.join(BUNDLE, "Additional_file_5.csv"), dtype=str,
                 keep_default_na=False)
ck("G 附件数据", "AF1 42 行逐细胞类型统计", len(d1) == 42, f"{len(d1)} 行")
ck("G 附件数据", "AF2 39 个样本", len(d2) == 39, f"{len(d2)} 行")
ck("G 附件数据", "AF5 6 个队列", len(d5) == 6, f"{len(d5)} 行")
p222 = d5.loc[d5.dataset == "GSE222318", "macrophage_mannwhitney_p"].tolist()
ck("G 附件数据", "AF5 中 GSE222318 的 P 已改为 not reported",
   p222 == ["not reported"], str(p222))
for s in ["revision_analyses.py", "revision_sensitivity.py",
          "build_supplementary_v2.py", "revision_figures.py"]:
    ck("G 附件数据", f"AF4 含大修脚本 {s}", any(s in x for x in af4))

# ---------------------------------------------------------------- 8. F: archiving
for label, text in [("投稿备忘", dossier), ("注册指南", guide)]:
    ck("H 归档与注册", f"{label}：DOI / GitHub / ORCID",
       all(s in text for s in [DOI, GH]) and (ORCID in text or label == "注册指南"))
readme = open(os.path.join(REPO, "README.md"), encoding="utf-8").read()
py_repo = [f for f in os.listdir(REPO) if f.endswith(".py")]
ck("H 归档与注册", "GitHub 仓库脚本与 README 已同步",
   len(py_repo) >= 28 and TITLE[:45] in readme, f"{len(py_repo)} 个 .py")
with zipfile.ZipFile(os.path.join(REPO, "scidb_upload.zip")) as z:
    n_scidb = len(z.namelist())
ck("H 归档与注册", "scidb_upload.zip 与 AF4 同步",
   n_scidb >= 30 and len(af4) >= 30, f"SciDB {n_scidb} 项 / AF4 {len(af4)} 项")
ck("H 归档与注册", "指南已写入 DOI 未注册的排查结论",
   "404" in guide or "未注册" in guide)

# ---------------------------------------------------------------- 9. build report
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
groups = {}
for sec, label, ok, detail in R:
    groups.setdefault(sec, []).append((label, ok, detail))
passed = sum(1 for _, _, ok, _ in R if ok)
failed = [(s, l, d) for s, l, ok, d in R if not ok]

lines = []
A = lines.append
A("# Genome Medicine 投稿文件汇总与终核查")
A("")
A(f"**生成时间**：{now}　|　**目标期刊**：Genome Medicine (BMC / Springer Nature)，Research")
A(f"**ORCID**：{ORCID}　|　**基金**：2024ZD0527001")
A("")
A(f"> **核查结论**：本地文件自动核查 {len(R)} 项，通过 {passed} 项，异常 {len(failed)} 项。"
  "外部 DOI 注册状态与线上归档属于需人工确认事项，不计入自动核查，见第六节。")
A("")
A("## 一、投稿文件夹")
A("")
A(f"所有需上传文件已集中到：`{BUNDLE.replace(chr(92), '/')}`"
  "（主目录平铺，不含任何备份或旧版文件）。")
A("")
A("```")
A("Submission_Final_Genome_Medicine/")
A("├── 00_投稿文件清单与核查报告.md / .docx   ← 本文件")
for name, _, role in UPLOAD:
    A(f"├── {name}")
A("├── _非上传_内部参考/     （Markdown 源、投稿备忘、注册指南，共 5 项）")
A("└── figures_可选单独上传/ （4 张主图 PNG，投稿系统若要求单独提供 Figure 文件时使用）")
A("```")
A("")
A("## 二、需上传文件清单（8 项）")
A("")
A("| # | 文件名 | 大小 | 投稿系统字段 | 内容 |")
A("|---|---|---|---|---|")
for i, (name, _, role) in enumerate(UPLOAD, 1):
    A(f"| {i} | `{name}` | {human(os.path.getsize(os.path.join(BUNDLE, name)))} | "
      f"{'Manuscript' if i == 1 else 'Cover letter' if i == 2 else 'Additional file ' + str(i-2)} | {role} |")
A("")
A("## 三、内部参考文件（不上传）")
A("")
A("| 文件 | 用途 |")
A("|---|---|")
for name, _, role in INTERNAL_FILES:
    A(f"| `{name}` | {role} |")
for name, _ in FIGURE_FILES:
    A(f"| `figures_可选单独上传/{name}` | 主图单独文件；正文 Word 已内嵌同一张图 |")
A("")
A("## 四、逐项核查结果")
A("")
for sec in sorted(groups):
    A(f"### {sec}")
    A("")
    A("| 结果 | 核查项 | 说明 |")
    A("|---|---|---|")
    for label, ok, detail in groups[sec]:
        A(f"| {'通过' if ok else '异常'} | {label} | {detail.replace('|', '/')} |")
    A("")
A("## 五、第三轮复核意见的落实（本轮新修 7 处）")
A("")
A("1. **Discussion 新增一段**：专门解释去除 MIF / ALOX5 / TP53 / JAG1 / MRC2 后 "
  "GSE213740 方向反转——急性 A 型夹层以巨噬细胞富集性炎症浸润为特征 [25,26]，"
  "该队列的 cell-level 信号很可能主要由炎症/激活相关转录本、而非基质与收缩基因承载；"
  "16 基因 panel 因此混合了「构成型壁基质程序」与「诱导型炎症反应」两类过程。"
  "明确写成 interpretation 而非机制，并列出巨噬亚型构成、解离应激、环境 RNA 污染等替代解释，"
  "指出需在前瞻配对标本中做亚型分辨、炎症校正评分才能检验。")
A("2. **Methods 引用补充材料**：Layer 1 与 Layer 2 的 16 基因定义处改为显式引用 "
  "`Additional file 6 (Section G, Table S6)`，并写明因 5 个炎症相关基因存在循环性风险，"
  "已预先设定并报告 11 基因缩减 panel 敏感性分析（`Section H`）。")
A("3. **Fig. 2 重画**：新增橙色醒目注释「小 delta（+0.02 至 +0.08）可对应极小的 "
  "cell-level nominal P；细胞不是独立重复，样本级推断（Table 4）为主」。"
  "队列标签改为水平排布，底部 Note / 脚注 / x 轴标签三行完全分离；GSE222318 仍独立分色标，"
  "GSE224559 仍剔除。新图已替换正文 Word 内嵌图。")
A("4. **Fig. 2 图注修正**：旧句「GSE224559 … shown for completeness only」与新图已剔除该列不一致，"
  "改为「omitted from the heatmap (N/A)」，并补入小效应量与样本级主推断的说明。")
A("5. **DOI 硬伤解除**：`10.57760/sciencedb.019x8` 经 DataCite API 与 doi.org 双重实测为未注册。"
  "正文 Declarations、Cover letter 不再声称「archived with a permanent DOI」，"
  "改以可核验的 GitHub 仓库 + 随稿 `Additional file 4` 版本快照为归档，"
  "ScienceDB 仅注明「record 019x8; DOI activation pending」。"
  "稿件因此不依赖该 DOI 也可合规投稿；另附 `activate_doi.py`，激活后一键回填正式 DOI。")
A("6. **投稿信用词**：`enriched polygenic susceptibility in vascular wall cells` "
  "改为 `localized polygenic susceptibility to vascular wall cells`。")
A(f"7. **日期与审稿人提示**：投稿信日期现为 `{SUBMIT_DATE}`（提交当日），"
  "`activate_doi.py` 在最终打包时会再次把它刷新为运行当天；"
  "投稿备忘新增「若实际 Submit 不是今天，请改为真实提交日期」的提示，"
  "并写明推荐审稿人须使用可独立核验的机构邮箱与 ORCID、禁止虚构身份。")
A("")
A("> 上一轮已修的项目（Ethics 豁免句删除、AF5 的 `2.31e-102` 改 `not reported`、"
  "AF1/AF3/AF5 描述补注、AF3 的 GSE222318 图脚注）继续保留，未回退。")
if not DOI_PENDING:
    A("> 补充：第 5 条记录的是 ScienceDB 审核期间的降级处理（历史记录）。"
      f"该记录现已审核通过，`{DOI}` 已回填到全部投稿文件；当前状态以第六、七节为准。")
A("")
A("> 说明：Additional file 1 作为**完整逐细胞类型原始统计表**仍保留各队列的 cell-level P 数值；"
  "这是数据完整性所需，主文 Table 3、AF5 与 AF1 描述均已明确这些 P 值仅探索性、"
  "GSE222318 不用于推断。如需一并抹去可再处理。")
A("")
A("## 六、投稿前仍需你本人处理（待办 / 待确认）")
A("")
A("| 级别 | 事项 | 现状 |")
A("|---|---|---|")
if DOI_PENDING:
    A(f"| 已解除阻断 | **ScienceDB DOI 仍在审核** | `api.datacite.org/dois/{DOI}` "
      "2026-11-14 09:21 复查仍返回 HTTP 404；发布申请已于当日重新提交，预计当天通过。"
      "正文 Declarations 与 Cover letter 已改为「GitHub 仓库 + 随稿 Additional file 4 "
      "版本快照 + ScienceDB 记录 019x8（DOI 待激活）」，不声称已有永久 DOI，"
      "因此**不构成投稿阻断**。按本人意见等记录通过后再发；通过当日运行 "
      "`scdrs_pipeline/activate_doi.py` 即一键回填正式 DOI、刷新投稿信日期并重新归集。 |")
else:
    A(f"| 已完成 | **ScienceDB DOI 已激活** | `{DOI}` 已在 DataCite 注册并可解析，"
      "已回填正文 Declarations、Cover letter、投稿备忘、注册指南与 README；"
      "正式 DOI 与随稿 Additional file 4 版本快照同时保留。 |")
A("| 待办 | **线上归档仍是修订前快照** | 本地 `scidb_upload.zip` 与 "
  "`Additional_file_4.zip` 已重建为含全部大修与第三轮脚本的新版；ScienceDB 记录中的文件需替换，"
  "GitHub 网页端也需补传新增脚本并更新 README，否则线上代码与终稿不一致。"
  "本地 git 与 GitHub 网页端 commit 历史不同，建议继续用网页上传而非 `git push`。 |")
A("| 待确认 | **APC / 开放获取协议** | 单位是否有 Springer Nature OA 转换协议可减免 APC，"
  "需在投稿系统填写。 |")
A("| 待确认 | **推荐审稿人** | 投稿备忘 §5 有策略建议；最终名单与回避名单需你确认。"
  "投稿系统中每位建议审稿人必须有可独立核验的机构邮箱与 ORCID——编辑部会逐一查验，"
  "虚构身份会按学术不端处理。 |")
A(f"| 待确认 | **投稿信日期** | 现为 `{SUBMIT_DATE}`（最终打包当日）。"
  "若实际点击 Submit 不是这天，请改为真实提交日期；不要改成已过去的年份。"
  "重跑 `activate_doi.py` 会自动刷新为运行当天。 |")
A("| 已明确 | **Ethics 措辞** | 已按你的要求删除 IRB 豁免句；若期刊编辑部要求"
  "明示「exemption」，可在返修阶段补一句机构认定，无需现在写具体文号。 |")
A("")
A("## 七、结论")
A("")
A("稿件正文、投稿信、6 个附件、图、表、引文、Declarations 与内部备忘已归集到同一文件夹，"
  "格式与数字口径一致；第三轮复核意见已逐条落实。"
  + (f"当前 ScienceDB 记录仍在审核，稿件以不依赖 DOI 的可核验归档状态等待；"
     f"通过当天运行 `activate_doi.py` 回填 `{DOI}` 后即可发送。"
     if DOI_PENDING else f"`{DOI}` 已回填，稿件处于可发送状态。")
  + "点击 Submit 前仍需你本人完成：确认 ScienceDB 挂载的是最新版代码 zip、"
    "线上归档同步、推荐审稿人机构邮箱/ORCID 核验、APC 协议确认，以及核对投稿信日期。")
A("")

report_md = "\n".join(lines)
md_path = os.path.join(BUNDLE, "00_投稿文件清单与核查报告.md")
open(md_path, "w", encoding="utf-8", newline="").write(report_md)

# ---- Word rendering (same renderer as the dossier) ----
BOLD = re.compile(r"(\*\*[^*]+\*\*)")


def rich(p, text, size=9.5, italic=False):
    for chunk in BOLD.split(text):
        if not chunk:
            continue
        if chunk.startswith("**") and chunk.endswith("**"):
            r = p.add_run(chunk[2:-2]); r.bold = True
        else:
            r = p.add_run(chunk)
        r.italic = italic
        r.font.size = Pt(size)


out = Document()
out.styles["Normal"].font.name = "Calibri"
out.styles["Normal"].font.size = Pt(9.5)
i = 0
while i < len(lines):
    line = lines[i].rstrip()
    if not line.strip() or line.strip() == "---":
        i += 1; continue
    if line.startswith("```"):
        i += 1
        buf = []
        while i < len(lines) and not lines[i].startswith("```"):
            buf.append(lines[i]); i += 1
        i += 1
        p = out.add_paragraph()
        r = p.add_run("\n".join(buf)); r.font.name = "Consolas"; r.font.size = Pt(8)
        continue
    if line.startswith("|") and i + 1 < len(lines) and \
       re.match(r"^\|[\s\-|:]+\|$", lines[i + 1].strip()):
        rows = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            if not all(re.fullmatch(r"[-: ]+", c or "-") for c in cells):
                rows.append(cells)
            i += 1
        ncol = max(len(r) for r in rows)
        t = out.add_table(rows=0, cols=ncol)
        try: t.style = "Light Grid Accent 1"
        except Exception: t.style = "Table Grid"
        for ri, cells in enumerate(rows):
            cr = t.add_row().cells
            for j in range(ncol):
                rich(cr[j].paragraphs[0], cells[j] if j < len(cells) else "", size=8.2)
                if ri == 0:
                    for r_ in cr[j].paragraphs[0].runs: r_.bold = True
        out.add_paragraph()
        continue
    if line.startswith("### "): out.add_heading(line[4:], level=2)
    elif line.startswith("## "): out.add_heading(line[3:], level=1)
    elif line.startswith("# "): out.add_heading(line[2:], level=0)
    elif line.startswith("> "):
        rich(out.add_paragraph(), line[2:], size=9, italic=True)
    elif re.match(r"^\d+\. ", line):
        rich(out.add_paragraph(style="List Number"), re.sub(r"^\d+\. ", "", line))
    elif line.startswith("- "):
        rich(out.add_paragraph(style="List Bullet"), line[2:])
    else:
        rich(out.add_paragraph(), line)
    i += 1

docx_path = os.path.join(BUNDLE, "00_投稿文件清单与核查报告.docx")
out.save(docx_path)

print(f"BUNDLE: {BUNDLE}")
print(f"files copied: {len(copied)} | checks: {len(R)} | pass: {passed} | issues: {len(failed)}")
for s, l, d in failed:
    print(f"  ISSUE [{s}] {l} :: {d}")
print("report:", md_path)
print("report docx:", docx_path)
