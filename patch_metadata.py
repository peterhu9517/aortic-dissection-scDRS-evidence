# patch_metadata.py
# Fill the source-accession / GWAS / LLM / acknowledgement / ethics placeholders in the
# Genome Medicine full manuscript using information retrieved from the data-collection record.
from docx import Document
from docx.oxml.ns import qn
from copy import deepcopy

DOCX = r"output/aortic_dissection_manuscript/stage3/Genome_Medicine_Full_Manuscript.docx"
d = Document(DOCX)


def set_text(p, text):
    """Replace paragraph content with text, preserving paragraph style."""
    # clear existing runs
    for r in list(p._p.findall(qn('w:r'))):
        p._p.remove(r)
    p.add_run(text)


# --- [18] healthy-aorta reference + GWAS source -----------------------------
p18 = d.paragraphs[18]
p18_text = (
    "The healthy-aorta reference comprised 57,999 aortic cells subset from the published "
    "human arterial vasculature single-cell atlas (Zhao et al. [31]; CZ CELLxGENE Discover "
    "collection 8f17ac63-aaba-44b5-9b78-60f121da4c2f, dataset version "
    "473452ed-3b89-466a-9610-14eb36cbd12c), uniformly processed and annotated into eight "
    "cell types: smooth muscle, fibroblast, microvasculature, endothelial (two states), "
    "macrophage, lymphocyte, and an uncharacterised cluster. GWAS summary statistics for "
    "aortic aneurysm and dissection were obtained as OMIX007191-02 (9,797,427 variants; "
    "genome build GRCh37/hg19; Du et al. [32]) from the National Genomics Data Center "
    "(NGDC), China National Center for Bioinformation; gene coordinates were taken from the "
    "UCSC ensGene annotation for hg19."
)
set_text(p18, p18_text)

# --- [33] LLM disclosure ----------------------------------------------------
set_text(d.paragraphs[33],
         "During preparation of this manuscript, Kimi Pro3 (Moonshot AI) was used for "
         "language editing and for assistance with code debugging. All generated text and "
         "code were checked and verified by the authors, who take full responsibility for "
         "the accuracy and integrity of the analyses, results and conclusions. No large "
         "language model is listed as an author.")

# --- [71] Ethics: drop the IRB-waiver placeholder ---------------------------
set_text(d.paragraphs[71],
         "This study re-analysed exclusively publicly available, de-identified single-cell "
         "RNA-sequencing data and summary-level genetic data obtained from the Gene "
         "Expression Omnibus, GTEx and published GWAS resources. No new human participants, "
         "human tissue or animal experiments were involved. Ethics approval and informed "
         "consent for the original data collections were obtained by the respective source "
         "studies and are reported in their publications. Because this work is a secondary "
         "analysis of publicly available, de-identified datasets, no new ethics approval was "
         "sought; the study qualifies for exemption from additional ethical review under the "
         "exemption provisions for de-identified public data.")

# --- [75] Availability of data and materials ---------------------------------
p75 = (
    "The datasets supporting the conclusions of this article are available in the NCBI Gene "
    "Expression Omnibus repository under accession numbers GSE213740, GSE155468, GSE224559, "
    "GSE226492, GSE254132 and GSE222318; each is formally cited with its accession number in "
    "the reference list. The AAD GWAS summary statistics (OMIX007191-02; 9,797,427 variants; "
    "genome build GRCh37/hg19) are available at the National Genomics Data Center (NGDC), "
    "China National Center for Bioinformation, under OMIX accession OMIX007191 "
    "(https://ngdc.cncb.ac.cn/omix) [32]. The healthy human arterial vasculature "
    "single-cell atlas used as the reference comprises 57,999 aortic cells subset from the "
    "CZ CELLxGENE Discover collection 8f17ac63-aaba-44b5-9b78-60f121da4c2f (dataset version "
    "473452ed-3b89-466a-9610-14eb36cbd12c) [31]. The derived cross-dataset statistics, "
    "verified sample-to-condition map, supplementary figures, analysis scripts and "
    "cohort-level QC summary are included in this article as Additional files 1-6. Project "
    "name: tri-level single-cell evidence chain for aortic dissection; project home page: "
    "[TO BE COMPLETED: GitHub repository URL, e.g., https://github.com/<user>/<repo>]; "
    "archived version: [TO BE COMPLETED: Zenodo DOI, e.g., 10.5281/zenodo.XXXXXXX]; "
    "operating system: Microsoft Windows; programming language: Python 3.13; other "
    "requirements: scDRS 1.0.2, Scanpy 1.12.5, AnnData 0.13.4, SciPy, pandas, NumPy, "
    "Matplotlib; licence: [TO BE COMPLETED: recommended MIT for code and CC-BY-4.0 for "
    "processed data]; any restrictions to use by non-academics: none."
)
set_text(d.paragraphs[75], p75)

# --- [83] Acknowledgements -> Not applicable ---------------------------------
set_text(d.paragraphs[83], "Not applicable.")

# --- Append references [31] and [32] after the last reference [30] (idx 116) -
from docx.oxml import OxmlElement
ref31 = ("[31] Zhao Q, Pedroza A, Sharma D, Gu W, Dalal A, Weldy C, et al. A cell and "
         "transcriptome atlas of human arterial vasculature. Cell Genomics. 2025;5(12):101034. "
         "doi:10.1016/j.xgen.2025.101034. PMID:41086809.")
ref32 = ("[32] Du Y, Guan Y, Shao Z, Jiang M, Qu M, Kong Y, et al. Integrative genome-wide "
         "association meta-analysis of aortic aneurysm and dissection identifies five novel "
         "genes. Genomics Proteomics Bioinformatics. 2025;23(5):qzaf039. "
         "doi:10.1093/gpbjnl/qzaf039.")


def make_ref_para(src_el, text):
    new_p = OxmlElement('w:p')
    ppr = src_el.find(qn('w:pPr'))
    if ppr is not None:
        new_p.append(deepcopy(ppr))
    run = OxmlElement('w:r')
    t = OxmlElement('w:t')
    t.set(qn('xml:space'), 'preserve')
    t.text = text
    run.append(t)
    new_p.append(run)
    return new_p


anchor = d.paragraphs[116]._p
for ref in (ref31, ref32):
    new_p = make_ref_para(anchor, ref)
    anchor.addnext(new_p)
    anchor = new_p

d.save(DOCX)
print("patched:", DOCX)
