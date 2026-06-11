#!/usr/bin/env python3
"""Load a CSV of paper metadata and generate output_dir/text/*.json files.

Expected CSV columns (3 columns, Chinese or English headers):
    题目, 作者, 摘要
or:
    title, author, abstract

Each row = one paper. The generated text/*.json files are in the same
format that extract_questions.py expects, so the DeepSeek extraction
pipeline can consume them directly.

Unlike the old parse_csv_input.py, this script does NOT extract research
questions — that is deferred to extract_questions.py (DeepSeek API).
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

from rq_lib import slugify, write_json

# ── header detection ────────────────────────────────────────────────
CN_HEADER_MAP = {
    "题目": "title",
    "作者": "author",
    "摘要": "abstract",
}
EN_HEADER_MAP = {
    "title": "title",
    "author": "author",
    "abstract": "abstract",
}


def detect_header_map(headers: list[str]) -> dict[str, str]:
    """Detect whether headers are Chinese or English and return col→field mapping.

    Returns an empty dict if detection fails (caller should raise a clear error).
    """
    stripped = [h.strip() for h in headers]

    cn_count = sum(1 for h in stripped if h in CN_HEADER_MAP)
    en_count = sum(1 for h in stripped if h.lower() in EN_HEADER_MAP)

    if cn_count >= 2:
        return {h: CN_HEADER_MAP[h] for h in stripped if h in CN_HEADER_MAP}
    if en_count >= 2:
        return {h: EN_HEADER_MAP[h.lower()] for h in stripped if h.lower() in EN_HEADER_MAP}
    return {}


def load_papers_from_csv(csv_path: Path) -> list[dict]:
    """Read CSV and return a list of paper dicts (title, author, abstract, _meta)."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

    header_map = detect_header_map(headers)
    if not header_map:
        raise ValueError(
            f"Could not detect CSV headers. Expected columns:\n"
            f"  Chinese: 题目, 作者, 摘要\n"
            f"  English:  title, author, abstract\n"
            f"  Got: {headers}"
        )

    papers = []
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for idx, raw_row in enumerate(reader, start=1):
            # Normalise column names
            row = {}
            for col_key, col_val in raw_row.items():
                field = header_map.get(col_key.strip())
                if field:
                    row[field] = (col_val or "").strip()

            title = row.get("title", "")
            abstract = row.get("abstract", "")
            author = row.get("author", "")

            if not title:
                print(f"[skip] row {idx}: empty title")
                continue
            if not abstract or len(abstract) < 20:
                print(f"[skip] row {idx} ({title[:40]}...): abstract too short or missing")
                continue

            paper_id = slugify(title) or f"paper_{idx:04d}"
            papers.append({
                "paper_id": paper_id,
                "title": title,
                "abstract": abstract,
                "author": author,
                "_meta": {
                    "source_type": "csv",
                    "source_file": csv_path.name,
                    "csv_row": idx,
                    "imported_at": datetime.now(timezone.utc).isoformat(),
                },
            })

    return papers


def save_papers_as_text(output_dir: Path, papers: list[dict]) -> int:
    """Write each paper dict as output_dir/text/<paper_id>.json.

    Returns the number of files written.
    """
    text_dir = output_dir / "text"
    text_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for paper in papers:
        # Build the format that extract_questions.py expects
        payload = {
            "paper_id": paper["paper_id"],
            "title": paper["title"],
            "abstract": paper["abstract"],
            "author": paper.get("author", ""),
            "source_pdf": "",                # CSV has no PDF
            "filename": paper["_meta"]["source_file"],
            "sections_read": [],
            "section_texts": {},             # CSV mode: no PDF sections
            "_meta": paper["_meta"],         # ← traceability carrier
        }
        out_path = text_dir / f"{paper['paper_id']}.json"
        write_json(out_path, payload)
        count += 1

    return count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load CSV → output_dir/text/*.json (3 columns: 题目,作者,摘要)"
    )
    parser.add_argument("--csv-input", required=True, help="Path to input CSV file")
    parser.add_argument("--output-dir", required=True, help="Output directory (text/*.json goes here)")
    args = parser.parse_args()

    csv_path = Path(args.csv_input)
    output_dir = Path(args.output_dir)

    papers = load_papers_from_csv(csv_path)
    if not papers:
        raise SystemExit("No valid papers found in CSV. Check column names and data.")

    n = save_papers_as_text(output_dir, papers)
    print(f"Done. Wrote {n} paper(s) to {output_dir / 'text'}/")

    # Quick audit: show what was produced
    for p in papers:
        print(f"  [{p['_meta']['csv_row']:3d}] {p['paper_id']}: {p['title'][:60]}")


if __name__ == "__main__":
    main()
