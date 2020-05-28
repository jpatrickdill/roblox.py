import logging

import maya
from async_property import async_property, async_cached_property

from roblox.enums import AssetType
from roblox.errors import *
from roblox.http import Session

log = logging.getLogger(__name__)


# util decorator
def p_info(name, nocache=False):
    """This decorator will check if the property is in the asset's _data, and if it isn't send a request to the
    ProductInfo API endpoint"""

    def decorator(fn):
        async def new_fn(self):
            if nocache or self._data[name] is None:
                await self._get_product_info()

            return self._data[name]

        return new_fn
    return decorator


class Asset:
    __slots__ = ("_data", "_state")

    def __init__(self, *, state: Session, data):
        self._state = state
        self._data = {
            "name": None,
            "description": None,
            "id": None,
            "productid": None,
            "created": None,
            "updated": None,
            "price": None,
            "assettypeid": None,
            "sales": None,
            "isforsale": None,
            "ispublicdomain": None,
            "islimited": None,
            "islimitedunique": None,
            "remaining": None,
            "serialnumber": None,
            "creator": None
        }

        self._update(data)

    def __repr__(self):
        return "Asset({!r})".format(self._data["name"] or self._data["id"])

    def __hash__(self):
        return self._data["id"] or -2

    def __eq__(self, other):
        if not isinstance(other, Asset):
            return False

        return self._data["id"] == other._data["id"]

    def _update(self, data: dict):
        for k in list(data.keys()):
            data[k.lower()] = data[k]

        data.setdefault("price", data.get("priceinrobux"))
        data.setdefault("id", data.get("assetid"))
        data.setdefault("name", data.get("assetname"))

        self._data.update(data)

    async def _get_product_info(self):
        data = await self._state.product_info(self._data["id"])
        self._update(data)

    @async_property
    @p_info("name")
    async def name(self):
        pass

    @async_property
    @p_info("description")
    async def description(self):
        pass

    @async_property
    @p_info("id")
    async def id(self):
        pass

    @async_property
    async def type(self):
        if self._data["assettypeid"] is None:
            await self._get_product_info()

        return AssetType(self._data["assettypeid"])

    @async_property
    @p_info("productid")
    async def product_id(self):
        pass

    @async_property
    async def created_at(self):
        if self._data["created"] is None:
            await self._get_product_info()

        try:
            return maya.parse(self._data["created"]).datetime()
        except OSError:
            return None

    @async_cached_property
    async def updated_at(self):
        if self._data["updated"] is None:
            await self._get_product_info()

        try:
            return maya.parse(self._data["updated"]).datetime()
        except OSError:
            return None

    @async_property
    @p_info("price", nocache=True)
    async def price(self):
        pass

    @async_property
    @p_info("sales", nocache=True)
    async def sales(self):
        pass

    @async_property
    async def for_sale(self):
        if self._data["isforsale"] is None and self._data["ispublicdomain"] is None:
            await self._get_product_info()

        return self._data["isforsale"] or self._data["ispublicdomain"]

    @async_property
    async def creator(self):
        if self._data["creator"] is None:
            await self._get_product_info()

        creator = self._data["creator"]
        if creator.get("CreatorType") == "User":
            return await self._state.client.get_user(username=creator["Name"])

    @async_property
    async def favorites(self):
        return await self._state.favorites_count(await self.id)

    @async_property
    async def is_favorited(self):
        model = await self._state.favorite_model(await self._state.client.user.id, await self.id)

        return False if model is None else True

    async def favorite(self):
        return await self._state.create_favorite(await self._state.client.user.id, await self.id)

    async def unfavorite(self):
        return await self._state.delete_favorite(await self._state.client.user.id, await self.id)

    async def toggle_favorite(self):
        if await self.is_favorited:
            return await self.unfavorite()
        else:
            return await self.favorite()

    async def purchase(self, expected_price=None):
        expected_price = expected_price or await self.price
        expected_seller = await (await self.creator).id

        return await self._state.purchase_product(await self.product_id, expected_price, expected_seller)

    async def download(self, path):
        file = open(path, "wb")
        await self._state.download_asset(await self.id, file)
        file.close()
