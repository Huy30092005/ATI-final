"""Export a chat answer (Markdown text + evidence list) to PDF, DOCX, Markdown, HTML or BibTeX."""

import io
import re
import html
from typing import List, Dict, Any


def _ref_line(idx: int, ev: Dict[str, Any]) -> str:
    authors = ", ".join(ev.get("authors") or []) or "Unknown"
    year = ev.get("year") or "n.d."
    url = ev.get("url") or ""
    return f"[{idx}] {authors} ({year}). {ev.get('title', 'Untitled')}. {url}".strip()


def to_markdown(title: str, content: str, evidence: List[Dict[str, Any]]) -> bytes:
    refs = "\n".join(_ref_line(i, e) for i, e in enumerate(evidence, 1))
    return f"# {title}\n\n{content}\n\n## References\n{refs}\n".encode("utf-8")


def to_html(title: str, content: str, evidence: List[Dict[str, Any]]) -> bytes:
    # Everything user/LLM/web-derived is escaped
    refs = "".join(f"<li>{html.escape(_ref_line(i, e)[len(f'[{i}] '):])}</li>" for i, e in enumerate(evidence, 1))
    page = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f"<title>{html.escape(title)}</title>"
        "<style>body{font-family:sans-serif;line-height:1.6;max-width:800px;margin:40px auto;padding:0 20px}</style>"
        f"</head><body><h1>{html.escape(title)}</h1>"
        f'<pre style="white-space:pre-wrap;font-family:inherit">{html.escape(content)}</pre>'
        f"<h2>References</h2><ol>{refs}</ol></body></html>"
    )
    return page.encode("utf-8")


def _bib_escape(value: str) -> str:
    return re.sub(r"[{}\\]", "", value or "")


def to_bibtex(evidence: List[Dict[str, Any]]) -> bytes:
    entries = []
    for i, e in enumerate(evidence, 1):
        authors = " and ".join(_bib_escape(a) for a in (e.get("authors") or [])) or "Anonymous"
        entries.append(
            f"@misc{{cite_{i},\n  title = {{{_bib_escape(e.get('title', ''))}}},\n"
            f"  author = {{{authors}}},\n  year = {{{e.get('year') or 'n.d.'}}},\n"
            f"  url = {{{_bib_escape(e.get('url') or '')}}}\n}}"
        )
    return "\n\n".join(entries).encode("utf-8")


def to_docx(title: str, content: str, evidence: List[Dict[str, Any]]) -> bytes:
    from docx import Document

    doc = Document()
    doc.add_heading(title, level=0)
    for block in re.split(r"\n{2,}", content.strip()):
        block = block.strip()
        m = re.match(r"^(#{1,3})\s+(.*)", block)
        if m:
            doc.add_heading(m.group(2), level=len(m.group(1)))
        else:
            doc.add_paragraph(block)
    if evidence:
        doc.add_heading("References", level=1)
        for i, e in enumerate(evidence, 1):
            doc.add_paragraph(_ref_line(i, e))
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def to_pdf(title: str, content: str, evidence: List[Dict[str, Any]]) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    styles = getSampleStyleSheet()
    esc = lambda t: html.escape(t).replace("\n", "<br/>")  # reportlab paragraphs use XML-ish markup
    story = [Paragraph(esc(title), styles["Title"]), Spacer(1, 12)]
    for block in re.split(r"\n{2,}", content.strip()):
        block = block.strip()
        m = re.match(r"^(#{1,3})\s+(.*)", block)
        story.append(Paragraph(esc(m.group(2)), styles["Heading2"]) if m else Paragraph(esc(block), styles["BodyText"]))
        story.append(Spacer(1, 6))
    if evidence:
        story.append(Paragraph("References", styles["Heading2"]))
        for i, e in enumerate(evidence, 1):
            story.append(Paragraph(esc(_ref_line(i, e)), styles["BodyText"]))
    buf = io.BytesIO()
    SimpleDocTemplate(buf, pagesize=A4).build(story)
    return buf.getvalue()


EXPORTERS = {
    "md": ("text/markdown", to_markdown),
    "html": ("text/html", to_html),
    "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", to_docx),
    "pdf": ("application/pdf", to_pdf),
}
