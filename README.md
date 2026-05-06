# 烹小灵 - AIGC 食谱推荐项目

拍照识别食材，AI 自动推荐菜谱。

## 目录

- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [常见问题](#常见问题)

---

## 环境要求

- **Python** 3.9+
- **浏览器** Chrome / Edge 等现代浏览器

---

## 快速开始

### 1. 下载代码

```bash
git clone -b Recipe_recommend--With--Photo_recognize https://github.com/qian-lv/--AIGC-.git
cd --AIGC-
```

### 2. 配置 API Key

进入 `后端` 目录，将 `.env.example` 重命名为 `.env`：

```bash
cd 后端
copy .env.example .env     # Windows
# 或
cp .env.example .env       # Mac/Linux
```

用记事本打开 `.env`，把 `your_api_key_here` 替换成真实的智谱 API Key：

```
ZHIPUAI_API_KEY=875491e249004f1db9463745560daa0c.xxxxxxxx
```

> **找谁拿 Key？** 联系王程越乾

### 3. 安装依赖

```bash
# 在 后端 目录下执行
pip install -r requirements.txt
```

如果下载慢，可以换国内镜像源：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. 启动后端

```bash
# 在 后端 目录下执行
python app.py
```

看到以下输出表示启动成功：

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8085
```

> 保持这个终端窗口打开，不要关闭。

### 5. 启动前端

**新开一个终端**，在 `--AIGC-` 根目录下执行：

```bash
python -m http.server 8081
```

### 6. 打开使用

浏览器访问：**http://localhost:8081**

---

## 常见问题

**Q: 启动后端时报错 "Address already in use"**
A: 端口 8085 被占用了，先关掉之前开的终端，或杀掉占用进程再试。

**Q: 上传图片后提示 "AI 服务调用失败"**
A: 检查 `.env` 里的 API Key 是否正确，以及网络是否能访问智谱 API。

**Q: 前端页面打不开**
A: 确认前端终端在 `--AIGC-` 根目录（不是 `后端` 目录），且端口是 8081。

---

## 项目结构

```
--AIGC-/
├── 后端/                  # FastAPI 后端
│   ├── app.py            # 主程序
│   ├── config.py         # 配置文件
│   ├── requirements.txt  # Python 依赖
│   └── .env              # API Key（自己配置，不上传）
├── 前端/                  # 静态前端页面
│   ├── food_app_home.html
│   ├── food_app_camera.html
│   ├── food_app_loading.html
│   ├── food_app_result.html
│   └── ...
└── 图片/                   # UI 设计图
```
