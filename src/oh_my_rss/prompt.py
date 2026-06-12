from __future__ import annotations

from .arxiv import Paper


def build_summary_prompt(paper: Paper) -> str:
    feeds = ", ".join(paper.feed_names)
    pdf_note = (
        f"已从 PDF 正文自动提取 {paper.pdf_text_chars} 个字符，并筛选 "
        f"{paper.pdf_context_chars} 个字符作为依据。"
        if paper.pdf_context
        else f"PDF 正文未成功提取；只能基于 RSS 摘要。原因：{paper.pdf_error or '未知'}"
    )
    pdf_block = paper.pdf_context or "(无 PDF 正文摘录)"
    abstract = paper.abstract or "(FreshRSS 条目没有提供摘要正文)"
    paper_id = paper.paper_id or paper.arxiv_id
    pdf_url = paper.pdf_url or "无直接 PDF 链接"
    if paper.source_kind == "arXiv":
        source_metadata = f"""arXiv ID: {paper.arxiv_id}
标题: {paper.title}
作者: {paper.authors or '未知'}
来源 Feed: {feeds or '未知'}
arXiv 页面: {paper.abs_url}
PDF: {pdf_url}"""
    else:
        source_metadata = f"""论文 ID: {paper_id}
来源类型: {paper.source_kind}
标题: {paper.title}
作者: {paper.authors or '未知'}
来源 Feed: {feeds or '未知'}
原文页面: {paper.abs_url}
PDF: {pdf_url}"""
    return f"""你是一个严谨的中文科研论文阅读助手。请优先基于下面的 PDF 正文摘录生成论文故事版中文总结，RSS 摘要只作为补充。目标是讲清楚一篇论文的完整故事，而不是罗列所有细节。不要编造正文摘录没有支持的内容。

输出要求：
- 使用 Markdown。
- 总长度控制在 900-1300 个中文字符之间。这是研究速读，不是复现实验笔记。
- 列表请使用 `-` 项目符号，不要使用编号列表；不要使用多层嵌套列表。
- 第一行是一级标题：# {paper.title}
- 必须严格包含并按顺序使用这些二级标题：## Motivation、## Contribution、## 技术原理、## 实验设计及分析、## 原文链接。
- Motivation 用 1 个短段落说明核心问题和为什么现有方法不够。
- Contribution 用 2-3 个要点说明本文做了什么，以及这些贡献如何支撑主线。
- 技术原理用 3-4 个高密度要点讲清楚核心机制：输入是什么、关键模块如何连接、训练/推理如何工作、为什么这种设计能解决 Motivation。不要逐层复述所有网络结构、所有参数或所有实现细节。
- 实验设计及分析用 3-4 个高密度要点讲清楚证据链：实验对象/任务类别、主要 baseline 类型、主结果、最关键的消融或分析、局限。不要逐项罗列所有任务名、所有 baseline 名和所有表格数字；只保留最能支撑论文结论的 2-4 个关键数字。
- 公式最多保留 1 个，而且只有在它是理解方法主线所必需时才保留。保留公式时必须使用标准 LaTeX display math：`$$ ... $$`；不要用反引号包公式，不要使用 Unicode 数学符号，如 ∇、⊙、Ẑ，应写成 `\\nabla`、`\\odot`、`\\hat{{Z}}` 等标准 LaTeX。
- 若公式不是必要，请用自然语言解释机制。
- 如果 PDF 摘录仍缺某些细节，写“PDF 摘录未覆盖该细节”。
- 原文链接中列出原文页面和 PDF（如果有）。

论文元数据：
{source_metadata}
PDF 提取状态: {pdf_note}

RSS 摘要（补充）：
{abstract}

PDF 正文摘录（主要依据，可能含版式噪声）：
{pdf_block}
"""
