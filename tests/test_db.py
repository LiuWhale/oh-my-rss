import sqlite3

from oh_my_rss.db import fetch_freshrss_entries


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
