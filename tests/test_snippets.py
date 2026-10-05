from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

from felogram.application.snippets import format_snippet
from felogram.ui.snippet_widget import SnippetWidget


def test_snippet_preserves_code_and_escapes_embedded_fences() -> None:
    code = "  print('```')\n\n"
    assert format_snippet(code, " python ") == "````python\n" + code + "````"


@pytest.mark.parametrize("code, language", [("  ", ""), ("x", "python\n```")])
def test_invalid_snippet_is_rejected(code: str, language: str) -> None:
    with pytest.raises(ValueError):
        format_snippet(code, language)


def test_copy_requires_valid_code_and_updates_clipboard(qtbot: QtBot) -> None:
    widget = SnippetWidget()
    qtbot.addWidget(widget)
    QApplication.clipboard().setText("existing")
    widget.copy_button.click()
    assert QApplication.clipboard().text() == "existing"
    widget.language.setText("rust")
    widget.code.setPlainText("fn main() {}")
    widget.copy_button.click()
    assert QApplication.clipboard().text() == "```rust\nfn main() {}\n```"
