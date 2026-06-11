---
name: research-question-map
description: >
  从 PDF 论文或 CSV 批量输入中自动提取研究问题，通过 DeepSeek Chat API 进行语义聚类，
  生成结构化的交互式思维导图（Markmap HTML）。
  支持三种输入模式：(1) PDF；(2) CSV；(3) 已有 questions/*.json（跳过提取直接聚类）。
  输出为 clusters.json → tree.json → 中英双语思维导图 HTML。
---

# Research Question Map — 研究问题图谱

从学术论文中自动提取研究问题，**语义聚类**后生成可交互的 Markmap 思维导图。

## 聚类逻辑（v2 — 语义聚类）

旧版 `cluster_questions.py` 使用词频余弦相似度，存在以下问题：
- 只匹配英文词，中文 RQ 被完全忽略
- 无 TF-IDF 降权，高频词（"robot""human"）主导
- 贪心增量聚类 + 低阈值 → 第一个簇吞掉 39% 数据
- "trust" 和 "confidence" 被视为不同主题

新版 `semantic_cluster.py` 使用 **DeepSeek Chat API 两阶段语义聚类**：
1. **Phase 1（主题发现）**：发送 100 条样本 RQ → DeepSeek 识别 15-30 个语义主题
2. **Phase 2（分配）**：逐批（50条/批）将所有 RQ 分配到已发现主题
3. 噪声 RQ 自动标记到 "未归类" 簇
4. 输出 `clusters.json`，兼容 `build_concept_tree.py`

```bash
# 语义聚类（推荐替代 cluster_questions.py）
python scripts/semantic_cluster.py --output-dir output/
```

## 使用方式

### 模式 1：PDF 输入（完整管线）

```bash
python scripts/run_pipeline.py --pdf-dir "papers/" --output-dir "output/"
```

### 模式 2：CSV 输入

```bash
python scripts/run_pipeline.py --csv-input "论文列表.csv" --output-dir "output/"
```

### 模式 3：已有 questions/*.json（跳过提取，直接聚类）

```bash
# Step 1: 语义聚类
python scripts/semantic_cluster.py --output-dir "output/"

# Step 2: 构建概念树（逐簇调用 DeepSeek API）
python scripts/build_concept_tree.py --output-dir "output/"

# Step 3: 导出 Markmap 文件
python scripts/export_markmap.py --output-dir "output/"
```

> 模式 3 的 HTML 思维导图需要手动生成（见下方「Markmap HTML 生成」）。

### CSV 格式要求

| 列名 | 说明 |
|------|------|
| `题目` | 论文标题 |
| `作者` | 作者 |
| `摘要` | 摘要全文 |

## 输出格式

### 聚类结果 (clusters.json)

```json
{
  "clusters": [
    {
      "cluster_id": 0,
      "size": 26,
      "representative": "Reciprocal Effort in Human-Robot Teaching",
      "members": [
        {
          "paper_id": "A_Humanoid_Robot_s_Effortful...",
          "paper_title": "A Humanoid Robot's Effortful Adaptation...",
          "abstract": "...",
          "rq_id": "RQ1",
          "rq_text": "Does a robot's apparent investment...",
          "rq_text_cn": "如果机器人明显投入努力..."
        }
      ]
    }
  ]
}
```

### 思维导图 (Markmap HTML)

使用 Markmap 库渲染为交互式放射状思维导图：
- 🔍 搜索自动折叠非匹配节点
- ⊞ 点击节点圆圈展开/折叠
- 🖱️ 拖拽平移、滚轮缩放
- 📱 响应式布局，移动端可用
- 🛡️ 零 CDN 依赖（JS 库已本地化）

## 文件结构

```
research-question-map/
├── SKILL.md
├── prompts/
│   ├── extract_rq.md          # DeepSeek 提取 prompt
│   └── build_tree.md          # 概念树构建 prompt（5种关系类型）
└── scripts/
    ├── run_pipeline.py        # 主入口
    ├── _csv_loader.py         # CSV → text/*.json
    ├── parse_pdf_sections.py  # PDF 解析 → text/*.json
    ├── extract_questions.py   # DeepSeek API 提取研究问题（支持并行）
    ├── rq_lib.py              # 共用工具
    ├── cluster_questions.py   # [旧] 词频聚类（已废弃，建议用 semantic_cluster.py）
    ├── semantic_cluster.py    # ★ 语义聚类（两阶段 DeepSeek Chat）
    ├── build_concept_tree.py  # 概念树构建（逐簇 LLM → 合并）
    ├── export_markmap.py      # Markdown + HTML 导出
    ├── export_review_csv.py   # 审核 CSV 导出
    └── retry_extraction.py    # 补提工具
```

## 聚类对比

| 指标 | 旧版 (cluster_questions.py) | 新版 (semantic_cluster.py) |
|------|--------------------------|--------------------------|
| 算法 | 词频余弦相似度 | DeepSeek Chat 语义理解 |
| 中文支持 | ❌ 完全忽略 | ✅ 中英同等权重 |
| 簇数 | 57（人工阈值 0.18） | 15-30（自动确定） |
| 最大簇占比 | 39% | <10% |
| 语义敏感 | "trust"≠"confidence" | "trust"="confidence" |
| 噪声处理 | 43个单条簇 | 显式标记 |
| API 调用 | 0 | ~15次（100样本+15批分配） |

## 依赖

- Python 3.10+
- `openai`（DeepSeek API）
- `pymupdf`（PDF 模式需要）
- 环境变量：`DEEPSEEK_API_KEY`

## Markmap HTML 生成

思维导图 HTML 通过以下本地 JS 文件渲染（无 CDN 依赖）：
- `d3.min.js` — D3.js v7
- `markmap-lib.js` — Markmap 转换库
- `markmap-view.js` — Markmap 渲染库

这些文件需与 HTML 放在同一目录。下载方式：
```bash
curl -o d3.min.js https://unpkg.com/d3@7.9.0/dist/d3.min.js
curl -o markmap-lib.js https://unpkg.com/markmap-lib@0.18.12/dist/browser/index.iife.js
curl -o markmap-view.js https://unpkg.com/markmap-view@0.18.12/dist/browser/index.js
```
