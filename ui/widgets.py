# ui/widgets.py
from PyQt6.QtWidgets import QLabel, QTextEdit, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent


class DragDropArea(QLabel):
    """A custom QLabel that accepts drag and drop for files."""

    filesDropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("Drag & Drop .epub Files Here\nor\nClick 'Browse' to Select Files")
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            DragDropArea {
                border: 2px dashed #aaa;
                border-radius: 15px;
                background-color: #f0f0f0;
                color: #555;
                font-size: 16px;
                font-style: italic;
            }
            DragDropArea[is_active="true"] {
                background-color: #e0eafc;
                border-color: #6a8dcd;
            }
        """)
        self.setProperty("is_active", False)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("is_active", True)
            self.style().polish(self)  # Refresh style
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("is_active", False)
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent):
        self.setProperty("is_active", False)
        self.style().polish(self)

        urls = event.mimeData().urls()
        file_paths = [url.toLocalFile() for url in urls if url.isLocalFile()]

        # Filter for .epub files
        epub_files = [path for path in file_paths if path.lower().endswith(".epub")]
        if epub_files:
            self.filesDropped.emit(epub_files)


class LogPanel(QTextEdit):
    """A simple read-only QTextEdit for logging messages."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #f0f0f0;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 13px;
                border-radius: 5px;
            }
        """)

    def add_log(self, message):
        self.append(message)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
