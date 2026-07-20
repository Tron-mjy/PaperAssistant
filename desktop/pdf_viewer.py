"""PyMuPDF-based PDF viewer with progressive rendering."""
import fitz  # PyMuPDF
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QLabel, QScrollArea, QVBoxLayout, QWidget, QHBoxLayout, QPushButton,
    QSizePolicy
)

HOVER_COLOR = QColor(99, 102, 241, 60)    # semi-transparent indigo
SELECT_COLOR = QColor(99, 102, 241, 120)  # slightly more opaque


class PdfPageWidget(QWidget):
    word_clicked = Signal(str)

    def __init__(self, pixmap, words):
        super().__init__()
        self._pixmap = pixmap
        self._words = words
        self._hover_rect = None   # (x, y, w, h) of word under cursor
        self._select_rect = None  # (x, y, w, h) of clicked word
        self.setFixedSize(pixmap.size())
        self.setCursor(Qt.IBeamCursor)
        self.setMouseTracking(True)

    def _find_word(self, px, py):
        for i, (word, x, y, w, h) in enumerate(self._words):
            if x <= px <= x + w and y <= py <= y + h:
                return i, (x, y, w, h)
        return None, None

    def paintEvent(self, event):
        p = QPainter(self)
        p.drawPixmap(0, 0, self._pixmap)

        # Draw hover highlight
        if self._hover_rect:
            x, y, w, h = self._hover_rect
            p.fillRect(int(x), int(y), int(w), int(h), HOVER_COLOR)
            p.setPen(QPen(QColor(99, 102, 241, 180), 1))
            p.drawRect(int(x), int(y), int(w), int(h))

        # Draw selection highlight
        if self._select_rect:
            x, y, w, h = self._select_rect
            p.fillRect(int(x), int(y), int(w), int(h), SELECT_COLOR)
            p.setPen(QPen(QColor(99, 102, 241), 1.5))
            p.drawRect(int(x), int(y), int(w), int(h))
        p.end()

    def mouseMoveEvent(self, event):
        px, py = event.position().x(), event.position().y()
        _, rect = self._find_word(px, py)
        if rect != self._hover_rect:
            self._hover_rect = rect
            self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton or not self._words:
            return
        px, py = event.position().x(), event.position().y()
        _, rect = self._find_word(px, py)
        if rect:
            self._select_rect = rect
            self._hover_rect = None
            self.update()
            # Find and emit the word
            for word, x, y, w, h in self._words:
                if x == rect[0] and y == rect[1]:
                    self.word_clicked.emit(word)
                    return

    def leaveEvent(self, event):
        if self._hover_rect:
            self._hover_rect = None
            self.update()


class PdfViewer(QWidget):
    word_clicked = Signal(str)

    def __init__(self):
        super().__init__()
        self._doc = None
        self._zoom = 1.5
        self._render_gen = 0
        self._page_index = 0
        self._container = None
        self._clayout = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Zoom toolbar
        tb = QHBoxLayout()
        tb.setContentsMargins(6, 4, 6, 4)
        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_out.setFixedSize(28, 28)
        self.btn_zoom_out.clicked.connect(lambda: self._schedule_zoom(-0.12))
        tb.addWidget(self.btn_zoom_out)
        self.lbl_zoom = QPushButton("150%")
        self.lbl_zoom.setFixedSize(56, 28)
        self.lbl_zoom.setStyleSheet("border:none; font-weight:bold; background:transparent; color:#fff;")
        tb.addWidget(self.lbl_zoom)
        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setFixedSize(28, 28)
        self.btn_zoom_in.clicked.connect(lambda: self._schedule_zoom(0.12))
        tb.addWidget(self.btn_zoom_in)
        tb.addStretch()

        # Page counter label
        self.lbl_page = QLabel("")
        self.lbl_page.setStyleSheet("color:#aaa; font-size:11px;")
        tb.addWidget(self.lbl_page)

        tw = QWidget()
        tw.setLayout(tb)
        tw.setStyleSheet(
            "background:#3a3d40;"
            "QPushButton { background:#555; color:#fff; border:1px solid #666; border-radius:3px; font-size:14px; }"
            "QPushButton:hover { background:#666; }"
        )
        layout.addWidget(tw)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setAlignment(Qt.AlignCenter)
        self.scroll.setStyleSheet("background:#525659; border:none;")
        layout.addWidget(self.scroll)
        self.scroll.viewport().installEventFilter(self)

        # Debounce timer for zoom
        self._zoom_timer = QTimer(self)
        self._zoom_timer.setSingleShot(True)
        self._zoom_timer.setInterval(150)
        self._zoom_timer.timeout.connect(self._start_render)

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if obj == self.scroll.viewport() and event.type() == QEvent.Wheel:
            if event.modifiers() & Qt.ControlModifier:
                delta = -0.05 if event.angleDelta().y() < 0 else 0.05
                self._schedule_zoom(delta)
                return True
        return super().eventFilter(obj, event)

    # ===== Public API =====

    def load(self, path):
        try:
            self._doc = fitz.open(path)
        except Exception:
            return
        self._start_render()

    def close_doc(self):
        self._zoom_timer.stop()
        self._render_gen += 1
        if self._doc:
            self._doc.close()
            self._doc = None
        self._clear_container()

    # ===== Internal =====

    def _schedule_zoom(self, delta):
        self._zoom = max(0.5, min(3.0, self._zoom + delta))
        self._zoom = round(self._zoom * 100) / 100
        self.lbl_zoom.setText(f"{int(self._zoom * 100)}%")
        self._zoom_timer.start()

    def _clear_container(self):
        old = self.scroll.widget()
        if old:
            try:
                old.setParent(None)
            except RuntimeError:
                pass

    def _start_render(self):
        if not self._doc:
            return
        self._render_gen += 1
        gen = self._render_gen
        self._page_index = 0
        total = len(self._doc)

        self._clear_container()
        self._container = QWidget()
        self._clayout = QVBoxLayout(self._container)
        self._clayout.setContentsMargins(0, 8, 0, 8)
        self._clayout.setSpacing(10)
        self._clayout.setAlignment(Qt.AlignCenter)
        self.scroll.setWidget(self._container)
        self.lbl_page.setText(f"1 / {total}")

        # Render pages one at a time via timer
        self._render_next(gen)

    def _render_next(self, gen):
        """Render one page, then schedule the next via QTimer."""
        if gen != self._render_gen or not self._doc:
            return

        i = self._page_index
        if i >= len(self._doc):
            self.lbl_page.setText("")
            return

        page = self._doc[i]
        mat = fitz.Matrix(self._zoom, self._zoom)
        pix = page.get_pixmap(matrix=mat)

        # Convert via PNG for reliability (avoids stride/format issues)
        data = pix.tobytes("png")
        qpix = QPixmap()
        qpix.loadFromData(data)

        # Extract word positions
        words_data = []
        try:
            for item in page.get_text("words"):
                words_data.append((
                    item[4],
                    item[0] * self._zoom, item[1] * self._zoom,
                    (item[2] - item[0]) * self._zoom, (item[3] - item[1]) * self._zoom
                ))
        except Exception:
            pass

        pw = PdfPageWidget(qpix, words_data)
        pw.word_clicked.connect(self.word_clicked.emit)
        self._clayout.addWidget(pw)

        self._page_index += 1
        self.lbl_page.setText(f"{self._page_index + 1} / {len(self._doc)}")

        # Schedule next page (yield to event loop)
        QTimer.singleShot(0, lambda: self._render_next(gen))
