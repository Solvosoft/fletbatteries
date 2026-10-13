from fletbatteries.contrib.history import HistoryMixin
from fletbatteries.contrib.trash import TrashMixin, register_trash
from fletbatteries.data import BaseManager

from data.models.note import Note


class NoteManager(HistoryMixin, TrashMixin, BaseManager):
    model = Note
    search_fields = ("title", "content", "category")
    default_order = "-id"


register_trash(NoteManager(), "Notas")
