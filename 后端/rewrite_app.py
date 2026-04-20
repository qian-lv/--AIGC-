from pathlib import Path
path = Path(r"d:\OneDrive\Desktop\food_app\后端\app.py")
content = '''from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import uuid

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # 允许跨域请求

# 豆包API AppKey
APP_KEY = "d256fd28-ff44-4664-abca-2110c866feaa"
BASE_URL = "https://api-ai.vivo.com.cn/v1"
MODEL_NAME = "Doubao-Seed-2.0-mini"

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({'error': '请输入饮食目标或偏好。'}), 400

    request_id = str(uuid.uuid4())
    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {APP_KEY}"
    }
    params = {
        "request_id": request_id
    }
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": "你是一个中文美食营养专家。根据用户的饮食目标、口味和需求，生成一份个性化食谱建议。输出要包含菜品名称、口味描述、主要食材、制作步骤和热量提示，语言简洁友好。"
            },
            {
                "role": "user",
                "content": f"请根据以下饮食需求生成个性化食谱：{user_message}"
            }
        ],
        "temperature": 0.8,
        "max_tokens": 900,
        "stream": False
    }

    try:
        response = requests.post(url, headers=headers, params=params, json=payload, timeout=30)
        response.raise_for_status()
        response_data = response.json()

        choices = response_data.get('choices') or []
        if not choices:
            return jsonify({'error': '后端未返回有效内容', 'detail': response_data}), 500

        first_choice = choices[0]
        message = first_choice.get('message', {})
        reply = message.get('content') or first_choice.get('text') or ''

        if not reply:
            return jsonify({'error': '后端返回内容为空', 'detail': response_data}), 500

        return jsonify({'reply': reply, 'detail': response_data})
    except requests.exceptions.RequestException as e:
        error_text = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_text = e.response.text
            except Exception:
                pass
        return jsonify({'error': '请求豆包接口失败', 'detail': error_text}), 500
    except Exception as e:
        return jsonify({'error': '服务器内部错误：' + str(e)}), 500

@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'ok', 'message': '豆包 AI 后端运行中'})

if __name__ == '__main__':
    app.run(debug=True)
'''
path.write_text(content, encoding='utf-8')
print('updated', path)
