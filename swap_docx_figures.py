"""Replace the four embedded figures in the final Genome Medicine manuscript
with the revised versions drawn by revision_figures.py.

Mapping (verified against the document's image relationships):
  rId5 -> graphical_abstract.png
  rId6 -> fig1.png
  rId7 -> fig2.png
  rId8 -> fig3.png

The display width is preserved; the height is recomputed from the new PNG's
aspect ratio so no image is stretched.
"""
import os
from docx import Document
from docx.oxml.ns import qn
from PIL import Image

ROOT = "C:/Users/胡行健/WorkBuddy/2026-11-10-09-05-56"
DOCX = os.path.join(ROOT, "output", "aortic_dissection_manuscript", "stage3",
                    "Genome_Medicine_Full_Manuscript.docx")
FIGDIR = os.path.join(ROOT, "scdrs_pipeline", "revision_out", "figures")

MAP = {
    "rId5": "graphical_abstract.png",
    "rId6": "fig1.png",
    "rId7": "fig2.png",
    "rId8": "fig3.png",
}

doc = Document(DOCX)

# --- index every inline drawing by its blip rId ---------------------------
drawings = {}
for blip in doc.element.body.iter(qn("a:blip")):
    rid = blip.get(qn("r:embed"))
    if not rid:
        continue
    drawings.setdefault(rid, []).append(blip)

for rid, fname in MAP.items():
    path = os.path.join(FIGDIR, fname)
    with open(path, "rb") as fh:
        blob = fh.read()
    with Image.open(path) as im:
        w, h = im.size
    rel = doc.part.rels[rid]
    part = rel.target_part
    old_n = len(part.blob)
    part._blob = blob

    for blip in drawings.get(rid, []):
        inline = None
        for anc in blip.iterancestors():
            if anc.tag == qn("wp:inline"):
                inline = anc
                break
        if inline is None:
            continue
        extent = inline.find(qn("wp:extent"))
        cx = int(extent.get("cx"))
        cy = int(round(cx * h / w))
        extent.set("cy", str(cy))
        # keep the picture transform in sync with the outer extent
        for xfrm_ext in inline.iter(qn("a:ext")):
            if xfrm_ext.get("cx") is not None:
                xfrm_ext.set("cx", str(cx))
                xfrm_ext.set("cy", str(cy))

    print(f"{rid} <- {fname}: {w}x{h}px, {old_n} -> {len(blob)} bytes")

doc.save(DOCX)
print("saved:", DOCX)

# --- verify ---------------------------------------------------------------
chk = Document(DOCX)
for rid, fname in MAP.items():
    with open(os.path.join(FIGDIR, fname), "rb") as fh:
        expect = fh.read()
    actual = chk.part.rels[rid].target_part.blob
    print(f"verify {rid}: {'OK' if actual == expect else 'MISMATCH'} ({len(actual)} bytes)")
