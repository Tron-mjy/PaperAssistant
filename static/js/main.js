// ===== State =====
let currentPaperId = null;
let currentPaperText = '';
let vocabulary = [];
let isAnalyzing = false;
let analysisText = '';

// ===== DOM =====
const $ = function(sel) { return document.querySelector(sel); };

const leftPanel = $('#leftPanel');
const splitter = $('#splitter');
const pdfObject = $('#pdfObject');
const pdfWelcome = $('#pdfWelcome');
const pdfUpload = $('#pdfUpload');
const wordInput = $('#wordInput');
const wordSearchBtn = $('#wordSearchBtn');
const wordResult = $('#wordResult');
const qaInput = $('#qaInput');
const qaBtn = $('#qaBtn');
const qaResult = $('#qaResult');
const analysisSection = $('#analysisSection');
const analysisContent = $('#analysisContent');
const analysisHeader = $('#analysisHeader');
const analysisToggle = $('#analysisToggle');
const wordbookList = $('#wordbookList');
const wordCount = $('#wordCount');
const exportBtn = $('#exportBtn');
const loadingOverlay = $('#loadingOverlay');
const loadingText = $('#loadingText');
const paperTitle = $('#paperTitle');
const toast = $('#toast');
const historySidebar = $('#historySidebar');
const historyList = $('#historyList');
const sidebarToggle = $('#sidebarToggle');
const historyCloseBtn = $('#historyCloseBtn');

// ===== CSRF & API =====
function getCookie(name) {
    var v = null;
    if (document.cookie && document.cookie !== '') {
        var cs = document.cookie.split(';');
        for (var i = 0; i < cs.length; i++) {
            var c = cs[i].trim();
            if (c.startsWith(name + '=')) { v = decodeURIComponent(c.substring(name.length + 1)); break; }
        }
    }
    return v;
}
var csrftoken = getCookie('csrftoken');

async function api(url, opts) {
    opts = opts || {};
    var headers = { 'X-CSRFToken': csrftoken };
    if (opts.headers) { Object.keys(opts.headers).forEach(function(k) { headers[k] = opts.headers[k]; }); }
    if (!(opts.body instanceof FormData)) { headers['Content-Type'] = 'application/json'; }
    var res = await fetch(url, { method: opts.method || 'GET', body: opts.body, headers: headers });
    if (!res.ok) {
        var data = await res.json().catch(function() { return {}; });
        throw new Error(data.error || '请求失败');
    }
    return res;
}

function showToast(msg, type) {
    toast.textContent = msg; toast.className = 'toast ' + (type || '');
    toast.style.display = 'block';
    clearTimeout(toast._tid); toast._tid = setTimeout(function() { toast.style.display = 'none'; }, 3000);
}

function showLoading(text) { loadingText.textContent = text || '处理中...'; loadingOverlay.style.display = 'flex'; }
function hideLoading() { loadingOverlay.style.display = 'none'; }

function escapeHtml(str) { var d = document.createElement('div'); d.textContent = str; return d.innerHTML; }

// ===== Markdown =====
function renderMarkdown(text) {
    if (!text) return '';
    var html = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, function(m, lang, code) { return '<pre><code>' + code.trim() + '</code></pre>'; });
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>'); html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>'); html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>'); html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^[*-]{3,}\s*$/gm, '<hr>');
    html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');
    html = html.replace(/<\/blockquote>\n<blockquote>/g, '<br>');
    html = html.replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>'); html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ol>$1</ol>');
    html = html.replace(/^[-*+] (.+)$/gm, '<li>$1</li>');
    var blocks = html.split(/(<ol>[\s\S]*?<\/ol>)/g);
    html = blocks.map(function(b) { if (b.startsWith('<ol>')) return b; return b.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>'); }).join('');
    html = html.replace(/\n\n+/g, '</p><p>'); html = html.replace(/\n/g, '<br>'); html = '<p>' + html + '</p>';
    html = html.replace(/<p>\s*(<(?:h[234]|pre|ul|ol|blockquote|hr))/g, '$1');
    html = html.replace(/(<\/(?:h[234]|pre|ul|ol|blockquote)>)\s*<\/p>/g, '$1');
    html = html.replace(/<p><\/p>/g, ''); html = html.replace(/<p>\s*<br>\s*<\/p>/g, '');
    return html;
}

// ===== Splitter =====
var _leftW = parseInt(localStorage.getItem('paperAssistant_leftWidth')) || Math.round(window.innerWidth * 0.75);
var _dragX = 0, _dragW = 0;

function applyWidth(w) {
    _leftW = Math.max(300, Math.min(window.innerWidth - 340, w));
    leftPanel.style.width = _leftW + 'px'; leftPanel.style.flex = 'none';
    localStorage.setItem('paperAssistant_leftWidth', _leftW.toString());
}
applyWidth(_leftW);

splitter.addEventListener('mousedown', function(e) {
    e.preventDefault();
    _dragX = e.clientX; _dragW = leftPanel.offsetWidth;
    splitter.classList.add('active');
    document.body.style.cursor = 'col-resize'; document.body.style.userSelect = 'none';
});

window.addEventListener('mousemove', function(e) {
    if (!splitter.classList.contains('active')) return;
    var sw = historySidebar.classList.contains('open') ? historySidebar.offsetWidth : 0;
    applyWidth(_dragW + (e.clientX - _dragX));
});

window.addEventListener('mouseup', function() {
    if (!splitter.classList.contains('active')) return;
    splitter.classList.remove('active');
    document.body.style.cursor = ''; document.body.style.userSelect = '';
});
window.addEventListener('resize', function() { applyWidth(_leftW); });

// ===== Sidebar =====
sidebarToggle.addEventListener('click', function() { historySidebar.classList.toggle('open'); loadHistory(); });
historyCloseBtn.addEventListener('click', function() { historySidebar.classList.remove('open'); });

async function loadHistory() {
    try {
        var res = await fetch('/api/papers/'); var data = await res.json();
        if (!data.papers.length) { historyList.innerHTML = '<div class="placeholder-text">暂无历史文档</div>'; return; }
        historyList.innerHTML = data.papers.map(function(p) {
            return '<div class="history-item' + (p.id === currentPaperId ? ' active' : '') + '" data-id="' + p.id + '">' +
                '<button class="h-delete" data-id="' + p.id + '" title="删除">&times;</button>' +
                '<div class="h-filename">' + escapeHtml(p.filename) + '</div><div class="h-meta">' + p.uploaded_at + '</div></div>';
        }).join('');
        historyList.querySelectorAll('.history-item').forEach(function(item) {
            item.addEventListener('click', function(e) {
                if (e.target.classList.contains('h-delete')) return;
                var id = parseInt(item.dataset.id); if (id !== currentPaperId) loadPaper(id);
            });
        });
        historyList.querySelectorAll('.h-delete').forEach(function(btn) {
            btn.addEventListener('click', async function(e) {
                e.stopPropagation(); var id = parseInt(btn.dataset.id);
                if (!confirm('删除？')) return;
                try { await api('/api/paper/' + id + '/delete/', { method: 'DELETE' }); if (id === currentPaperId) resetViewer(); loadHistory(); showToast('已删除', 'success'); }
                catch (err) { showToast(err.message, 'error'); }
            });
        });
    } catch (e) {}
}

async function loadPaper(id) {
    showLoading('正在加载...');
    try {
        var ctx = await (await fetch('/api/paper/' + id + '/context/')).json();
        currentPaperId = ctx.id; currentPaperText = ctx.extracted_text || ''; paperTitle.textContent = ctx.filename;
        if (ctx.file_url) { pdfObject.data = ctx.file_url; pdfObject.style.display = ''; pdfWelcome.style.display = 'none'; }
        try { var ana = await (await fetch('/api/paper/' + id + '/analysis/')).json(); if (ana.analysis) showAnalysis(ana.analysis); } catch (e) {}
        await loadVocabulary(); loadHistory(); hideLoading(); showToast('论文已加载', 'success');
    } catch (err) { hideLoading(); showToast(err.message, 'error'); }
}

function resetViewer() {
    currentPaperId = null; currentPaperText = ''; analysisText = '';
    pdfObject.data = ''; pdfObject.style.display = 'none'; pdfWelcome.style.display = 'flex';
    paperTitle.textContent = ''; qaResult.innerHTML = '<div class="placeholder-text">问答回复将显示在这里</div>';
    analysisSection.style.display = 'none'; analysisContent.innerHTML = '';
    wordResult.innerHTML = '<div class="placeholder-text">单词含义将显示在这里</div>';
    vocabulary = []; renderWordbook();
}

// ===== Upload =====
document.querySelector('.upload-btn').addEventListener('click', function() { pdfUpload.click(); });
pdfUpload.addEventListener('change', async function(e) {
    var file = e.target.files[0]; if (!file) return; await handleUpload(file); pdfUpload.value = '';
});

async function handleUpload(file) {
    if (isAnalyzing) return; isAnalyzing = true;
    showLoading('正在上传并分析论文...');
    var fd = new FormData(); fd.append('file', file);
    try {
        var data = await (await api('/api/upload/', { method: 'POST', body: fd })).json();
        currentPaperId = data.id; paperTitle.textContent = data.filename;
        try { var ctx = await (await fetch('/api/paper/' + data.id + '/context/')).json(); currentPaperText = ctx.extracted_text || ''; } catch (e) {}
        pdfObject.data = data.file_url; pdfObject.style.display = ''; pdfWelcome.style.display = 'none';
        showAnalysis(data.analysis);
        await loadVocabulary(); loadHistory(); hideLoading(); showToast('分析完成！', 'success');
    } catch (err) { hideLoading(); showToast(err.message, 'error'); }
    finally { isAnalyzing = false; }
}

function showAnalysis(text) {
    if (!text) return; analysisText = text;
    analysisSection.style.display = ''; analysisContent.innerHTML = renderMarkdown(text);
    analysisContent.classList.remove('collapsed'); analysisToggle.classList.remove('collapsed'); analysisToggle.textContent = '▼';
}
analysisHeader.addEventListener('click', function() {
    var c = analysisContent.classList.toggle('collapsed');
    analysisToggle.classList.toggle('collapsed', c); analysisToggle.textContent = c ? '▶' : '▼';
});

// ===== Word Lookup =====
wordSearchBtn.addEventListener('click', function() { lookupWord(); });
wordInput.addEventListener('keydown', function(e) { if (e.key === 'Enter') lookupWord(); });

async function lookupWord() {
    var word = wordInput.value.trim();
    if (!word) { showToast('请输入单词', 'error'); return; }
    wordSearchBtn.disabled = true; wordSearchBtn.textContent = '查询中...';
    wordResult.innerHTML = '<div class="placeholder-text">查询中...</div>';
    try {
        var data = await (await api('/api/word/', {
            method: 'POST', body: JSON.stringify({ word: word, paper_id: currentPaperId, context: currentPaperText })
        })).json();
        wordResult.innerHTML = renderMarkdown(data.meaning);
        addToWordbook(word, data.meaning);
    } catch (err) {
        wordResult.innerHTML = '<div class="placeholder-text" style="color:var(--danger)">' + err.message + '</div>';
    } finally { wordSearchBtn.disabled = false; wordSearchBtn.textContent = '查询'; }
}

// ===== AI Q&A =====
qaBtn.addEventListener('click', function() { askAI(); });
qaInput.addEventListener('keydown', function(e) { if (e.key === 'Enter' && e.ctrlKey) askAI(); });

async function askAI() {
    var q = qaInput.value.trim(); if (!q) { showToast('请输入问题', 'error'); return; }
    qaBtn.disabled = true; qaBtn.textContent = '思考中...';
    try {
        var data = await (await api('/api/ask/', {
            method: 'POST', body: JSON.stringify({ question: q, paper_id: currentPaperId })
        })).json();
        qaResult.innerHTML = renderMarkdown(data.answer); qaResult.scrollTop = 0; qaInput.value = '';
    } catch (err) {
        qaResult.innerHTML = '<div class="placeholder-text" style="color:var(--danger)">' + err.message + '</div>';
    } finally { qaBtn.disabled = false; qaBtn.textContent = '提问'; }
}

// ===== Wordbook =====
function addToWordbook(word, meaning) {
    var ex = vocabulary.find(function(v) { return v.word.toLowerCase() === word.toLowerCase(); });
    if (ex) ex.meaning = meaning;
    else vocabulary.unshift({ id: Date.now(), word: word, meaning: meaning });
    renderWordbook();
}

async function loadVocabulary() {
    try {
        var params = currentPaperId ? '?paper_id=' + currentPaperId : '';
        var data = await (await fetch('/api/vocabulary/' + params)).json();
        vocabulary = data.words; renderWordbook();
    } catch (e) {}
}

function renderWordbook() {
    if (!vocabulary.length) { wordbookList.innerHTML = '<div class="placeholder-text">查询过的单词将自动添加到此处</div>'; wordCount.textContent = '0'; return; }
    wordCount.textContent = vocabulary.length;
    wordbookList.innerHTML = vocabulary.map(function(v) {
        return '<div class="wordbook-item" data-id="' + v.id + '">' +
            '<div class="word-info"><div class="word">' + escapeHtml(v.word) + '</div>' +
            '<div class="meaning">' + escapeHtml(v.meaning || '').substring(0, 150) + '</div></div>' +
            '<button class="wordbook-delete" data-id="' + v.id + '" title="删除">&times;</button></div>';
    }).join('');
    wordbookList.querySelectorAll('.wordbook-delete').forEach(function(btn) {
        btn.addEventListener('click', function(e) { e.stopPropagation(); deleteWord(btn.dataset.id); });
    });
    wordbookList.querySelectorAll('.wordbook-item').forEach(function(item) {
        item.addEventListener('click', function() {
            var w = item.querySelector('.word'); if (w) { wordInput.value = w.textContent; lookupWord(); }
        });
    });
}

async function deleteWord(id) {
    vocabulary = vocabulary.filter(function(v) { return v.id !== parseInt(id); }); renderWordbook();
    try { await api('/api/vocabulary/' + id + '/delete/', { method: 'DELETE' }); } catch (e) {}
}

exportBtn.addEventListener('click', function() {
    if (currentPaperId) { window.open('/api/vocabulary/export/?paper_id=' + currentPaperId, '_blank'); return; }
    var csv = '单词,含义\n';
    vocabulary.forEach(function(v) { csv += '"' + v.word + '","' + (v.meaning || '').replace(/"/g, '""') + '"\n'; });
    var blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' });
    var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'vocabulary.csv';
    a.click(); URL.revokeObjectURL(a.href); showToast('CSV 已导出', 'success');
});

// ===== Init =====
loadVocabulary(); loadHistory();
