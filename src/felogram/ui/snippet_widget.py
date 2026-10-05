from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from felogram.application.snippets import format_snippet


class SnippetWidget(QWidget):
    """An offline developer tool; copying never sends a Telegram message."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        description = QLabel(
            "Prepare a Markdown code snippet for a message draft. "
            "Runs locally and works before login."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        self.language = QLineEdit()
        self.language.setPlaceholderText("Language (optional): python, typescript, rust…")
        self.language.setAccessibleName("Snippet language")
        layout.addWidget(self.language)
        self.code = QPlainTextEdit()
        self.code.setPlaceholderText("Paste your code here")
        self.code.setAccessibleName("Snippet code")
        layout.addWidget(self.code)
        self.copy_button = QPushButton("Copy Markdown snippet")
        self.copy_button.clicked.connect(self._copy)
        layout.addWidget(self.copy_button)
        self.feedback = QLabel("Nothing is sent to Telegram by this tool.")
        self.feedback.setWordWrap(True)
        layout.addWidget(self.feedback)

    def _copy(self) -> None:
        try:
            snippet = format_snippet(self.code.toPlainText(), self.language.text())
        except ValueError as exc:
            self.feedback.setText(str(exc))
            return
        QApplication.clipboard().setText(snippet)
        self.feedback.setText("Copied. Paste into a draft that supports Markdown fences.")
