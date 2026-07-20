"""OpenAI API service — shared configuration with Django .env."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Load .env from project root (parent of desktop/)
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

API_KEY = os.getenv('OPENAI_API_KEY', '')
BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')


def _get_client():
    return OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=60.0)


def _print_error(context, e):
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"[Desktop] API Error: {context}", file=sys.stderr)
    print(f"  URL: {BASE_URL}  Model: {MODEL}", file=sys.stderr)
    print(f"  {type(e).__name__}: {e}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)


def analyze_paper(text):
    client = _get_client()
    prompt = f"""请仔细阅读以下学术论文内容，并按照以下格式进行分析回答：

## 论文思路
## 论文创新点
## 论文总结
## 论文展望
## 缩写/概念解释

论文内容：
{text[:120000]}"""
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": "你是专业的计算机科学研究助手，用中文回答。"},
                      {"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return resp.choices[0].message.content
    except Exception as e:
        _print_error("analyze_paper", e)
        raise


def lookup_word(word, context):
    client = _get_client()
    prompt = f"""解释英文单词：{word}
论文上下文：{context[:3000]}
格式：1.一般含义 2.文中含义 3.补充说明"""
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": "你是计算机科学术语解释助手，用中文回答。"},
                      {"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return resp.choices[0].message.content
    except Exception as e:
        _print_error("lookup_word", e)
        raise


def ask_question(question, paper_context):
    client = _get_client()
    prompt = f"""论文内容：{paper_context[:80000]}
用户问题：{question}
基于论文内容回答。如论文未涉及，从CS通用知识给出参考。"""
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": "你是计算机科学论文阅读助手，用中文回答。"},
                      {"role": "user", "content": prompt}],
            temperature=0.5,
        )
        return resp.choices[0].message.content
    except Exception as e:
        _print_error("ask_question", e)
        raise
