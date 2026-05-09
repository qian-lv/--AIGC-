# 烹小灵 - 开发记录

## 2026-05-06 会话记录

### 修复的问题

#### 1. 食材识别正确但生成食谱失败
- **原因**: FastAPI `request: dict` 写法在部分版本中无法正确解析 JSON 请求体
- **修复**: 将 `/api/generate-recipe-structured` 和 `/api/chat` 改为 `request: Request` + `await request.json()`
- **涉及文件**: `后端/app.py`

#### 2. 前端 backendUrl 变量未定义
- **原因**: `food_app_result.html` 中 `createRecipeCard` 的图片请求使用了未定义的 `backendUrl` 变量
- **修复**: 替换为硬编码 URL `http://10.130.104.236:8085`
- **涉及文件**: `前端/food_app_result.html`

#### 3. 菜谱食材不全
- **现象**: 做番茄炒蛋食材列表只有番茄，漏掉了鸡蛋
- **修复**: 
  - 增强 AI prompt，明确要求不能遗漏食材
  - 增加后处理逻辑：自动检查菜名和步骤中提到的用户食材，遗漏的自动补上
- **涉及文件**: `后端/app.py`（`generate_recipe_structured` 函数的 system_prompt 和 post-processing）

#### 4. 菜谱封面图片加载慢且不稳定
- **原因**: DuckDuckGo 在中国被 GFW 屏蔽，每次请求等待 10 秒超时
- **修复**:
  - 后端去掉 DuckDuckGo，改用 Bing 为主 + 百度图片搜索为备用
  - 超时从 10s 缩短到 8s
  - 前端图片请求增加 5 秒 AbortController 超时控制
- **涉及文件**: 
  - `后端/app.py`（`search_image` 函数）
  - `前端/food_app_result.html`
  - `前端/food_app_recipe_view.html`
  - `前端/food_app_home.html`

### 服务器信息
- 后端地址: `http://10.130.104.236:8085`
- 前端地址: `http://10.130.104.236:8081`
- API Key: `875491e249004f1db9463745560daa0c.lAKmd8k0nbsa9Crc`
- AI 模型: `glm-4v`（智谱）

### 已确认正常的功能
- [x] `/health` — 健康检查
- [x] `/detect` — 拍照识别食材
- [x] `/api/generate-recipe-structured` — 生成结构化菜谱
- [x] `/api/chat` — AI 聊天推荐
- [x] `/api/search-image` — 根据菜名搜索图片（Bing + 百度）

## 2026-05-07 会话记录

### 前端重构

#### 1. 导航系统重写 — NavigationStack → History API
- **原因**: 原 NavigationStack 类 120 行 + 每个页面 inline 40 行兜底代码，同一逻辑重复 15 次
- **修复**: 
  - 删除 NavigationStack 类，改为 `navigateTo()` + `goBack()` 基于 `history.back()` 实现
  - 删除 `navigation.js` 中所有 localStorage 持久化逻辑
  - 删除所有页面的 NavigationStack 内联兜底代码（累计删除 600+ 行）
- **涉及文件**: 
  - `前端/navigation.js`（120 行 → 2 行）
  - `前端/touch.js`
  - 所有 16 个 HTML 页面

#### 2. 公共配置提取 — common.js
- **修复**: 创建 `前端/common.js`，统一管理 `backendUrl` 常量
  - `food_app_loading.html` 去掉 inline `backendUrl` 定义
  - `food_app_home.html`、`food_app_result.html`、`food_app_recipe_view.html` 添加 common.js 引用
- **涉及文件**: `前端/common.js`（新增）

#### 3. 硬编码 IP 替换
- **原因**: `10.130.104.236` 是旧局域网 IP，环境变更后失效
- **修复**: 所有硬编码 IP 改为引用 `backendUrl`，并设为 `localhost:8085`
- **涉及文件**: `前端/common.js`，`前端/food_app_home.html`，`前端/food_app_result.html`，`前端/food_app_recipe_view.html`

#### 4. 加载页优化
- **修复**: 
  - CSS spinner 替换为 `<video>` 元素（角色小跑动画，圆形裁切）
  - 删除不存在的 logo 图片（`images/app_icon.png`）
  - 删除对应的 CSS（`@keyframes spin`、`.loading-spinner`、`.app-logo`）
- **涉及文件**: `前端/food_app_loading.html`

### 服务器信息
- 后端地址: `http://localhost:8085`（common.js 统一管理）
- 前端地址: `http://localhost:8081`
- API Key: `875491e249004f1db9463745560daa0c.lAKmd8k0nbsa9Crc`
- AI 模型: `glm-4v`（智谱）

### 前端文件结构（变更后）
```
前端/
├── common.js              # 公共配置（backendUrl）
├── navigation.js          # 导航函数（navigateTo / goBack）
├── touch.css
├── touch.js
├── *.html                 # 16 个页面
└── video/                 # 角色动画视频
```

### 已确认正常的功能
- [x] `/health` — 健康检查
- [x] `/detect` — 拍照识别食材
- [x] `/api/generate-recipe-structured` — 生成结构化菜谱
- [x] `/api/chat` — AI 聊天推荐
- [x] `/api/search-image` — 根据菜名搜索图片（Bing + 百度）
- [x] 加载页视频播放
- [x] 页面导航返回

## 2026-05-08 会话记录

### 移动端滚动修复

#### 1. 页面无法滚动
- **原因**: 多个页面 body 使用了 `display: flex; flex-direction: column; overflow: hidden;`，内容超出屏幕时无法滚动
- **修复**: 移除 body 的 flex 布局和 overflow:hidden，改为自然文档流；首页底部导航栏改为 `position: fixed` 固定底部；`100vh` 改为 `100dvh` 适配移动端浏览器
- **涉及文件**: 
  - `前端/food_app_home.html`
  - `前端/food_app_more.html`
  - `前端/food_app_schedule.html`
  - `前端/food_app_favorites.html`
  - `前端/food_app_category.html`
  - `前端/food_app_settings.html`

#### 2. 后端地址多端适配
- **原因**: `common.js` 硬编码 `localhost:8085`，手机访问时 localhost 指向手机自身，导致 API 调用失败
- **修复**: 改为动态获取 `window.location.hostname`，电脑和手机自动使用对应的后端地址
- **涉及文件**: `前端/common.js`

#### 3. 首页推荐卡片封面
- **修复**: 四张推荐卡片（Italian Pasta、Chicken Salad、Beef Steak、Fish Curry）的渐变背景替换为本地图片
- **涉及文件**: `前端/food_app_home.html`，新增 `前端/picture/` 目录

### 服务器信息
- 后端地址: `http://localhost:8085`（common.js 动态适配）
- 前端地址: `http://localhost:8081`
- API Key: `875491e249004f1db9463745560daa0c.lAKmd8k0nbsa9Crc`
- AI 模型: `glm-4v`（智谱）

### 已确认正常的功能
- [x] `/health` — 健康检查
- [x] `/detect` — 拍照识别食材
- [x] `/api/generate-recipe-structured` — 生成结构化菜谱
- [x] `/api/chat` — AI 聊天推荐
- [x] `/api/search-image` — 根据菜名搜索图片（Bing + 百度）
- [x] 移动端页面滚动
- [x] 首页底部导航栏
- [x] 多端后端地址自动适配
