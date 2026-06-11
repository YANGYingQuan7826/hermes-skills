"""Shared utilities for research-question-map skill."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

METHOD_TITLE_RE = re.compile(
    r"\b(methods?|methodology|experiments?|evaluation|results?|implementation|"
    r"materials and methods|case study|datasets?)\b",
    re.I,
)
PROBLEM_TITLE_RE = re.compile(
    r"\b(problem formulation|problem statement|preliminaries|background|"
    r"related work|literature review|overview)\b",
    re.I,
)
GAP_SIGNAL_RE = re.compile(
    r"\b(how|whether|why|what|which|challenge|gap|problem|question|objective|"
    r"aim|limitation|open issue|future work|remains unclear|lack of)\b",
    re.I,
)
TOP_SECTION_RE = re.compile(
    r"(?m)^([1-9])\s+([A-Za-z][A-Za-z0-9 ,\-/]{4,70})\s*$"
)
INVALID_SECTION_TITLE_RE = re.compile(
    r"\b(CCD|FSR|USB|RGB|RGB-D|cm|mm|Hz|MHz|GPU|CPU|DOF|FSR|IEEE|"
    r"camera|cameras|mouth|mouths|jaw|jaws|eyelid|resistor|sensor|sensors|"
    r"microphone|potentiometer|transducer)\b|"
    r"\d+\s*,\s*\d+|^\d+\s+\w+\s*$",
    re.I,
)
PAGE_FOOTER_RE = re.compile(
    r"(?m)^\d{1,4}\s+[A-Z][A-Za-z\-']+(?:\s+[A-Z][A-Za-z\-']+)?,?\s+et al\.\s*$|"
    r"^SCIENCE CHINA\s*$|^https://doi\.org/.*$|^Received .* published .*$|"
    r"^February \d{4}|^October \d{4}|^•Review•$",
    re.I,
)


def load_dotenv(project_dir: Path | None = None) -> None:
    candidates = []
    if project_dir:
        candidates.append(project_dir / ".env")
    candidates.append(Path.cwd() / ".env")
    candidates.append(Path.home() / ".cursor" / "skills" / "research-question-map" / ".env")
    for path in candidates:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def slugify(name: str) -> str:
    """Generate a filesystem-safe identifier from a title.

    For ASCII-heavy titles: lowercase, replace non-alphanumeric with '_',
    trim to 80 chars.

    For titles containing CJK characters: keep first 2 Chinese chars +
    8-char md5 suffix for uniqueness and readability (e.g. '基于-3f2a1b8c').
    """
    stem = Path(name).stem
    has_cjk = bool(re.search(r"[\u4e00-\u9fff]", stem))

    if has_cjk:
        import hashlib
        cjk_chars = re.findall(r"[\u4e00-\u9fff]", stem)
        prefix = "".join(cjk_chars[:2]) if cjk_chars else "cn"
        hash_suffix = hashlib.md5(stem.encode()).hexdigest()[:8]
        return f"{prefix}-{hash_suffix}"

    # Pure ASCII / Latin path
    cleaned = re.sub(r"[^\w]+", "_", stem, flags=re.UNICODE).strip("_").lower()
    return cleaned[:80] or "paper"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_deepseek_client():
    from openai import OpenAI

    load_dotenv()
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY is not set. Add it to .env or environment variables."
        )
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    return OpenAI(api_key=api_key, base_url=base_url)


def normalize_section_headers(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    text = re.sub(
        r"(?m)^([1-9])\s*\r?\n\s*([A-Z][A-Za-z0-9 ,\-/]{4,70})\s*$",
        r"\1 \2",
        text,
    )
    text = re.sub(
        r"(?m)^([1-9])\s{2,}$\s*\r?\n\s*([A-Z][^\n]{4,80})\s*$",
        r"\1 \2",
        text,
    )
    return text


def extract_title_from_citation(head_text: str) -> str:
    citation = re.search(
        r"(?is)\bCitation:\s*(.+?)(?=\n1\s+Introduction|\n1\s*\n\s*Introduction)",
        head_text,
    )
    if not citation:
        return ""
    chunk = re.sub(r"\s+", " ", citation.group(1)).strip()
    match = re.search(r"et al\.\s*(.+?)\.\s*Sci China", chunk, re.I)
    if match:
        return match.group(1).strip(" .")
    match = re.search(r"^[A-Za-z ,.'\-]+\.\s*(.+?)\.\s*Sci China", chunk, re.I)
    if match:
        return match.group(1).strip(" .")
    return ""


def clean_pdf_text(text: str) -> str:
    text = normalize_section_headers(text)
    raw_lines = text.splitlines()
    merged_lines: list[str] = []
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i].strip()
        if re.fullmatch(r"[1-9]", line) and i + 1 < len(raw_lines):
            nxt = raw_lines[i + 1].strip()
            if re.match(r"^[A-Z]", nxt):
                merged_lines.append(f"{line} {nxt}")
                i += 2
                continue
        merged_lines.append(line)
        i += 1

    lines = []
    for line in merged_lines:
        line = line.strip()
        if not line:
            lines.append("")
            continue
        if PAGE_FOOTER_RE.match(line):
            continue
        if re.match(r"^\d+$", line):
            continue
        lines.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines))


VALID_SECTION_KEYWORDS_RE = re.compile(
    r"\b(introduction|mechanical|actuator|actuators|sensor|sensors|emotional|"
    r"conventional|advanced|design|development|challenge|application|interaction|"
    r"methods|background|overview|formulation|architecture|platform)\b",
    re.I,
)


def is_valid_section_title(title: str) -> bool:
    if len(title) < 8:
        return False
    if re.search(r"et al\.|Vol\.|Iss\.|doi\.org|Copyright|Reproduced with permission", title, re.I):
        return False
    if sum(ch.isdigit() for ch in title) > max(3, len(title) // 3):
        return False
    words = re.findall(r"[A-Za-z]{3,}", title)
    if len(words) < 2:
        return False
    if re.fullmatch(r"[\d,\s\w]+", title) and "," in title:
        return False
    if VALID_SECTION_KEYWORDS_RE.search(title):
        return True
    if INVALID_SECTION_TITLE_RE.search(title):
        return False
    return True


def looks_like_author_line(line: str) -> bool:
    if re.search(r"\bet al\.|University|Laboratory|School of|@|^\d+\s", line, re.I):
        return True
    if re.search(r"[A-Z]{2,}.*\*", line):
        return True
    if re.match(r"^[A-Z]{2,}\s+[A-Z][a-z]", line):
        return True
    if re.match(r"^[A-Z][a-z]+\s+[A-Z][a-z]+$", line) and len(line) < 30:
        return True
    if line.count(",") >= 2 and len(line) < 120:
        return True
    return False


def extract_title_and_abstract(head_text: str) -> tuple[str, str]:
    head_text = normalize_section_headers(head_text)
    abstract = ""
    intro_pos = re.search(r"(?m)^1\s+Introduction\s*$", head_text)

    abstract_match = re.search(
        r"(?is)\bAbstract\b\s*(.+?)(?=\bKeywords\b|\bKey words\b|\b1\s+Introduction\b)",
        head_text,
    )
    if abstract_match:
        abstract = re.sub(r"\s+", " ", abstract_match.group(1)).strip()
    else:
        published = re.search(r"(?is)published online[^.\n]*[.\n]", head_text)
        if published:
            tail = head_text[published.end() :]
            stop = re.search(
                r"(?is)\b(Citation:|Keywords:|Key words:|1\s+Introduction\b|"
                r"humanoid robot head,|© Science China Press)",
                tail,
            )
            abstract = re.sub(r"\s+", " ", tail[: stop.start() if stop else len(tail)]).strip()

    doi = re.search(r"https://doi\.org/[^\s]+", head_text)
    title_region = head_text[doi.end() : intro_pos.start()] if doi and intro_pos else head_text[:4000]
    received = re.search(r"(?is)\bReceived\b", title_region)
    if received:
        title_region = title_region[: received.start()]

    title_lines: list[str] = []
    for ln in title_region.splitlines():
        ln = ln.strip()
        if not ln:
            if title_lines:
                break
            continue
        if re.search(r"Vol\.|Iss\.|Review|SCIENCE CHINA|doi\.org", ln, re.I):
            continue
        if looks_like_author_line(ln):
            break
        if re.fullmatch(r"[A-Z\s\.&\-']+", ln):
            continue
        title_lines.append(ln)

    citation_title = extract_title_from_citation(head_text)
    line_title = re.sub(r"\s+", " ", " ".join(title_lines)).strip()
    title = citation_title or line_title
    return title, abstract[:4000]


def discover_section_headers(cleaned_text: str) -> list[dict[str, str]]:
    intro = re.search(r"(?m)^1\s+Introduction\s*$", cleaned_text)
    if not intro:
        return []

    headers: list[dict[str, str]] = [
        {"number": "1", "title": "Introduction", "header": "1 Introduction"}
    ]
    scan_text = cleaned_text[intro.end() : intro.end() + 120000]
    cursor = 0
    for num in ("2", "3"):
        found = None
        for m in TOP_SECTION_RE.finditer(scan_text, cursor):
            candidate_num, title = m.group(1), m.group(2).strip()
            if candidate_num != num:
                continue
            if not is_valid_section_title(title):
                continue
            found = {"number": num, "title": title, "header": f"{num} {title}"}
            cursor = m.end()
            break
        if found:
            headers.append(found)

    return headers


def find_top_sections(full_text: str) -> list[dict[str, str]]:
    cleaned = clean_pdf_text(full_text)
    headers = discover_section_headers(cleaned)
    if not headers:
        return []

    sections = []
    for i, header in enumerate(headers):
        pattern = rf"(?m)^{re.escape(header['number'])}\s+{re.escape(header['title'][:35])}"
        match = re.search(pattern, cleaned)
        if not match:
            pattern = rf"(?m)^{re.escape(header['header'])}\s*$"
            match = re.search(pattern, cleaned)
        if not match:
            continue
        start = match.end()
        end = len(cleaned)
        if i + 1 < len(headers):
            next_header = headers[i + 1]["header"]
            next_match = re.search(rf"(?m)^{re.escape(next_header)}\s*$", cleaned[start:])
            if next_match:
                end = start + next_match.start()
        body = cleaned[start:end].strip()
        sections.append(
            {
                "number": header["number"],
                "title": header["title"],
                "header": header["header"],
                "text": body[:12000],
            }
        )
    return sections


def should_skip_section_three(section: dict[str, str]) -> bool:
    title = section["title"]
    if PROBLEM_TITLE_RE.search(title):
        return False
    if not METHOD_TITLE_RE.search(title):
        return False
    sample = section["text"][:800]
    return GAP_SIGNAL_RE.search(sample) is None


def select_reading_sections(sections: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[str]]:
    chosen = []
    notes = []
    by_num = {s["number"]: s for s in sections}
    for num in ("1", "2", "3"):
        sec = by_num.get(num)
        if not sec:
            continue
        if num == "3" and should_skip_section_three(sec):
            notes.append(f"Skipped Section 3 ({sec['title']}): pure method/experiment section.")
            continue
        chosen.append(sec)
    return chosen, notes
