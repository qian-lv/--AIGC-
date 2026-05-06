"""测试智谱SDK调用 - 从 .env 读取 API Key"""

import base64
import json
import os

from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ZHIPUAI_API_KEY", "")
if not api_key:
    print("错误: 请设置 ZHIPUAI_API_KEY 环境变量或在 .env 文件中配置")
    exit(1)

import zhipuai

zhipuai.api_key = api_key

with open("test.jpg", "rb") as f:
    img_data = f.read()

image_base64 = base64.b64encode(img_data).decode("utf-8")

messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": '识别图片中的食材，返回 JSON 格式：{"ingredients": ["食材1", "食材2"]}'},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
        ],
    }
]

print("开始调用智谱API...")

try:
    response = zhipuai.model_api.invoke(
        model="glm-4v",
        prompt=messages,
        temperature=0.3,
        max_tokens=1000,
    )
    print("响应:", json.dumps(response, ensure_ascii=False, indent=2))
except Exception as e:
    print(f"错误: {e}")
