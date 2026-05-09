# 烹小灵 — AIGC 智能食谱推荐

拍照识别食材，AI 生成菜谱，语音智能体陪做饭。基于 FastAPI + 智谱 GLM-4V + DeepSeek + 百度 ASR。

---

## 目录

- [项目结构](#项目结构)
- [启动步骤（评审测试用）](#启动步骤评审测试用)
- [测试各功能](#测试各功能)
- [API 接口](#api-接口)
- [常见问题](#常见问题)
- [手机访问](#手机访问)

---

## 项目结构

```
--AIGC-/
├── 后端/                        # FastAPI 后端
│   ├── app.py                  # 主程序（8 个接口）
│   ├── config.py               # 配置文件（环境变量读取）
│   ├── requirements.txt        # Python 依赖
│   ├── .env.example            # API Key 模板
│   ├── .env                    # API Key（需自己创建）
│   ├── scf_bootstrap           # 云函数部署脚本
│   └── __pycache__/
├── 前端/                        # 多页 HTML 前端
│   ├── index.html              # 首页入口
│   ├── food_app_home.html      # 主页
│   ├── food_app_camera.html    # 拍照识别食材
│   ├── food_app_loading.html   # AI 识别加载页
│   ├── food_app_result.html    # 识别结果 + 菜谱推荐
│   ├── food_app_recipe_view.html # 菜谱详情
│   ├── food_app_video_call.html  # 糯糯语音做饭智能体
│   ├── food_app_detail*.html   # 各类菜系详情页
│   ├── food_app_category.html  # 分类浏览
│   ├── food_app_favorites.html # 收藏
│   ├── food_app_schedule.html  # 日程
│   ├── food_app_settings.html  # 设置
│   ├── food_app_splash.html    # 启动页
│   ├── food_app_more.html      # 更多功能
│   ├── game_app_complete.html  # 结算页
│   ├── common.js               # 后端地址配置
│   ├── navigation.js           # 页面导航
│   ├── touch.css / touch.js    # 触摸体验
│   ├── assets/                 # 语音智能体素材
│   │   ├── agent_raccoon.png   # 糯糯形象
│   │   └── agent_speaking.mp4  # 说话动画
│   ├── picture/                # 菜谱封面图
│   │   ├── italian Pasta.png
│   │   ├── Chicken Salad.png
│   │   ├── Beef Steak.png
│   │   └── Fish Curry.png
│   └── video/character-run.mp4 # 加载页动画
├── 图片/                        # UI 设计稿
├── README.md
├── 项目文档.md
└── package.json
```

---

## 启动步骤（评审测试用）

### 环境要求

- **Python** 3.9+
- **浏览器** Chrome 或 Edge（语音功能必须）
- **操作系统** Windows / macOS / Linux 均可

### 第一步：解压项目

```bash
unzip --AIGC--main.zip -d AIGC
cd AIGC
```

> Windows 用户直接右键解压到当前文件夹。

### 第二步：配置 API Key

进入后端目录，创建 `.env` 文件：

```bash
cd 后端
```

**Windows：**
```cmd
copy .env.example .env
notepad .env
```

**Mac/Linux：**
```bash
cp .env.example .env
nano .env
```

填入以下内容（将 `your_xxx` 替换为真实 Key）：

```env
# 智谱 AI（拍照识别食材）
ZHIPUAI_API_KEY=your_zhipu_key_here
ZHIPUAI_MODEL=glm-4v
SERVER_HOST=0.0.0.0
SERVER_PORT=8085

# DeepSeek（语音智能体对话）
DEEPSEEK_API_KEY=your_deepseek_key_here
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash

# 百度短语音识别（语音转文字）
BAIDU_ASR_APP_ID=your_baidu_app_id
BAIDU_ASR_API_KEY=your_baidu_api_key
BAIDU_ASR_SECRET_KEY=your_baidu_secret_key
BAIDU_ASR_DEV_PID=1537
BAIDU_ASR_CUID=cooking-agent-local
```

> 三个 Key 缺一不可。智谱用于拍照识别，DeepSeek + 百度 ASR 用于语音做饭智能体。

### 第三步：安装依赖

```bash
pip install -r requirements.txt
```

如果下载慢，换国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 第四步：启动后端

```bash
python app.py
```

看到以下输出表示成功：

```
INFO:     Uvicorn running on http://0.0.0.0:8085 (Press CTRL+C to quit)
```

验证后端：

浏览器访问 http://127.0.0.1:8085/api/ping

应返回：
```json
{
  "status": "ok",
  "has_deepseek_key": true,
  "has_baidu_asr_key": true
}
```

三个 Key 状态都应为 `true`。如果有 `false`，检查 `.env` 对应 Key 是否填写正确。

### 第五步：启动前端

**新开一个终端**，回到项目根目录（`--AIGC-/`）：

```bash
cd ..          # 回到 --AIGC-/ 根目录
python -m http.server 8081
```

### 第六步：打开页面

浏览器访问：**http://127.0.0.1:8081**

> 不要直接双击 HTML 文件，`file://` 协议下麦克风权限无法使用。

---

## 测试各功能

### 1. 首页浏览 — 基础 UI

访问 http://127.0.0.1:8081

验证项：
- [ ] 页面正常显示，顶部显示 "Hello, Amir-Zhen"
- [ ] 推荐卡片（Italian Pasta / Chicken Salad / Beef Steak / Fish Curry）显示菜品图片
- [ ] 页面可以上下滚动
- [ ] 点击卡片跳转到对应详情页
- [ ] 点击心形图标可收藏/取消收藏
- [ ] 底部导航栏固定在屏幕底部

### 2. 拍照识别食材 — 核心功能

点击搜索栏的相机图标 → 允许相机权限 → 拍照

流程：
1. 拍照 → 自动跳转加载页（小浣熊跑动动画）
2. 加载中调用智谱 GLM-4V 识别图片中的食材
3. 识别完成跳转到结果页，显示识别出的食材
4. 输入饮食偏好（如"少油低盐"），点击生成食谱
5. 查看完整菜谱（菜名、用量、步骤、卡路里、评分）

验证项：
- [ ] 相机能正常打开
- [ ] 拍照后进入加载页，动画播放
- [ ] 食材识别成功，显示食材列表
- [ ] 食谱生成成功，包含完整的步骤和食材用量
- [ ] 食谱卡片封面图片正常加载

### 3. 语音做饭智能体 — 亮点功能

访问 http://127.0.0.1:8081/前端/food_app_video_call.html

流程：
1. 看到"糯糯小浣熊"形象和待机界面
2. 点击底部绿色"开始通话"按钮
3. 浏览器弹出麦克风权限 → 点"允许"
4. 糯糯自动播报欢迎语（中文 TTS 语音）
5. 直接说话（如"我要做番茄炒蛋"）
6. 说完停顿约 1 秒，系统自动识别并上传
7. 百度 ASR 转文字 → DeepSeek 生成回复 → 糯糯 TTS 播报
8. 对话历史显示在聊天区域

语音智能体特性：
- **实时 VAD**：自动检测说话开始和结束，无需手动控制
- **语音回复**：浏览器 TTS 播报，语速 0.96 倍，自然女声
- **文字降级**：底部输入框可打字发送，不依赖语音
- **不存音频**：后端仅在内存中处理，不保存任何音频文件
- **音量指示器**：底部实时显示麦克风音量和峰值

验证项：
- [ ] 麦克风权限授权后能听到欢迎语
- [ ] 说话后能正确识别为文字并显示
- [ ] DeepSeek 回复内容合理（烹饪指导风格）
- [ ] TTS 语音播报清晰可听
- [ ] 对话历史正确累积
- [ ] 文字输入降级功能正常
- [ ] 点击"结束"跳转结算页
- [ ] 点击麦克风按钮可开关收音

### 4. 其他页面

| 页面 | 路径 | 验证 |
|------|------|------|
| 分类浏览 | `food_app_category.html` | 按菜系/口味筛选 |
| 收藏页 | `food_app_favorites.html` | 收藏的菜谱显示 |
| 日程页 | `food_app_schedule.html` | 饮食计划记录 |
| 设置页 | `food_app_settings.html` | 偏好设置 |
| 更多功能 | `food_app_more.html` | 入口导航 |

---

## API 接口

后端共 **8 个接口**：

### 拍照识别

```
POST /detect
Content-Type: multipart/form-data
参数: image (jpg/jpeg/png/webp, ≤10MB)

返回: {"ingredients": ["番茄", "鸡蛋"], "message": "识别成功"}
```

### AI 菜谱聊天（智谱）

```
POST /api/chat
Content-Type: application/json
Body: {"message": "我想吃清淡的", "ingredients": ["鸡蛋", "番茄"]}

返回: {"reply": "推荐番茄炒蛋..."}
```

### 结构化菜谱生成（智谱）

```
POST /api/generate-recipe-structured
Body: {"ingredients": ["鸡蛋", "番茄"], "preference": "少油"}

返回: {"summary": "...", "recipe": {"name": "番茄炒蛋", "ingredients": [...], "steps": [...]}}
```

### 菜谱图片搜索

```
GET /api/search-image?q=番茄炒蛋

返回: {"image_url": "https://...", "query": "番茄炒蛋"}
```

### 文字烹饪指导（DeepSeek）

```
POST /api/cooking-agent
Body: {"message": "我要做番茄炒蛋", "history": [], "recipe_context": {}}

返回: {"reply": "太好了！我们先从打鸡蛋开始...", "model": "deepseek-v4-flash"}
```

### 语音烹饪指导（百度 ASR + DeepSeek）

```
POST /api/cooking-voice
Content-Type: multipart/form-data
参数: audio (WAV/16kHz/16bit/mono), history, recipe_context

返回: {"asr_text": "我要做番茄炒蛋", "reply": "好的！第一步...", "asr_engine": "baidu_short_speech"}
```

### 服务检查

```
GET /api/ping
返回: {"status": "ok", "has_deepseek_key": true, "has_baidu_asr_key": true, "audio_saved": false}

GET /health
返回: {"status": "ok", "message": "烹小灵后端服务运行正常"}
```

---

## 常见问题

**Q: 启动后端报 "Address already in use"**
A: 端口 8085 已被占用。关闭之前开的终端窗口，或修改 `.env` 中的 `SERVER_PORT`。

**Q: 拍照后提示 "AI 服务调用失败"**
A: 检查 `.env` 中 `ZHIPUAI_API_KEY` 是否正确填写，以及网络能否访问智谱 API。

**Q: 语音智能体识别不到声音**
A: 检查页面底部 RMS 数值：
- RMS 长期为 0.0000：浏览器没拿到麦克风音频，检查系统默认输入设备或浏览器权限
- RMS 有变化但不上传：声音太小，靠近麦克风或提高输入音量
- 上传后报 3301：百度认为音频质量差，靠近麦克风说完整一句

**Q: 语音智能体提示后端连接失败**
A: 确认后端终端仍在运行，访问 http://127.0.0.1:8085/api/ping 验证。

**Q: 百度鉴权失败**
A: 检查 `.env` 中 `BAIDU_ASR_API_KEY` 和 `BAIDU_ASR_SECRET_KEY` 是否正确（不要把 AppID 填到 API Key 位置）。

**Q: 语音播报没声音**
A: 使用 Chrome/Edge 浏览器，Firefox 不支持 Web Speech API。确保系统音量未静音。

**Q: 手机上页面无法滚动**
A: 已适配移动端，使用 `100dvh` 和 `position: fixed` 底部导航。若仍有问题请清除浏览器缓存。

---

## 手机访问

电脑和手机连接同一 WiFi：

1. 查看电脑 IP 地址：
   - **Windows**：`ipconfig` → 找到 `192.168.x.x`
   - **Mac**：系统设置 → 网络 → Wi-Fi → IP 地址

2. 手机浏览器访问：`http://电脑IP:8081`

3. 语音功能需用手机 Chrome 打开，且允许麦克风权限。
