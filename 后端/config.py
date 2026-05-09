"""配置文件 - 所有敏感信息从环境变量读取"""

import os
from dotenv import load_dotenv

load_dotenv()  # 从 .env 文件加载

# 智谱API配置
API_KEY = os.getenv("ZHIPUAI_API_KEY", "")
API_URL = os.getenv("ZHIPUAI_API_URL", "https://open.bigmodel.cn/api/paas/v4/chat/completions")
MODEL_NAME = os.getenv("ZHIPUAI_MODEL", "glm-4v")

# 识别食材的 prompt
PROMPT = (
    "你是一个食材识别专家。请仔细看这张图片，识别出图中的主要食材（最多返回10种）。"
    '只返回JSON数组格式，不要包含其他文字，格式如下：["食材1", "食材2", "食材3"]。'
    "只返回数组，不要有markdown标记或其他说明文字。"
)

# 服务器配置
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8085"))

# 图片处理配置
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))  # 默认 10MB
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

# CORS配置
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# DeepSeek API 配置（仅在后端，不要写在前端）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com").rstrip("/")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash").strip() or "deepseek-v4-flash"
DEEPSEEK_TIMEOUT = int(os.getenv("DEEPSEEK_TIMEOUT", "45"))

# 百度短语音识别配置（仅在后端，不要写在前端）
BAIDU_ASR_APP_ID = os.getenv("BAIDU_ASR_APP_ID", "").strip()
BAIDU_ASR_API_KEY = os.getenv("BAIDU_ASR_API_KEY", "").strip()
BAIDU_ASR_SECRET_KEY = os.getenv("BAIDU_ASR_SECRET_KEY", "").strip()
BAIDU_ASR_DEV_PID = int(os.getenv("BAIDU_ASR_DEV_PID", "1537"))
BAIDU_ASR_CUID = os.getenv("BAIDU_ASR_CUID", "cooking-agent-local").strip()[:60] or "cooking-agent-local"
BAIDU_ASR_TIMEOUT = int(os.getenv("BAIDU_ASR_TIMEOUT", "20"))
