import os

from dotenv import load_dotenv

load_dotenv()

TOP_N = 5

# DashScope / 通义千问
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL = "qwen3.7-plus"

# 飞书
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")

# GitHub Pages 看板地址
PAGES_BASE_URL = os.getenv("PAGES_BASE_URL", "")

# RSSHub
RSSHUB_BASE = os.getenv("RSSHUB_BASE", "https://rsshub.app")

# Product Hunt 官方 token（可选）
PH_API_TOKEN = os.getenv("PH_API_TOKEN", "")

# HTTP 公共
REQUEST_TIMEOUT = 15
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (ai-hotboard daily digest)"}

# 源标识 → 展示名
SOURCES = {
    "hackernews": "Hacker News",
    "github": "GitHub Trending",
    "producthunt": "Product Hunt",
    "v2ex": "V2EX",
    "rss_zh": "36氪·少数派·虎嗅",
    "juejin": "掘金",
}
