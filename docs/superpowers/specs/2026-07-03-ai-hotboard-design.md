# 科技 × AI 每日热点看板 — 设计文档

- **日期**：2026-07-03
- **状态**：Draft（待实现）
- **项目位置**：`e:\work\my-python\ai-hotboard\`

## 1. 背景与目标

构建一个每日自动运行的系统，聚合科技圈与 AI 前沿的多源热点，经 AI（通义千问 `qwen3.7-plus`）加工为中文日报，通过飞书机器人推送互动卡片，并同步发布一个深色科技风的交互式 HTML 看板到公网（GitHub Pages）。

**目标用户**：项目作者本人（前端工程师，持续关注科技 / AI 动态）。

**成功标准**：
- 每天北京时间 09:30 自动在飞书收到一张含全部 Top 标题的互动卡片（可点跳原文）。
- 同步更新公网 HTML 看板，手机 / 任意设备可点开查看。
- 单源故障不影响整体推送；AI 故障有兜底，不阻断主流程。

## 2. 已确认的关键决策

| 维度 | 决策 |
|---|---|
| 飞书投递 | `interactive` 互动卡片（完整标题 + 原文链接 + "查看完整看板"按钮）；**不发图片、不发文件** |
| 数据源 | Hacker News · GitHub Trending · Product Hunt · V2EX · 中文科技媒体 RSS（36氪 / 少数派 / 虎嗅）· 掘金 |
| AI 加工 | 档位 2：`qwen3.7-plus` 生成"今日要点"导语 + 英文标题中文化（DashScope OpenAI 兼容端点） |
| HTML 看板 | 深色科技风（深底 + 青/紫霓虹 + 玻璃拟态），发布到 GitHub Pages |
| 自动化 | GitHub Actions 云端定时，北京时间 09:30，免 VPN、电脑无需开机 |
| 技术栈 | Python：`requests` + `beautifulsoup4` + `feedparser` + `jinja2` + `openai` + `python-dotenv`（不使用 Playwright） |
| 每源条数 | Top 5（共约 30 条） |
| 语言 | 全中文（英文条目由 Qwen 翻译） |

## 3. 系统架构

### 3.1 模块结构

```
ai-hotboard/
├── .github/workflows/daily.yml        # GH Actions：cron 北京09:30
├── .env.example                        # 环境变量模板
├── .gitignore
├── requirements.txt
├── config.py                           # 源配置 / Top N / 端点 / 样式常量 / RSSHUB_BASE
├── main.py                             # 编排：fetch → AI → render；CLI 入口
├── sources/
│   ├── __init__.py
│   ├── base.py                         # Item 数据类 + BaseFetcher 接口
│   ├── hackernews.py                   # HN Algolia API
│   ├── github_trending.py              # requests + BeautifulSoup 抓 trending 页
│   ├── producthunt.py                  # RSSHub /producthunt（免 token）
│   ├── v2ex.py                         # api/topics/hot.json
│   ├── rss_zh.py                       # 少数派官方 + RSSHub(36氪/虎嗅)
│   └── juejin.py                       # recommend feed API
├── ai_summarizer.py                    # qwen3.7-plus → JSON{今日要点, 中文标题}
├── dashboard.py                        # Jinja2 渲染 index.html
├── templates/dashboard.html.j2         # 深色科技风模板 + 内联 CSS/JS
├── feishu.py                           # 构造 interactive 卡片 JSON
├── send_card.py                        # 读 payload.json → POST 飞书卡片
└── output/                             # 本地调试：index.html + payload.json
```

### 3.2 数据流

1. `main.py` 并发抓取 6 个源（每源 Top 5）→ 统一 `Item` 列表（失败源降级，不阻断）。
2. `ai_summarizer.py` 调 `qwen3.7-plus` → JSON `{editorial, translations}`。
3. `dashboard.py` 用 Jinja2 渲染 `output/index.html`；同时写 `output/payload.json`（卡片所需数据）。
4. CI 部署 `output/index.html` 到 gh-pages 分支 → 公网 URL。
5. `send_card.py` 读 `payload.json` → 构造并 POST 飞书互动卡片（链接指向 gh-pages URL）。

> **顺序约定**：CI 中"部署 gh-pages"步骤在"发卡片"之前执行，保证卡片里的看板链接点开是当天最新版。

## 4. 模块详细设计

### 4.1 数据模型（sources/base.py）

```python
@dataclass
class Item:
    source: str          # 源标识，如 "hackernews"
    source_label: str    # 展示名，如 "Hacker News"
    rank: int            # 源内排名 1..5
    title: str           # 原始标题
    title_zh: str        # 中文标题（英文条目由 AI 填，中文条目=原标题）
    url: str             # 原文链接
    score: int           # 热度数值
    score_label: str     # 热度文案，如 "▲ 123"、"★ 1.2k"
    extra: str           # 附加信息，如语言/作者

class BaseFetcher:
    def fetch(self, limit: int = 5) -> list[Item]: ...  # 失败返回空列表并记日志
```

### 4.2 各数据源

| 源 | 取数方式 | 排序依据 | 备注 |
|---|---|---|---|
| Hacker News | Algolia API `hn.algolia.com/api/v1/search?tags=front_page` | points 降序 | 官方、稳定 |
| GitHub Trending | requests GET `github.com/trending?since=daily` + BeautifulSoup | 页面顺序（star） | GH Actions 在美国机房直连；选择器需维护 |
| Product Hunt | RSSHub `/producthunt/today`（feedparser） | 顺序 | 免 token；备选：官方 GraphQL（配 `PH_API_TOKEN`） |
| V2EX | `v2ex.com/api/topics/hot.json` | replies 降序 | 官方、稳定 |
| 中文科技 RSS | 少数派 `sspai.com/feed` + RSSHub(36氪/虎嗅) | 发布时间最新 | RSSHub base 可配置 |
| 掘金 | `api.juejin.cn/recommend_api/v1/article/recommend_all_feed`（POST） | digg_count 降序 | 无需鉴权 |

**容错**：每个 fetcher 独立 `try/except`，失败返回 `[]` 并写日志；主流程对该源标记"获取失败"。

### 4.3 AI 加工（ai_summarizer.py）

- **端点**：`https://dashscope.aliyuncs.com/compatible-mode/v1`（DashScope OpenAI 兼容模式）
- **API key**：环境变量 `DASHSCOPE_API_KEY`
- **模型**：`qwen3.7-plus`
- **单次调用**，要求 JSON 输出：
  ```json
  {
    "editorial": [
      {"text": "一句话要点", "refs": ["item_key", ...]}
    ],
    "translations": {"<item_key>": "中文标题"}
  }
  ```
  - `editorial`：3–5 条跨源"今日要点"，每条带来源引用。
  - `translations`：仅英文条目（HN / GitHub / PH）的中文标题；中文条目不重复翻译。
- **兜底**：调用失败 → `editorial=[]`、`translations={}`，看板 / 卡片回退用原始英文标题，不阻断。

### 4.4 HTML 看板（dashboard.py + templates/dashboard.html.j2）

- Jinja2 渲染为**单文件** `index.html`（CSS / JS 全内联，便于 gh-pages 部署、无外部依赖）。
- **深色科技风**：`#0B0F1A` 底色 + 青/紫渐变点缀 + 玻璃拟态卡片 + 等宽数据字。
- 结构：顶栏（标题 + 日期 / 周几）→ "今日要点" banner → 6 源卡片网格（2 列）→ 页脚（数据源数 / 生成时间）。
- 轻交互：源标签筛选 / Tab 切换（纯 JS）。
- 宽度 1080px，移动端自适应。

### 4.5 飞书卡片（feishu.py + send_card.py）

- 构造 `interactive` 卡片 JSON：
  - **header**：标题 + 日期（彩色 header 模板）。
  - **今日要点**：div + markdown。
  - **6 源 section**：每源 Top 5，序号 + 中文标题 + 热度 + 原文链接（lark md url）。
  - **action button**：「查看完整看板」→ `PAGES_BASE_URL`（gh-pages 公网地址）。
  - **note**：生成时间 / 数据源数。
- `send_card.py` 读 `output/payload.json` → POST 到 `FEISHU_WEBHOOK_URL`。
- **重试**：发送失败重试 1 次，仍失败记日志。

### 4.6 编排与 CLI（main.py）

| 命令 | 行为 |
|---|---|
| `python main.py` | 抓取 → AI → 渲染 `output/index.html` → 写 `output/payload.json`（**不发卡片**，本地预览用） |
| `python main.py --send` | 同上，并额外**立即 POST 飞书卡片**（本地真发测试） |
| `python main.py --source <name>` | 仅抓单个源（调试） |

### 4.7 CI / 自动化（.github/workflows/daily.yml）

- **触发**：`schedule: cron "30 1 * * *"`（UTC）= 北京时间 09:30；附 `workflow_dispatch` 手动触发。
- **Secrets**：`DASHSCOPE_API_KEY`、`FEISHU_WEBHOOK_URL`。
- **环境变量**：`PAGES_BASE_URL`（gh-pages 公网地址）、`RSSHUB_BASE`（默认 `https://rsshub.app`）。
- **steps**：
  1. checkout
  2. setup-python 3.11
  3. `pip install -r requirements.txt`
  4. `python main.py`（生成 index.html + payload.json）
  5. `peaceiris/actions-gh-pages` 部署 `output/index.html` → gh-pages 分支
  6. `python send_card.py`（读 payload.json → POST 飞书卡片）

## 5. 配置（.env / config.py）

环境变量：

| 变量 | 用途 | 必填 |
|---|---|---|
| `DASHSCOPE_API_KEY` | 调用 qwen3.7-plus | 是 |
| `FEISHU_WEBHOOK_URL` | 飞书自定义机器人 webhook | 是 |
| `PAGES_BASE_URL` | gh-pages 公网看板地址（卡片按钮指向） | 是 |
| `RSSHUB_BASE` | RSSHub 实例地址，默认 `https://rsshub.app` | 否 |
| `PH_API_TOKEN` | Product Hunt 官方 API token（可选，切官方源用） | 否 |

`.env.example` 提供模板；CI 用 GitHub Secrets。

## 6. 容错与降级

- **单源失败**：该 section / 卡片显示"获取失败，稍后重试"，其余源正常。
- **Qwen 失败**：跳过 AI 导语，标题回退原文。
- **gh-pages 部署失败**：卡片仍照常发送（链接可能指向上一版），CI 步骤 `continue-on-error`。
- **飞书发送失败**：重试 1 次，失败记日志（不中断部署）。

## 7. 测试策略

- **本地预览**：`python main.py` → 浏览器打开 `output/index.html` 验视觉。
- **单源调试**：`python main.py --source hackernews`。
- **真发验证**：`python main.py --send` 实际推送飞书卡片。
- **CI 端到端**：`workflow_dispatch` 手动触发整条链路。
- fetcher 单元测试（mock 响应）按需补充。

## 8. 风险

- **RSSHub 公共实例不稳定**：36氪 / 虎嗅 / PH 依赖它 → 可配置 `RSSHUB_BASE` 指向自建实例；PH 可切官方 token。
- **GitHub Trending 页结构变更**：BeautifulSoup 选择器需维护。
- **GH Actions cron 不精确**：可能延迟几分钟到十几分钟（平台特性，可接受）。
- **飞书卡片长度限制**：单条消息有大小上限，约 30 条标题应在限内；如超限则每源降为 Top 4。

## 9. 不做（YAGNI）

- 历史数据存储 / 趋势图（首版只做当日）。
- 跨源去重 / 主题聚类（档位 3，未来再说）。
- 多用户 / 订阅。
- 图片 / PDF 版本。

## 10. 后续可能的演进

- 接入更多源（arXiv、Hugging Face Trending、知乎热榜等）。
- 升级到档位 3（跨源去重 + 趋势解读）。
- 历史归档与周/月趋势图。
