from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class PdfLine:
    text: str
    font: str = "regular"
    size: int = 10
    gap: int = 14


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
MARGIN_X = 54
TOP_Y = 724
BOTTOM_Y = 58


def generate_document_pdf(title: str, subtitle: str, body: str) -> bytes:
    lines = _layout_lines(title, subtitle, body)
    pages: list[list[PdfLine]] = []
    current: list[PdfLine] = []
    y = TOP_Y
    for line in lines:
        if y - line.gap < BOTTOM_Y:
            pages.append(current)
            current = []
            y = TOP_Y
        current.append(line)
        y -= line.gap
    if current:
        pages.append(current)

    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [%s] /Count %d >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
    ]

    page_object_numbers = []
    content_object_numbers = []
    next_object = 5
    for _ in pages:
        page_object_numbers.append(next_object)
        content_object_numbers.append(next_object + 1)
        next_object += 2

    rendered_pages: list[bytes] = []
    rendered_contents: list[bytes] = []
    for page_index, page_lines in enumerate(pages):
        content = _render_page(page_lines, page_index + 1, len(pages))
        rendered_contents.append(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content))
        rendered_pages.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
                f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
                f"/Contents {content_object_numbers[page_index]} 0 R >>"
            ).encode("latin-1")
        )

    objects[1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (
        b" ".join(f"{number} 0 R".encode("latin-1") for number in page_object_numbers),
        len(page_object_numbers),
    )

    for page, content in zip(rendered_pages, rendered_contents, strict=True):
        objects.append(page)
        objects.append(content)

    return _build_pdf(objects)


def _layout_lines(title: str, subtitle: str, body: str) -> list[PdfLine]:
    lines: list[PdfLine] = [PdfLine(_clean(title), "bold", 18, 24)]
    if subtitle:
        lines.extend(_wrap(_clean(subtitle), 76, "regular", 10, 18))
    lines.append(PdfLine("", "regular", 10, 12))

    for raw_line in body.splitlines():
        line = _clean(raw_line)
        if not line:
            lines.append(PdfLine("", "regular", 10, 8))
            continue
        if line.startswith("# "):
            lines.extend(_wrap(line[2:], 54, "bold", 16, 22))
        elif line.startswith("## "):
            lines.append(PdfLine("", "regular", 10, 8))
            lines.extend(_wrap(line[3:].upper(), 64, "bold", 11, 17))
        elif line.startswith("- "):
            lines.extend(_wrap("- " + line[2:], 86, "regular", 10, 14))
        else:
            lines.extend(_wrap(line, 88, "regular", 10, 14))
    return lines


def _wrap(text: str, width: int, font: str, size: int, gap: int) -> list[PdfLine]:
    words = text.split()
    if not words:
        return [PdfLine("", font, size, gap)]
    lines: list[PdfLine] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(PdfLine(current, font, size, gap))
            current = word
    if current:
        lines.append(PdfLine(current, font, size, gap))
    return lines


def _render_page(lines: list[PdfLine], page_number: int, page_count: int) -> bytes:
    commands = [
        "0.96 0.97 0.94 rg 0 0 612 792 re f",
        "0.08 0.13 0.11 rg 0 752 612 40 re f",
        "0.84 0.27 0.14 rg 54 736 96 4 re f",
        "1 1 1 rg BT /F2 9 Tf 54 766 Td (JOBHUNTER AI) Tj ET",
        "0.11 0.18 0.16 rg",
    ]
    y = TOP_Y
    for line in lines:
        if line.text:
            font = "F2" if line.font == "bold" else "F1"
            commands.append(f"BT /{font} {line.size} Tf {MARGIN_X} {y} Td ({_escape_pdf(line.text)}) Tj ET")
        y -= line.gap
    commands.append(f"0.35 0.39 0.36 rg BT /F1 8 Tf 276 30 Td (Page {page_number} of {page_count}) Tj ET")
    return "\n".join(commands).encode("latin-1", "replace")


def _build_pdf(objects: list[bytes]) -> bytes:
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("latin-1"))
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    output.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("latin-1")
    )
    return bytes(output)


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text.replace("–", "-").replace("—", "-").replace("’", "'").replace("“", '"').replace("”", '"')


def _escape_pdf(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
