# 烹小灵后端

基于 Python + FastAPI 开发，提供拍照识别食材功能。

## 技术栈

- Python 3.8+
- FastAPI
- 智谱 GLM-4V（视觉模型）

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 API Key（二选一）
cp .env.example .env    # 然后编辑 .env 填入你的 Key
# 或
export ZHIPUAI_API_KEY=your_key_here

# 启动服务
python app.py
```

服务启动后访问：
- API 文档: http://localhost:8002/docs
- 健康检查: http://localhost:8002/health

## API 接口

### 1. 食材识别

```
POST /detect
Content-Type: multipart/form-data

参数: image (文件, 支持 jpg/jpeg/png/webp, 最大 10MB)
```

成功响应：
```json
{
  "ingredients": ["西红柿", "鸡蛋", "葱"],
  "message": "识别成功"
}
```

### 2. 健康检查

```
GET /health
```

响应：
```json
{
  "status": "ok",
  "message": "烹小灵后端服务运行正常"
}
```

## 配置项

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ZHIPUAI_API_KEY` | (必填) | 智谱 API Key |
| `ZHIPUAI_MODEL` | `glm-4v` | 模型名称 |
| `SERVER_HOST` | `0.0.0.0` | 监听地址 |
| `SERVER_PORT` | `8002` | 监听端口 |
| `MAX_FILE_SIZE` | `10485760` | 最大文件大小(字节) |
| `CORS_ORIGINS` | `*` | 允许的跨域来源 |

## 部署

项目已适配 [Mangum](https://mangum.io/)，可直接部署到 AWS Lambda 或腾讯云函数。

```bash
# 云函数 bootstrap 脚本（scf_bootstrap）已配置
# 默认监听 9000 端口
```
