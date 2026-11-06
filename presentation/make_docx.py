"""Build the Word report from the Markdown source: presentation/Rapport-CuistoBongo-IA.md.

    uv run python presentation/make_docx.py            # -> Rapport-CuistoBongo-IA.docx

Handles exactly the constructs used by the report: headings, bold/italic/code
inline, tables, bullet and numbered lists, code fences, the cover page, the
figure (courbe-apprentissage.png) and a footer. The PDF is exported from the
.docx with Word (see README of the presentation directory).
"""

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "Rapport-CuistoBongo-IA.md"
TARGET = HERE / "Rapport-CuistoBongo-IA.docx"
FIGURE = HERE / "courbe-apprentissage.png"

INLINE = re.compile(r"(\*\*.+?\*\*|\*[^*\n]+?\*|`[^`\n]+?`)")


def add_runs(paragraph, text):
    """Add runs to a paragraph, honouring **bold**, *italic* and `code`."""
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            run = paragraph.add_run(part[1:-1])
            run.italic = True
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(9.5)
        else:
            paragraph.add_run(part)


def shade(paragraph, color):
    """Light background for a paragraph."""
    element = paragraph._p.get_or_add_pPr()
    shd = element.makeelement(qn("w:shd"), {qn("w:val"): "clear", qn("w:fill"): color})
    element.append(shd)


def add_table(doc, rows):
    """A Markdown table (list of lists of cells) as a Word table."""
    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    table.style = "Table Grid"
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            paragraph = table.rows[r].cells[c].paragraphs[0]
            add_runs(paragraph, cell.strip())
            for run in paragraph.runs:
                run.font.size = Pt(9)
                if r == 0:
                    run.bold = True
    for spacing in (doc.paragraphs[-1].paragraph_format if doc.paragraphs else None,):
        pass
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def add_code_block(doc, lines):
    for i, line in enumerate(lines):
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.left_indent = Cm(0.4)
        run = paragraph.add_run(line if line else " ")
        run.font.name = "Consolas"
        run.font.size = Pt(8.5)
        shade(paragraph, "F2F2F2")
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def main():
    text = SOURCE.read_text(encoding="utf-8")
    doc = Document()

    # Base style: Calibri 11, justified body.
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    for level, size, color in ((1, 16, "1F3864"), (2, 13, "2E5395"), (3, 11.5, "2E5395")):
        style = doc.styles[f"Heading {level}"]
        style.font.name = "Calibri"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)

    # Footer on every page.
    footer = doc.sections[0].footer.paragraphs[0]
    footer.text = "Cuisto Bongo — rapport IA"
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in footer.runs:
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor.from_string("808080")

    lines = text.splitlines()
    i, in_code, code_lines = 0, False, []
    while i < len(lines):
        line = lines[i]

        if line.startswith("```"):
            if in_code:
                add_code_block(doc, code_lines)
                code_lines = []
            in_code = not in_code
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue

        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c.strip()) for c in cells):
                    rows.append(cells)
                i += 1
            add_table(doc, rows)
            continue

        if line.startswith("# "):
            title = line[2:].replace("<u>", "").replace("</u>", "")
            paragraph = doc.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = paragraph.add_run(title)
            run.bold = True
            run.underline = True
            run.font.size = Pt(22)
            run.font.color.rgb = RGBColor.from_string("1F3864")
        elif line.startswith("## "):
            doc.add_heading(line[3:], level=1)
        elif line.startswith("### "):
            doc.add_heading(line[4:], level=2)
        elif line.startswith("#### "):
            paragraph = doc.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_runs(paragraph, line[5:])
            for run in paragraph.runs:
                run.font.size = Pt(13)
        elif line.startswith("- "):
            paragraph = doc.add_paragraph(style="List Bullet")
            add_runs(paragraph, line[2:])
        elif re.match(r"^\d+\. ", line):
            paragraph = doc.add_paragraph(style="List Number")
            add_runs(paragraph, re.sub(r"^\d+\. ", "", line))
        elif line == "---" or not line.strip():
            pass
        elif line.startswith("**Figure"):
            paragraph = doc.add_paragraph()
            add_runs(paragraph, line)
            for run in paragraph.runs:
                run.font.size = Pt(9.5)
                run.italic = True
            if FIGURE.exists():
                picture = doc.add_paragraph()
                picture.alignment = WD_ALIGN_PARAGRAPH.CENTER
                picture.add_run().add_picture(str(FIGURE), width=Cm(16.5))
        elif line.startswith("**Tableau"):
            paragraph = doc.add_paragraph()
            add_runs(paragraph, line)
        else:
            paragraph = doc.add_paragraph()
            add_runs(paragraph, line)
        i += 1

    doc.save(TARGET)
    print(f"{TARGET} ({TARGET.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    sys.exit(main())
