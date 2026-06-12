from __future__ import annotations

from dataclasses import dataclass
import html


@dataclass(frozen=True)
class StarterFeed:
    title: str
    xml_url: str
    html_url: str


STARTER_FEEDS = [
    StarterFeed("arXiv cs.RO", "https://export.arxiv.org/rss/cs.RO", "https://arxiv.org/list/cs.RO/recent"),
    StarterFeed("arXiv cs.AI", "https://export.arxiv.org/rss/cs.AI", "https://arxiv.org/list/cs.AI/recent"),
    StarterFeed("arXiv cs.LG", "https://export.arxiv.org/rss/cs.LG", "https://arxiv.org/list/cs.LG/recent"),
    StarterFeed("arXiv cs.CV", "https://export.arxiv.org/rss/cs.CV", "https://arxiv.org/list/cs.CV/recent"),
    StarterFeed("arXiv cs.CL", "https://export.arxiv.org/rss/cs.CL", "https://arxiv.org/list/cs.CL/recent"),
    StarterFeed("arXiv stat.ML", "https://export.arxiv.org/rss/stat.ML", "https://arxiv.org/list/stat.ML/recent"),
    StarterFeed("arXiv eess.SY", "https://export.arxiv.org/rss/eess.SY", "https://arxiv.org/list/eess.SY/recent"),
    StarterFeed(
        "IJRR OnlineFirst",
        "https://journals.sagepub.com/action/showFeed?type=axatoc&feed=rss&jc=ijr",
        "https://journals.sagepub.com/toc/ijra/0/0",
    ),
    StarterFeed(
        "Soft Robotics OnlineFirst",
        "https://journals.sagepub.com/action/showFeed?type=axatoc&feed=rss&jc=srba",
        "https://journals.sagepub.com/toc/srba/0/0",
    ),
]


def render_starter_opml(category: str = "论文") -> str:
    outlines = "\n".join(f"      {render_feed_outline(feed)}" for feed in STARTER_FEEDS)
    category_text = _xml_attr(category)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<opml version="2.0">\n'
        "  <head>\n"
        "    <title>Oh My RSS starter paper feeds</title>\n"
        "  </head>\n"
        "  <body>\n"
        f'    <outline text="{category_text}" title="{category_text}">\n'
        f"{outlines}\n"
        "    </outline>\n"
        "  </body>\n"
        "</opml>\n"
    )


def render_feed_outline(feed: StarterFeed) -> str:
    title = _xml_attr(feed.title)
    return (
        f'<outline type="rss" text="{title}" title="{title}" '
        f'xmlUrl="{_xml_attr(feed.xml_url)}" htmlUrl="{_xml_attr(feed.html_url)}" />'
    )


def _xml_attr(value: str) -> str:
    return html.escape(value, quote=True)
