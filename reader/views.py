import csv
import io
import json

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from PyPDF2 import PdfReader

from .models import Paper, Vocabulary
from .services import analyze_paper, ask_question, explain_paragraph, lookup_word


# ===== Auth Views =====

@ensure_csrf_cookie
def login_view(request):
    if request.method == 'GET':
        return render(request, 'reader/login.html')

    data = json.loads(request.body)
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return JsonResponse({'error': '请输入用户名和密码'}, status=400)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({'error': '用户名或密码错误'}, status=401)

    login(request, user)
    return JsonResponse({'ok': True, 'username': user.username})


@ensure_csrf_cookie
def register_view(request):
    if request.method == 'GET':
        return render(request, 'reader/register.html')

    data = json.loads(request.body)
    username = data.get('username', '').strip()
    password = data.get('password', '')
    password2 = data.get('password2', '')

    if not username or not password:
        return JsonResponse({'error': '请输入用户名和密码'}, status=400)
    if len(username) < 3:
        return JsonResponse({'error': '用户名至少需要3个字符'}, status=400)
    if len(password) < 6:
        return JsonResponse({'error': '密码至少需要6个字符'}, status=400)
    if password != password2:
        return JsonResponse({'error': '两次输入的密码不一致'}, status=400)

    try:
        user = User.objects.create_user(username=username, password=password)
    except IntegrityError:
        return JsonResponse({'error': '该用户名已被注册'}, status=409)

    login(request, user)
    return JsonResponse({'ok': True, 'username': user.username})


def logout_view(request):
    logout(request)
    return redirect('login')


# ===== Main View =====

@ensure_csrf_cookie
@login_required
def index(request):
    papers = Paper.objects.filter(user=request.user).order_by('-uploaded_at')[:10]
    return render(request, 'reader/index.html', {'papers': papers})


# ===== Paper Views =====

@require_http_methods(['POST'])
@login_required
def upload_pdf(request):
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return JsonResponse({'error': '请选择要上传的PDF文件'}, status=400)

    if not uploaded_file.name.lower().endswith('.pdf'):
        return JsonResponse({'error': '只支持PDF格式文件'}, status=400)

    if uploaded_file.size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
        return JsonResponse({'error': f'文件大小超过限制 ({settings.FILE_UPLOAD_MAX_MEMORY_SIZE // (1024*1024)}MB)'}, status=400)

    paper = Paper.objects.create(
        user=request.user,
        file=uploaded_file,
        filename=uploaded_file.name,
    )

    try:
        file_path = paper.file.path
        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        extracted_text = '\n\n'.join(text_parts)
        paper.extracted_text = extracted_text
    except Exception as e:
        paper.delete()
        return JsonResponse({'error': f'PDF文本提取失败: {str(e)}'}, status=500)

    try:
        analysis = analyze_paper(extracted_text)
        paper.analysis = analysis
    except Exception as e:
        paper.delete()
        return JsonResponse({'error': f'AI分析失败: {str(e)}'}, status=500)

    paper.save()

    return JsonResponse({
        'id': paper.id,
        'filename': paper.filename,
        'file_url': paper.file.url,
        'analysis': analysis['analysis_text'],
        'page_count': len(reader.pages),
    })


@require_http_methods(['GET'])
@login_required
def get_analysis(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id, user=request.user)
    return JsonResponse({
        'id': paper.id,
        'filename': paper.filename,
        'analysis': paper.analysis.get('analysis_text', '') if paper.analysis else '',
    })


@require_http_methods(['GET'])
@login_required
def get_paper_context(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id, user=request.user)
    return JsonResponse({
        'id': paper.id,
        'filename': paper.filename,
        'file_url': paper.file.url,
        'extracted_text': paper.extracted_text,
    })


@require_http_methods(['GET'])
@login_required
def paper_list(request):
    papers = Paper.objects.filter(user=request.user).order_by('-uploaded_at')[:30]
    items = [
        {
            'id': p.id,
            'filename': p.filename,
            'uploaded_at': timezone.localtime(p.uploaded_at).strftime('%Y-%m-%d %H:%M'),
            'has_analysis': bool(p.analysis),
        }
        for p in papers
    ]
    return JsonResponse({'papers': items})


@require_http_methods(['DELETE'])
@login_required
def paper_delete(request, paper_id):
    paper = get_object_or_404(Paper, id=paper_id, user=request.user)
    paper.delete()
    return JsonResponse({'ok': True})


# ===== Word Lookup =====

@require_http_methods(['POST'])
@login_required
def word_lookup(request):
    data = json.loads(request.body)
    word = data.get('word', '').strip()
    context = data.get('context', '').strip()
    paper_id = data.get('paper_id')

    if not word:
        return JsonResponse({'error': '请输入要查询的单词'}, status=400)

    if not paper_id:
        return JsonResponse({'error': '请先上传PDF文档'}, status=400)

    paper = get_object_or_404(Paper, id=paper_id, user=request.user)
    if not context and paper.extracted_text:
        text = paper.extracted_text
        idx = text.lower().find(word.lower())
        if idx >= 0:
            start = max(0, idx - 500)
            end = min(len(text), idx + len(word) + 500)
            context = text[start:end]

    try:
        result = lookup_word(word, context)
    except Exception as e:
        return JsonResponse({'error': f'AI查询失败: {str(e)}'}, status=500)

    existing = Vocabulary.objects.filter(
        user=request.user, paper=paper, word__iexact=word,
    ).first()
    if existing:
        existing.meaning_context = result['meaning']
        existing.save(update_fields=['meaning_context'])
    else:
        Vocabulary.objects.create(
            user=request.user, paper=paper, word=word,
            meaning_general='', meaning_context=result['meaning'],
        )

    return JsonResponse({'word': word, 'meaning': result['meaning']})


# ===== Paragraph Explain =====

@require_http_methods(['POST'])
@login_required
def paragraph_explain(request):
    data = json.loads(request.body)
    paragraph = data.get('paragraph', '').strip()
    paper_id = data.get('paper_id')

    if not paragraph:
        return JsonResponse({'error': '请选择要解释的文本'}, status=400)

    if not paper_id:
        return JsonResponse({'error': '请先上传PDF文档'}, status=400)

    paper = get_object_or_404(Paper, id=paper_id, user=request.user)
    paper_context = paper.extracted_text

    try:
        result = explain_paragraph(paragraph, paper_context)
    except Exception as e:
        return JsonResponse({'error': f'AI解释失败: {str(e)}'}, status=500)

    return JsonResponse({'explanation': result['explanation']})


# ===== AI Q&A =====

@require_http_methods(['POST'])
@login_required
def ask_ai(request):
    data = json.loads(request.body)
    question = data.get('question', '').strip()
    paper_id = data.get('paper_id')

    if not question:
        return JsonResponse({'error': '请输入您的问题'}, status=400)

    if not paper_id:
        return JsonResponse({'error': '请先上传PDF文档'}, status=400)

    paper = get_object_or_404(Paper, id=paper_id, user=request.user)
    paper_context = paper.extracted_text

    try:
        result = ask_question(question, paper_context)
    except Exception as e:
        return JsonResponse({'error': f'AI回答失败: {str(e)}'}, status=500)

    return JsonResponse({'answer': result['answer']})


# ===== Vocabulary (Wordbook) =====

@require_http_methods(['GET'])
@login_required
def vocabulary_list(request):
    paper_id = request.GET.get('paper_id')
    if paper_id:
        vocab = Vocabulary.objects.filter(
            user=request.user, paper_id=paper_id
        ).order_by('-created_at')
    else:
        vocab = Vocabulary.objects.filter(
            user=request.user
        ).order_by('-created_at')[:200]

    items = [
        {
            'id': v.id,
            'word': v.word,
            'meaning': v.meaning_context,
            'created_at': timezone.localtime(v.created_at).strftime('%Y-%m-%d %H:%M'),
        }
        for v in vocab
    ]
    return JsonResponse({'words': items})


@require_http_methods(['POST'])
@login_required
def vocabulary_add(request):
    data = json.loads(request.body)
    word = data.get('word', '').strip()
    meaning = data.get('meaning', '').strip()
    paper_id = data.get('paper_id')

    if not word:
        return JsonResponse({'error': '请输入单词'}, status=400)

    paper = None
    if paper_id:
        paper = get_object_or_404(Paper, id=paper_id, user=request.user)

    v = Vocabulary.objects.create(
        user=request.user,
        paper=paper,
        word=word,
        meaning_context=meaning,
    )
    return JsonResponse({
        'id': v.id,
        'word': v.word,
        'meaning': v.meaning_context,
    })


@require_http_methods(['DELETE'])
@login_required
def vocabulary_delete(request, word_id):
    v = get_object_or_404(Vocabulary, id=word_id, user=request.user)
    v.delete()
    return JsonResponse({'ok': True})


@login_required
def vocabulary_export(request):
    paper_id = request.GET.get('paper_id')
    if paper_id:
        vocab = Vocabulary.objects.filter(
            user=request.user, paper_id=paper_id
        ).order_by('-created_at')
    else:
        vocab = Vocabulary.objects.filter(user=request.user).order_by('-created_at')

    output = io.StringIO()
    output.write('﻿')
    writer = csv.writer(output)
    writer.writerow(['单词', '含义', '添加时间'])
    for v in vocab:
        local_time = timezone.localtime(v.created_at)
        writer.writerow([v.word, v.meaning_context, local_time.strftime('%Y-%m-%d %H:%M')])

    response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="vocabulary.csv"'
    return response
