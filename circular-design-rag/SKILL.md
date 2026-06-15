---
name: circular-design-rag
description: RAG文献检索系统——循环设计/循环经济论文库（436篇），TF-IDF粗召回+DeepSeek语义重排+生成回答。支持中英文查询。项目在Graduation_Project/循环设计rag/。
triggers:
  - circular design
  - circular economy
  - 循环设计
  - 循环经济
  - circular product
  - 文献检索
  - 论文检索
  - 循环设计论文
  - 循环设计文献
  - 循环设计rag
---

# Circular Design RAG

A two-stage retrieval-augmented generation system for 436 circular design / circular economy research papers exported from EndNote.

## Project location

```
C:\Users\77203\Desktop\Graduation_Project\循环设计rag\
```

## Architecture (two-stage)

```
User query
   │
   ▼
[① TF-IDF recall] ── scikit-learn char n-gram (2-3), 8000 dims
   │                  436 docs → 20 candidates (high recall)
   ▼
[② DeepSeek rerank] ── LLM scores each candidate 1-10
   │                  20 → 5 best (high precision semantic)
   ▼
[③ DeepSeek answer] ── Chinese synthesis with [1]~[5] citations
```

**Why two-stage instead of embeddings?**
- HuggingFace blocked from China → can't download sentence-transformers
- DeepSeek has NO embeddings API (404 on all model names tested)
- LLM rerank is better than vector similarity — it reads and understands

## File structure

```
循环设计rag/
├── 循环设计教材.txt          # Raw EndNote export (436 refs)
├── requirements.txt          # scikit-learn scipy openai numpy
├── parse_ris.py              # Step ①: Parse RIS → parsed.json
├── build_index.py            # Step ②: Build TF-IDF index
├── query.py                  # Step ③: Query + rerank + answer
└── data/
    ├── parsed.json           # Full structured data (817KB)
    ├── metadata.json         # Index metadata
    ├── vectorizer.pkl        # TF-IDF vectorizer
    └── tfidf_matrix.npz      # Sparse TF-IDF matrix
```

## Query usage

```bash
cd "C:\Users\77203\Desktop\Graduation_Project\循环设计rag"
python query.py "your question in Chinese or English"
```

Supports bilingual: English abstracts with Chinese queries, Chinese papers, mixed.

## Rebuilding the index

If you add new papers to `循环设计教材.txt`:

```bash
cd "C:\Users\77203\Desktop\Graduation_Project\循环设计rag"
python parse_ris.py          # Re-parse the RIS file
python build_index.py        # Rebuild TF-IDF index
```

## API key

Loaded from `C:\Users\77203\Desktop\Graduation_Project\api key\deepseek api key.txt`. Falls back to `~/.hermes/.env` → environment variable.

## Pitfalls

1. **sklearn version mismatch** — If you rebuild with a different sklearn version, old `.pkl` files won't load. Solution: always run `build_index.py` after `pip install` changes.

2. **Chinese TF-IDF is weak** — char n-gram catches Chinese characters but has no semantic understanding. The DeepSeek rerank fixes this but depends on API availability.

3. **RIS parser** — only tested against EndNote RIS format from this specific export. Other RIS dialects may break.

4. **Cost** — each query ≈ 7000 tokens (rerank + generation) ≈ ¥0.01. Negligible but not zero.

5. **No incremental index** — adding papers requires full rebuild. 436 papers takes ~30s, acceptable.
