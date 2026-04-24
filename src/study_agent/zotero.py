from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import ZoteroItem


class ZoteroLookupError(RuntimeError):
    pass


def find_zotero_item(title_query: str, zotero_dir: Path) -> ZoteroItem:
    db = zotero_dir / "zotero.sqlite"
    candidates = [db, zotero_dir / "zotero.sqlite.bak", zotero_dir / "zotero.sqlite.1.bak"]
    errors: list[str] = []

    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            item = _find_in_db(title_query, zotero_dir, candidate)
            if item:
                return item
        except sqlite3.OperationalError as exc:
            errors.append(f"{candidate.name}: {exc}")

    detail = "; ".join(errors) if errors else "no matching title"
    raise ZoteroLookupError(f"Could not find Zotero item for '{title_query}' ({detail}).")


def _find_in_db(title_query: str, zotero_dir: Path, db_path: Path) -> ZoteroItem | None:
    query = f"%{title_query}%"
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=1)
    try:
        rows = conn.execute(
            """
            select d.itemID, v.value
            from itemData d
            join itemDataValues v on d.valueID = v.valueID
            where v.value like ?
            order by length(v.value) asc
            limit 20
            """,
            (query,),
        ).fetchall()
        if not rows:
            return None

        parent_id = _choose_parent_item(conn, rows)
        title = _best_title(rows, title_query)
        abstract = _longest_value(rows)
        attachment = conn.execute(
            """
            select itemID, path
            from itemAttachments
            where parentItemID = ? and contentType = 'application/pdf'
            order by itemID desc
            limit 1
            """,
            (parent_id,),
        ).fetchone()

        attachment_id = int(attachment[0]) if attachment else None
        pdf_path = _resolve_attachment_path(conn, zotero_dir, attachment_id, attachment[1]) if attachment else None
        return ZoteroItem(
            title=title,
            item_id=parent_id,
            attachment_item_id=attachment_id,
            pdf_path=pdf_path,
            abstract=abstract,
            source_db=db_path,
        )
    finally:
        conn.close()


def _choose_parent_item(conn: sqlite3.Connection, rows: list[tuple[int, str]]) -> int:
    for item_id, _ in rows:
        attachment_parent = conn.execute(
            "select parentItemID from itemAttachments where itemID = ?",
            (item_id,),
        ).fetchone()
        if attachment_parent and attachment_parent[0]:
            return int(attachment_parent[0])
        has_pdf = conn.execute(
            "select 1 from itemAttachments where parentItemID = ? and contentType = 'application/pdf' limit 1",
            (item_id,),
        ).fetchone()
        if has_pdf:
            return int(item_id)
    return int(rows[0][0])


def _best_title(rows: list[tuple[int, str]], query: str) -> str:
    values = [value for _, value in rows]
    exactish = [value for value in values if query.lower() in value.lower() and len(value) < 220]
    return min(exactish or values, key=len)


def _longest_value(rows: list[tuple[int, str]]) -> str:
    return max((value for _, value in rows), key=len, default="")


def _resolve_attachment_path(conn: sqlite3.Connection, zotero_dir: Path, attachment_id: int | None, path: str) -> Path | None:
    if not path:
        return None
    if path.startswith("storage:"):
        filename = path.removeprefix("storage:")
        key = None
        if attachment_id is not None:
            row = conn.execute("select key from items where itemID = ?", (attachment_id,)).fetchone()
            key = row[0] if row else None
        if key:
            candidate = zotero_dir / "storage" / key / filename
            if candidate.exists():
                return candidate
        matches = list((zotero_dir / "storage").glob(f"*/{filename}"))
        return matches[0] if matches else zotero_dir / "storage" / filename
    return Path(path)
