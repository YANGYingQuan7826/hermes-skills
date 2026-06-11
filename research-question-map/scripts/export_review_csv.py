#!/usr/bin/env python3
"""Export extracted RQs to CSV for human review."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from rq_lib import read_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Export review CSV")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    questions_dir = output_dir / "questions"
    review_dir = output_dir / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    csv_path = review_dir / "questions_review.csv"

    rows = []
    for path in sorted(questions_dir.glob("*.json")):
        data = read_json(path)
        paper_id = data["paper_id"]
        title = data.get("title", "")
        for rq in data.get("research_questions", []):
            rows.append(
                {
                    "paper_id": paper_id,
                    "paper_title": title,
                    "rq_id": rq.get("id", ""),
                    "rq_text": rq.get("text", ""),
                    "rq_text_cn": rq.get("text_cn", ""),
                    "type": rq.get("type", ""),
                    "explicit": rq.get("explicit", ""),
                    "source_section": rq.get("source_section", ""),
                    "evidence_quote": rq.get("evidence_quote", ""),
                    "confidence": rq.get("confidence", ""),
                    "keep": "y",
                }
            )

    fieldnames = [
        "paper_id",
        "paper_title",
        "rq_id",
        "rq_text",
        "rq_text_cn",
        "type",
        "explicit",
        "source_section",
        "evidence_quote",
        "confidence",
        "keep",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} row(s) to {csv_path}")


if __name__ == "__main__":
    main()
