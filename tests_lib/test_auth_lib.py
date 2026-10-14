"""Bloqueo por intentos, cambio y recuperación de contraseña, tokens y correo."""

import datetime

import pytest

from fletbatteries.auth.backend import AuthError, DatabaseAuthBackend, LoginAttemptManager, UserManager
from fletbatteries.auth.passwords import verify_password
from fletbatteries.forms.validators import ValidationError


def test_lockout_after_failed_attempts(admin):
    backend = DatabaseAuthBackend(max_attempts=3, lockout_minutes=10)
    for _i in range(3):
        assert backend.authenticate("root", "mala") is None
    with pytest.raises(AuthError) as info:
        backend.authenticate("root", "S3guro-root!")
    assert "10 minutos" in str(info.value)
    attempts = LoginAttemptManager().filter(username="root")
    assert [a.reason for a in attempts][:4] == ["locked", "bad_password", "bad_password", "bad_password"]
    # Al vencer la ventana vuelve a entrar y el éxito reinicia el contador
    with LoginAttemptManager().session() as s:
        from fletbatteries.auth.models import LoginAttempt

        for attempt in s.query(LoginAttempt).all():
            attempt.created_at -= datetime.timedelta(minutes=11)
    assert backend.authenticate("root", "S3guro-root!").username == "root"
    assert backend.authenticate("root", "mala") is None
    assert backend.locked_minutes("root") == 0


def test_lockout_can_be_disabled(admin):
    backend = DatabaseAuthBackend(max_attempts=None)
    for _i in range(10):
        backend.authenticate("root", "mala")
    assert backend.authenticate("root", "S3guro-root!") is not None


def test_change_password(admin):
    users = UserManager()
    with pytest.raises(ValidationError) as info:
        users.change_password(admin.id, "incorrecta", "Nueva-clave-99")
    assert set(info.value.error_dict) == {"old_password"}
    with pytest.raises(ValidationError) as info:
        users.change_password(admin.id, "S3guro-root!", "123")
    assert set(info.value.error_dict) == {"new_password"}
    users.change_password(admin.id, "S3guro-root!", "Nueva-clave-99")
    assert verify_password("Nueva-clave-99", users.get(admin.id).password)


def test_password_reset_flow(admin, outbox):
    from fletbatteries.auth.reset import PasswordResetService

    service = PasswordResetService(app_name="Lib")
    assert service.request_reset("nadie") is None and outbox == []
    code = service.request_reset("ROOT@example.com")
    assert len(code) == 6 and len(outbox) == 1
    assert outbox[0].to == ["root@example.com"] and code in outbox[0].body and "Lib" in outbox[0].subject
    with pytest.raises(ValidationError) as info:
        service.confirm_reset("root", "000000" if code != "000000" else "111111", "Otra-clave-77")
    assert set(info.value.error_dict) == {"code"}
    with pytest.raises(ValidationError) as info:
        service.confirm_reset("root", code, "Otra-clave-77", confirm="distinta")
    assert set(info.value.error_dict) == {"confirm"}
    assert service.confirm_reset("root", code, "Otra-clave-77", confirm="Otra-clave-77")
    assert DatabaseAuthBackend().authenticate("root", "Otra-clave-77") is not None
    with pytest.raises(ValidationError):  # el código ya se usó
        service.confirm_reset("root", code, "Otra-clave-88")


def test_password_reset_code_expires_and_limits_attempts(admin):
    from fletbatteries.auth.reset import PasswordResetService

    service = PasswordResetService(max_attempts=2)
    code = service.request_reset("root")
    wrong = "999999" if code != "999999" else "888888"
    for _i in range(2):
        with pytest.raises(ValidationError):
            service.confirm_reset("root", wrong, "Otra-clave-77")
    with pytest.raises(ValidationError):  # se agotaron los intentos
        service.confirm_reset("root", code, "Otra-clave-77")
    code = service.request_reset("root")
    with service.resets.session() as s:
        from fletbatteries.auth.models import PasswordReset

        for r in s.query(PasswordReset).all():
            r.expires_at = datetime.datetime.now() - datetime.timedelta(minutes=1)
    with pytest.raises(ValidationError):
        service.confirm_reset("root", code, "Otra-clave-77")


def test_api_tokens(admin):
    from fletbatteries.auth.tokens import ApiTokenManager, authenticate_token

    manager = ApiTokenManager()
    raw = manager.issue(admin.id, "script")
    assert raw.startswith("fbt_")
    token = manager.first(name="script")
    assert raw[4:12] == token.prefix and token.key_hash != raw
    assert "key_hash" not in manager.to_dict(token)
    user = authenticate_token(raw)
    assert user.username == "root" and user.is_superuser
    assert manager.get(token.id).last_used_at is not None
    assert authenticate_token("fbt_x_y") is None and authenticate_token("otro") is None
    assert manager.delete(token.id)  # borrar = revocar
    assert manager.get(token.id).revoked and authenticate_token(raw) is None
    expired = manager.issue(admin.id, "viejo", days=1)
    manager.update(manager.first(name="viejo").id, expires_at=datetime.datetime.now() - datetime.timedelta(days=1))
    assert authenticate_token(expired) is None
    UserManager().update(admin.id, is_active=False)
    assert authenticate_token(manager.issue(admin.id, "inactivo")) is None


def test_email_backends(monkeypatch):
    from fletbatteries.contrib import email

    monkeypatch.setenv("FLETBATTERIES_EMAIL_BACKEND", "smtp")
    monkeypatch.setenv("FLETBATTERIES_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("FLETBATTERIES_SMTP_PORT", "587")
    monkeypatch.setenv("FLETBATTERIES_SMTP_TLS", "1")
    monkeypatch.setenv("FLETBATTERIES_EMAIL_FROM", "App <app@example.com>")
    backend = email.email_backend_from_env()
    assert isinstance(backend, email.SMTPBackend)
    assert (backend.host, backend.port, backend.use_tls, backend.from_email) == (
        "smtp.example.com", 587, True, "App <app@example.com>")

    sent = []

    class FakeSMTP:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def send_message(self, msg, to_addrs):
            sent.append((msg, to_addrs))

    monkeypatch.setattr(backend, "connect", lambda: FakeSMTP())
    assert email.send_mail(["a@x.com"], "Hola", "texto", html="<b>hola</b>", bcc="c@x.com", backend=backend) == 1
    msg, to = sent[0]
    assert msg["From"] == "App <app@example.com>" and msg["Subject"] == "Hola" and to == ["a@x.com", "c@x.com"]
    assert msg.is_multipart()

    monkeypatch.setenv("FLETBATTERIES_EMAIL_BACKEND", "console")
    assert isinstance(email.email_backend_from_env(), email.ConsoleBackend)
    memory = email.MemoryBackend()
    assert email.send_mail([], "x", "y", backend=memory) == 0 and memory.outbox == []


async def test_send_mail_async(db, outbox):
    from fletbatteries.contrib.email import send_mail_async

    assert await send_mail_async("a@x.com", "Asunto", "Cuerpo") == 1
    assert outbox[0].subject == "Asunto"
