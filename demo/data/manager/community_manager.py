from fletbatteries.data import BaseManager

from data.models.community import Community


class CommunityManager(BaseManager):
    model = Community
    search_fields = ("name",)
    unique_fields = ("name",)
