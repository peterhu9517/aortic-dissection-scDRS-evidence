"""Bring the pre-submission dossier in line with the revised (post-major-review)
final manuscript. The dossier remains a planning memo; this script replaces the
stale, paste-ready blocks with the authoritative text from the final .md and
marks the historical checklists as superseded."""
import os, re

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56"
KIT = os.path.join(ROOT, "output", "aortic_dissection_manuscript", "submission_kit")
MD = os.path.join(ROOT, "output", "aortic_dissection_manuscript", "stage3",
                  "Genome_Medicine_Full_Manuscript.md")
DOS = os.path.join(KIT, "Submission_Dossier_Genome_Medicine.md")

L = open(MD, encoding="utf-8").read().split("\n")
title = L[0].strip()


def section(header):
    """Return the text of the first paragraph after a '## header' line."""
    for i, l in enumerate(L):
        if l.strip() == "## " + header:
            j = i + 1
            while j < len(L) and not L[j].strip():
                j += 1
            return L[j].strip()
    raise KeyError(header)


abstract = "\n\n".join(
    "**" + l.split(":", 1)[0] + ":**" + l.split(":", 1)[1]
    for l in L if re.match(r"^(Background|Methods|Results|Conclusions):", l)
)

dec = {k: section(k) for k in [
    "Ethics approval and consent to participate",
    "Consent for publication",
    "Availability of data and materials",
    "Competing interests",
    "Funding",
    "Authors' contributions",
    "Acknowledgements",
    "Authors' information",
]}

fig1_title = next(l for l in L if l.startswith("Fig. 1. ")).replace("Fig. 1. ", "").strip()
fig1_legend = L[next(i for i, l in enumerate(L) if l.startswith("Fig. 1. ")) + 1].strip()

af_lines = [l.strip() for l in L if l.startswith("Additional file ") and ":" in l]
af_rows = []
for l in af_lines:
    m = re.match(r"Additional file (\d+): (.+?)\. File format: (\.\w+)\. (.*)", l)
    if m:
        af_rows.append((m.group(1), m.group(3), m.group(2), m.group(4)))

d = open(DOS, encoding="utf-8").read()

# ---------------------------------------------------------------- header
d = re.sub(r"\*\*目标稿件\*\*：.*", "**目标稿件**：" + title, d, count=1)
d = d.replace(
    "**整理日期**：2026-11-12 ｜ **数据核实日期**：2026-11-12\n"
    "**本材料不改动论文正文 .docx**，所有可粘贴文段独立给出，改稿时再并入正文。",
    "**整理日期**：2026-11-12 ｜ **数据核实日期**：2026-11-12 ｜ **末次同步**：2026-11-13（大修后终稿）\n\n"
    "> **状态说明（重要）**：本文件是 2026-11-12 的**投稿规划备忘**，不是投稿文件本身。"
    "期刊指标、转投阶梯、审稿人策略等历史判断仍保留供决策参考；但 §2、§3、§8 的"
    "「待补」清单**均已在大修中完成**，不得再按旧清单操作。\n"
    "> **权威交付物**：`stage3/Genome_Medicine_Full_Manuscript.docx`（正文，4 表 4 图）、"
    "`stage3/Cover_Letter_Genome_Medicine.docx`（投稿信）、"
    "`additional_files/Additional_file_1..6`（附件）。§4 的粘贴文本已同步为终稿原文。\n"
    "> **大修口径**：sample/donor-level 推断为主分析，cell-level P 值仅探索性；"
    "标题改为 related aortopathies；Layer 1 / Option 2 为 directional support（8/16 基因重叠）；"
    "Layer 2 巨噬信号为 hypothesis-generating。共 8 项 pre-specified 稳健性分析见 Additional file 6。",
    1)

d = d.replace("## 2. Genome Medicine Research 硬性格式核对（逐条对照当前稿件）",
              "## 2. Genome Medicine Research 硬性格式核对（**历史状态表，已全部完成**）\n\n"
              "> 下表记录的是 2026-11-12 初稿的缺口。结构化摘要、Declarations 8 节、缩写表、"
              "Background/Conclusions 标题、图题/图例拆分、Additional files 清单与逐文件引用、"
              "LLM 披露、ORCID 与 Cover letter 占位符均已在终稿补齐，请直接以终稿 .docx 为准。\n",
              1)
d = d.replace("## 3. 投稿前必补 7 项（按优先级）",
              "## 3. 投稿前必补 7 项（**历史清单，P0/P1 已落实**）\n\n"
              "> 统计层级：已新增 Table 4（样本均值 95% CI / Welch / 混合效应模型）与 2,000 次 "
              "**样本级**标签置换；阴性对照、留一队列、bootstrap CI、GSE222318 剔除均已完成并"
              "扩为 8 项分析；16 基因 panel 逐项注释见 AF6 Table S6；11 基因去炎症敏感性见 AF6 Table S7。"
              "基金号、作者贡献、ORCID、LLM 披露、GitHub 与 ScienceDB DOI 均已回填。\n",
              1)

# ---------------------------------------------------------------- §4.1
start = d.index("### 4.1 Structured Abstract")
end = d.index("### 4.2 Declarations")
d = d[:start] + "### 4.1 Structured Abstract（终稿原文；≤350 词）\n\n" + abstract + "\n\n" + d[end:]

# ---------------------------------------------------------------- §4.2
start = d.index("### 4.2 Declarations")
end = d.index("### 4.3 Availability")
block = ["### 4.2 Declarations（终稿原文；8 小节齐全，无占位符）", "", "**Declarations**", ""]
for k, v in dec.items():
    block += ["**" + k + "**", v, ""]
d = d[:start] + "\n".join(block) + "\n" + d[end:]

# ---------------------------------------------------------------- §4.3
start = d.index("### 4.3 Availability")
end = d.index("### 4.4 Additional")
block = (
    "### 4.3 Availability of data and materials（终稿原文）\n\n"
    "> 期刊要求软件/代码给出 Project name / home page / archived version (DOI) / OS / "
    "language / requirements / licence / restrictions 八项；终稿已全部写明。公开数据集与图谱、"
    "GWAS 均在参考文献列表中以 accession / DOI 正式引用。\n\n"
    + dec["Availability of data and materials"] + "\n\n"
)
d = d[:start] + block + d[end:]

# ---------------------------------------------------------------- §4.4
start = d.index("### 4.4 Additional")
end = d.index("### 4.5 List")
rows = ["| File name | File format | Title of data | Description of data |",
        "|---|---|---|---|"]
for n, fmt, tname, desc in af_rows:
    rows.append(f"| Additional file {n} | {fmt} | {tname} | {desc} |")
block = (
    "### 4.4 Additional files 清单（终稿原文，共 6 个）\n\n"
    + "\n".join(rows) + "\n\n"
    "> 每个文件 ≤20 MB，按 \"Additional file 1…\" 连续编号；正文已逐文件显式引用。"
    "禁止只挂个人/科室网站链接。Additional file 6 为本次大修重生成版本（7 表 6 图）。\n\n"
)
d = d[:start] + block + d[end:]

# ---------------------------------------------------------------- §4.6
start = d.index("### 4.6 Figure")
end = d.index("### 4.7 LLM")
block = (
    "### 4.6 Figure title / legend 拆分示例（Fig 1，终稿原文）\n\n"
    f"**Figure title (≤15 words):** {fig1_title}\n\n"
    f"**Legend (≤300 words):** {fig1_legend}\n\n"
    "> Fig 2、Fig 3 与 Graphical Abstract 的图题/图例见终稿 Figure legends 段；"
    "新版 4 张图已全部重画并替换进 .docx，图内不含 \"Figure N\" 字样。\n\n"
)
d = d[:start] + block + d[end:]

# ---------------------------------------------------------------- §4.7
start = d.index("### 4.7 LLM")
end = d.index("\n---\n", start)
block = (
    "### 4.7 LLM 使用披露（终稿 Methods 原文口径）\n\n"
    "**Use of large language models.** Kimi Pro3 (Moonshot AI) was used for language editing "
    "and code-debugging assistance during preparation of this manuscript. All generated content "
    "was checked and verified by the authors, who take full responsibility for the accuracy "
    "and integrity of the work. No large language model is listed as an author.\n\n"
    "> 期刊明文：LLM 目前不满足作者资格；使用须在 Methods 记录。"
)
d = d[:start] + block + d[end:]

# ---------------------------------------------------------------- §6 quick table
d = re.sub(r"\| Title \| .*", "| Title | " + title + " |", d, count=1)
d = re.sub(r"\| Tables \| .*",
           "| Tables | 4（Table 1 逐细胞类型 z；Table 2 队列构成；Table 3 巨噬细胞 module delta；Table 4 样本级主分析） |",
           d, count=1)
d = re.sub(r"\| References \| .*",
           "| References | 32 条，Vancouver [n]，全部经 NCBI 官方书目接口核实；无孤儿条目 |",
           d, count=1)
d = re.sub(r"\| Additional files \| .*",
           "| Additional files | 6 个（Additional_file_1.csv / _2.csv / _3.pdf / _4.zip / _5.csv / _6.docx），每个 ≤20 MB |",
           d, count=1)
d = re.sub(r"\| Funding / COI \| .*",
           "| Funding / COI | National Science and Technology Major Project of the Ministry of Science and Technology of China, grant 2024ZD0527001；funder had no role；authors declare no competing interests |",
           d, count=1)
d = re.sub(r"\| Manuscript \| .*",
           "| Manuscript | 结构化摘要 ≤350 词；Background / Methods / Results / Discussion / Conclusions 齐全；4 表 4 图 |",
           d, count=1)

# ---------------------------------------------------------------- §8 checklist
start = d.index("## 8. 需你确认 / 补齐的清单")
end = d.index("## 9. 数据可靠性说明")
block = (
    "## 8. 需你确认 / 补齐的清单（**已全部解决，仅保留审计痕迹**）\n\n"
    "| 原待办 | 现状 |\n|---|---|\n"
    "| 利益冲突声明 | ✅ 已写 \"The authors declare that they have no competing interests.\" |\n"
    "| 基金名称与编号、funder role | ✅ 2024ZD0527001；funder had no role |\n"
    "| 作者贡献 | ✅ 按你提供的 initials 原文回填 |\n"
    "| 通讯作者 ORCID | ✅ 0000-0002-8554-6138（其他作者 ORCID 如需可在投稿系统补填） |\n"
    "| 伦理口径 | ✅ 写为公开去标识数据二次分析、原始研究已获伦理批准；按你的要求未写具体 IRB 批号 |\n"
    "| LLM 使用情况 | ✅ Methods 单列 Use of large language models，工具名 Kimi Pro3 (Moonshot AI) |\n"
    "| GWAS / 图谱出处与版本 | ✅ OMIX007191-02，GRCh37/hg19，9,797,427 variants；CZ CELLxGENE collection 8f17ac63-aaba-44b5-9b78-60f121da4c2f，dataset 473452ed-3b89-466a-9610-14eb36cbd12c |\n"
    "| GitHub + 归档 DOI | ✅ https://github.com/peterhu9517/aortic-dissection-scDRS-evidence ；10.57760/sciencedb.019x8 |\n"
    "| Licence | ✅ 代码 MIT；共享衍生数据 CC-BY-4.0 |\n"
    "| 大修统计与表述 | ✅ 8 项稳健性分析、样本级主分析、11 基因敏感性、4 图重画、投稿信清理均已完成 |\n\n"
    "**仍需你本人确认的两项**：(i) ScienceDB DOI 目前在 doi.org 仍显示「未注册」，"
    "投稿前请确认记录已审核通过且 DOI 可解析；(ii) 单位是否有 Springer Nature OA 转换协议可减免 APC。\n\n"
)
d = d[:start] + block + d[end:]

open(DOS, "w", encoding="utf-8").write(d)
print("updated:", DOS)
print("title:", title[:90])
print("additional files:", len(af_rows))

# ---------------------------------------------------------------- verify
t = d
for s in ["four of five", "2.3e-102", "[待补]", "[Insert", "[Zenodo DOI]",
          "The genetic substrate of aortic dissection resides", "P approximately 0",
          "[DRAFT", "[tool name"]:
    print(f"  stale {s!r}: {s in t}")
for s in ["10.57760/sciencedb.019x8", "0000-0002-8554-6138", "0.0026",
          "Additional file 6", "Kimi Pro3", "Table S6"]:
    print(f"  required {s!r}: {s in t}")
