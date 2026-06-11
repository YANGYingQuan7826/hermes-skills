#!/usr/bin/env python3
"""Read a CSV with pre-extracted research questions and generate questions/*.json.

Expected CSV columns (Chinese or English):
    题目, 作者, 摘要, 研究问题
    title, author, abstract, research_question

Each row = one paper. Multiple RQs separated by newline, ；, ;, or numbered.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from rq_lib import slugify, write_json

RQG_SPLIT_RE = re.compile(r"\s*(?:\d+[\.\、\)）]\s*|\n+|；|;)\s*")
CN_HEADER_MAP = {"题目": "title", "作者": "author", "摘要": "abstract", "研究问题": "research_question"}
EN_HEADER_MAP = {"title": "title", "author": "author", "abstract": "abstract", "research_question": "research_question"}


def extract_rqs(raw: str) -> list[str]:
    if not raw or not raw.strip():
        return []
    candidates = [s.strip() for s in RQG_SPLIT_RE.split(raw) if s.strip()]
    return [re.sub(r"^\d+[\.\、\)）]\s*", "", c).strip() for c in candidates if len(c) > 5]


def build_question_json(row: dict[str, str], idx: int) -> dict:
    title = row.get("title", "").strip()
    abstract = row.get("abstract", "").strip()
    author = row.get("author", "").strip()
    rq_raw = row.get("research_question", "")
    paper_id = slugify(title) if title else f"paper_{idx:04d}"
    rqs = extract_rqs(rq_raw)
    return {
        "paper_id": paper_id,
        "title": title,
        "abstract": abstract,
        "author": author,
        "sections_read": [],
        "research_questions": [
            {"id": f"RQ{j+1}", "text": t, "type": "main", "explicit": True,
             "source_section": "", "evidence_quote": "", "confidence": "high"}
            for j, t in enumerate(rqs)
        ],
        "extraction_notes": f"Imported from CSV. Author: {author}" if author else "Imported from CSV.",
    }


def detect_header_map(headers: list[str]) -> dict[str, str]:
    header_map = {}
    cn_count = sum(1 for h in headers if h.strip() in CN_HEADER_MAP)
    if cn_count >= 3:
        for h in headers:
            if h.strip() in CN_HEADER_MAP:
                header_map[h.strip()] = CN_HEADER_MAP[h.strip()]
    else:
        for h in headers:
            if h.strip().lower() in EN_HEADER_MAP:
                header_map[h.strip().lower()] = EN_HEADER_MAP[h.strip().lower()]
    if not header_map:
        for i, key in enumerate(["题目", "作者", "摘要", "研究问题"]):
            if i < len(headers):
                header_map[headers[i].strip()] = CN_HEADER_MAP[key]
    return header_map


def main() -> None:
    parser = argparse.ArgumentParser(description="Import CSV with pre-extracted RQs")
    parser.add_argument("--csv-input", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    csv_path = Path(args.csv_input)
    output_dir = Path(args.output_dir)
    questions_dir = output_dir / "questions"
    questions_dir.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

    header_map = detect_header_map(headers)
    print(f"Header mapping: {header_map}")

    total_rqs = 0
    paper_count = 0
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        for idx, raw_row in enumerate(csv.DictReader(f), start=1):
            normalized = {}
            for col_key, col_val in raw_row.items():
                target = header_map.get(col_key.strip(), col_key.strip().lower())
                normalized[target] = col_val

            qj = build_question_json(normalized, idx)
            if not qj["research_questions"]:
                print(f"[skip] row {idx}: no RQ found")
                continue

            write_json(questions_dir / f"{qj['paper_id']}.json", qj)
            paper_count += 1
            total_rqs += len(qj["research_questions"])
            print(f"[imported] {qj['paper_id']}: {len(qj['research_questions'])} RQ(s)")

    print(f"Done. {paper_count} papers, {total_rqs} RQs.")


if __name__ == "__main__":
    main()
