"""详细测试 - 从 .env 读取 API Key"""

import json
import os

from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ZHIPUAI_API_KEY", "")
if not api_key:
    print("错误: 请设置 ZHIPUAI_API_KEY 环境变量或在 .env 文件中配置")
    exit(1)

import base64

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

print("调用智谱API...")
response = zhipuai.model_api.invoke(
    model="glm-4v",
    prompt=messages,
    temperature=0.3,
    max_tokens=1000,
)

print("智谱响应:")
print(json.dumps(response, ensure_ascii=False, indent=2))

if response.get("success"):
    data = response.get("data", {})
    choices = data.get("choices", [])
    if choices and len(choices) > 0:
        content = choices[0].get("content", "")
        print(f"\n原始content: {content}")

        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])
            print(f"清理后的content: {content}")

        try:
            result = json.loads(content)
            print(f"\n解析后的result: {result}")
        except json.JSONDecodeError as e:
            print(f"\nJSON解析失败: {e}")
