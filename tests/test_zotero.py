from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

from study_agent.zotero import find_zotero_item


class ZoteroTests(unittest.TestCase):
    def test_find_item_and_resolve_storage_attachment(self) -> None:
        root = Path.cwd() / ".tmp" / "test_zotero"
        db = root / "zotero.sqlite.bak"
        storage = root / "storage" / "ABC123"
        storage.mkdir(parents=True, exist_ok=True)
        pdf = storage / "Demo Paper.pdf"
        pdf.write_text("fake pdf", encoding="utf-8")
        if db.exists():
            db.unlink()

        conn = sqlite3.connect(db)
        try:
            conn.executescript(
                """
                create table items (itemID integer primary key, key text);
                create table itemDataValues (valueID integer primary key, value text);
                create table itemData (itemID int, fieldID int, valueID int, primary key(itemID, fieldID));
                create table itemAttachments (
                    itemID integer primary key,
                    parentItemID int,
                    linkMode int,
                    contentType text,
                    charsetID int,
                    path text,
                    syncState int,
                    storageModTime int,
                    storageHash text,
                    lastProcessedModificationTime int
                );
                """
            )
            conn.execute("insert into items values (1, 'PARENT')")
            conn.execute("insert into items values (2, 'ABC123')")
            conn.execute("insert into itemDataValues values (1, 'Demo World-Value-Action Model')")
            conn.execute("insert into itemData values (1, 1, 1)")
            conn.execute(
                "insert into itemAttachments values (2, 1, 1, 'application/pdf', null, 'storage:Demo Paper.pdf', 0, null, null, null)"
            )
            conn.commit()
        finally:
            conn.close()

        item = find_zotero_item("World-Value-Action", root)

        self.assertEqual(item.item_id, 1)
        self.assertEqual(item.attachment_item_id, 2)
        self.assertEqual(item.pdf_path, pdf)


if __name__ == "__main__":
    unittest.main()
