#!/usr/bin/env python3
"""Run the full research-question-map pipeline."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def run(script: str, *args: str) -> None:
    cmd = [sys.executable, str(SCRIPTS / script), *args]
    print("\n>>", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RQ map pipeline")
    parser.add_argument("--papers-dir", default="", help="Folder containing PDF files")
    parser.add_argument("--csv-input", default="", help="CSV with paper metadata (3 columns: 题目,作者,摘要 — RQs are auto-extracted by DeepSeek)")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--skip-extract", action="store_true")
    parser.add_argument("--skip-tree", action="store_true")
    parser.add_argument("--fallback-tree", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.csv_input:
        # CSV mode: load from CSV → generate text/*.json → DeepSeek extract → pipeline
        run("_csv_loader.py", "--csv-input", args.csv_input, "--output-dir", args.output_dir)
        if not args.skip_extract:
            run("extract_questions.py", "--output-dir", args.output_dir)
            run("export_review_csv.py", "--output-dir", args.output_dir)
        else:
            print("Skipped extraction. Ensure output/questions already exists.")
    elif args.papers_dir:
        # PDF mode (original pipeline)
        run("parse_pdf_sections.py", "--papers-dir", args.papers_dir, "--output-dir", args.output_dir)

        if not args.skip_extract:
            run("extract_questions.py", "--output-dir", args.output_dir)
            run("export_review_csv.py", "--output-dir", args.output_dir)
        else:
            print("Skipped extraction. Ensure output/questions already exists.")
    else:
        parser.error("Either --papers-dir or --csv-input must be provided.")

    if args.skip_tree:
        print("Skipped clustering/tree/export.")
        return

    run("cluster_questions.py", "--output-dir", args.output_dir)
    run("build_concept_tree.py", "--output-dir", args.output_dir)
    run("export_markmap.py", "--output-dir", args.output_dir)


if __name__ == "__main__":
    main()
