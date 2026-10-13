"""
Harness para probar la app Flet en proceso, sin Flutter ni display.

Usa el SDK real de Flet 1.x: crea una `Session` con una conexión falsa que
registra los mensajes enviados al cliente y responde las llamadas a métodos
del cliente (por ejemplo `push_route`). Los eventos se disparan con
`Session.dispatch_event`, igual que cuando llegan desde Flutter.
"""

import asyncio
import dataclasses
import inspect
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Iterable, Optional

import msgpack

import flet as ft
from flet.app import _context_page
from flet.controls.base_control import BaseControl
from flet.controls.dialog_control import DialogControl
from flet.messaging.connection import Connection
from flet.messaging.protocol import MessageAction, configure_encode_object_for_msgpack
from flet.messaging.session import Session
from flet.pubsub.pubsub_hub import PubSubHub

PAGE_URL = "http://127.0.0.1:8550"

# Campos de texto que se revisan al buscar controles por texto
TEXT_FIELDS = ("value", "content", "text", "label", "title", "hint_text", "tooltip", "semantics_label")


class FakeConnection(Connection):
    """Conexión en memoria que simula al cliente Flutter."""

    def __init__(self, harness: "AppHarness"):
        super().__init__()
        self.harness = harness
        self.page_url = PAGE_URL
        self.page_name = ""
        self.messages = []
        self.invocations = []

    def send_message(self, message):
        # Igual que las conexiones reales: serializar con msgpack captura los
        # snapshots que Flet usa para calcular los siguientes diffs.
        msgpack.packb(
            [message.action, message.body],
            default=configure_encode_object_for_msgpack(BaseControl),
        )
        self.messages.append(message)
        if message.action == MessageAction.INVOKE_METHOD:
            body = message.body
            self.invocations.append((body.name, body.args))
            self.loop.create_task(self.harness._reply_invoke(body))
        elif message.action == MessageAction.SESSION_CRASHED:
            self.harness.errors.append(message.body.message)


class _ErrorLogHandler(logging.Handler):
    def __init__(self, errors: list):
        super().__init__(level=logging.ERROR)
        self.errors = errors

    def emit(self, record):
        self.errors.append(self.format(record))


class AppHarness:
    """
    Ejecuta `main(page)` contra una sesión Flet en memoria.

    Uso:
        app = AppHarness(main)
        await app.start()
        await app.goto("/products")
        app.find_one(text="Products")
        await app.click(app.find_one(text="Login", type=ft.Button))
        app.assert_no_errors()
    """

    def __init__(self, main: Callable, route: str = "/", width: int = 1280, height: int = 800):
        self.main = main
        self.initial_route = route
        self.width = width
        self.height = height
        self.errors: list[str] = []
        # Respuestas para métodos del cliente: name -> callable(args) -> result
        self.client_methods: dict[str, Callable[[Any], Any]] = {}
        self.session: Optional[Session] = None
        self.conn: Optional[FakeConnection] = None
        self._log_handler = _ErrorLogHandler(self.errors)
        self._executor = ThreadPoolExecutor()
        self._prev_excepthook = None

    @property
    def page(self) -> ft.Page:
        return self.session.page

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    async def start(self):
        loop = asyncio.get_running_loop()
        self.conn = FakeConnection(self)
        self.conn.loop = loop
        self.conn.executor = self._executor
        self.conn.pubsubhub = PubSubHub(loop=loop, executor=self._executor)

        logging.getLogger("flet").addHandler(self._log_handler)
        self._prev_excepthook = threading.excepthook
        threading.excepthook = self._thread_excepthook

        self.session = Session(self.conn)
        # Lo que el cliente Flutter envía al registrarse
        self.session.apply_page_patch(
            {
                "route": self.initial_route,
                "web": False,
                "platform": "linux",
                "width": self.width,
                "height": self.height,
            }
        )
        # Respuesta de registro: se serializa para fijar la línea base de los diffs
        msgpack.packb(
            self.session.get_page_patch(),
            default=configure_encode_object_for_msgpack(BaseControl),
        )
        self.session.start_updates_scheduler()

        _context_page.set(self.page)
        try:
            if inspect.iscoroutinefunction(self.main):
                await self.main(self.page)
            else:
                self.main(self.page)
            await self.session.after_event(self.page)
        except Exception as e:  # igual que flet.app.on_session_created
            logging.getLogger("flet").error("Unhandled error in main() handler", exc_info=True)
            self.errors.append(repr(e))
        await self.settle()
        return self

    async def stop(self):
        logging.getLogger("flet").removeHandler(self._log_handler)
        if self._prev_excepthook is not None:
            threading.excepthook = self._prev_excepthook
        if self.session:
            self.session.close()
        # Deja terminar tareas pendientes (timers, loaders) sin bloquear
        await asyncio.sleep(0)
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _thread_excepthook(self, args):
        self.errors.append(f"Exception in thread {args.thread}: {args.exc_type.__name__}: {args.exc_value}")

    async def settle(self, delay: float = 0.02, rounds: int = 3):
        """Deja correr las tareas pendientes (navegación, actualizaciones)."""
        for _ in range(rounds):
            await asyncio.sleep(delay)
            await self._dismiss_closed_dialogs()

    async def _dismiss_closed_dialogs(self):
        # Flutter envía `dismiss` cuando termina de cerrar un diálogo; Flet lo
        # quita entonces de la pila de diálogos.
        for dialog in list(self.page._dialogs.controls):
            if not dialog.open:
                await self.session.dispatch_event(dialog._i, "dismiss", None)

    async def _reply_invoke(self, body):
        result, error = None, None
        try:
            if body.name == "push_route":
                route = body.args["route"]
                self.session.apply_page_patch({"route": route})
                await self.session.dispatch_event(self.page._i, "route_change", {"route": route})
            handler = self.client_methods.get(body.name)
            if handler:
                result = handler(body.args)
        except Exception as e:
            error = str(e)
        try:
            self.session.handle_invoke_method_results(body.control_id, body.call_id, result, error)
        except RuntimeError:
            # El control ya no está montado
            pass

    # ------------------------------------------------------------------
    # Navegación y eventos
    # ------------------------------------------------------------------
    async def goto(self, route: str):
        await self.page.push_route(route)
        await self.settle()

    async def trigger(self, control: BaseControl, event: str, data: Any = None):
        await self.session.dispatch_event(control._i, event, data)
        await self.settle()

    async def click(self, control: BaseControl):
        await self.trigger(control, "click")

    async def fill(self, control: BaseControl, value: str, event: str = "change"):
        """Simula que el usuario escribe en un TextField."""
        self.session.apply_patch(control._i, {"value": value})
        await self.trigger(control, event, value)

    async def select(self, control: BaseControl, value: str):
        """Simula elegir una opción en un Dropdown."""
        self.session.apply_patch(control._i, {"value": value})
        await self.trigger(control, "select", value)

    # ------------------------------------------------------------------
    # Árbol de controles
    # ------------------------------------------------------------------
    def walk(self, root: Optional[BaseControl] = None, visible_only: bool = True) -> Iterable[BaseControl]:
        """Recorre el árbol (vistas, appbar, overlay, diálogos) en orden."""
        seen = set()
        stack = [root if root is not None else self.page]
        while stack:
            ctrl = stack.pop()
            if id(ctrl) in seen:
                continue
            seen.add(id(ctrl))
            if visible_only and not is_shown(ctrl):
                continue
            yield ctrl
            stack.extend(reversed(list(children(ctrl))))

    def find(
        self,
        text: Optional[str] = None,
        type: Optional[type] = None,
        key: Optional[str] = None,
        contains: Optional[str] = None,
        where: Optional[Callable[[BaseControl], bool]] = None,
        visible_only: bool = True,
        root: Optional[BaseControl] = None,
    ) -> list[BaseControl]:
        found = []
        for ctrl in self.walk(root=root, visible_only=visible_only):
            if type is not None and not isinstance(ctrl, type):
                continue
            if key is not None and getattr(ctrl, "key", None) != key:
                continue
            if text is not None and text not in texts(ctrl):
                continue
            if contains is not None and not any(contains in t for t in texts(ctrl)):
                continue
            if where is not None and not where(ctrl):
                continue
            found.append(ctrl)
        return found

    def find_one(self, **kwargs) -> BaseControl:
        found = self.find(**kwargs)
        assert found, f"No se encontró control con {kwargs}"
        return found[0]

    def all_texts(self) -> list[str]:
        result = []
        for ctrl in self.walk():
            result.extend(texts(ctrl))
        return result

    def assert_no_errors(self):
        assert not self.errors, "Errores en la app:\n" + "\n\n".join(self.errors)


def is_shown(ctrl: BaseControl) -> bool:
    if getattr(ctrl, "visible", True) is False:
        return False
    if isinstance(ctrl, DialogControl) and not ctrl.open:
        return False
    return True


def children(ctrl: BaseControl) -> Iterable[BaseControl]:
    """Controles hijos de un control (cualquier campo que contenga controles)."""
    if not dataclasses.is_dataclass(ctrl):
        return
    for f in dataclasses.fields(ctrl):
        if f.name in ("_values", "_internals", "parent"):
            continue
        try:
            value = getattr(ctrl, f.name)
        except Exception:
            continue
        yield from _controls_in(value)


def _controls_in(value):
    if isinstance(value, BaseControl):
        yield value
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _controls_in(v)
    elif isinstance(value, dict):
        for v in value.values():
            yield from _controls_in(v)


def texts(ctrl: BaseControl) -> list[str]:
    result = []
    for name in TEXT_FIELDS:
        v = getattr(ctrl, name, None)
        if isinstance(v, str):
            result.append(v)
    return result
