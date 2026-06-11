#!/usr/bin/env python3
"""Build conceptual research-question tree — per-cluster, then merge."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from rq_lib import get_deepseek_client, load_dotenv, read_json, write_json

SKILL_ROOT = Path(__file__).resolve().parents[1]
TREE_PROMPT = (SKILL_ROOT / "prompts" / "build_tree.md").read_text(encoding="utf-8")


def build_cluster_payload(cluster: dict) -> dict:
    """Prepare a single cluster's payload for the LLM."""
    papers = []
    for member in cluster["members"]:
        papers.append(
            {
                "paper_id": member["paper_id"],
                "title": member.get("paper_title", ""),
                "abstract": (member.get("abstract") or "")[:600],
                "rq_id": member.get("rq_id", ""),
                "rq_text": member.get("rq_text", ""),
                "rq_text_cn": member.get("rq_text_cn", ""),
            }
        )
    return {
        "cluster_id": cluster["cluster_id"],
        "representative_question": cluster["representative"],
        "papers": papers,
    }


def flat_subtree(cluster: dict) -> dict:
    """Fallback: create a flat subtree without LLM."""
    children = []
    for member in cluster["members"]:
        children.append(
            {
                "question": member["rq_text"],
                "question_cn": member.get("rq_text_cn", ""),
                "relation_to_parent": "root",
                "reason": "fallback — no LLM structuring",
                "papers": [
                    {
                        "paper_id": member["paper_id"],
                        "title": member.get("paper_title", ""),
                        "rq_id": member.get("rq_id", ""),
                    }
                ],
                "children": [],
            }
        )
    return {
        "question": cluster["representative"],
        "papers": [],
        "children": children,
    }


def build_one_subtree(client, cluster: dict, model: str, thinking: bool) -> dict:
    """Send one cluster to LLM, return its subtree."""
    payload = build_cluster_payload(cluster)
    user_content = json.dumps(payload, ensure_ascii=False, indent=2)

    extra_body = {}
    if thinking:
        extra_body = {"thinking": {"type": "enabled"}, "reasoning_effort": "medium"}

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": TREE_PROMPT},
            {"role": "user", "content": user_content},
        ],
        extra_body=extra_body,
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    content = response.choices[0].message.content or "{}"
    try:
        result = json.loads(content)
        subtree = result.get("subtree", {})
        if not subtree or "children" not in subtree:
            return flat_subtree(cluster)
        return subtree
    except (json.JSONDecodeError, TypeError):
        return flat_subtree(cluster)


def merge_subtrees(subtrees: list[dict], root_question: str) -> dict:
    """Merge per-cluster subtrees into one master tree.

    Each subtree root becomes a top-level child of the master root.
    """
    root_children = []
    for i, subtree in enumerate(subtrees):
        # The subtree's own question becomes the top-level cluster node
        node = {
            "id": f"c{i}",
            "question": subtree.get("question", f"Cluster {i}"),
            "question_cn": subtree.get("question_cn", ""),
            "relation_to_parent": "cluster",
            "papers": subtree.get("papers", []),
            "children": [],
        }
        for child in subtree.get("children", []):
            child_node = _copy_node(child, f"c{i}", 1)
            node["children"].append(child_node)
        root_children.append(node)

    return {
        "root": {
            "id": "n0",
            "question": root_question,
            "relation_to_parent": "root",
            "papers": [],
            "children": root_children,
        }
    }


def _copy_node(node: dict, prefix: str, depth: int) -> dict:
    """Recursively copy a node from subtree, assigning stable IDs."""
    child_count = _copy_node._counter.get(prefix, 0)  # type: ignore[attr-defined]
    _copy_node._counter[prefix] = child_count + 1  # type: ignore[attr-defined]
    new_node = {
        "id": f"{prefix}_n{depth}_{child_count}",
        "question": node.get("question", ""),
        "question_cn": node.get("question_cn", ""),
        "relation_to_parent": node.get("relation_to_parent", "decomposition"),
        "reason": node.get("reason", ""),
        "papers": node.get("papers", []),
        "children": [],
    }
    for child in node.get("children", []):
        new_node["children"].append(_copy_node(child, prefix, depth + 1))
    return new_node


_copy_node._counter = {}  # type: ignore[attr-defined]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build concept tree per cluster")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--root-question",
        default="仿人机器人研究问题全景",
        help="Master root question",
    )
    args = parser.parse_args()

    load_dotenv(Path(args.output_dir))
    output_dir = Path(args.output_dir)
    clusters_data = read_json(output_dir / "clusters.json")
    clusters = clusters_data.get("clusters", [])

    if not clusters:
        raise SystemExit("No clusters to build tree from.")

    model = os.environ.get("RQ_MODEL_TREE", "deepseek-chat")
    thinking = os.environ.get("RQ_TREE_THINKING", "").strip().lower() in {
        "1", "true", "yes", "on",
    }
    client = get_deepseek_client()

    subtrees = []
    for i, cluster in enumerate(clusters):
        size = len(cluster.get("members", []))
        print(f"[tree] cluster {cluster['cluster_id']} ({size} RQs) …", end=" ", flush=True)
        try:
            subtree = build_one_subtree(client, cluster, model, thinking)
            subtrees.append(subtree)
            child_count = len(subtree.get("children", []))
            print(f"→ {child_count} top-level node(s)")
        except Exception as exc:
            print(f"→ FAILED ({exc}), using fallback")
            subtrees.append(flat_subtree(cluster))

    tree = merge_subtrees(subtrees, args.root_question)
    write_json(output_dir / "tree.json", tree)
    n_clusters = len(subtrees)
    total_nodes = sum(
        len(s.get("children", [])) for s in subtrees
    )
    print(f"Done: {n_clusters} cluster(s) → {total_nodes} top-level node(s) under root.")


if __name__ == "__main__":
    main()
