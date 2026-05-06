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
