import sqlite3

from oh_my_rss.db import fetch_freshrss_entries, update_summary_links


def test_fetch_freshrss_entries_includes_non_arxiv_paper_feeds(tmp_path):
    db_path = tmp_path / "db.sqlite"
    con = sqlite3.connect(db_path)
    try:
        con.executescript(
            """
            CREATE TABLE category (id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE feed (id INTEGER PRIMARY KEY, name TEXT, url TEXT, category INTEGER);
            CREATE TABLE entry (
              id INTEGER PRIMARY KEY,
              guid TEXT,
              title TEXT,
              author TEXT,
              content TEXT,
              link TEXT,
              date INTEGER,
              id_feed INTEGER
            );
            INSERT INTO category VALUES (1, '论文'), (2, '新闻');
            INSERT INTO feed VALUES (1, 'IJRR OnlineFirst', 'https://journals.example/rss', 1);
            INSERT INTO feed VALUES (2, 'News', 'https://news.example/rss', 2);
            INSERT INTO entry VALUES (
              10,
              'https://doi.org/10.1177/02783649261234567',
              'IJRR Paper',
              'Grace',
              'A robotics journal abstract.',
              'https://journals.example/doi/10.1177/02783649261234567',
              200,
              1
            );
            INSERT INTO entry VALUES (
              11,
              'https://news.example/item',
              'News Item',
              '',
              'Not a paper category.',
              'https://news.example/item',
              201,
              2
            );
            """
        )
        con.commit()
    finally:
        con.close()

    rows = fetch_freshrss_entries(db_path, "论文", since_epoch=100, limit=10)

    assert [row["id"] for row in rows] == [10]
    assert rows[0]["feed_name"] == "IJRR OnlineFirst"


def test_update_summary_links_accepts_mixed_string_and_integer_entry_ids(tmp_path):
    db_path = tmp_path / "db.sqlite"
    con = sqlite3.connect(db_path)
    try:
        con.executescript(
            """
            CREATE TABLE entry (
              id INTEGER PRIMARY KEY,
              content TEXT,
              lastModified INTEGER,
              lastUserModified INTEGER
            );
            INSERT INTO entry VALUES (10, 'Original abstract.', 0, 0);
            """
        )
        con.commit()
    finally:
        con.close()

    updated = update_summary_links(
        db_path,
        "2606.12345v1",
        ["10", 10],
        "https://example.com/summaries/2606.12345v1.html",
    )

    assert updated == 1
    con = sqlite3.connect(db_path)
    try:
        content = con.execute("SELECT content FROM entry WHERE id = 10").fetchone()[0]
    finally:
        con.close()
    assert "Codex 中文总结" in content
    assert "Original abstract." in content
