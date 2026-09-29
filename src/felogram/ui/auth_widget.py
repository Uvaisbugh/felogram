from __future__ import annotations

import os
from collections.abc import Callable
from html import escape

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from felogram.application.auth import AuthInputError, AuthRequestFactory
from felogram.security import SecretStoreError
from felogram.telegram.runtime import RuntimeCommand
from felogram.telegram.transport import JsonObject


class AuthWidget(QWidget):
    """Present the input requested by the current TDLib authorization state."""

    command_submitted = Signal(object)
    input_error = Signal(str)

    def __init__(
        self,
        request_factory: AuthRequestFactory | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._requests = request_factory or AuthRequestFactory()
        self._pages = QStackedWidget()
        self._pages.setObjectName("authPages")

        self._waiting_page = self._message_page("authWaitingPage", "Connecting to Telegram…")
        self._api_page = self._build_api_page()
        self._phone_page = self._build_phone_page()
        self._code_page = self._build_code_page()
        self._password_page = self._build_password_page()
        self._email_page = self._build_email_page()
        self._email_code_page = self._build_email_code_page()
        self._registration_page = self._build_registration_page()
        self._device_page = self._build_device_page()
        self._premium_page = self._message_page(
            "authPremiumPage",
            "Telegram requires a Premium purchase before this account can continue.",
        )
        self._ready_page = self._message_page("authReadyPage", "Signed in. Messaging comes next.")
        self._unsupported_page = self._message_page(
            "authUnsupportedPage", "Telegram needs an authorization step Felogram cannot show yet."
        )

        for page in (
            self._waiting_page,
            self._api_page,
            self._phone_page,
            self._code_page,
            self._password_page,
            self._email_page,
            self._email_code_page,
            self._registration_page,
            self._device_page,
            self._premium_page,
            self._ready_page,
            self._unsupported_page,
        ):
            self._pages.addWidget(page)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.addWidget(self._pages)

    def handle_authorization(self, state: JsonObject) -> None:
        raw_state_type = state.get("@type")
        state_type = raw_state_type if isinstance(raw_state_type, str) else ""
        page = {
            "authorizationStateWaitTdlibParameters": self._api_page,
            "authorizationStateWaitPhoneNumber": self._phone_page,
            "authorizationStateWaitCode": self._code_page,
            "authorizationStateWaitPassword": self._password_page,
            "authorizationStateWaitEmailAddress": self._email_page,
            "authorizationStateWaitEmailCode": self._email_code_page,
            "authorizationStateWaitRegistration": self._registration_page,
            "authorizationStateWaitOtherDeviceConfirmation": self._device_page,
            "authorizationStateWaitPremiumPurchase": self._premium_page,
            "authorizationStateReady": self._ready_page,
        }.get(state_type, self._unsupported_page)

        if state_type in {
            "authorizationStateClosing",
            "authorizationStateClosed",
            "authorizationStateLoggingOut",
        }:
            page = self._waiting_page

        if state_type == "authorizationStateWaitPassword":
            hint = state.get("password_hint")
            self._password_hint.setText(
                f"Hint: {hint}"
                if isinstance(hint, str) and hint
                else "Two-step verification is enabled."
            )
        elif state_type == "authorizationStateWaitOtherDeviceConfirmation":
            link = state.get("link")
            self._device_link.setText(
                f'<a href="{escape(link, quote=True)}">{escape(link)}</a>'
                if isinstance(link, str) and link
                else "Open Telegram on another signed-in device to confirm this login."
            )

        self._pages.setCurrentWidget(page)

    @staticmethod
    def friendly_state(state_type: str) -> str:
        return {
            "authorizationStateWaitTdlibParameters": "Enter your Telegram API credentials",
            "authorizationStateWaitPhoneNumber": "Enter your Telegram phone number",
            "authorizationStateWaitCode": "Enter the code Telegram sent you",
            "authorizationStateWaitPassword": "Enter your two-step verification password",
            "authorizationStateWaitEmailAddress": "Telegram requires an email address",
            "authorizationStateWaitEmailCode": "Enter the code sent to your email",
            "authorizationStateWaitRegistration": "Finish creating your Telegram account",
            "authorizationStateWaitOtherDeviceConfirmation": "Confirm this login on another device",
            "authorizationStateWaitPremiumPurchase": "Telegram requires Premium to continue",
            "authorizationStateReady": "Signed in to Telegram",
            "authorizationStateLoggingOut": "Signing out…",
            "authorizationStateClosing": "Closing Telegram session…",
            "authorizationStateClosed": "Telegram session closed",
        }.get(state_type, f"Telegram authorization: {state_type}")

    def _build_api_page(self) -> QWidget:
        page, form = self._form_page(
            "authApiPage",
            "Connect Felogram",
            "Create an app at my.telegram.org, then enter its API ID and API hash.",
        )
        self._api_id = QLineEdit(os.environ.get("TELEGRAM_API_ID", ""))
        self._api_id.setObjectName("apiIdInput")
        self._api_id.setPlaceholderText("API ID")
        self._api_hash = QLineEdit(os.environ.get("TELEGRAM_API_HASH", ""))
        self._api_hash.setObjectName("apiHashInput")
        self._api_hash.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_hash.setPlaceholderText("32-character API hash")
        form.addRow("API ID", self._api_id)
        form.addRow("API hash", self._api_hash)
        self._add_button(
            form,
            "Continue",
            self._submit_api,
        )
        return page

    def _build_phone_page(self) -> QWidget:
        page, form = self._form_page(
            "authPhonePage", "Phone number", "Include the country code, such as +91."
        )
        self._phone = QLineEdit()
        self._phone.setObjectName("phoneInput")
        self._phone.setPlaceholderText("+919876543210")
        form.addRow("Phone", self._phone)
        self._add_button(
            form, "Send code", lambda: self._submit(self._requests.phone, self._phone.text())
        )
        return page

    def _build_code_page(self) -> QWidget:
        page, form = self._form_page(
            "authCodePage", "Authentication code", "Check Telegram on your other devices or SMS."
        )
        self._code = QLineEdit()
        self._code.setObjectName("codeInput")
        self._code.setInputMethodHints(Qt.InputMethodHint.ImhDigitsOnly)
        form.addRow("Code", self._code)
        self._add_button(
            form, "Verify", lambda: self._submit_and_clear(self._requests.code, self._code)
        )
        return page

    def _build_password_page(self) -> QWidget:
        page, form = self._form_page("authPasswordPage", "Two-step verification", "")
        self._password_hint = QLabel("Two-step verification is enabled.")
        self._password_hint.setWordWrap(True)
        form.addRow(self._password_hint)
        self._password = QLineEdit()
        self._password.setObjectName("passwordInput")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Password", self._password)
        self._add_button(
            form,
            "Verify",
            lambda: self._submit_and_clear(self._requests.password, self._password),
        )
        return page

    def _build_email_page(self) -> QWidget:
        page, form = self._form_page(
            "authEmailPage", "Email address", "Telegram will send a verification code here."
        )
        self._email = QLineEdit()
        self._email.setObjectName("emailInput")
        self._email.setInputMethodHints(Qt.InputMethodHint.ImhEmailCharactersOnly)
        form.addRow("Email", self._email)
        self._add_button(
            form, "Send code", lambda: self._submit(self._requests.email, self._email.text())
        )
        return page

    def _build_email_code_page(self) -> QWidget:
        page, form = self._form_page(
            "authEmailCodePage", "Email verification", "Enter the code Telegram sent to your email."
        )
        self._email_code = QLineEdit()
        self._email_code.setObjectName("emailCodeInput")
        form.addRow("Code", self._email_code)
        self._add_button(
            form,
            "Verify",
            lambda: self._submit_and_clear(self._requests.email_code, self._email_code),
        )
        return page

    def _build_registration_page(self) -> QWidget:
        page, form = self._form_page(
            "authRegistrationPage", "Create your Telegram account", "Tell Telegram your name."
        )
        self._first_name = QLineEdit()
        self._first_name.setObjectName("firstNameInput")
        self._last_name = QLineEdit()
        self._last_name.setObjectName("lastNameInput")
        form.addRow("First name", self._first_name)
        form.addRow("Last name", self._last_name)
        self._add_button(
            form,
            "Create account",
            lambda: self._submit(
                self._requests.registration, self._first_name.text(), self._last_name.text()
            ),
        )
        return page

    def _build_device_page(self) -> QWidget:
        page, layout = self._plain_page("authDevicePage", "Confirm on another device")
        self._device_link = QLabel()
        self._device_link.setWordWrap(True)
        self._device_link.setOpenExternalLinks(True)
        self._device_link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        layout.addWidget(self._device_link)
        layout.addStretch()
        return page

    def _submit(self, factory: Callable[..., RuntimeCommand], *values: str) -> None:
        try:
            command = factory(*values)
        except (AuthInputError, SecretStoreError) as exc:
            self.input_error.emit(str(exc))
            return
        self.command_submitted.emit(command)

    def _submit_api(self) -> None:
        try:
            command = self._requests.configure(self._api_id.text(), self._api_hash.text())
        except (AuthInputError, SecretStoreError) as exc:
            self.input_error.emit(str(exc))
            return
        self._api_hash.clear()
        self.command_submitted.emit(command)

    def _submit_and_clear(self, factory: Callable[[str], RuntimeCommand], field: QLineEdit) -> None:
        try:
            command = factory(field.text())
        except (AuthInputError, SecretStoreError) as exc:
            self.input_error.emit(str(exc))
            return
        field.clear()
        self.command_submitted.emit(command)

    @staticmethod
    def _form_page(name: str, title: str, description: str) -> tuple[QWidget, QFormLayout]:
        page = QWidget()
        page.setObjectName(name)
        layout = QFormLayout(page)
        heading = QLabel(title)
        heading.setObjectName("authHeading")
        layout.addRow(heading)
        if description:
            detail = QLabel(description)
            detail.setWordWrap(True)
            layout.addRow(detail)
        return page, layout

    @staticmethod
    def _plain_page(name: str, title: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        page.setObjectName(name)
        layout = QVBoxLayout(page)
        heading = QLabel(title)
        heading.setObjectName("authHeading")
        layout.addWidget(heading)
        return page, layout

    @classmethod
    def _message_page(cls, name: str, message: str) -> QWidget:
        page, layout = cls._plain_page(name, message)
        layout.addStretch()
        return page

    @staticmethod
    def _add_button(form: QFormLayout, text: str, callback: Callable[[], None]) -> None:
        button = QPushButton(text)
        button.clicked.connect(callback)
        form.addRow(button)
