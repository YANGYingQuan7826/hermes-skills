#!/usr/bin/env python3
"""Cluster similar research questions without heavy ML deps."""

from __future__ import annotations

import argparse
import csv
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from rq_lib import read_json, write_json


def tokenize(text: str) -> Counter:
    words = re.findall(r"[a-z]{3,}", text.lower())
    return Counter(words)


def cosine(counter_a: Counter, counter_b: Counter) -> float:
    if not counter_a or not counter_b:
        return 0.0
    common = set(counter_a) & set(counter_b)
    dot = sum(counter_a[w] * counter_b[w] for w in common)
    norm_a = math.sqrt(sum(v * v for v in counter_a.values()))
    norm_b = math.sqrt(sum(v * v for v in counter_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def cluster_items(items: list[dict], threshold: float) -> list[dict]:
    vectors = [tokenize(item["rq_text"]) for item in items]
    clusters: list[list[int]] = []

    for i in range(len(items)):
        placed = False
        for cluster in clusters:
            rep = cluster[0]
            if cosine(vectors[i], vectors[rep]) >= threshold:
                cluster.append(i)
                placed = True
                break
        if not placed:
            clusters.append([i])

    payload = []
    for cluster_id, member_ids in enumerate(clusters):
        members = [items[i] for i in member_ids]
        payload.append(
            {
                "cluster_id": cluster_id,
                "size": len(members),
                "representative": members[0]["rq_text"],
                "members": members,
            }
        )
    return payload


def load_reviewed_questions(output_dir: Path) -> list[dict]:
    review_csv = output_dir / "review" / "questions_review.csv"
    questions_dir = output_dir / "questions"

    if review_csv.exists():
        rows = []
        with review_csv.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if str(row.get("keep", "y")).strip().lower() in {"n", "no", "0", "false"}:
                    continue
                rows.append(row)
        enriched = []
        for row in rows:
            paper = read_json(questions_dir / f"{row['paper_id']}.json")
            enriched.append(
                {
                    "paper_id": row["paper_id"],
                    "paper_title": row.get("paper_title") or paper.get("title", ""),
                    "abstract": paper.get("abstract", ""),
                    "rq_id": row.get("rq_id", ""),
                    "rq_text": row.get("rq_text", ""),
                    "rq_text_cn": row.get("rq_text_cn", ""),
                    "type": row.get("type", "main"),
                }
            )
        return enriched

    items = []
    for path in sorted(questions_dir.glob("*.json")):
        paper = read_json(path)
        for rq in paper.get("research_questions", []):
            items.append(
                {
                    "paper_id": paper["paper_id"],
                    "paper_title": paper.get("title", ""),
                    "abstract": paper.get("abstract", ""),
                    "rq_id": rq.get("id", ""),
                    "rq_text": rq.get("text", ""),
                    "rq_text_cn": rq.get("text_cn", ""),
                    "type": rq.get("type", "main"),
                }
            )
    return items


def main() -> None:
    parser = argparse.ArgumentParser(description="Cluster research questions")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--similarity-threshold", type=float, default=0.18)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    items = load_reviewed_questions(output_dir)
    if not items:
        raise SystemExit("No research questions to cluster.")

    cluster_payload = cluster_items(items, args.similarity_threshold)
    write_json(output_dir / "clusters.json", {"clusters": cluster_payload})
    print(f"Clustered {len(items)} RQ(s) into {len(cluster_payload)} cluster(s).")


if __name__ == "__main__":
    main()
