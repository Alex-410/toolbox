# 多功能工具平台

基于 Django 的多功能工具平台，集成了人生模拟器、动漫旅行、PDF 工具等模块。

## 功能模块

### 人生模拟器 (Life Simulator)

AI 驱动的文字人生模拟游戏，支持多种世界观：

- **现代都市** - 当代社会的人生体验
- **古代江湖修仙** - 武侠修仙世界
- **未来赛博科幻** - 赛博朋克风格

特性：
- 基于 Ollama 本地 LLM (deepseek-r1:1.5b) 生成剧情
- 随机角色背景生成
- 分阶段人生剧情推进（共 10 阶段）
- 属性系统：智力、魅力、体质、运气、财富
- 多结局评价系统

### 动漫旅行 (Anime Travel)

动漫风格的旅行体验服务。

### PDF 工具 (PDF Tools)

PDF 文件处理工具。

## 技术栈

- **后端框架**: Django 4.2+
- **AI 服务**: Ollama (deepseek-r1:1.5b)
- **图像处理**: OpenCV, Pillow, NumPy
- **数据可视化**: Matplotlib
- **数据库**: SQLite

## 快速开始

### 环境要求

- Python 3.10+
- Ollama (本地运行)

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

复制 `.env.example` 为 `.env`，填写必要的配置：

```bash
cp backend/.env.example backend/.env
```

### 启动 Ollama 服务

```bash
ollama pull deepseek-r1:1.5b
ollama serve
```

### 运行项目

```bash
cd backend
python manage.py migrate
python manage.py runserver
```

## API 接口

| 模块 | 路径前缀 | 说明 |
|------|----------|------|
| Life Simulator | `/api/life/` | 人生模拟器相关接口 |
| PDF Tools | `/api/pdf/` | PDF 处理工具接口 |
| Anime Travel | `/api/anime-travel/` | 动漫旅行服务接口 |

## 项目结构

```
backend/
├── config/          # Django 配置
├── api/             # 通用 API
├── life_simulator/  # 人生模拟器模块
├── anime_travel/    # 动漫旅行模块
├── pdf_tools/       # PDF 工具模块
├── rag/             # RAG 相关
├── rag_data/        # RAG 数据
├── static/          # 静态文件
└── tools/           # 工具脚本
```

## 许可证

MIT License