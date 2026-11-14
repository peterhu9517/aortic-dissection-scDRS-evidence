"""Restore the formal ScienceDB DOI across the whole submission package once the
DOI actually resolves, and refresh the cover-letter date to the real submission
day.

Background
----------
The current submission files deliberately avoid claiming a registered DOI
(DataCite still returned HTTP 404 for 10.57760/sciencedb.019x8 on 2026-11-14
09:21, because the ScienceDB publication request had only just been resubmitted).
They instead use the verifiable GitHub repository + the versioned code snapshot
supplied as Additional file 4, with ScienceDB noted as "DOI activation pending".

The user asked to wait until the ScienceDB record is approved later today and
only then send the manuscript. This script is the single command to run at that
moment.

Usage
-----
    python activate_doi.py --status    # only check DataCite, change nothing
    python activate_doi.py             # check DataCite, then restore DOI + date
    python activate_doi.py --force     # skip the online check (offline use)

It is idempotent: running it twice is harmless.
"""
import os
import re
import sys
import json
import datetime
import subprocess
import urllib.request
import urllib.error
from docx import Document

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56"
PIPE = os.path.join(ROOT, "scdrs_pipeline")
ST = os.path.join(ROOT, "output", "aortic_dissection_manuscript", "stage3")
KIT = os.path.join(ROOT, "output", "aortic_dissection_manuscript", "submission_kit")
DOI = "10.57760/sciencedb.019x8"

M_MD = os.path.join(ST, "Genome_Medicine_Full_Manuscript.md")
M_DOCX = os.path.join(ST, "Genome_Medicine_Full_Manuscript.docx")
C_MD = os.path.join(KIT, "Cover_Letter_Genome_Medicine.md")
D_MD = os.path.join(KIT, "Submission_Dossier_Genome_Medicine.md")
G_MD = os.path.join(ROOT, "代码归档与注册指南.md")
R_MD = os.path.join(ROOT, "github_repo", "README.md")

_t = datetime.date.today()
TODAY = f"{_t.day} {_t.strftime('%B %Y')}"
DATE_RE = re.compile(r"\b\d{1,2} [A-Z][a-z]+ 20\d{2}\b")

PENDING_M = ("archived version: a versioned snapshot of the complete analysis "
             "code is supplied as Additional file 4, and the repository is "
             "additionally deposited in ScienceDB (record 019x8; DOI activation "
             "pending);")
ACTIVE_M = f"archived version: {DOI};"

PENDING_C = ("; a versioned snapshot of the complete analysis code is supplied "
             "as Additional file 4, and the repository has been deposited in "
             "ScienceDB (record 019x8; DOI activation pending and to be supplied "
             "before publication).")
ACTIVE_C = f" and is archived with a permanent DOI ({DOI})."

PENDING_R = ("**Archival deposit:** ScienceDB record 019x8 (DOI activation "
             "pending). A versioned snapshot of the complete analysis code is "
             "supplied with the manuscript as Additional file 4.")
ACTIVE_R = f"**Archived DOI:** {DOI} (ScienceDB)"

PAIRS_G = [
    ("| 归档 DOI | `10.57760/sciencedb.019x8`（ScienceDB；Zenodo 国内不可达，故改用此路径） "
     "| ⚠️ 2026-11-13 实测未注册；**已从投稿文件移除「已注册」声称**，待激活后回填 |",
     f"| 归档 DOI | `{DOI}`（ScienceDB；Zenodo 国内不可达，故改用此路径） | ✅ 已激活并回填 |"),
    ("6. **当前状态**：该 DOI 实测未注册，因此本轮已把正文 `archived version:` 字段与 "
     "Cover Letter 改成「GitHub 仓库 + 随稿 Additional file 4 版本快照 + ScienceDB 记录 019x8"
     "（DOI 待激活）」，不再声称已有永久 DOI；稿件因此不依赖该 DOI 也可合规投稿。"
     "待 DOI 真正激活后，运行 `scdrs_pipeline/activate_doi.py` 一键回填。",
     f"6. **当前状态**：ScienceDB 记录已审核通过，DOI `{DOI}` 可解析，并已回填到正文 "
     f"**Availability of data and materials** 段（`archived version: {DOI};`）以及 Cover Letter。"),
    ("- `archived version:` 字段目前写的是 GitHub + Additional file 4 版本快照 + "
     "ScienceDB 记录 019x8（DOI 待激活）；激活后运行 `scdrs_pipeline/activate_doi.py` 回填",
     f"- `archived version: {DOI};`（已由 `activate_doi.py` 回填）"),
]

PAIRS_D = [
    ("| GitHub + 代码归档 | ✅ https://github.com/peterhu9517/"
     "aortic-dissection-scDRS-evidence ；版本快照随稿作为 Additional file 4 提交；"
     "ScienceDB 记录 019x8 的 DOI 待激活 |",
     f"| GitHub + 归档 DOI | ✅ https://github.com/peterhu9517/"
     f"aortic-dissection-scDRS-evidence ；{DOI} |"),
]


def doi_live():
    """Return 'live', 'absent' (HTTP 404) or 'unknown' (network unavailable)."""
    url = f"https://api.datacite.org/dois/{DOI}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "WorkBuddy/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            body = json.loads(r.read().decode("utf-8"))
            return "live" if (r.status == 200 and "data" in body) else "unknown"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("  DataCite: HTTP 404 - record not registered yet")
            return "absent"
        print(f"  DataCite: HTTP {e.code}")
        return "unknown"
    except Exception as e:
        print(f"  DataCite check unavailable: {type(e).__name__}: {e}")
        return "unknown"


if "--check-anchors" in sys.argv:
    print("  Dry-run: verify every replacement anchor exists in the current files")
    todo_prefix = "1. ⚠️ **ScienceDB DOI `10.57760/sciencedb.019x8` 实测未注册**"
    checks = [
        (M_MD, [PENDING_M]),
        (C_MD, [PENDING_C]),
        (D_MD, [PENDING_M] + [p[0] for p in PAIRS_D]),
        (G_MD, [p[0] for p in PAIRS_G]),
        (R_MD, [PENDING_R]),
    ]
    bad = 0
    for path, olds in checks:
        s = open(path, encoding="utf-8").read()
        for old in olds:
            n = s.count(old)
            print(f"    {os.path.basename(path):44s} {n} x {old[:44]}")
            if n == 0:
                bad += 1
    todo_ok = any(l.startswith(todo_prefix)
                  for l in open(D_MD, encoding="utf-8"))
    print(f"    dossier todo line: {todo_ok}")
    if not todo_ok:
        bad += 1
    print("  anchors missing:", bad)
    sys.exit(1 if bad else 0)

if "--status" in sys.argv:
    state = doi_live()
    label = {"live": "REGISTERED", "absent": "NOT registered yet (HTTP 404)",
             "unknown": "cannot verify (network unavailable)"}[state]
    print(f"  {DOI} -> {label}")
    print("  Pending wording still in manuscript: "
          f"{'DOI activation pending' in open(M_MD, encoding='utf-8').read()}")
    sys.exit(0)

state = "skipped" if "--force" in sys.argv else doi_live()
if state == "skipped":
    print("  --force: skipping the online DataCite check")
elif state == "absent":
    print(f"\n  {DOI} is still NOT registered. Nothing was changed.")
    print("  The ScienceDB record is probably still under review. Wait for the")
    print("  approval mail, verify https://doi.org/" + DOI + " resolves, then run")
    print("  this script again. The manuscript is already submittable in its")
    print("  DOI-independent state, so this is not a blocker in the meantime.")
    sys.exit(1)
elif state == "unknown":
    print("\n  Could not reach DataCite from this machine, so the DOI status is")
    print("  UNKNOWN (this is a network issue, NOT evidence of a 404). Nothing")
    print("  was changed. If you have confirmed in a browser that")
    print("  https://doi.org/" + DOI + " resolves, run:")
    print("      python activate_doi.py --force")
    print("  Otherwise retry later; the package stays submittable meanwhile.")
    sys.exit(1)
else:
    print(f"  DataCite record found for {DOI}")


def patch_text(path, pairs, refresh_date=False):
    s = open(path, encoding="utf-8").read()
    orig = s
    for old, new in pairs:
        n = s.count(old)
        if n:
            s = s.replace(old, new)
            print(f"  {os.path.basename(path)}: {n} x {old[:46]}...")
        elif new in s:
            print(f"  {os.path.basename(path)}: already active")
        else:
            print(f"  {os.path.basename(path)}: anchor absent (skipped) {old[:46]}...")
    if refresh_date:
        found = sorted(set(DATE_RE.findall(s)))
        s = DATE_RE.sub(TODAY, s)
        print(f"  {os.path.basename(path)}: dates {found} -> {TODAY}")
    if s != orig:
        open(path, "w", encoding="utf-8", newline="").write(s)


def replace_line(path, prefix, new_line):
    lines = open(path, encoding="utf-8").read().split("\n")
    hit = 0
    for i, l in enumerate(lines):
        if l.startswith(prefix):
            lines[i] = new_line
            hit += 1
    if hit:
        open(path, "w", encoding="utf-8", newline="").write("\n".join(lines))
    print(f"  {os.path.basename(path)}: {hit} todo line(s) rewritten")


def patch_docx_paragraphs(path, pairs):
    d = Document(path)
    changed = 0
    for p in d.paragraphs:
        t = p.text
        new = t
        for old, repl in pairs:
            new = new.replace(old, repl)
        if new != t:
            if p.runs:
                p.runs[0].text = new
                for r in p.runs[1:]:
                    r.text = ""
            else:
                p.add_run(new)
            changed += 1
    if changed:
        try:
            d.save(path)
            print(f"  {os.path.basename(path)}: {changed} paragraph(s) updated")
        except PermissionError:
            print(f"  ERROR: {os.path.basename(path)} is locked by the local preview.")
            print("  Close the preview and re-run activate_doi.py; markdown sources")
            print("  were already updated, so the rebuild is safe to repeat.")
            sys.exit(2)
    else:
        print(f"  {os.path.basename(path)}: no change (already active)")


print("\nPATCH markdown sources")
patch_text(M_MD, [(PENDING_M, ACTIVE_M)])
patch_text(C_MD, [(PENDING_C, ACTIVE_C)], refresh_date=True)
patch_text(D_MD, [(PENDING_M, ACTIVE_M)] + PAIRS_D, refresh_date=True)
patch_text(G_MD, PAIRS_G)
patch_text(R_MD, [(PENDING_R, ACTIVE_R)])
replace_line(
    D_MD, "1. ⚠️ **ScienceDB DOI `10.57760/sciencedb.019x8` 实测未注册**",
    f"1. ✅ **ScienceDB DOI `{DOI}` 已激活并回填**（{TODAY}）：正文 `archived version:` "
    "字段与 Cover letter 均已写入正式 DOI，DataCite 记录可解析。投稿前请确认 ScienceDB "
    "记录中挂载的是最新版 `scidb_upload.zip`（含全部大修脚本），因为 DOI 发布后快照即冻结。")

print("\nPATCH manuscript Word")
patch_docx_paragraphs(M_DOCX, [(PENDING_M, ACTIVE_M)])

print("\nREBUILD cover letter / dossier / archives / bundle / audit")
for script in ["build_cover_letter.py", "build_dossier_docx.py",
               "refresh_archives.py", "bundle_build.py", "final_check.py"]:
    r = subprocess.run([sys.executable, script], cwd=PIPE,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    tail = [x for x in (r.stdout or "").strip().split("\n") if x.strip()][-2:]
    print(f"  {script}: rc={r.returncode} | " + " | ".join(tail))
    if r.returncode != 0:
        print((r.stderr or "")[:800])

print(f"\nDONE. {DOI} should now appear in the manuscript, cover letter, dossier, "
      "guide and README.")
print(f"Cover-letter date set to {TODAY} (the day the package was finalised).")
print("Before clicking Submit: confirm the ScienceDB record contains the LATEST")
print("scidb_upload.zip / Additional_file_4.zip, otherwise the DOI snapshot will")
print("freeze the pre-revision code.")
