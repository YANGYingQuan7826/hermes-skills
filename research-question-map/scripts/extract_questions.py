#!/usr/bin/env python3
"""Extract research questions via DeepSeek V4 API — with concurrent workers."""

from __future__ import annotations

import argparse
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from rq_lib import get_deepseek_client, load_dotenv, read_json, write_json

SKILL_ROOT = Path(__file__).resolve().parents[1]
EXTRACT_PROMPT = (SKILL_ROOT / "prompts" / "extract_rq.md").read_text(encoding="utf-8")

_lock = threading.Lock()
_done = 0
_total = 0


def build_user_payload(parsed: dict) -> str:
    parts = [
        f"Title: {parsed.get('title', '')}",
        f"Abstract: {parsed.get('abstract', '')}",
        "",
        "Sections (read completely):",
    ]
    for header, text in parsed.get("section_texts", {}).items():
        parts.append(f"\n## {header}\n{text[:10000]}")
    return "\n".join(parts)


def extract_one(client, parsed: dict, model: str) -> dict:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": EXTRACT_PROMPT},
            {"role": "user", "content": build_user_payload(parsed)},
        ],
        extra_body={"thinking": {"type": "enabled"}, "reasoning_effort": "medium"},
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    content = response.choices[0].message.content or "{}"
    extracted = json.loads(content)
    return {
        "paper_id": parsed["paper_id"],
        "title": parsed.get("title", ""),
        "abstract": parsed.get("abstract", ""),
        "author": parsed.get("author", ""),
        "source_pdf": parsed.get("source_pdf", ""),
        "filename": parsed.get("filename", ""),
        "sections_read": parsed.get("sections_read", []),
        "research_questions": extracted.get("research_questions", []),
        "extraction_notes": extracted.get("extraction_notes", ""),
        "_meta": parsed.get("_meta", None),
    }


def _process_one(args: tuple) -> dict:
    """Worker function for concurrent extraction.  Returns (success, result_or_error)."""
    client, path, questions_dir, model = args
    global _done
    try:
        parsed = read_json(path)
        result = extract_one(client, parsed, model)
        out_path = questions_dir / f"{result['paper_id']}.json"
        write_json(out_path, result)
        rq_count = len(result.get("research_questions", []))
        with _lock:
            _done += 1
            print(f"[extracted {_done}/{_total}] {result['paper_id']}: {rq_count} RQ(s)")
        return {"ok": True, "paper_id": result["paper_id"]}
    except Exception as exc:
        with _lock:
            _done += 1
            pid = Path(path).stem
            print(f"[ERROR {_done}/{_total}] {pid}: {exc}")
        return {"ok": False, "paper_id": Path(path).stem, "error": str(exc)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract RQs with DeepSeek V4 (concurrent)")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--paper-id", default="", help="Extract one paper only")
    parser.add_argument(
        "--workers",
        type=int,
        default=5,
        help="Number of concurrent API workers (default: 5; set 1 for serial)",
    )
    args = parser.parse_args()

    load_dotenv(Path(args.output_dir))
    output_dir = Path(args.output_dir)
    text_dir = output_dir / "text"
    questions_dir = output_dir / "questions"
    questions_dir.mkdir(parents=True, exist_ok=True)

    model = os.environ.get("RQ_MODEL_EXTRACT", "deepseek-v4-pro")
    client = get_deepseek_client()

    files = sorted(text_dir.glob("*.json"))
    if args.paper_id:
        files = [p for p in files if p.stem == args.paper_id]
    if not files:
        raise SystemExit(f"No parsed text JSON in {text_dir}. Run parse_pdf_sections.py or _csv_loader.py first.")

    global _total
    _total = len(files)

    if args.workers == 1:
        # Serial mode (for debugging)
        for path in files:
            _process_one((client, path, questions_dir, model))
    else:
        print(f"Extracting RQs from {_total} papers with {args.workers} concurrent workers...")
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {
                pool.submit(_process_one, (client, path, questions_dir, model)): path
                for path in files
            }
            ok = 0
            failed = 0
            for future in as_completed(futures):
                result = future.result()
                if result["ok"]:
                    ok += 1
                else:
                    failed += 1
            print(f"Done: {ok} OK, {failed} failed (of {_total})")


if __name__ == "__main__":
    main()
