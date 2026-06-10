from __future__ import annotations

from pathlib import Path
import shutil
import sqlite3
import time

from .freshrss import make_summary_snippet, upsert_summary_snippet


def fetch_freshrss_entries(db_path: Path, category: str, since_epoch: int, limit: int) -> list[dict[str, object]]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            """
            SELECT e.id, e.guid, e.title, e.author, e.content, e.link, e.date, e.id_feed,
                   f.name AS feed_name, f.url AS feed_url
            FROM entry e
            JOIN feed f ON e.id_feed = f.id
            JOIN category c ON f.category = c.id
            WHERE c.name = ?
              AND e.date >= ?
              AND (lower(e.guid) LIKE '%arxiv.org%'
                   OR lower(e.link) LIKE '%arxiv.org%'
                   OR lower(f.url) LIKE '%arxiv.org%')
            ORDER BY e.date DESC
            LIMIT ?
            """,
            (category, since_epoch, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def backup_db(db_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    target = backup_dir / f"freshrss-db-{stamp}.sqlite"
    shutil.copyfile(db_path, target)
    return target


def update_summary_links(db_path: Path, arxiv_id: str, entry_ids: list[int], summary_url: str) -> int:
    snippet = make_summary_snippet(arxiv_id, summary_url)
    con = sqlite3.connect(db_path)
    try:
        updated = 0
        now = int(time.time())
        for entry_id in sorted(set(entry_ids)):
            row = con.execute("SELECT content FROM entry WHERE id = ?", (entry_id,)).fetchone()
            if not row:
                continue
            new_content, changed = upsert_summary_snippet(row[0] or "", arxiv_id, snippet)
            if not changed:
                continue
            con.execute(
                "UPDATE entry SET content = ?, lastModified = ?, lastUserModified = ? WHERE id = ?",
                (new_content, now, now, entry_id),
            )
            updated += 1
        con.commit()
        return updated
    finally:
        con.close()
