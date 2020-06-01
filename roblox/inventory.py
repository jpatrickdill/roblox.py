import logging
from roblox.iterables import AsyncIterator
from roblox.asset import Asset
from roblox.enums import AssetType
from roblox.http import Session

log = logging.getLogger(__name__)


class Inventory(AsyncIterator):
    """
    Async Iterator for a user's inventory. You can iterate over this using the ``async for`` syntax::

        async for item in this_iterator:
            print(item)

    Yields:
        :class:`.Asset`
    """

    def __repr__(self):
        return repr(self._opts["user"]) + ".inventory"

    async def __aiter__(self):
        for a_type in AssetType:
            async for asset in self.by_type(a_type):
                yield asset

    def by_type(self, asset_type):
        """
        :class:`.AsyncIterator` that yields the assets of a specific type in a user's inventory.

        Yields:
            :class:`.Asset`
        """

        if isinstance(asset_type, str):
            n_asset_type = getattr(AssetType, asset_type)
            if n_asset_type is None:
                raise ValueError("Asset type {!r} not recognized. Use AssetType enum.".format(n_asset_type))
            asset_type = n_asset_type

        async def gen():
            async for data in self._state.inventory_by_type(await self._opts["user"].id, int(asset_type)):
                yield Asset(state=self._state, data=data)

        return AsyncIterator(gen=gen(), state=self._state)

    async def has(self, asset) -> bool:
        a_id = asset if isinstance(asset, int) else await asset.id
        return await self._state.has_asset(await self._opts["user"].id, a_id)
