#!/usr/bin/env python3
"""Extract title, abstract, and sections 1-3 from PDFs."""

from __future__ import annotations

import argparse
from pathlib import Path

import fitz

from rq_lib import (
    extract_title_and_abstract,
    find_top_sections,
    select_reading_sections,
    slugify,
    write_json,
)


def parse_pdf(pdf_path: Path) -> dict:
    doc = fitz.open(pdf_path)
    pages = [doc.load_page(i).get_text() for i in range(doc.page_count)]
    doc.close()

    head_text = "".join(pages[: min(8, len(pages))])
    full_text = "".join(pages)
    title, abstract = extract_title_and_abstract(head_text)
    sections = find_top_sections(full_text)
    chosen, skip_notes = select_reading_sections(sections)

    return {
        "paper_id": slugify(pdf_path.name),
        "source_pdf": str(pdf_path.resolve()),
        "filename": pdf_path.name,
        "title": title,
        "abstract": abstract,
        "sections_read": [s["header"] for s in chosen],
        "section_texts": {s["header"]: s["text"] for s in chosen},
        "parse_notes": skip_notes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse PDF sections for RQ extraction")
    parser.add_argument("--papers-dir", required=True, help="Folder containing PDF files")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    args = parser.parse_args()

    papers_dir = Path(args.papers_dir)
    output_dir = Path(args.output_dir)
    text_dir = output_dir / "text"
    text_dir.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(papers_dir.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"No PDF files found in {papers_dir}")

    index = []
    for pdf in pdfs:
        parsed = parse_pdf(pdf)
        out_path = text_dir / f"{parsed['paper_id']}.json"
        write_json(out_path, parsed)
        index.append({"paper_id": parsed["paper_id"], "filename": pdf.name, "title": parsed["title"]})
        print(f"[parsed] {pdf.name} -> {out_path.name}")
        for note in parsed["parse_notes"]:
            print(f"  note: {note}")

    write_json(output_dir / "papers_index.json", index)
    print(f"Done. Parsed {len(pdfs)} PDF(s).")


if __name__ == "__main__":
    main()
