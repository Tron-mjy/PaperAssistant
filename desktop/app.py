"""PaperAssistant Desktop - PySide6 GUI."""
import re
import sys
from pathlib import Path

from PyPDF2 import PdfReader
from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QAction, QFont
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QPushButton, QSplitter, QStatusBar, QTextEdit, QVBoxLayout,
    QWidget, QSizePolicy
)

BASE_DIR = Path(__file__).resolve().parent

# ===== Markdown to HTML =====
def _md(text):
    """Convert simple markdown to HTML for QTextEdit display."""
    if not text:
        return ""
    html = text
    html = html.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Code blocks
    html = re.sub(r'```(\w*)\n([\s\S]*?)```', r'<pre><code>\2</code></pre>', html)
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    # Bold / italic
    html = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', html)
    html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html)
    html = re.sub(r'\*(.+?)\*', r'<i>\1</i>', html)
    # Headers
    html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.M)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.M)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.M)
    html = re.sub(r'^# (.+)$', r'<h2>\1</h2>', html, flags=re.M)
    # HR
    html = re.sub(r'^[*-]{3,}\s*$', '<hr>', html, flags=re.M)
    # Blockquote
    html = re.sub(r'^&gt; (.+)$', r'<blockquote>\1</blockquote>', html, flags=re.M)
    html = html.replace('</blockquote>\n<blockquote>', '<br>')
    # Ordered list
    html = re.sub(r'^(\d+)\. (.+)$', r'<li>\2</li>', html, flags=re.M)
    html = re.sub(r'((?:<li>.*</li>\n?)+)', r'<ol>\1</ol>', html)
    # Unordered list
    html = re.sub(r'^[-*+] (.+)$', r'<li>\1</li>', html, flags=re.M)
    parts = re.split(r'(<ol>[\s\S]*?</ol>)', html)
    html = ''.join(
        p if p.startswith('<ol>') else re.sub(r'((?:<li>.*</li>\n?)+)', r'<ul>\1</ul>', p)
        for p in parts
    )
    # Paragraphs
    html = re.sub(r'\n\n+', '</p><p>', html)
    html = html.replace('\n', '<br>')
    html = f'<p>{html}</p>'
    html = re.sub(r'<p>\s*(<(?:h[234]|pre|ul|ol|blockquote|hr))', r'\1', html)
    html = re.sub(r'(</(?:h[234]|pre|ul|ol|blockquote)>)\s*</p>', r'\1', html)
    html = re.sub(r'<p></p>', '', html)
    return html


def _style():
    """Base CSS for markdown HTML display."""
    return """
    <style>
    body { font-family: "Microsoft YaHei", sans-serif; font-size: 13px; color: #1e293b; line-height: 1.7; }
    h2 { color: #4f46e5; font-size: 15px; margin: 12px 0 6px; }
    h3 { color: #4f46e5; font-size: 14px; margin: 10px 0 4px; }
    h4 { color: #4f46e5; font-size: 13px; margin: 8px 0 4px; }
    pre { background: #1e293b; color: #e2e8f0; padding: 10px 14px; border-radius: 4px; font-size: 12px; overflow-x: auto; }
    code { background: #e0e7ff; color: #4f46e5; padding: 1px 4px; border-radius: 2px; font-size: 12px; }
    pre code { background: none; color: inherit; padding: 0; }
    blockquote { border-left: 3px solid #4f46e5; padding: 4px 10px; margin: 8px 0; color: #64748b; background: #e0e7ff; border-radius: 0 4px 4px 0; }
    ul, ol { padding-left: 20px; margin: 4px 0; }
    li { margin: 2px 0; }
    hr { border: none; border-top: 1px solid #e2e8f0; margin: 10px 0; }
    </style>
    """

import database as db
import services as svc

BASE_DIR = Path(__file__).resolve().parent


class AnalyzeWorker(QThread):
    finished = Signal(str, str)  # extracted_text, analysis
    error = Signal(str)

    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath

    def run(self):
        try:
            reader = PdfReader(self.filepath)
            parts = [p.extract_text() for p in reader.pages if p.extract_text()]
            text = '\n\n'.join(parts)
            analysis = svc.analyze_paper(text)
            self.finished.emit(text, analysis)
        except Exception as e:
            self.error.emit(str(e))


class WordLookupWorker(QThread):
    finished = Signal(str)  # meaning
    error = Signal(str)

    def __init__(self, word, context):
        super().__init__()
        self.word = word
        self.context = context

    def run(self):
        try:
            meaning = svc.lookup_word(self.word, self.context)
            self.finished.emit(meaning)
        except Exception as e:
            self.error.emit(str(e))


class AskAIWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, question, context):
        super().__init__()
        self.question = question
        self.context = context

    def run(self):
        try:
            answer = svc.ask_question(self.question, self.context)
            self.finished.emit(answer)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PaperAssistant - AI 论文陪读助手")
        self.resize(1400, 900)

        self.current_paper_id = None
        self.current_paper_text = ""

        db.init()

        self._build_ui()
        self._load_history()

    # ===== Build UI =====
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # -- Header toolbar
        header = QHBoxLayout()
        header.setContentsMargins(10, 6, 10, 6)

        self.btn_upload = QPushButton("上传 PDF")
        self.btn_upload.setStyleSheet(
            "padding:5px 14px; font-size:12px; font-weight:bold;"
            "background:#4f46e5; color:#fff; border:none; border-radius:4px;"
        )
        self.btn_upload.clicked.connect(self._on_upload)
        header.addWidget(self.btn_upload)

        self.lbl_header_title = QLabel("PaperAssistant  AI 论文陪读助手")
        self.lbl_header_title.setStyleSheet("font-size:16px; font-weight:bold; color:#4f46e5;")
        header.addWidget(self.lbl_header_title)

        self.lbl_paper_name = QLabel("")
        self.lbl_paper_name.setStyleSheet("color:#64748b; font-size:13px;")
        header.addWidget(self.lbl_paper_name, 1)

        header_w = QWidget()
        header_w.setLayout(header)
        header_w.setStyleSheet("background:#fff; border-bottom:1px solid #e2e8f0;")
        outer.addWidget(header_w)

        # Splitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(8)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background: #e2e8f0;
                margin: 0 2px;
            }
            QSplitter::handle:hover {
                background: #4f46e5;
            }
        """)
        # Wrap splitter + sidebar in a horizontal row
        body_row = QHBoxLayout()
        body_row.setContentsMargins(0, 0, 0, 0)
        body_row.setSpacing(0)

        # History sidebar
        self.history_list = QListWidget()
        self.history_list.setFixedWidth(240)
        self.history_list.setStyleSheet("background:#fff; color:#1e293b; border-right:1px solid #e2e8f0; font-size:12px;")
        self.history_list.itemClicked.connect(self._on_history_click)
        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self._on_history_context_menu)
        self.history_list.hide()
        body_row.addWidget(self.history_list)

        body_row.addWidget(self.splitter)

        body_w = QWidget()
        body_w.setLayout(body_row)
        outer.addWidget(body_w, 1)

        # -- Left: PDF viewer
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.pdf_view = QWebEngineView()
        self.pdf_view.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
        self.pdf_view.settings().setAttribute(QWebEngineSettings.PdfViewerEnabled, True)
        self.pdf_view.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        self.pdf_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pdf_view.hide()
        left_layout.addWidget(self.pdf_view)

        # Welcome placeholder
        self.welcome = QLabel("请上传一篇 PDF 论文开始阅读\n\n点击左上角「上传 PDF」按钮")
        self.welcome.setAlignment(Qt.AlignCenter)
        self.welcome.setStyleSheet("color: #999; font-size: 16px; background: #e5e7eb;")
        left_layout.addWidget(self.welcome)

        self.splitter.addWidget(left)

        # -- Right panel with vertical splitter
        right = QWidget()
        right.setMinimumWidth(300)
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.setHandleWidth(6)
        right_splitter.setStyleSheet("QSplitter::handle { background:#e2e8f0; } QSplitter::handle:hover { background:#6366f1; }")

        # Upper section (scrollable: analysis + word + Q&A)
        upper = QWidget()
        ul = QVBoxLayout(upper)
        ul.setContentsMargins(14, 12, 14, 8)
        ul.setSpacing(8)

        COLOR = "#6366f1"
        BTN_STYLE = f"background:{COLOR}; color:#fff; border:none; border-radius:5px; padding:7px 14px; font-weight:600; font-size:12px;"
        INPUT_STYLE = "border:1px solid #e2e8f0; border-radius:5px; padding:8px 10px; font-size:13px; color:#0f172a; background:#fff;"
        BOX_STYLE = "background:#f8fafc; color:#0f172a; border:1px solid #e2e8f0; border-radius:5px; font-size:13px; padding:10px 12px;"

        self.btn_analysis_toggle = QPushButton("▼ AI 分析报告")
        self.btn_analysis_toggle.setStyleSheet(f"text-align:left; font-weight:700; border:none; background:none; color:{COLOR}; padding:4px 0; font-size:13px;")
        self.btn_analysis_toggle.clicked.connect(self._toggle_analysis)
        ul.addWidget(self.btn_analysis_toggle)

        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setMaximumHeight(200)
        self.analysis_text.setStyleSheet(BOX_STYLE)
        self.analysis_text.setPlaceholderText("上传论文后，AI 分析结果将显示在这里")
        ul.addWidget(self.analysis_text)

        ul.addWidget(QLabel("单词查询"))
        ul.itemAt(ul.count() - 1).widget().setStyleSheet("font-weight:700; font-size:12px; color:#475569; text-transform:uppercase; letter-spacing:0.5px;")
        wl_row = QHBoxLayout()
        self.word_input = QLineEdit()
        self.word_input.setPlaceholderText("输入要查询的单词...")
        self.word_input.setStyleSheet(INPUT_STYLE)
        self.word_input.returnPressed.connect(self._on_word_lookup)
        wl_row.addWidget(self.word_input)
        self.btn_word = QPushButton("查询")
        self.btn_word.clicked.connect(self._on_word_lookup)
        self.btn_word.setStyleSheet(BTN_STYLE)
        wl_row.addWidget(self.btn_word)
        ul.addLayout(wl_row)

        self.word_result = QTextEdit()
        self.word_result.setReadOnly(True)
        self.word_result.setMaximumHeight(120)
        self.word_result.setStyleSheet(BOX_STYLE)
        self.word_result.setPlaceholderText("单词含义")
        ul.addWidget(self.word_result)

        ul.addWidget(QLabel("AI 问答"))
        ul.itemAt(ul.count() - 1).widget().setStyleSheet("font-weight:700; font-size:12px; color:#475569; text-transform:uppercase; letter-spacing:0.5px;")
        self.qa_input = QTextEdit()
        self.qa_input.setMaximumHeight(80)
        self.qa_input.setPlaceholderText("向AI提问...（Ctrl+Enter 发送）")
        self.qa_input.setStyleSheet(INPUT_STYLE)
        ul.addWidget(self.qa_input)

        self.btn_ask = QPushButton("提问")
        self.btn_ask.clicked.connect(self._on_ask_ai)
        self.btn_ask.setStyleSheet(BTN_STYLE)
        ul.addWidget(self.btn_ask)

        self.qa_result = QTextEdit()
        self.qa_result.setReadOnly(True)
        self.qa_result.setStyleSheet(BOX_STYLE)
        self.qa_result.setPlaceholderText("问答回复")
        ul.addWidget(self.qa_result, 1)

        right_splitter.addWidget(upper)

        # Lower section: wordbook (header fixed, list fills remaining)
        lower = QWidget()
        ll = QVBoxLayout(lower)
        ll.setContentsMargins(14, 8, 14, 10)
        ll.setSpacing(6)

        wb_header = QHBoxLayout()
        wb_label = QLabel("生词本")
        wb_label.setStyleSheet("font-weight:700; font-size:12px; color:#475569; text-transform:uppercase;")
        wb_header.addWidget(wb_label)
        self.lbl_wb_count = QLabel("0")
        self.lbl_wb_count.setStyleSheet(f"background:{COLOR}; color:#fff; border-radius:10px; padding:2px 8px; font-size:11px; font-weight:700;")
        wb_header.addWidget(self.lbl_wb_count)
        wb_header.addStretch()
        ll.addLayout(wb_header)

        self.wordbook_list = QListWidget()
        self.wordbook_list.setStyleSheet("font-size:13px; color:#0f172a; background:#f8fafc; border:1px solid #e2e8f0; border-radius:5px;")
        ll.addWidget(self.wordbook_list, 1)

        wb_btns = QHBoxLayout()
        self.btn_export = QPushButton("导出 CSV")
        self.btn_export.setStyleSheet("background:#f1f5f9; color:#475569; border:1px solid #e2e8f0; border-radius:4px; padding:5px 12px; font-size:12px;")
        self.btn_export.clicked.connect(self._on_export)
        wb_btns.addWidget(self.btn_export)
        self.btn_delete_word = QPushButton("删除选中")
        self.btn_delete_word.setStyleSheet("background:#f1f5f9; color:#475569; border:1px solid #e2e8f0; border-radius:4px; padding:5px 12px; font-size:12px;")
        self.btn_delete_word.clicked.connect(self._on_delete_word)
        wb_btns.addWidget(self.btn_delete_word)
        ll.addLayout(wb_btns)

        right_splitter.addWidget(lower)
        right_splitter.setSizes([600, 220])
        rl.addWidget(right_splitter)

        self.splitter.addWidget(right)
        self.splitter.setSizes([1000, 400])

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        # Menu
        menu = self.menuBar()
        file_menu = menu.addMenu("文件")
        act_upload = QAction("上传 PDF", self)
        act_upload.triggered.connect(self._on_upload)
        file_menu.addAction(act_upload)
        act_history = QAction("显示/隐藏历史", self)
        act_history.triggered.connect(lambda: self.history_list.setVisible(not self.history_list.isVisible()))
        file_menu.addAction(act_history)
        file_menu.addSeparator()
        act_exit = QAction("退出", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

    # ===== History =====
    def _load_history(self):
        self.history_list.clear()
        papers = db.get_papers()
        for p in papers:
            item = QListWidgetItem(p['filename'] + "\n" + (p['created_at'] or ''))
            item.setData(Qt.UserRole, p['id'])
            self.history_list.addItem(item)

    def _on_history_click(self, item):
        paper_id = item.data(Qt.UserRole)
        paper = db.get_paper(paper_id)
        if not paper:
            return
        self.current_paper_id = paper_id
        self.current_paper_text = paper.get('extracted_text', '')
        self.welcome.hide()
        self.pdf_view.show()
        filepath = paper.get('filepath', '')
        if filepath and Path(filepath).exists():
            self.pdf_view.setUrl(QUrl.fromLocalFile(str(Path(filepath).resolve())))
        # Show analysis
        if paper.get('analysis'):
            self.analysis_text.setHtml(_style() + _md(paper['analysis']))
        self._load_wordbook()
        self.lbl_paper_name.setText(paper.get('filename', ''))
        self.status_bar.showMessage("已加载")

    def _on_history_context_menu(self, pos):
        item = self.history_list.itemAt(pos)
        if not item:
            return
        menu = self.history_list.parent().createStandardContextMenu() if False else None
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        act_delete = QAction("删除", self)
        act_delete.triggered.connect(lambda: self._delete_history_item(item))
        menu.addAction(act_delete)
        menu.exec(self.history_list.mapToGlobal(pos))

    def _delete_history_item(self, item):
        pid = item.data(Qt.UserRole)
        reply = QMessageBox.question(self, "确认", "确定删除这篇论文吗？",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        db.delete_paper(pid)
        if pid == self.current_paper_id:
            self._reset_viewer()
        self._load_history()

    # ===== Upload =====
    def _on_upload(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
        self.status_bar.showMessage("正在分析论文...")
        self.btn_upload.setEnabled(False)

        self.worker = AnalyzeWorker(path)
        self.worker.finished.connect(lambda text, analysis: self._on_analyzed(path, text, analysis))
        self.worker.error.connect(self._on_analyze_error)
        self.worker.start()

    def _on_analyzed(self, filepath, text, analysis):
        filename = Path(filepath).name
        pid = db.add_paper(filepath, filename, text, analysis)
        self.current_paper_id = pid
        self.current_paper_text = text

        self.welcome.hide()
        self.pdf_view.show()
        self.pdf_view.setUrl(QUrl.fromLocalFile(str(Path(filepath).resolve())))

        self.lbl_paper_name.setText(filename)
        self.analysis_text.setHtml(_style() + _md(analysis))
        self._load_history()
        self._load_wordbook()
        self.btn_upload.setEnabled(True)
        self.status_bar.showMessage("分析完成")

    def _on_analyze_error(self, msg):
        QMessageBox.critical(self, "分析失败", msg)
        self.btn_upload.setEnabled(True)
        self.status_bar.showMessage("分析失败")

    def _reset_viewer(self):
        self.current_paper_id = None
        self.current_paper_text = ""
        self.pdf_view.setUrl(QUrl("about:blank"))
        self.pdf_view.hide()
        self.welcome.show()
        self.lbl_paper_name.setText("")
        self.analysis_text.clear()
        self.qa_result.clear()
        self.word_result.clear()
        self.wordbook_list.clear()
        self.lbl_wb_count.setText("0")

    def _toggle_analysis(self):
        v = self.analysis_text.isVisible()
        self.analysis_text.setVisible(not v)
        self.btn_analysis_toggle.setText("▶ AI 分析报告" if v else "▼ AI 分析报告")

    # ===== Word Lookup =====
    def _on_word_lookup(self):
        if not self.current_paper_id:
            QMessageBox.information(self, "提示", "请先上传PDF文档")
            return
        word = self.word_input.text().strip()
        if not word:
            return
        self.btn_word.setEnabled(False)
        self.word_result.setPlainText("查询中...")
        self.wl_worker = WordLookupWorker(word, self.current_paper_text)
        self.wl_worker.finished.connect(lambda m: self._on_word_done(word, m))
        self.wl_worker.error.connect(lambda e: self.word_result.setPlainText(f"错误: {e}"))
        self.wl_worker.finished.connect(lambda _: self.btn_word.setEnabled(True))
        self.wl_worker.error.connect(lambda _: self.btn_word.setEnabled(True))
        self.wl_worker.start()

    def _on_word_done(self, word, meaning):
        self.word_result.setHtml(_style() + _md(meaning))
        if self.current_paper_id:
            db.add_vocabulary(self.current_paper_id, word, meaning)
            self._load_wordbook()

    # ===== AI Q&A =====
    def _on_ask_ai(self):
        if not self.current_paper_id:
            QMessageBox.information(self, "提示", "请先上传PDF文档")
            return
        q = self.qa_input.toPlainText().strip()
        if not q:
            return
        self.btn_ask.setEnabled(False)
        self.qa_result.setPlainText("思考中...")
        self.ask_worker = AskAIWorker(q, self.current_paper_text)
        self.ask_worker.finished.connect(lambda a: self.qa_result.setHtml(_style() + _md(a)))
        self.ask_worker.finished.connect(lambda _: self.btn_ask.setEnabled(True))
        self.ask_worker.error.connect(lambda e: self.qa_result.setPlainText(f"错误: {e}"))
        self.ask_worker.error.connect(lambda _: self.btn_ask.setEnabled(True))
        self.ask_worker.start()

    # ===== Wordbook =====
    def _load_wordbook(self):
        self.wordbook_list.clear()
        vocab = db.get_vocabulary(self.current_paper_id)
        self.lbl_wb_count.setText(str(len(vocab)))
        for v in vocab:
            text = f"{v['word']}\n  {v['meaning'][:80]}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, v['id'])
            self.wordbook_list.addItem(item)

    def _on_delete_word(self):
        item = self.wordbook_list.currentItem()
        if not item:
            return
        vid = item.data(Qt.UserRole)
        db.delete_vocabulary(vid)
        self._load_wordbook()

    def _on_export(self):
        csv_data = db.export_csv(self.current_paper_id)
        path, _ = QFileDialog.getSaveFileName(self, "导出 CSV", "vocabulary.csv", "CSV (*.csv)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(csv_data)
            self.status_bar.showMessage(f"已导出: {path}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
