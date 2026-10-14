"""
Envío de correos con backends intercambiables.

    from fletbatteries.contrib.email import send_mail, configure_email, SMTPBackend

    configure_email(SMTPBackend(host="smtp.example.com", port=587, username="app", password="...",
                                use_tls=True, from_email="App <no-reply@example.com>"))
    send_mail("ana@example.com", "Hola", "Texto plano", html="<b>HTML</b>")
    await send_mail_async(...)      # desde un handler async (no bloquea la UI)

Sin configuración se usa el backend que indique la variable de entorno
`FLETBATTERIES_EMAIL_BACKEND` (`console` por defecto, `smtp` o `memory`):

    FLETBATTERIES_EMAIL_BACKEND=smtp
    FLETBATTERIES_SMTP_HOST=smtp.example.com     FLETBATTERIES_SMTP_PORT=587
    FLETBATTERIES_SMTP_USER=...                  FLETBATTERIES_SMTP_PASSWORD=...
    FLETBATTERIES_SMTP_TLS=1                     FLETBATTERIES_SMTP_SSL=0
    FLETBATTERIES_EMAIL_FROM="App <no-reply@example.com>"

`MemoryBackend` guarda los mensajes en `outbox` (útil en pruebas).
"""

import asyncio
import dataclasses
import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Iterable, Optional, Union

log = logging.getLogger(__name__)

DEFAULT_FROM = "webmaster@localhost"


@dataclasses.dataclass
class Message:
    to: list[str]
    subject: str
    body: str
    html: Optional[str] = None
    from_email: Optional[str] = None
    cc: list[str] = dataclasses.field(default_factory=list)
    bcc: list[str] = dataclasses.field(default_factory=list)
    reply_to: Optional[str] = None

    def to_email_message(self, default_from: str) -> EmailMessage:
        msg = EmailMessage()
        msg["Subject"] = self.subject
        msg["From"] = self.from_email or default_from
        msg["To"] = ", ".join(self.to)
        if self.cc:
            msg["Cc"] = ", ".join(self.cc)
        if self.reply_to:
            msg["Reply-To"] = self.reply_to
        msg.set_content(self.body)
        if self.html:
            msg.add_alternative(self.html, subtype="html")
        return msg

    @property
    def recipients(self) -> list[str]:
        return [*self.to, *self.cc, *self.bcc]


class EmailBackend:
    def __init__(self, from_email: Optional[str] = None):
        self.from_email = from_email or os.environ.get("FLETBATTERIES_EMAIL_FROM") or DEFAULT_FROM

    def send(self, messages: Iterable[Message]) -> int:
        """Envía los mensajes y devuelve cuántos se enviaron."""
        raise NotImplementedError


class ConsoleBackend(EmailBackend):
    """Escribe los correos en el log (desarrollo)."""

    def send(self, messages):
        count = 0
        for message in messages:
            log.info("Correo para %s: %s\n%s", ", ".join(message.recipients), message.subject, message.body)
            count += 1
        return count


class MemoryBackend(EmailBackend):
    """Guarda los correos en `outbox` (pruebas)."""

    def __init__(self, from_email: Optional[str] = None):
        super().__init__(from_email)
        self.outbox: list[Message] = []

    def send(self, messages):
        messages = list(messages)
        for message in messages:
            message.from_email = message.from_email or self.from_email
        self.outbox.extend(messages)
        return len(messages)


class SMTPBackend(EmailBackend):
    def __init__(self, host: str = "localhost", port: int = 25, username: Optional[str] = None,
                 password: Optional[str] = None, use_tls: bool = False, use_ssl: bool = False,
                 timeout: Optional[float] = 30, from_email: Optional[str] = None):
        super().__init__(from_email)
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.timeout = timeout

    def connect(self) -> smtplib.SMTP:
        if self.use_ssl:
            conn = smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout, context=ssl.create_default_context())
        else:
            conn = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            if self.use_tls:
                conn.starttls(context=ssl.create_default_context())
        if self.username:
            conn.login(self.username, self.password or "")
        return conn

    def send(self, messages):
        messages = list(messages)
        if not messages:
            return 0
        count = 0
        with self.connect() as conn:
            for message in messages:
                email = message.to_email_message(self.from_email)
                conn.send_message(email, to_addrs=message.recipients)
                count += 1
        return count


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    return default if value is None else value.strip().lower() in ("1", "true", "yes", "on")


def email_backend_from_env() -> EmailBackend:
    """Backend según `FLETBATTERIES_EMAIL_BACKEND` (`console`, `smtp` o `memory`)."""
    kind = (os.environ.get("FLETBATTERIES_EMAIL_BACKEND") or "console").strip().lower()
    if kind == "smtp":
        return SMTPBackend(
            host=os.environ.get("FLETBATTERIES_SMTP_HOST", "localhost"),
            port=int(os.environ.get("FLETBATTERIES_SMTP_PORT", "25")),
            username=os.environ.get("FLETBATTERIES_SMTP_USER") or None,
            password=os.environ.get("FLETBATTERIES_SMTP_PASSWORD") or None,
            use_tls=_env_bool("FLETBATTERIES_SMTP_TLS"),
            use_ssl=_env_bool("FLETBATTERIES_SMTP_SSL"),
        )
    if kind == "memory":
        return MemoryBackend()
    return ConsoleBackend()


_backend: Optional[EmailBackend] = None


def configure_email(backend: Optional[EmailBackend]):
    """Define el backend de correo del proceso (`None` vuelve a leerlo del entorno)."""
    global _backend
    _backend = backend


set_email_backend = configure_email


def get_email_backend() -> EmailBackend:
    global _backend
    if _backend is None:
        _backend = email_backend_from_env()
    return _backend


def _as_list(value: Union[str, Iterable[str], None]) -> list[str]:
    if not value:
        return []
    return [value] if isinstance(value, str) else [v for v in value if v]


def send_mail(to: Union[str, Iterable[str]], subject: str, body: str, html: Optional[str] = None,
              from_email: Optional[str] = None, cc=None, bcc=None, reply_to: Optional[str] = None,
              backend: Optional[EmailBackend] = None) -> int:
    message = Message(to=_as_list(to), subject=subject, body=body, html=html, from_email=from_email,
                      cc=_as_list(cc), bcc=_as_list(bcc), reply_to=reply_to)
    if not message.recipients:
        return 0
    return (backend or get_email_backend()).send([message])


async def send_mail_async(*args, **kwargs) -> int:
    """`send_mail` en un hilo aparte, para no bloquear la interfaz."""
    return await asyncio.to_thread(send_mail, *args, **kwargs)


__all__ = [
    "Message",
    "EmailBackend",
    "ConsoleBackend",
    "MemoryBackend",
    "SMTPBackend",
    "configure_email",
    "set_email_backend",
    "get_email_backend",
    "email_backend_from_env",
    "send_mail",
    "send_mail_async",
]
