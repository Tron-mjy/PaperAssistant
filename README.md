# PaperAssistant — AI 论文陪读助手

基于 Django + OpenAI 的 AI 辅助英文论文阅读工具。上传 PDF 后 AI 自动分析论文结构、创新点和关键概念。提供 **Web 版**（浏览器访问）和 **桌面版**（PySide6 原生应用）两种使用方式。

## 功能特性

### AI 论文分析
上传 PDF 后自动生成：
- **论文思路** — 研究方法论、技术路线
- **论文创新点** — 主要贡献及相比现有工作的优势
- **论文总结** — 背景、方法、实验、发现
- **论文展望** — 未来方向和改进空间
- **缩写/概念解释** — 重要术语的详细解释

### 查词与问答
- **单词查询**：右侧输入框手动输入单词，AI 返回通用含义 + 论文语境含义
- **AI 问答**：针对论文内容自由提问（Ctrl+Enter 发送），AI 结合原文回答
- **段落解析**：选中原文段落，AI 逐句详细解析

### 单词本
- 查询过的单词自动收录（同一单词不重复）
- 支持删除和 CSV 导出（UTF-8 BOM，Excel 直接打开）
- 底部区域高度可通过分隔条拖动调整

### 多用户
- 用户注册 / 登录（Session 认证）
- 每个用户的论文和单词本完全隔离

### 界面
- 顶部 Header：上传按钮、历史记录、论文名称、用户信息
- 左侧 PDF 阅读区 + 右侧工具面板，**中间分隔线可拖动调整比例**
- 右侧面板内部上（分析+查词+问答）/ 下（单词本）**垂直分隔线可拖动**
- Markdown 富文本渲染（标题、列表、代码块、引用等）

### 历史文档
- 左侧汉堡菜单展开历史面板
- 点击加载之前上传的论文（含 AI 分析结果和单词本）
- 右键删除历史记录（同步删除服务器文件）

---

## Web 版

### 环境要求
- Python 3.11+
- Anaconda 或 Miniconda
- OpenAI API Key（兼容 OpenAI 接口格式即可）

### 快速开始

**1. 配置 `.env`：**
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

> 国内兼容服务（DeepSeek、通义千问等）：修改 `OPENAI_BASE_URL` 和 `OPENAI_MODEL` 即可。

**2. 一键安装：**
- Windows：双击 `setup_conda.bat`
- Linux/Mac：`bash setup_conda.sh`

**3. 启动：**
```bash
conda activate paper_assistant
python manage.py runserver
```
浏览器访问 **http://127.0.0.1:8000**

**局域网部署：**
- Windows：双击 `run_lan.bat`
- Linux/Mac：`bash run_lan.sh`

启动后显示本机局域网 IP，同一网络下其他设备通过 `http://<IP>:8000` 访问。

### 使用流程
1. 注册账号并登录
2. 点击左上角「上传 PDF」选择论文
3. 等待 AI 分析完成（10-30 秒），分析报告显示在右侧
4. 左侧显示 PDF 原文（浏览器原生渲染），正常阅读
5. 遇到生词 → 右侧「单词查询」输入框输入 → 点击「查询」
6. 对论文内容有疑问 → 「AI 问答」输入问题 → Ctrl+Enter
7. 单词本自动记录查询过的单词，可导出 CSV
8. 后续可通过左侧「历史文档」面板加载之前的论文

### 项目结构
```
PaperAssistant/
├── manage.py                  # Django 入口
├── .env                       # API 配置
├── requirements.txt           # Web 版 Python 依赖
├── setup_conda.bat / .sh      # 一键环境配置
├── run_lan.bat / .sh          # 局域网启动脚本
├── test_api.py                # API 连通性测试
├── paper_assistant/           # Django 项目配置
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── reader/                    # 主应用
│   ├── models.py              # Paper + Vocabulary
│   ├── views.py               # 视图 + 认证
│   ├── services.py            # OpenAI 调用
│   ├── urls.py
│   └── templates/reader/
│       ├── index.html
│       ├── login.html
│       └── register.html
├── static/
│   ├── css/style.css
│   └── js/main.js
├── media/papers/              # 上传的 PDF 文件
└── desktop/                   # 桌面版（见下文）
```

### API 接口
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/login/` | 登录 |
| POST | `/register/` | 注册 |
| GET | `/logout/` | 退出 |
| POST | `/api/upload/` | 上传 PDF |
| POST | `/api/word/` | 查单词 |
| POST | `/api/paragraph/` | 解段落 |
| POST | `/api/ask/` | AI 问答 |
| GET | `/api/papers/` | 论文列表 |
| DELETE | `/api/paper/<id>/delete/` | 删除论文 |
| GET | `/api/paper/<id>/context/` | 获取论文文本 |
| GET | `/api/paper/<id>/analysis/` | 获取分析结果 |
| GET | `/api/vocabulary/` | 单词本列表 |
| DELETE | `/api/vocabulary/<id>/delete/` | 删除单词 |
| GET | `/api/vocabulary/export/` | 导出 CSV |

所有接口需登录后访问。

### API 连通性测试
```bash
conda activate paper_assistant
python test_api.py
```
三步检测：包安装 → 网络连通 → 实际 API 调用，失败时给出具体诊断提示。

---

## 桌面版

基于 PySide6 + PyMuPDF 的原生桌面应用，功能与 Web 版对应，无需浏览器和 Django 服务器。

### 与 Web 版的区别
| | Web 版 | 桌面版 |
|---|---|---|
| PDF 渲染 | 浏览器 `<object>` 标签 | PyMuPDF 渲染为图片 |
| 点击查词 | 不支持（浏览器 PDF 隔离） | ✅ 点击 PDF 中单词直接查词 |
| Ctrl+滚轮缩放 | 浏览器自带 | 自定义缩放（带防抖） |
| 数据存储 | Django SQLite | 独立 SQLite (`desktop/data.db`) |
| 部署 | 需要 Django 服务器 | 单文件双击启动 |

### 安装与启动
```bash
cd desktop
pip install -r requirements.txt    # PySide6 + PyMuPDF + openai
python main.py
```

或双击 `desktop/setup_desktop.bat` 一键安装。

### 项目结构
```
desktop/
├── main.py            # 入口
├── app.py             # GUI 主程序
├── pdf_viewer.py      # PyMuPDF PDF 查看器
├── services.py        # OpenAI API 调用
├── database.py        # 本地 SQLite
├── requirements.txt   # PySide6, PyMuPDF, openai, PyPDF2, python-dotenv
├── setup_desktop.bat  # 一键安装脚本
└── data.db            # 本地数据库（自动生成）
```

---

## 常见问题

**Q: AI 分析/查词失败？**
运行 `python test_api.py` 诊断。常见原因：API Key 错误、网络不通、账户欠费。

**Q: Web 版查词很慢？**
每次查询调用 AI API，可在 `.env` 中改用更快模型（如 `gpt-4o-mini`）。

**Q: 桌面版 PDF 不显示？**
确保 `PyMuPDF` 已安装：`pip install PyMuPDF`。

**Q: 桌面版点单词没反应？**
部分扫描版 PDF 没有文字层，需要原生文本型 PDF。

**Q: 局域网其他设备无法访问 Web 版？**
检查 Windows 防火墙：允许 Python 通过防火墙，或临时关闭防火墙测试。

**Q: 如何部署到公网服务器？**
- 设 `DJANGO_DEBUG=False`
- 生成强随机 `DJANGO_SECRET_KEY`
- 配置 `ALLOWED_HOSTS`
- 生产环境建议 PostgreSQL + Gunicorn + Nginx

**Q: 支持哪些 AI 服务？**
所有兼容 OpenAI Chat Completions API 的服务均可。国内 DeepSeek、通义千问等修改 `OPENAI_BASE_URL` 即可。
