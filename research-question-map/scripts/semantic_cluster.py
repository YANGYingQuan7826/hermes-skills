#!/usr/bin/env python3
"""
Semantic clustering via DeepSeek Chat (two-phase: topic discovery → assignment).
Outputs clusters.json compatible with build_concept_tree.py.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SKILL_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SKILL_SCRIPTS))
from rq_lib import get_deepseek_client, load_dotenv, read_json, write_json


# ── Data loading ──

def load_all_rqs(output_dir: Path) -> list[dict]:
    items = []
    for path in sorted((output_dir / "questions").glob("*.json")):
        paper = read_json(path)
        for rq in paper.get("research_questions", []):
            items.append({
                "paper_id": paper["paper_id"],
                "paper_title": paper.get("title", ""),
                "abstract": (paper.get("abstract") or "")[:400],
                "rq_id": rq.get("id", ""),
                "rq_text": rq.get("text", ""),
                "rq_text_cn": rq.get("text_cn", ""),
            })
    return items


# ── Phase 1: Topic discovery ──

def build_topic_discovery_prompt(rqs: list[dict]) -> str:
    lines = []
    for i, rq in enumerate(rqs):
        en = rq["rq_text"][:100]
        cn = rq.get("rq_text_cn", "")[:60]
        line = f"[{i}] {en}"
        if cn:
            line += f" | {cn}"
        lines.append(line)
    rq_list = "\n".join(lines)

    return f"""Analyze these {len(rqs)} research questions about humanoid robots.
Identify 15-25 distinct research TOPICS (categorize by the phenomenon studied, not by method).

Rules:
- Group by SEMANTIC MEANING, not exact words. "trust" = "confidence" = "credibility".
- Focus on the MAIN phenomenon: trust, appearance, emotion, behavior, decision-making, etc.
- Give each topic a concise label (3-8 words, English).
- Return ONLY JSON (no markdown, no explanation):
{{"topics": ["Label 1", "Label 2", ...]}}

Questions:
{rq_list}"""


def parse_topics(content: str) -> list[str]:
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        if lines[-1].strip() == "```":
            content = "\n".join(lines[1:-1])
        else:
            content = "\n".join(lines[1:])
    try:
        return json.loads(content).get("topics", [])
    except json.JSONDecodeError:
        return []


# ── Phase 2: Assignment ──

def build_assignment_prompt(rqs: list[dict], indices: list[int], topics: list[str]) -> str:
    rq_lines = []
    for rq, idx in zip(rqs, indices):
        en = rq["rq_text"][:100]
        cn = rq.get("rq_text_cn", "")[:60]
        line = f"[{idx}] {en}"
        if cn:
            line += f" | {cn}"
        rq_lines.append(line)

    topic_lines = "\n".join(f"  {i}: {t}" for i, t in enumerate(topics))
    rq_list = "\n".join(rq_lines)

    return f"""Assign each research question to ONE topic (by index) or mark as noise (-1).

Topics:
{topic_lines}

Return ONLY JSON (no markdown, no explanation):
{{"assignments": {{"0": [23, 45], "1": [12, 34], ...}}, "noise": [99, 101]}}

Rules:
- Each RQ gets exactly ONE topic.
- Use noise (-1) for RQs that don't fit any topic (< 10%).
- Topic keys are integer strings.

Questions:
{rq_list}"""


def parse_assignments(content: str, expected_indices: list[int]) -> tuple[dict[int, list[int]], list[int]]:
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        if lines[-1].strip() == "```":
            content = "\n".join(lines[1:-1])
        else:
            content = "\n".join(lines[1:])

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        return {}, list(expected_indices)

    assignments_raw = result.get("assignments", {})
    noise = [int(i) for i in result.get("noise", []) if int(i) in expected_indices]

    assignments: dict[int, list[int]] = {}
    all_assigned = set(noise)
    for k, v in assignments_raw.items():
        topic_idx = int(k)
        # Handle both list and single int
        if isinstance(v, int):
            v = [v]
        elif not isinstance(v, list):
            continue
        members = [int(i) for i in v if int(i) in expected_indices]
        assignments[topic_idx] = members
        all_assigned.update(members)

    # Add unassigned to noise
    for idx in expected_indices:
        if idx not in all_assigned:
            noise.append(idx)

    return assignments, noise


# ── Output builder ──

def build_clusters_json(rqs: list[dict], clusters_raw: list[dict], noise_indices: list[int]) -> dict:
    clusters = []
    for cid, c_raw in enumerate(clusters_raw):
        indices = [i for i in c_raw.get("member_indices", []) if 0 <= i < len(rqs)]
        if not indices:
            continue
        members = []
        for idx in indices:
            rq = rqs[idx]
            members.append({
                "paper_id": rq["paper_id"], "paper_title": rq["paper_title"],
                "abstract": rq["abstract"], "rq_id": rq["rq_id"],
                "rq_text": rq["rq_text"], "rq_text_cn": rq.get("rq_text_cn", ""),
            })
        clusters.append({
            "cluster_id": cid, "size": len(members),
            "representative": c_raw.get("label", f"Cluster {cid}"),
            "members": members,
        })

    if noise_indices:
        noise_members = []
        for idx in noise_indices:
            if 0 <= idx < len(rqs):
                rq = rqs[idx]
                noise_members.append({
                    "paper_id": rq["paper_id"], "paper_title": rq["paper_title"],
                    "abstract": rq["abstract"], "rq_id": rq["rq_id"],
                    "rq_text": rq["rq_text"], "rq_text_cn": rq.get("rq_text_cn", ""),
                })
        clusters.append({
            "cluster_id": len(clusters), "size": len(noise_members),
            "representative": "未归类 / Uncategorized",
            "members": noise_members,
        })

    return {"clusters": clusters}


# ── Main ──

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    load_dotenv(output_dir)

    rqs = load_all_rqs(output_dir)
    n = len(rqs)
    print(f"Loaded {n} RQs")

    client = get_deepseek_client()
    model = os.environ.get("RQ_MODEL_EXTRACT", "deepseek-v4-pro")

    # Phase 1: Discover topics
    sample = rqs[:min(100, n)]
    print(f"\nPhase 1: Discovering topics from {len(sample)} sample RQs...")
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": "You cluster research literature. Output ONLY JSON."},
                   {"role": "user", "content": build_topic_discovery_prompt(sample)}],
        extra_body={"thinking": {"type": "disabled"}},
        temperature=0.2, max_tokens=8000,
    )
    topics = parse_topics(resp.choices[0].message.content or "")
    print(f"  {len(topics)} topics: {[t[:50] for t in topics]}")
    if resp.usage:
        print(f"  Tokens: {resp.usage.total_tokens}")

    if not topics:
        raise SystemExit("No topics discovered — aborting")

    # Phase 2: Assign all RQs in batches
    print(f"\nPhase 2: Assigning {n} RQs to {len(topics)} topics (batch=50)...")
    all_assignments: dict[int, list[int]] = {}
    noise_list: list[int] = []
    BATCH = 50

    for start in range(0, n, BATCH):
        batch = rqs[start:start + BATCH]
        indices = list(range(start, min(start + BATCH, n)))
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": "Output ONLY JSON. No explanation."},
                       {"role": "user", "content": build_assignment_prompt(batch, indices, topics)}],
            extra_body={"thinking": {"type": "disabled"}},
            temperature=0.0, max_tokens=4000,
        )
        batch_a, batch_n = parse_assignments(resp.choices[0].message.content or "", indices)
        for tidx, idxs in batch_a.items():
            all_assignments.setdefault(tidx, []).extend(idxs)
        noise_list.extend(batch_n)
        assigned = sum(len(v) for v in batch_a.values())
        print(f"  Batch {start // BATCH + 1}/{(n + BATCH - 1) // BATCH}: {assigned} assigned, {len(batch_n)} noise"
              + (f" (tokens: {resp.usage.total_tokens})" if resp.usage else ""))

    # Build clusters
    clusters_raw = []
    for tidx in sorted(all_assignments):
        if tidx < len(topics):
            clusters_raw.append({"label": topics[tidx], "member_indices": all_assignments[tidx]})

    clusters_data = build_clusters_json(rqs, clusters_raw, noise_list)

    total = sum(c["size"] for c in clusters_data["clusters"])
    print(f"\nFinal: {len(clusters_data['clusters'])} clusters, {len(noise_list)} noise, {total} total")
    for c in clusters_data["clusters"]:
        print(f"  [{c['cluster_id']}] {c['representative'][:60]} — {c['size']} RQs")

    write_json(output_dir / "clusters.json", clusters_data)
    print(f"\nWrote {output_dir / 'clusters.json'}")


if __name__ == "__main__":
    main()
