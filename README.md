# PaperAssistant — AI 论文陪读助手

基于 Django + OpenAI 的 AI 辅助英文论文阅读工具。上传 PDF 后 AI 自动分析论文结构、创新点和关键概念；阅读时选中单词或段落即可实时获取翻译和详解。

## 功能特性

### AI 论文分析
上传 PDF 后，AI 自动生成：
- **论文思路**：研究方法论、技术路线、研究推进逻辑
- **论文创新点**：主要贡献及相对现有工作的优势
- **论文总结**：研究背景、方法、实验和主要发现
- **论文展望**：未来工作方向和潜在改进空间
- **缩写/概念解释**：重要缩写、专业术语详细解释

### 交互式阅读
- **单词查询**：鼠标选中 PDF 中的单词，自动弹出含义卡片（通用含义 + 文中语境含义）
- **段落解析**：选中大段文本后，出现提示按钮可向 AI 询问段落详解
- **自由问答**：右侧面板可对论文内容自由提问（Ctrl+Enter 发送）

### 单词本
- 查询过的单词自动收录到右下角单词本
- 支持删除已收录单词
- 支持导出 CSV 文件（UTF-8 BOM，Excel 直接打开不乱码）

### 多用户支持
- 用户注册 / 登录系统（Session 认证）
- 每位用户的论文和单词本完全隔离
- 首次使用需注册账号

### 界面
- 左侧 PDF 阅读区 + 右侧工具面板，**中间分隔线可拖动调整比例**
- PDF 原文渲染（基于 PDF.js），文字可选
- Markdown 富文本渲染（标题、列表、代码块、引用等）

## 环境要求

- Python 3.11+
- Anaconda 或 Miniconda
- OpenAI API Key（或兼容 OpenAI 接口的 API 服务）

## 快速开始

### 1. 配置 .env

编辑项目根目录的 `.env` 文件：

```env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
```

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | API 密钥（必填） | — |
| `OPENAI_BASE_URL` | API 服务地址 | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | 模型名称 | `gpt-4o` |

> 使用第三方 API 代理/国内兼容服务（如 DeepSeek、通义千问等）：修改 `OPENAI_BASE_URL` 和 `OPENAI_MODEL` 即可。

### 2. 一键配置环境

**Windows：** 双击 `setup_conda.bat`

**Linux / Mac：**
```bash
bash setup_conda.sh
```

脚本自动完成：创建 Conda 环境 → 安装依赖 → 初始化数据库。

### 3. 手动配置（可选）

```bash
conda create -n paper_assistant python=3.11 -y
conda activate paper_assistant
pip install -r requirements.txt
python manage.py migrate
```

### 4. 启动

**本机使用：**
```bash
conda activate paper_assistant
python manage.py runserver
```
浏览器访问 **http://127.0.0.1:8000**

**局域网部署（其他设备可访问）：**

Windows — 双击 `run_lan.bat`

Linux/Mac：
```bash
bash run_lan.sh
```

或手动：
```bash
conda activate paper_assistant
python manage.py runserver 0.0.0.0:8000
```

启动后会显示本机局域网 IP。同一局域网下的其他设备（手机、平板、其他电脑）通过 `http://<本机IP>:8000` 即可访问。

## 使用指南

### 注册与登录

1. 首次使用点击「立即注册」→ 输入用户名（≥3字符）和密码（≥6字符）
2. 注册成功自动登录
3. 后续访问直接登录，右上角显示用户名和退出按钮

### 上传论文

1. 点击右侧面板顶部「上传 PDF 论文」按钮 → 选择 PDF
2. 等待 AI 分析完成（通常 10-30 秒）
3. 左侧显示 PDF 原文，右侧显示 AI 分析结果

### 查单词

- **鼠标选中** PDF 中一个英文单词 → 弹出含义卡片（通用含义 + 文中语境）
- 或手动在右侧输入框输入单词 → 点「查询」

### 段落详解

1. 选中一大段文本 → 上方出现提示 + 「询问AI」按钮
2. 点击按钮 → 右侧显示该段落的详细中文解析

### 自由问答

在右侧 AI 问答区输入问题 → 点「提问」（或 Ctrl+Enter）→ AI 基于论文内容回答

### 单词本

- 右下角自动收录所有查询过的单词
- 点击单词可再次查询
- 点击 × 删除
- 「导出 CSV」下载单词表

### 调整布局

拖动左右面板之间的分隔线自由调整比例，设置会自动保存。

## 项目结构

```
PaperAssistant/
├── manage.py
├── .env                      # API 配置（不提交 Git）
├── requirements.txt
├── setup_conda.bat           # Windows 一键配置
├── setup_conda.sh            # Linux/Mac 一键配置
├── paper_assistant/          # Django 项目配置
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── reader/                   # 主应用
│   ├── models.py             # Paper + Vocabulary 数据模型
│   ├── views.py              # 视图（含认证 + API）
│   ├── services.py           # OpenAI API 调用
│   ├── urls.py               # 路由
│   ├── admin.py
│   └── templates/reader/
│       ├── index.html        # 主页面
│       ├── login.html        # 登录页
│       └── register.html     # 注册页
├── static/
│   ├── css/style.css
│   └── js/main.js
└── media/papers/             # 上传的 PDF
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/login/` | 登录 `{username, password}` |
| POST | `/register/` | 注册 `{username, password, password2}` |
| POST | `/api/upload/` | 上传 PDF（multipart/form-data） |
| POST | `/api/word/` | 查单词 `{word, paper_id, context}` |
| POST | `/api/paragraph/` | 解段落 `{paragraph, paper_id}` |
| POST | `/api/ask/` | AI 问答 `{question, paper_id}` |
| GET | `/api/paper/<id>/analysis/` | 获取分析结果 |
| GET | `/api/vocabulary/` | 生词本列表 |
| DELETE | `/api/vocabulary/<id>/delete/` | 删除生词 |
| GET | `/api/vocabulary/export/` | 导出 CSV |

所有 API 接口需要登录后才能访问。

## 常见问题

**Q: "AI分析失败"？**
检查 `.env` 中 `OPENAI_API_KEY` 是否正确，网络是否能访问 `OPENAI_BASE_URL`，API 账户是否有额度。

**Q: PDF 文字无法选中？**
扫描版 PDF（图片转 PDF）没有文字层，需要原生文本型 PDF。

**Q: 查词/回答很慢？**
每次查询调用 AI API，速度取决于 API 服务商。可在 `.env` 中改用更快的模型（如 `gpt-4o-mini`）。

**Q: 如何部署到服务器？**
- 设 `DJANGO_DEBUG=False`
- 配置 `ALLOWED_HOSTS` 和 `DJANGO_SECRET_KEY`
- 生产环境建议用 PostgreSQL + Gunicorn + Nginx

**Q: 局域网其他设备无法访问？**
检查 Windows 防火墙：控制面板 → Windows Defender 防火墙 → 允许应用通过防火墙 → 找到 Python 并勾选"专用"和"公用"，或者临时关闭防火墙测试。

**Q: 支持哪些 AI 服务？**
所有兼容 OpenAI Chat Completions API 的服务均可。国内 DeepSeek、通义千问等只需修改 `OPENAI_BASE_URL`。
