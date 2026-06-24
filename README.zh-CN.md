# Oh My RSS

![Oh My RSS GitHub cover](assets/github-cover.png)

[English](README.md) | [简体中文](README.zh-CN.md)

RSS 原生 AI 科研雷达。Oh My RSS 会把 FreshRSS 中的论文订阅转换成中文论文故事总结、静态公开 RSS、分类 RSS，以及月度趋势报告；Reeder 等 RSS 客户端可以直接订阅这些结果。

## 功能

- 从 FreshRSS SQLite 数据库读取 RSS 条目。
- 可选地用 arXiv API 做宽范围发现，让没有订阅到的相关论文也能进入处理队列。
- 从 RSS 标题、链接和正文中识别 arXiv、DOI 以及普通论文链接。
- 自动去重同一篇论文在多个订阅源中重复出现的情况。
- 有直接 PDF 链接时下载论文，并用 `pdftotext` 提取正文；否则回退到 RSS 摘要。
- 渲染论文首页 PNG 预览图，并嵌入 Codex 总结页面。
- 按研究领域分类，例如机器人学习、操作、类人/腿足机器人、VLA、导航、SLAM、感知、安全/控制、具身 AI、Benchmark 等。
- 调用 Codex CLI 生成中文总结，结构包括：
  - `Motivation`
  - `Contribution`
  - `技术原理`
  - `实验设计及分析`
  - `原文链接`
- 生成支持 MathJax 的静态 HTML 页面。
- 生成公开主 RSS：`feed.xml`。
- 在公开首页暴露 RSS 和 OPML 自动发现链接。
- 生成月度研究雷达 RSS，包含趋势表和 SVG 图表。
- 生成热点研究方向 RSS，每个热点方向一条 item。
- 生成热点关键词 RSS，跟踪 VLA、diffusion policy、humanoid、SLAM、safety filter、sim-to-real 等术语。
- 生成源健康检查雷达，记录每个发现源的候选数量、抓取失败、突然归零和过期 venue 年份。
- 使用基于 hash 的详情页 URL，避免浏览器和 RSS 客户端读到旧缓存。
- 可选地备份 FreshRSS 数据库，并把 FreshRSS 条目更新成可点击的总结链接。
- 输出常见论文订阅源的 starter OPML，方便新的 FreshRSS 部署快速开始。
- 在导入 FreshRSS 前校验 OPML 中的 feed URL 是否有效。

## 项目目标

Oh My RSS 不是要替代 RSS 阅读器，而是要成为一个自托管的 AI 科研雷达。长期目标是让用户接入论文源、会议源、期刊源、实验室博客和新闻源，然后发布一条干净的知识流：包含 AI 总结、研究领域分类、趋势报告和 RSS 原生分发。

## 运行要求

- Python 3.11+
- 使用 SQLite 的 FreshRSS
- `curl`
- Poppler 提供的 `pdftotext`
- PyMuPDF，作为 Python 依赖自动安装
- 运行任务的机器上已经完成 Codex CLI 授权

## 快速开始

```bash
git clone https://github.com/LiuWhale/oh-my-rss.git
cd oh-my-rss
python3.11 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
oh-my-rss init-config --output config.yaml
```

编辑 `config.yaml`，然后检查环境：

```bash
oh-my-rss doctor --config config.yaml
```

环境检查通过后，生成总结：

```bash
oh-my-rss run --config config.yaml --limit 1
```

如果只想预览会处理哪些论文，不调用 Codex：

```bash
oh-my-rss run --config config.yaml --dry-run --limit 5
```

运行后或发布前，可以校验生成的公开站点文件：

```bash
oh-my-rss validate-site --site-dir ./site
```

生成 FreshRSS 论文订阅 starter OPML：

```bash
oh-my-rss print-starter-opml --output starter-paper-feeds.opml
```

导入前先校验：

```bash
oh-my-rss validate-opml --opml starter-paper-feeds.opml
```

然后把 OPML 导入 FreshRSS，并把 `freshrss.category` 设置为导入后的论文分类。

## 配置

参考 [`configs/example.yaml`](configs/example.yaml)。

关键字段：

- `freshrss.db_path`：FreshRSS `db.sqlite` 路径。
- `freshrss.category`：要扫描的 FreshRSS 分类，例如 `论文` 或 `Papers`。
- `site.output_dir`：HTML 文件写入的本地目录。
- `site.public_base_url`：生成页面的公开 URL 前缀。
- `codex.command`：调用 Codex CLI 的命令。
- `arxiv_discovery.enabled`：可选的宽范围 arXiv API 发现。开启后，Oh My RSS 会按关键词抓取 arXiv 候选，并根据标题和摘要内容重新分类，而不是把 arXiv subject 名称直接作为公开分类。
- `arxiv_discovery.max_results`：每次运行最多检查的 arXiv API 候选数量。
- `arxiv_discovery.keywords`：可选的替换关键词列表。留空时使用内置的 robotics、embodied AI、VLA、navigation、SLAM、tactile、control-barrier 等发现词。
- `runtime.state_dir`：状态、PDF 缓存、prompt、日志和数据库备份目录。

## 公开 Feed

每次运行会写出：

- `index.html`：公开总结索引
- `feed.xml`：生成总结的公开主 RSS
- `feeds.json`：所有公开 RSS 和 OPML 入口的机器可读目录
- `status.json`：服务状态摘要，包含总结数量、分类数量、报告数量、最新总结和公开 feed URL
- `robots.txt` 和 `sitemap.xml`：公开首页、总结页、月度报告、热点方向、热点关键词的爬虫发现文件
- `opml.xml`：完整 OPML，包含主 feed、分类 feed、月度报告 feed、热点方向 feed 和热点关键词 feed
- `categories/*.xml`：按来源或分类拆分的 RSS
- `categories/index.json`：机器可读的分类 feed 列表
- `categories/opml.xml`：只包含分类 feed 的 OPML，适合 RSS 客户端导入
- `reports/monthly.xml`：月度研究趋势报告 RSS
- `reports/monthly/YYYY-MM.html`：月度报告页面，包含方向柱状图、来源分布、动态图表和代表论文
- `reports/trending.xml`：热点研究方向 RSS
- `reports/trending/*.html`：方向页面，包含趋势数量、来源和代表论文
- `reports/keywords.xml`：热点关键词 RSS
- `reports/keywords/*.html`：关键词页面，包含趋势数量、来源和代表论文
- `reports/source-health.xml`：源健康检查 RSS
- `reports/source-health/index.html`：源健康雷达页面，展示每个源的数量和告警
- `reports/source-health/index.json`：机器可读的源健康报告
- `manifest.json`：机器可读的总结元数据

混合论文来源会使用规范化后的分类名：发布时会移除开头的 `arXiv ` 前缀，并清理旧版本留下的 `categories/arxiv-*.xml` 文件。

新生成的记录会包含 `paper_id`、`source_kind` 和 `research_domains`。`source_kind` 可以是 `arXiv`、`DOI` 或 `RSS`。分类 feed 和月度报告会优先使用研究领域标签；只有无法推断研究主题时，才回退到规范化后的 feed 名称。

用户可以订阅主 feed：

```text
<site.public_base_url>/feed.xml
```

也可以订阅分类 feed。RSS 客户端通常不能直接订阅 JSON；如果想一键导入完整订阅，请使用完整 OPML：

```text
<site.public_base_url>/opml.xml
```

如果只想导入主题或来源 feed，使用分类 OPML：

```text
<site.public_base_url>/categories/opml.xml
```

JSON 只适合需要机器可读列表的集成：

```text
<site.public_base_url>/categories/index.json
```

如果集成需要拿到所有公开 RSS 和 OPML 入口，使用：

```text
<site.public_base_url>/feeds.json
```

轻量监控或健康检查可以使用：

```text
<site.public_base_url>/status.json
```

爬虫发现文件：

```text
<site.public_base_url>/robots.txt
<site.public_base_url>/sitemap.xml
```

月度趋势报告单独发布为 RSS：

```text
<site.public_base_url>/reports/monthly.xml
```

每个月度报告页面都包含动态图表、方向柱状图、来源分布图、摘要表，以及指向底层 Codex 论文总结的链接。

热点研究方向也会发布为独立 feed：

```text
<site.public_base_url>/reports/trending.xml
```

每个热点方向 item 会链接到一个方向页面，页面包含来源数量、近期趋势数量、代表论文，以及对应的论文总结链接。

具体关键词趋势发布为另一个 RSS：

```text
<site.public_base_url>/reports/keywords.xml
```

每个关键词 item 会链接到一个页面，用来追踪 VLA、diffusion policy、humanoid、SLAM、safety filter、sim-to-real 等术语在近期论文总结中的变化。

源健康检查发布为运维雷达 feed：

```text
<site.public_base_url>/reports/source-health.xml
```

源健康页面和 JSON 报告会展示哪些发现源产生了新候选、哪些源抓取失败、哪些源在之前非零后突然变成零，以及哪些 venue-year 配置看起来已经过期：

```text
<site.public_base_url>/reports/source-health/index.html
<site.public_base_url>/reports/source-health/index.json
```

这些 feed 都是静态文件。其他人可以读取生成的总结，而不需要登录你的 FreshRSS 账户，也不会共享你的已读/未读状态。

## 定时运行

生成一个带锁的 10 分钟 cron：

```bash
oh-my-rss print-cron \
  --cwd /opt/oh-my-rss \
  --config config.yaml \
  --limit 1 \
  --interval-minutes 10 \
  --log-path state/cron.log \
  --venv .venv
```

命令会输出类似这样的 cron 行：

```cron
*/10 * * * * cd /opt/oh-my-rss && . .venv/bin/activate && flock -n /tmp/oh-my-rss.lock oh-my-rss run --config config.yaml --limit 1 >> state/cron.log 2>&1
```

把这行粘贴到 cron 或等价的调度器里即可。如果 `oh-my-rss` 已安装在调度器默认 `PATH` 中，可以使用 `--no-venv`。

## 部署说明

- Synology NAS 和 FreshRSS Docker 部署见 [`docs/synology-freshrss.md`](docs/synology-freshrss.md)。
- 添加 RSS 订阅、分组和 OPML 导入见 [`docs/feed-management.md`](docs/feed-management.md)。
- Reeder/FreshRSS 行为说明见 [`docs/reeder-workflow.md`](docs/reeder-workflow.md)。

Docker Compose 场景下，只有需要覆盖默认运行设置时才需要把 `.env.example` 复制为 `.env`。compose 文件已经内置默认值，不要求本地必须存在 `.env`。

## 开发

```bash
PYTHONPATH=src pytest -q
ruff check .
```

## 安全

不要提交：

- FreshRSS 数据库文件
- Codex 授权文件
- 真实域名、私有 IP、代理凭据或用户账户
- 生成的 PDF 缓存

使用 `.env.example` 和 `configs/example.yaml` 作为模板。

## 许可证

MIT
