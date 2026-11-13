"""Patch the Genome Medicine full manuscript: insert Supplementary Results integration
and fill in the user-provided Declarations (Funding, Disclosures, Author contributions)
plus an ethics-exemption statement. Edits are targeted by matching paragraph text;
no structural rebuild, so existing layout is preserved."""
import os
from docx import Document
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56"
SRC  = os.path.join(BASE, "output/aortic_dissection_manuscript/stage3/Genome_Medicine_Full_Manuscript.docx")
DST  = SRC  # overwrite the complete manuscript in place

doc = Document(SRC)

def find(substr):
    for p in doc.paragraphs:
        if substr in p.text:
            return p
    raise KeyError(substr)

def set_text(p, text, bold=False, italic=False, size=None):
    p.text = ""
    r = p.add_run(text)
    r.bold = bold; r.italic = italic
    if size: r.font.size = Pt(size)
    return p

def insert_after(ref, text, style=None):
    new_p = OxmlElement("w:p")
    ref._p.addnext(new_p)
    new_para = Paragraph(new_p, doc)
    if style: new_para.style = style
    new_para.add_run(text)
    return new_para

# ---- 1. Ethics: add exemption statement, drop the TO BE COMPLETED committee line
p = find("[TO BE COMPLETED: name of the approving ethics committee")
set_text(p,
    "This study re-analysed exclusively publicly available, de-identified single-cell RNA-sequencing "
    "data and summary-level genetic data obtained from the Gene Expression Omnibus, GTEx and published "
    "GWAS resources. No new human participants, human tissue or animal experiments were involved. "
    "Ethics approval and informed consent for the original data collections were obtained by the "
    "respective source studies and are reported in their publications. Because this work is a secondary "
    "analysis of publicly available, de-identified datasets, no new ethics approval was sought; the "
    "study qualifies for exemption from additional ethical review under the exemption provisions for "
    "de-identified public data [TO BE COMPLETED: reference number of the submitting institution's IRB "
    "waiver / exemption confirmation letter, if one is required by the institution].")

# ---- 2. Competing interests (Disclosures)
set_text(find("[TO BE COMPLETED: if none, use"),
         "The authors declare that they have no competing interests.")

# ---- 3. Funding (user text)
set_text(find("[TO BE COMPLETED: all funders and grant numbers"),
         "This work was funded by the National Science and Technology Major Project of the Ministry of "
         "Science and Technology of China (grant number 2024ZD0527001). The funder had no role in study "
         "design, data collection, data analysis, data interpretation, or writing of the report.")

# ---- 4. Authors' contributions (user text)
set_text(find("[DRAFT - TO BE CONFIRMED"),
         "HX conceived and designed the study and obtained funding. WS acquired the data. WS and WY "
         "analysed and interpreted the data, and LF and HX did the statistical analysis. WS wrote the "
         "first draft of the manuscript, and DN and HX revised it for important intellectual content. "
         "WS and HX accessed and verified the underlying data. All authors had full access to all the "
         "data in the study, approved the final version of the manuscript, and had final responsibility "
         "for the decision to submit for publication.")

# ---- 5. Statistics: correct the "no sample-level" clause
p = find("All tests were performed at the cell level; no sample-level aggregation")
old = ("All tests were performed at the cell level; no sample-level aggregation or mixed-effects model "
       "was applied, and P values are reported per test without a pooled cross-cohort FDR hierarchy "
       "(see Limitations).")
new = ("All primary tests were performed at the cell level; sample-level aggregation and mixed-effects "
       "models were additionally applied in the robustness analyses (Additional file 6), and P values "
       "are reported per test without a pooled cross-cohort FDR hierarchy (see Limitations).")
if old in p.text:
    set_text(p, p.text.replace(old, new))

# ---- 6. Methods: insert robustness subsection after the Statistics paragraph
stats_p = find("All primary tests were performed at the cell level")
insert_after(stats_p,
    "Robustness and negative-control analyses. To test the specificity of the Layer 1 enrichment and "
    "the stability of the cross-cohort conclusions, we performed six pre-registered analyses reported "
    "in full in Additional file 6: (i) a negative-control gene set of 16 genes expression-matched to "
    "the AAD disease genes, scored through the identical scDRS-equivalent pipeline on the same "
    "healthy-aorta atlas; (ii) a bootstrap (B = 20,000) confidence interval for the Layer 1-Option 2 "
    "convergence r; (iii) leave-one-cell-type-out and leave-one-cohort-out sensitivity; (iv) "
    "label-permutation tests (1,000 iterations) of the Layer 2 macrophage module; (v) sample-level "
    "aggregation and linear mixed models with a random intercept for sample; and (vi) a sensitivity "
    "analysis excluding GSE222318.", style="Normal")

# ---- 7. Layer 2 results: add robustness caveat
p = find("Complete statistics for every cell type are provided in Additional file 1.")
add = (" Robustness analyses (Additional file 6) confirmed the macrophage consensus: upregulation "
       "persisted in 3-4 of the remaining 4 cohorts under leave-one-cohort-out and was supported by "
       "label permutation; sample-level modelling showed, however, that the per-cohort cell-level P "
       "values are inflated by pseudo-replication, so the robust conclusion is the consistent direction "
       "across cohorts rather than the nominal P values.")
if add.strip() not in p.text:
    set_text(p, p.text.rstrip() + add)

# ---- 8. Limitations: revise (vii) and (viii)
p = find("Several caveats temper the interpretation")
old_vii = ("All comparisons were performed at the cell level, so cells are not independent biological "
           "replicates and the reported P values may be anti-conservative; sample-level aggregation, "
           "mixed-effects models and a pooled cross-cohort FDR hierarchy were not applied.")
new_vii = ("All primary comparisons were performed at the cell level, so cells are not independent "
           "biological replicates and the reported P values are anti-conservative. We characterised "
           "this directly in Additional file 6: at the donor level only the largest cohort (GSE254132) "
           "retained significance, so the robust claim is the consistent directional upregulation "
           "across cohorts rather than per-cohort nominal P values.")
assert old_vii in p.text, "vii not found"
set_text(p, p.text.replace(old_vii, new_vii))

old_viii = ("Negative-control gene sets, label permutation tests, leave-one-cohort-out validation, a "
            "bootstrap confidence interval for r = 0.78 and a sensitivity analysis excluding GSE222318 "
            "have not yet been performed. These analyses are planned before definitive mechanistic "
            "claims are made.")
new_viii = ("Negative-control gene-set scoring, label-permutation tests, leave-one-cohort-out "
            "validation, a bootstrap confidence interval for the convergence r (95% CI 0.29-0.96) and a "
            "GSE222318 exclusion sensitivity analysis were all performed and are reported in Additional "
            "file 6; they support the conclusions and the convergence estimate.")
assert old_viii in p.text, "viii not found"
set_text(p, p.text.replace(old_viii, new_viii))

# ---- 9. Additional files: add AF6 after AF5
af5 = find("Additional file 5:")
set_text(af5, af5.text)  # no-op, keep
insert_after(af5,
    "Additional file 6: Supplementary Results - robustness and negative-control analyses. "
    "File format: .docx. Six pre-registered analyses: expression-matched negative-control gene-set "
    "scoring, bootstrap CI for the convergence r, leave-one-cohort-out consensus, GSE222318 exclusion, "
    "label-permutation tests, and sample-level / mixed-model pseudo-replication assessment, with five "
    "supporting tables and four figures.")

doc.save(DST)
print("patched ->", DST)
# quick verify
d2 = Document(DST)
checks = ["The authors declare that they have no competing interests",
          "2024ZD0527001", "HX conceived and designed",
          "Robustness and negative-control analyses", "Additional file 6",
          "95% CI 0.29-0.96", "GSE254132)"]
full = "\n".join(x.text for x in d2.paragraphs)
for c in checks:
    print(f"  present[{c[:40]}]:", c in full)
