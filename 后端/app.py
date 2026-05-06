"""FastAPI主应用 - 专注于拍照识别食材功能"""

import base64
import json
import logging
import re

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from zhipuai import ZhipuAI

from config import (
    ALLOWED_EXTENSIONS,
    API_KEY,
    CORS_ORIGINS,
    MAX_FILE_SIZE,
    MODEL_NAME,
    PROMPT,
    SERVER_HOST,
    SERVER_PORT,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("pengxiaoling")

client = ZhipuAI(api_key=API_KEY)

app = FastAPI(title="烹小灵后端API", description="专注于拍照识别食材功能", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_json_array(text: str) -> list[str]:
    """从 AI 返回文本中提取 JSON 数组。"""
    text = text.strip()

    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1].replace('\\"', '"').replace("\\n", "\n")

    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [str(item).strip() for item in data if item]
    except json.JSONDecodeError:
        match = re.search(r"\[.*?\]", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                if isinstance(data, list):
                    return [str(item).strip() for item in data if item]
            except json.JSONDecodeError:
                pass

    return []


@app.post("/detect")
async def detect_ingredients(image: UploadFile = File(...)):
    """上传图片并识别食材。"""
    if not allowed_file(image.filename):
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {image.filename}")

    try:
        contents = await image.read()
    except Exception as e:
        logger.error("读取图片失败: %s", e)
        raise HTTPException(status_code=400, detail="图片读取失败")

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过限制")

    image_base64 = base64.b64encode(contents).decode("utf-8")
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
            ],
        }
    ]

    logger.info("调用智谱 API, model=%s", MODEL_NAME)
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.3,
            max_tokens=500,
        )
    except Exception as e:
        logger.error("智谱 API 调用失败: %s", e)
        raise HTTPException(status_code=502, detail="AI 服务调用失败")

    content = resp.choices[0].message.content if resp.choices else ""
    if not content:
        raise HTTPException(status_code=500, detail="AI 未返回有效结果")

    logger.info("AI 原始返回: %s", content[:200])

    ingredients = extract_json_array(content)
    if not ingredients:
        raise HTTPException(status_code=500, detail="未能从结果中提取食材")

    return {"ingredients": ingredients, "message": "识别成功"}


@app.post("/api/chat")
async def chat_with_ai(request: dict):
    """AI 聊天接口，根据识别出的食材和饮食偏好生成食谱推荐。"""
    user_message = (request.get("message") or "").strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="请输入饮食目标或偏好")

    ingredients = request.get("ingredients", [])
    ingredients_str = ", ".join(ingredients) if ingredients else ""

    if ingredients_str:
        user_prompt = (
            f"我手上有这些食材：{ingredients_str}。\n"
            f"我的需求：{user_message}\n\n"
            f"请基于我手上的食材来推荐菜谱，不要推荐我没有的食材。"
        )
    else:
        user_prompt = user_message

    system_prompt = (
        "你是一个中文美食营养专家。根据用户手头的食材和饮食需求，"
        "生成一份个性化食谱建议。输出要包含菜品名称、口味描述、主要食材、"
        "制作步骤和热量提示，语言简洁友好。"
        "注意：只推荐用户已有的食材能做的菜，不要推荐用户没有的食材。"
    )

    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
            max_tokens=900,
        )
    except Exception as e:
        logger.error("AI 聊天调用失败: %s", e)
        raise HTTPException(status_code=502, detail="AI 服务调用失败")

    reply = resp.choices[0].message.content if resp.choices else ""
    if not reply:
        raise HTTPException(status_code=500, detail="AI 未返回有效结果")

    return {"reply": reply}


@app.post("/api/generate-recipe-structured")
async def generate_recipe_structured(request: dict):
    """根据识别出的食材和用户偏好，生成结构化菜谱数据。"""
    ingredients = request.get("ingredients", [])
    preference = (request.get("preference") or "").strip()
    ingredients_str = ", ".join(ingredients) if ingredients else "（未提供具体食材）"

    system_prompt = (
        "你是一个专业的中餐厨师和营养师。根据用户提供的食材和需求，"
        "推荐一道美味且健康的菜谱。\n"
        "【重要规则】\n"
        "1. 只使用用户提供的食材来设计菜谱，绝对不要添加用户没有的食材。\n"
        "2. summary 和 recipe 必须完全对应，推荐同一道菜。\n"
        "3. 所有输出内容必须使用中文。"
    )

    user_prompt = (
        f"我手上有这些食材：{ingredients_str}\n"
        f"我的需求：{preference}\n\n"
        "请严格按照以下JSON格式返回（只返回JSON，不要markdown标记，不要其他文字），所有字段值使用中文：\n"
        '{\n'
        '  "summary": "用一两句简短的话推荐菜谱，20字以内",\n'
        '  "recipe": {\n'
        '    "name": "菜名（中文）",\n'
        '    "cook_time": "制作时长（如30分钟）",\n'
        '    "difficulty": "难度（简单/中等/困难）",\n'
        '    "calories": "热量提示（如每份约300千卡）",\n'
        '    "flavor": "口味描述（如酸甜可口）",\n'
        '    "category": "分类（中式/西式/日式/韩式/甜点等）",\n'
        '    "rating": "推荐指数（如★★★★★）",\n'
        '    "ingredients": [\n'
        '      {"name": "食材名（必须来自我提供的食材列表）", "amount": "用量", "emoji": "\U0001f345"}\n'
        '    ],\n'
        '    "steps": [\n'
        '      "步骤1",\n'
        '      "步骤2"\n'
        '    ]\n'
        '  }\n'
        '}\n\n'
        "【重要】summary和recipe中的菜品必须一致，recipe中的食材必须来自我提供的列表。"
        "所有输出必须使用中文。summary控制在20字以内。"
    )

    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1200,
        )
    except Exception as e:
        logger.error("结构化菜谱生成调用失败: %s", e)
        raise HTTPException(status_code=502, detail="AI 服务调用失败")

    content = resp.choices[0].message.content if resp.choices else ""
    if not content:
        raise HTTPException(status_code=500, detail="AI 未返回有效结果")

    logger.info("AI 结构化原始返回: %s", content[:300])

    content = content.strip()
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        logger.error("JSON 解析失败，原始内容: %s", content)
        raise HTTPException(status_code=500, detail="AI 返回格式异常，无法解析")

    summary = data.get("summary", "")
    recipe = data.get("recipe", data)
    if not summary:
        recipe_name = recipe.get("name", "") if isinstance(recipe, dict) else ""
        if recipe_name:
            summary = f"推荐做{recipe_name}，简单又美味！"
        else:
            summary = "推荐菜谱已生成，详情见下方卡片"

    return {"summary": summary, "recipe": recipe, "message": "菜谱生成成功"}


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "烹小灵后端服务运行正常"}


handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host=SERVER_HOST, port=SERVER_PORT, reload=False)
