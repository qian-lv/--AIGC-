"""FastAPI主应用 - 专注于拍照识别食材功能"""

import base64
import json
import logging
import os
import re
import time
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from zhipuai import ZhipuAI

from config import (
    ALLOWED_EXTENSIONS,
    API_KEY,
    BAIDU_ASR_API_KEY,
    BAIDU_ASR_APP_ID,
    BAIDU_ASR_CUID,
    BAIDU_ASR_DEV_PID,
    BAIDU_ASR_SECRET_KEY,
    BAIDU_ASR_TIMEOUT,
    CORS_ORIGINS,
    DEEPSEEK_API_BASE,
    DEEPSEEK_API_KEY,
    DEEPSEEK_MODEL,
    DEEPSEEK_TIMEOUT,
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


BAIDU_TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
BAIDU_ASR_URL = "http://vop.baidu.com/server_api"
_baidu_token_cache: dict = {"access_token": "", "expires_at": 0}


def _deepseek_chat(messages: list, temperature: float = 0.65, max_tokens: int = 900) -> str:
    """Call DeepSeek Chat Completions API. The API key stays only on the backend."""
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("后端没有配置 DEEPSEEK_API_KEY。请在 后端/.env 中填写。")
    url = f"{DEEPSEEK_API_BASE}/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": DEEPSEEK_MODEL, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": False}
    response = requests.post(url, headers=headers, json=payload, timeout=DEEPSEEK_TIMEOUT)
    if response.status_code >= 400:
        raise RuntimeError(f"DeepSeek API 请求失败：HTTP {response.status_code}，{response.text}")
    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"DeepSeek API 未返回 choices：{data}")
    message = choices[0].get("message") or {}
    reply = (message.get("content") or choices[0].get("text") or "").strip()
    if not reply:
        raise RuntimeError(f"DeepSeek API 返回内容为空：{data}")
    return reply


def _safe_history(raw_history, max_items: int = 12) -> list:
    if not isinstance(raw_history, list):
        return []
    cleaned = []
    for item in raw_history[-max_items:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = str(item.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            cleaned.append({"role": role, "content": content[:1200]})
    return cleaned


def _recipe_context_to_text(recipe_context: dict) -> str:
    if not isinstance(recipe_context, dict):
        return "用户当前在做饭页面，但没有传入具体菜谱。"
    title = str(recipe_context.get("title") or "当前菜谱").strip()
    meta = str(recipe_context.get("meta") or "").strip()
    ingredients = recipe_context.get("ingredients") or []
    if isinstance(ingredients, list):
        ingredients_text = "、".join([str(x).strip() for x in ingredients if str(x).strip()])
    else:
        ingredients_text = str(ingredients)
    page = str(recipe_context.get("page") or "").strip()
    return f"菜谱：{title}\n页面信息：{meta}\n已有食材：{ingredients_text or '页面未列出'}\n来源页面：{page or '未知'}"


def _build_cooking_messages(user_message: str, recipe_context: dict, history: list) -> list:
    recipe_text = _recipe_context_to_text(recipe_context)
    system_prompt = (
        '你是「糯糯」，一个小浣熊形象的中文做饭语音智能体，正在通过类似豆包语音通话的页面陪用户做饭。\n'
        '你的任务：像真人厨友一样，一步一步指导用户完成当前菜谱，并持续给情绪价值。\n\n'
        f'当前菜谱上下文：\n{recipe_text}\n\n'
        '回复规则：\n'
        '1. 面向语音播报，回复要自然、温暖、有陪伴感，先肯定用户，再给下一步。\n'
        '2. 一次只讲一个明确步骤，不要一次性把完整菜谱全部讲完。\n'
        '3. 每次回复尽量控制在 30 到 120 个汉字，适合 TTS 朗读。\n'
        '4. 用户说「好了 / 做好了 / 下一步 / 继续」时，推进到下一步；用户卡住时，先安抚再解释。\n'
        '5. 涉及刀具、热油、明火、烤箱、过敏原、食材变质时，要简短提醒安全。\n'
        '6. 不要编造自己能看见用户画面；如果需要确认状态，就直接问用户。\n'
        '7. 不输出 Markdown 表格，不使用复杂编号。可以用短句和少量标点。'
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message[:1200]})
    return messages


def _get_baidu_access_token() -> str:
    if not BAIDU_ASR_API_KEY or not BAIDU_ASR_SECRET_KEY:
        raise RuntimeError("后端没有配置百度 ASR：请在 .env 中填写 BAIDU_ASR_API_KEY 和 BAIDU_ASR_SECRET_KEY。")
    now = int(time.time())
    cached = _baidu_token_cache.get("access_token")
    if cached and int(_baidu_token_cache.get("expires_at", 0)) > now + 300:
        return str(cached)
    params = {"grant_type": "client_credentials", "client_id": BAIDU_ASR_API_KEY, "client_secret": BAIDU_ASR_SECRET_KEY}
    response = requests.post(BAIDU_TOKEN_URL, params=params, timeout=BAIDU_ASR_TIMEOUT)
    if response.status_code >= 400:
        raise RuntimeError(f"百度 access_token 获取失败：HTTP {response.status_code}，{response.text}")
    data = response.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"百度 access_token 返回为空：{data}")
    expires_in = int(data.get("expires_in", 2592000))
    _baidu_token_cache["access_token"] = token
    _baidu_token_cache["expires_at"] = now + expires_in - 600
    return str(token)


def _baidu_asr_from_wav_bytes(wav_bytes: bytes) -> dict:
    if not wav_bytes:
        raise RuntimeError("没有收到音频数据。")
    if len(wav_bytes) < 1200:
        raise RuntimeError("收到的音频太短，请说完整一句话。")
    if len(wav_bytes) > 10 * 1024 * 1024:
        raise RuntimeError("单次语音过长，请每次说一句短句。")
    token = _get_baidu_access_token()
    payload = {
        "format": "wav",
        "rate": 16000,
        "channel": 1,
        "cuid": BAIDU_ASR_CUID,
        "token": token,
        "dev_pid": BAIDU_ASR_DEV_PID,
        "speech": base64.b64encode(wav_bytes).decode("utf-8"),
        "len": len(wav_bytes),
    }
    response = requests.post(BAIDU_ASR_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=BAIDU_ASR_TIMEOUT)
    if response.status_code >= 400:
        raise RuntimeError(f"百度 ASR 请求失败：HTTP {response.status_code}，{response.text}")
    data = response.json()
    err_no = int(data.get("err_no", -1))
    if err_no != 0:
        err_msg = data.get("err_msg", "unknown error")
        sn = data.get("sn", "")
        friendly = {
            2000: "音频数据为空或格式不对。",
            3300: "参数错误，请检查 wav/16000/单声道 配置。",
            3301: "音频质量过差或没有清晰人声，请靠近麦克风再说。",
            3302: "鉴权失败，请检查百度 API Key / Secret Key。",
            3303: "百度服务端识别异常，请稍后重试。",
            3304: "请求并发或次数受限，请稍后重试。",
            3305: "免费额度或 QPS 可能受限，请检查百度控制台。",
        }.get(err_no, "百度 ASR 没有识别成功。")
        raise RuntimeError(f"{friendly} 百度返回：err_no={err_no}, err_msg={err_msg}, sn={sn}")
    result = data.get("result") or []
    text = str(result[0]).strip() if result else ""
    if not text:
        raise RuntimeError(f"百度 ASR 识别结果为空：{data}")
    return {"text": text, "raw": data}


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
async def chat_with_ai(request: Request):
    """AI 聊天接口，根据识别出的食材和饮食偏好生成食谱推荐。"""
    body = await request.json()
    user_message = (body.get("message") or "").strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="请输入饮食目标或偏好")

    ingredients = body.get("ingredients", [])
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
async def generate_recipe_structured(request: Request):
    """根据识别出的食材和用户偏好，生成结构化菜谱数据。"""
    body = await request.json()
    ingredients = body.get("ingredients", [])
    preference = (body.get("preference") or "").strip()
    ingredients_str = ", ".join(ingredients) if ingredients else "（未提供具体食材）"

    system_prompt = (
        "你是一个专业的中餐厨师和营养师。根据用户提供的食材和需求，"
        "推荐一道美味且健康的菜谱。\n"
        "【重要规则】\n"
        "1. 只使用用户提供的食材来设计菜谱，绝对不要添加用户没有的食材。\n"
        "2. 菜谱食材列表必须包含这道菜会用到的所有食材，不能遗漏任何一个。"
        "例如：用户提供[鸡蛋, 番茄, 葱]，做番茄炒蛋时，食材列表必须包含番茄和鸡蛋，不能只列番茄。\n"
        "3. summary 和 recipe 必须完全对应，推荐同一道菜。\n"
        "4. 所有输出内容必须使用中文。"
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
        '      {"name": "食材名", "amount": "用量", "emoji": "对应emoji"}\n'
        '    ],\n'
        '    "steps": [\n'
        '      "步骤1",\n'
        '      "步骤2"\n'
        '    ]\n'
        '  }\n'
        '}\n\n'
        "【关键】ingredients数组必须列出所有会用到的食材，不能遗漏。"
        f"你只能从以下列表中选取食材：{ingredients_str}，不能添加列表之外的食材。"
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
            max_tokens=2048,
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

    # 后处理：补齐 AI 遗漏的用户食材
    if isinstance(recipe, dict) and ingredients:
        existing_names = {i["name"] for i in recipe.get("ingredients", [])}
        recipe_text = recipe.get("name", "") + " " + " ".join(recipe.get("steps", []))
        for user_ing in ingredients:
            if user_ing not in existing_names and user_ing in recipe_text:
                recipe.setdefault("ingredients", []).append(
                    {"name": user_ing, "amount": "适量", "emoji": "🥘"}
                )

    return {"summary": summary, "recipe": recipe, "message": "菜谱生成成功"}


@app.get("/api/search-image")
async def search_image(q: str = Query(..., description="搜索关键词（菜名）")):
    """根据菜名搜索图片，返回第一张图片的 URL。"""
    if not q.strip():
        raise HTTPException(status_code=400, detail="请输入搜索关键词")

    keyword = f"{q.strip()} 美食"
    logger.info("搜索图片: %s", keyword)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    def try_baidu(keyword):
        """用百度图片搜索JSON接口找第一张结果图"""
        url = f"https://image.baidu.com/search/acjson?tn=resultjson_com&word={quote(keyword)}&pn=0&rn=5"
        resp = requests.get(url, headers={**headers, "Referer": "https://image.baidu.com/"}, timeout=8)
        resp.raise_for_status()
        matches = re.findall(r'"thumbURL"\s*:\s*"(http[^"]+)"', resp.text)
        if matches:
            return matches[0]
        return None

    image_url = try_baidu(keyword)
    if image_url:
        return {"image_url": image_url, "query": q}

    logger.warning("百度图片搜索失败: %s", q)
    return {"image_url": None, "query": q}


@app.post("/api/cooking-agent")
async def cooking_agent(request: Request):
    """文字烹饪智能体：接收用户消息和菜谱上下文，通过 DeepSeek 返回逐步烹饪指导。"""
    body = await request.json()
    user_message = str(body.get("message", "")).strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="没有收到用户文字。")

    recipe_context = body.get("recipe_context") or {}
    history = _safe_history(body.get("history"), max_items=14)

    try:
        messages = _build_cooking_messages(user_message, recipe_context, history)
        reply = _deepseek_chat(messages, temperature=0.7, max_tokens=450)
        return {"reply": reply, "model": DEEPSEEK_MODEL, "ts": int(time.time())}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/cooking-voice")
async def cooking_voice(
    audio: UploadFile = File(...),
    history: str = Form("[]"),
    recipe_context: str = Form("{}"),
    client_stats: str = Form("{}"),
):
    """
    前端麦克风采集 → 内存 WAV Blob → 百度 ASR → DeepSeek → 文字回复。
    后端不保存音频文件，只在内存中处理。
    """
    try:
        wav_bytes = await audio.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"音频读取失败: {e}")

    try:
        asr = _baidu_asr_from_wav_bytes(wav_bytes)
        user_text = asr["text"]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    try:
        history_raw = json.loads(history)
    except Exception:
        history_raw = []

    try:
        recipe_ctx = json.loads(recipe_context)
    except Exception:
        recipe_ctx = {}

    try:
        chat_history = _safe_history(history_raw, max_items=14)
        messages = _build_cooking_messages(user_text, recipe_ctx, chat_history)
        reply = _deepseek_chat(messages, temperature=0.7, max_tokens=450)
        return {
            "asr_text": user_text,
            "reply": reply,
            "model": DEEPSEEK_MODEL,
            "asr_engine": "baidu_short_speech",
            "ts": int(time.time()),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/ping")
def ping():
    return {
        "status": "ok",
        "message": "DeepSeek + Baidu ASR 语音服务正常",
        "model": DEEPSEEK_MODEL,
        "has_deepseek_key": bool(DEEPSEEK_API_KEY),
        "has_baidu_asr_key": bool(BAIDU_ASR_API_KEY and BAIDU_ASR_SECRET_KEY),
        "baidu_dev_pid": BAIDU_ASR_DEV_PID,
        "audio_saved": False,
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "烹小灵后端服务运行正常"}


handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host=SERVER_HOST, port=SERVER_PORT, reload=False)
