# Reference

## Section 3 skip logic

Skip Section 3 when **both** are true:

1. Title matches method-like patterns: `method`, `methodology`, `experiment`, `evaluation`, `results`, `implementation`, `materials and methods`, `case study`, `dataset`.
2. First 800 characters lack problem/gap signals: `how`, `whether`, `why`, `what`, `challenge`, `gap`, `problem`, `question`, `objective`, `aim`, `limitation`, `open issue`, `future work`.

Keep Section 3 when title matches: `problem formulation`, `problem statement`, `preliminaries`, `background`, `related work`, or review-topic nouns (e.g. `actuator`, `perception`, `architecture`).

## DeepSeek V4 API

```python
from openai import OpenAI

client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")

# Extraction / tree
client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[...],
    extra_body={"thinking": {"type": "enabled"}, "reasoning_effort": "medium"},
    response_format={"type": "json_object"},
)

# Light tasks
client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[...],
    extra_body={"thinking": {"type": "disabled"}},
)
```

## Markmap workflow

1. Edit `research-map.md` heading hierarchy.
2. Run `export_markmap.py` to rebuild HTML.
3. Open `research-map.html` in a browser.

Optional: import `research-map.md` into XMind (File → Import → Markdown) for drag-and-drop editing.

## Obsidian (optional, not required)

Obsidian can store one note per paper and render heading-based mind maps via plugins, but the primary deliverable for this skill is Markmap HTML + MD.
