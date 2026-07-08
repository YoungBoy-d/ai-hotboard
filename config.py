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

# RSSHub（机器之心 / 量子位 等）
RSSHUB_BASE = os.getenv("RSSHUB_BASE", "https://rsshub.app")

# HTTP 公共
REQUEST_TIMEOUT = 15
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (ai-hotboard daily digest)"}

# 源标识 → 展示名（全部聚焦 AI 技术热点）
SOURCES = {
    "hf": "HuggingFace 模型",
    "arxiv": "arXiv 论文",
    "github": "GitHub AI 仓库",
    "hackernews": "Hacker News",
    "ai_zh": "机器之心·量子位",
    "juejin": "掘金 AI",
}

# 源标识 → 展示图标
SOURCE_ICONS = {
    "hf": "🤗",
    "arxiv": "📄",
    "github": "🐙",
    "hackernews": "🟧",
    "ai_zh": "📰",
    "juejin": "⛏️",
}

# AI 关键词：用于在泛源（HN / GitHub Trending / 掘金）里过滤出 AI 相关条目。
# 英文大小写无关；中文直接子串匹配。短词（AI/LLM/AGI）单独按边界/子串处理。
AI_KEYWORDS_EN = [
    "ai", "a.i.", "llm", "llms", "gpt", "chatgpt", "openai", "anthropic",
    "claude", "gemini", "llama", "llama", "mistral", "deepseek", "qwen",
    "rag", "transformer", "diffusion", "stable diffusion", "midjourney",
    "sora", "dall-e", "neural", "deep learning", "machine learning",
    "agi", "fine-tun", "embedding", "inference", "hugging face",
    "huggingface", "copilot", "multimodal", "language model",
    "foundation model", "text-to-image", "text-to-speech", "mcp",
    "prompt", "vibe coding", "vision-language", "vlm", "moe",
]
AI_KEYWORDS_ZH = [
    "ai", "人工智能", "大模型", "大语言模型", "智能体", "神经网络",
    "深度学习", "机器学习", "自然语言", "多模态", "具身智能", "aigc",
    "生成式", "提示词", "微调", "向量数据库", "知识库", "文生图", "文生视频",
]


def is_ai_related(text: str) -> bool:
    """判断一段文本（标题/描述）是否与 AI 相关，供泛源过滤复用。"""
    if not text:
        return False
    low = text.lower()
    for kw in AI_KEYWORDS_EN:
        if kw in low:
            return True
    for kw in AI_KEYWORDS_ZH:
        if kw in text:
            return True
    return False
