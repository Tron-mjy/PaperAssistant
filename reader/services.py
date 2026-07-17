import sys

from django.conf import settings
from openai import APIError, APIConnectionError, APITimeoutError, AuthenticationError, OpenAI, PermissionDeniedError


def get_client():
    return OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        timeout=60.0,
    )


def _print_error(context: str, e: Exception):
    """Print API error details to console for debugging."""
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"[PaperAssistant] API Error: {context}", file=sys.stderr)
    print(f"  Base URL: {settings.OPENAI_BASE_URL}", file=sys.stderr)
    print(f"  Model:    {settings.OPENAI_MODEL}", file=sys.stderr)
    print(f"  Key:      {settings.OPENAI_API_KEY[:12]}...{settings.OPENAI_API_KEY[-4:] if len(settings.OPENAI_API_KEY) > 16 else '***'}", file=sys.stderr)
    print(f"  Type:     {type(e).__name__}", file=sys.stderr)
    print(f"  Message:  {e}", file=sys.stderr)
    if isinstance(e, APIConnectionError):
        print(f"  HINT:     Connection failed. Check:", file=sys.stderr)
        print(f"            1. OPENAI_BASE_URL is correct in .env", file=sys.stderr)
        print(f"            2. Network / VPN / proxy is working", file=sys.stderr)
        print(f"            3. Firewall is not blocking the connection", file=sys.stderr)
    elif isinstance(e, AuthenticationError):
        print(f"  HINT:     Authentication failed. Check OPENAI_API_KEY in .env", file=sys.stderr)
    elif isinstance(e, PermissionDeniedError):
        print(f"  HINT:     Request blocked (403). Possible causes:", file=sys.stderr)
        print(f"            - API key expired / revoked / out of balance", file=sys.stderr)
        print(f"            - Model '{settings.OPENAI_MODEL}' not available on this plan", file=sys.stderr)
        print(f"            - Service provider restricted your access", file=sys.stderr)
    elif isinstance(e, APITimeoutError):
        print(f"  HINT:     Request timed out. Consider using a faster model or check network.", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)


def analyze_paper(text: str) -> dict:
    """Analyze a paper and return structured results."""
    client = get_client()
    prompt = f"""请仔细阅读以下学术论文内容，并按照以下格式进行分析回答：

## 论文思路
（请详细描述论文的研究思路、方法论和技术路线，包括作者是如何一步步推进研究的）

## 论文创新点
（请列出论文的主要创新点和贡献，说明这些创新点相对于现有工作的优势）

## 论文总结
（请对论文进行全面的总结，包括研究背景、方法、实验和主要发现）

## 论文展望
（请分析论文的未来工作方向、潜在改进空间和研究展望）

## 缩写/概念解释
（请列出论文中出现的重要缩写、专业术语和概念，并给出详细解释）

---

论文内容如下：
{text[:120000]}"""

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的计算机科学研究助手，擅长分析和解读学术论文。请用中文回答。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        return {"analysis_text": response.choices[0].message.content}
    except Exception as e:
        _print_error("analyze_paper", e)
        raise


def lookup_word(word: str, context: str) -> dict:
    """Look up a word's meaning with paper context."""
    client = get_client()
    prompt = f"""请解释以下英文单词或短语的含义：

单词/短语：{word}

论文上下文（该词出现的段落）：
{context[:3000]}

请按照以下格式回答：
1. 一般含义：（该词在日常英语或学术英语中的通用含义）
2. 文中含义：（结合论文上下文，该词在本文中最合适的含义）
3. 补充说明：（如有相关的计算机科学概念，请简要说明）"""

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的计算机科学术语解释助手。请用中文回答，解释要准确、简洁。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        return {"meaning": response.choices[0].message.content}
    except Exception as e:
        _print_error("lookup_word", e)
        raise


def explain_paragraph(paragraph: str, paper_context: str) -> dict:
    """Explain a selected paragraph in detail."""
    client = get_client()
    prompt = f"""请详细解释以下论文段落的内容：

段落内容：
{paragraph}

论文整体背景（供参考）：
{paper_context[:2000]}

请包含以下内容：
1. 段落主旨：这段内容在讲什么
2. 详细解释：逐句解释段落中的关键内容
3. 技术要点：段落中涉及的技术概念和方法的说明"""

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的计算机科学论文解读助手。请用中文回答，解释要详细、通俗易懂。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        return {"explanation": response.choices[0].message.content}
    except Exception as e:
        _print_error("explain_paragraph", e)
        raise


def ask_question(question: str, paper_context: str) -> dict:
    """Answer a question about the paper."""
    client = get_client()
    prompt = f"""用户正在阅读一篇学术论文，有以下问题需要解答。

论文内容（供参考）：
{paper_context[:80000]}

用户的问题：
{question}

请基于论文内容详细回答用户的问题。如果论文中没有涉及相关内容，请如实告知，并尝试从计算机科学的通用知识角度给出参考意见。"""

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的计算机科学论文阅读助手。请用中文回答，回答要准确、有深度。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
        )
        return {"answer": response.choices[0].message.content}
    except Exception as e:
        _print_error("ask_question", e)
        raise
