from pathlib import Path
import requests
from bs4 import BeautifulSoup


_HEADERS = {"User-Agent": "research-auditor/0.1 (audit bot)"}
_MAX_TEXT = 12000


def fetch_paper_text(paper_url: str | None, pdf_path: str | None, run_dir: Path) -> str:
    if pdf_path:
        return _extract_pdf(Path(pdf_path), run_dir)

    if paper_url:
        return _fetch_url(paper_url, run_dir)

    raise ValueError("Either paper.url or paper.pdf_path must be provided.")


def _fetch_url(url: str, run_dir: Path) -> str:
    resp = requests.get(url, headers=_HEADERS, timeout=30)
    resp.raise_for_status()

    raw_path = run_dir / "artifacts" / "paper_raw.html"
    raw_path.write_bytes(resp.content)

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    cleaned = "\n".join(lines)

    out_path = run_dir / "artifacts" / "paper_text.txt"
    out_path.write_text(cleaned, encoding="utf-8")

    return cleaned[:_MAX_TEXT]


def _extract_pdf(pdf_path: Path, run_dir: Path) -> str:
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf_path))
        pages = []
        for page in doc:
            pages.append(page.get_text())
        text = "\n".join(pages)
        out_path = run_dir / "artifacts" / "paper_text.txt"
        out_path.write_text(text, encoding="utf-8")
        return text[:_MAX_TEXT]
    except ImportError:
        return f"[PDF extraction skipped: PyMuPDF not installed. pip install pymupdf]\nPath: {pdf_path}"
