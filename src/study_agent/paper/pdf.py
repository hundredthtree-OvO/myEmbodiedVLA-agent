from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class PdfDocument:
    text: str
    page_texts: list[str]
    text_backend: str
    page_backend: str


def extract_pdf_text(path: Path, timeout_seconds: int = 120) -> str:
    return extract_pdf_document(path, timeout_seconds).text


def extract_pdf_document(path: Path, timeout_seconds: int = 120) -> PdfDocument:
    del timeout_seconds  # PyMuPDF extraction is local and synchronous.
    if not path.exists():
        raise FileNotFoundError(f"PDF does not exist: {path}")

    document = _open_pdf_document(path)
    try:
        page_texts = [_normalize_page_text(page.get_text("text")) for page in document]
    finally:
        document.close()

    text = "\n\n".join(page_texts).strip()
    return PdfDocument(
        text=text,
        page_texts=page_texts,
        text_backend="pymupdf",
        page_backend="pymupdf",
    )


def focus_excerpt(text: str, focus_terms: list[str], max_chars: int = 14000) -> str:
    if not text:
        return ""
    lowered = text.lower()
    positions: list[int] = []
    for term in focus_terms:
        idx = lowered.find(term.lower())
        if idx >= 0:
            positions.append(idx)

    if not positions:
        keyword_positions = [lowered.find(term) for term in ["latent", "planning", "inference", "attention", "action"]]
        positions = [idx for idx in keyword_positions if idx >= 0]

    if not positions:
        return text[:max_chars]

    center = min(positions)
    start = max(0, center - max_chars // 3)
    end = min(len(text), start + max_chars)
    return text[start:end]


def extract_pdf_page_texts(path: Path) -> list[str]:
    return extract_pdf_document(path).page_texts


def select_key_figure_pages(page_texts: list[str], focus_terms: list[str], max_pages: int = 4) -> list[int]:
    scored: list[tuple[int, int]] = []
    lowered_focus = [term.lower() for term in focus_terms if term]
    normalized_focus_tokens = {
        piece
        for term in lowered_focus
        for piece in re.split(r"[^a-z0-9]+", term.replace("_", " ").replace("-", " "))
        if piece
    }
    for index, text in enumerate(page_texts, start=1):
        lowered = text.lower()
        score = 0
        if re.search(r"\bfigure\b|\bfig\.\b", lowered):
            score += 5
        if any(token in lowered for token in ("architecture", "overview", "method", "policy", "attention")):
            score += 3
        if any(token in lowered for token in ("query", "kv", "cross attention", "self attention", "decoder", "action")):
            score += 2
        for term in lowered_focus:
            if term and term in lowered:
                score += 2
        for token in normalized_focus_tokens:
            if token and token in lowered:
                score += 1
        if len(lowered.strip()) < 120:
            score -= 1
        if score > 0:
            scored.append((score, index))

    if not scored:
        fallback_count = min(max_pages, len(page_texts))
        return list(range(1, fallback_count + 1))
    ordered = [index for _, index in sorted(scored, key=lambda item: (-item[0], item[1]))]
    unique: list[int] = []
    for page in ordered:
        if page not in unique:
            unique.append(page)
        if len(unique) >= max_pages:
            break
    return unique


def render_pdf_pages(path: Path, pages: list[int], output_dir: Path, dpi: int = 144) -> list[Path]:
    document = _open_pdf_document(path)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        rendered: list[Path] = []
        zoom = max(dpi, 72) / 72.0
        matrix = None

        for page_number in pages:
            target = output_dir / f"page-{page_number:02d}.png"
            if target.exists():
                rendered.append(target)
                continue
            if page_number < 1 or page_number > document.page_count:
                continue
            if matrix is None:
                fitz = _import_fitz()
                matrix = fitz.Matrix(zoom, zoom)
            page = document.load_page(page_number - 1)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            pixmap.save(target)
            if target.exists():
                rendered.append(target)
        return rendered
    finally:
        document.close()


def _normalize_page_text(text: str) -> str:
    return (text or "").replace("\x00", "").strip()


def _open_pdf_document(path: Path):
    fitz = _import_fitz()
    return fitz.open(path)


def _import_fitz():
    try:
        import fitz
    except ImportError as exc:  # pragma: no cover - exercised in real env, not unit tests
        raise RuntimeError("PyMuPDF is required for PDF extraction and page rendering.") from exc
    return fitz
