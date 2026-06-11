# Examples

## Sample command

```bash
python ~/.cursor/skills/research-question-map/scripts/run_pipeline.py \
  --papers-dir "C:/path/to/papers" \
  --output-dir "C:/path/to/output"
```

## Output files

- `output/questions/*.json` — per-paper extracted RQs
- `output/review/questions_review.csv` — edit `keep` column before clustering
- `output/research-map.html` — open in browser; click paper chips for title + abstract
- `output/research-map.md` — edit headings, then rerun `export_markmap.py`

## Tested on

Science China review PDFs about humanoid robot heads / AI-driven face robots.
