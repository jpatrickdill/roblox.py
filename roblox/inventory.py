import logging

from roblox.asset import Asset
from roblox.enums import AssetType
from roblox.http import Session

log = logging.getLogger(__name__)


class Inventory:
    __slots__ = ("_state", "user")

    def __init__(self, *, state: Session, user):
        self._state = state
        self.user = user

    def __repr__(self):
        return repr(self.user) + ".inventory"

    async def by_type(self, asset_type):
        async for data in self._state.inventory_by_type(await self.user.id, int(asset_type)):
            yield Asset(state=self._state, data=data)

    async def __aiter__(self):
        for a_type in AssetType:
            async for asset in self.by_type(a_type):
                yield asset

    async def contains(self, asset):
        pass
