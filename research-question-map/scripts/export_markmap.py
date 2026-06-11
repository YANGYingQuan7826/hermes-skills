#!/usr/bin/env python3
"""Export research-map.md (bilingual) and interactive research-map.html."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from rq_lib import read_json

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Research Question Map</title>
  <style>
    :root {
      --bg: #f7f7f8;
      --panel: #ffffff;
      --text: #1f2328;
      --muted: #656d76;
      --line: #d0d7de;
      --accent: #0969da;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    header {
      padding: 16px 20px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }
    header h1 { margin: 0 0 6px; font-size: 20px; }
    header p { margin: 0; color: var(--muted); font-size: 14px; }
    main {
      display: grid;
      grid-template-columns: 1fr 360px;
      gap: 16px;
      padding: 16px;
      min-height: calc(100vh - 88px);
    }
    .tree-panel, .detail-panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 16px;
    }
    .tree-panel { overflow: auto; }
    ul.tree { list-style: none; margin: 0; padding-left: 18px; }
    ul.tree.root { padding-left: 0; }
    .node { margin: 10px 0; }
    .question {
      font-weight: 600;
      line-height: 1.45;
      margin-bottom: 2px;
    }
    .question .cn {
      display: block;
      font-weight: 400;
      font-size: 13px;
      color: var(--muted);
      margin-top: 2px;
    }
    .badges { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 6px; margin-top: 4px; }
    .badge {
      font-size: 11px;
      padding: 2px 7px;
      border-radius: 10px;
      border: 1px solid var(--line);
      background: #f6f8fa;
      color: var(--muted);
    }
    .badge.relation { color: #8250df; border-color: #d0bfff; background: #f5f0ff; }
    .badge.reason { color: #0969da; border-color: #bdd7ff; background: #f0f6ff; }
    .papers { display: flex; flex-wrap: wrap; gap: 6px; }
    .paper-link {
      border: 1px solid var(--line);
      background: #f6f8fa;
      color: var(--accent);
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 12px;
      cursor: pointer;
    }
    .paper-link:hover { background: #eef6ff; }
    .detail-panel h2 { margin: 0 0 8px; font-size: 18px; }
    .detail-panel .meta { color: var(--muted); font-size: 13px; margin-bottom: 12px; }
    .detail-panel .abstract {
      white-space: pre-wrap;
      line-height: 1.55;
      font-size: 14px;
    }
    .empty { color: var(--muted); font-size: 14px; }
    @media (max-width: 960px) {
      main { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Research Question Map</h1>
    <p>Click a paper chip to view title and abstract. Edit research-map.md and rerun export to update.</p>
  </header>
  <main>
    <section class="tree-panel" id="tree-root"></section>
    <aside class="detail-panel">
      <div id="detail-empty" class="empty">Select a paper to view details.</div>
      <div id="detail-content" hidden>
        <h2 id="detail-title"></h2>
        <div class="meta" id="detail-meta"></div>
        <div class="abstract" id="detail-abstract"></div>
      </div>
    </aside>
  </main>
  <script>
    const TREE = __TREE_JSON__;
    const papersById = {};

    function indexPapers(node) {
      (node.papers || []).forEach(p => { papersById[p.paper_id + "::" + (p.rq_id || "")] = p; });
      (node.children || []).forEach(indexPapers);
    }
    indexPapers(TREE.root);

    function renderNode(node) {
      const li = document.createElement("li");
      li.className = "node";

      const q = document.createElement("div");
      q.className = "question";
      q.textContent = node.question || "";
      if (node.question_cn && node.question_cn !== node.question) {
        const cn = document.createElement("span");
        cn.className = "cn";
        cn.textContent = node.question_cn;
        q.appendChild(cn);
      }
      li.appendChild(q);

      // Badges: relation type + reason
      const badges = document.createElement("div");
      badges.className = "badges";
      const paperCount = (node.papers || []).length;
      if (paperCount) {
        const cnt = document.createElement("span");
        cnt.className = "badge";
        cnt.textContent = paperCount + " papers";
        badges.appendChild(cnt);
      }
      if (node.relation_to_parent && node.relation_to_parent !== "root") {
        const rel = document.createElement("span");
        rel.className = "badge relation";
        rel.textContent = node.relation_to_parent;
        badges.appendChild(rel);
      }
      if (node.reason) {
        const reason = document.createElement("span");
        reason.className = "badge reason";
        reason.textContent = node.reason;
        reason.title = node.reason;
        badges.appendChild(reason);
      }
      if (badges.children.length) li.appendChild(badges);

      const papers = document.createElement("div");
      papers.className = "papers";
      (node.papers || []).forEach(p => {
        const btn = document.createElement("button");
        btn.className = "paper-link";
        btn.type = "button";
        btn.textContent = p.paper_id;
        btn.title = p.title || p.paper_id;
        btn.onclick = () => showPaper(p);
        papers.appendChild(btn);
      });
      if ((node.papers || []).length) li.appendChild(papers);

      const children = node.children || [];
      if (children.length) {
        const ul = document.createElement("ul");
        ul.className = "tree";
        children.forEach(child => ul.appendChild(renderNode(child)));
        li.appendChild(ul);
      }
      return li;
    }

    function showPaper(paper) {
      document.getElementById("detail-empty").hidden = true;
      const content = document.getElementById("detail-content");
      content.hidden = false;
      document.getElementById("detail-title").textContent = paper.title || paper.paper_id;
      document.getElementById("detail-meta").textContent =
        [paper.paper_id, paper.rq_id ? ("RQ: " + paper.rq_id) : ""].filter(Boolean).join(" · ");
      document.getElementById("detail-abstract").textContent = paper.abstract || "(No abstract available)";
    }

    const rootList = document.createElement("ul");
    rootList.className = "tree root";
    rootList.appendChild(renderNode(TREE.root));
    document.getElementById("tree-root").appendChild(rootList);
  </script>
</body>
</html>
"""


def _label(node: dict) -> str:
    """Preferred display label: Chinese if available, else English."""
    cn = node.get("question_cn", "").strip()
    return cn if cn else node.get("question", "")


def node_to_markdown(node: dict, depth: int = 1) -> list[str]:
    """Render node to markdown headings, preferring Chinese text."""
    label = _label(node)
    en = node.get("question", "")
    cn = node.get("question_cn", "").strip()

    # Heading: show Chinese, fallback to English
    lines = [f"{'#' * min(depth, 6)} {label}"]

    # If bilingual, show the other language as a subline
    if cn and en and cn != en:
        # Show English as comment-like line
        lines.append(f"> {en}")

    # Paper count and relation badge
    extras = []
    paper_count = len(node.get("papers", []))
    if paper_count:
        extras.append(f"{paper_count}篇")
    relation = node.get("relation_to_parent", "")
    if relation and relation != "root":
        extras.append(f"关系：{relation}")
    reason = node.get("reason", "")
    if reason:
        extras.append(f"理由：{reason}")
    if extras:
        lines.append(f"*{' · '.join(extras)}*")
        lines.append("")

    # Paper links
    for paper in node.get("papers", []):
        pid = paper.get("paper_id", "paper")
        title = paper.get("title", "").replace("[", "(").replace("]", ")")
        lines.append(f"- [{pid} — {title}](#paper-{pid})")

    # Children
    for child in node.get("children", []):
        lines.extend(node_to_markdown(child, depth + 1))

    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Export mind map files")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    tree = read_json(output_dir / "tree.json")

    # --- Markdown export ---
    md_lines = ["# 研究问题图谱", ""] + node_to_markdown(tree["root"], depth=1)
    md_path = output_dir / "research-map.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    # Also write Chinese version (same content now, since we prefer CN)
    cn_path = output_dir / "research-map-cn.md"
    cn_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    # --- HTML export ---
    html_content = HTML_TEMPLATE.replace(
        "__TREE_JSON__",
        json.dumps(tree, ensure_ascii=False),
    )
    html_path = output_dir / "research-map.html"
    html_path.write_text(html_content, encoding="utf-8")

    print(f"Wrote {md_path}")
    print(f"Wrote {cn_path}")
    print(f"Wrote {html_path}")


if __name__ == "__main__":
    main()
