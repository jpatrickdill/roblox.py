import logging

import maya
from async_property import async_property, async_cached_property

from roblox.asset import Asset
from roblox.http import Session

log = logging.getLogger(__name__)


class Place(Asset):
    __slots__ = ("_data", "_state")

    def __init__(self, *, state, data):
        super().__init__(state=state, data=data)

        self._data.update({
            "isplayable": None,
            "universeid": None,
            "reasonprohibited": None,
            "imageToken": None,
            "universerootplaceid": None,
            "url": None
        })

        self._update(data)

    def __repr__(self):
        return "Place({!r})".format(self._data["name"] or self._data["id"])

    async def _get_place_details(self):
        details = (await self._state.get_place_details(await self.id))[0]
        self._update(details)

    @async_property
    async def universe(self):
        if self._data["universeid"] is None:
            await self._get_place_details()

        return Universe(state=self._state, data={"id": self._data["universeid"]})

    game = universe

    @async_property
    async def url(self):
        if self._data["url"] is None:
            await self._get_place_details()

        return self._data["url"]


# util decorator
def g_info(name, nocache=False):
    """This decorator will check if the property is in the game's _data, and if it isn't send a request to the
    Games API endpoint"""

    def decorator(fn):
        async def new_fn(self):
            if nocache or self._data[name] is None:
                await self._get_game_details()

            return self._data[name]

        return new_fn

    return decorator


class Universe:
    __slots__ = ("_data", "_state")

    def __init__(self, *, state: Session, data):
        self._state = state
        self._data = {
            "name": None,
            "description": None,
            "id": None,
            "rootplaceid": None,
            "created": None,
            "updated": None,
            "price": None,
            "sales": None,
            "creator": None,
            "allowedgearcategories": None,
            "playing": None,
            "visits": None,
            "maxplayers": None,
            "studioaccesstoapisallowed": None,
            "createvipserversallowed": None,
            "universeavatartype": None,
            "genre": None
        }

        self._update(data)

    def __repr__(self):
        return "Universe({!r})".format(self._data["name"] or self._data["id"])

    def _update(self, data):
        for k in list(data.keys()):
            data[k.lower()] = data[k]

        self._data.update(**data)

    async def _get_game_details(self):
        details = (await self._state.get_game_details(await self.id))["data"][0]
        self._update(details)

    @async_property
    async def id(self):
        return self._data["id"]

    @async_property
    @g_info("name")
    async def name(self):
        pass

    @async_property
    @g_info("description")
    async def description(self):
        pass

    @async_property
    async def created_at(self):
        if self._data["created"] is None:
            await self._get_game_details()

        try:
            return maya.parse(self._data["created"]).datetime()
        except OSError:
            return None

    @async_cached_property
    async def updated_at(self):
        if self._data["updated"] is None:
            await self._get_game_details()

        try:
            return maya.parse(self._data["updated"]).datetime()
        except OSError:
            return None

    @async_property
    async def creator(self):
        if self._data["creator"] is None:
            await self._get_game_details()

        creator = self._data["creator"]
        if creator.get("type") == "User":
            return await self._state.client.get_user(username=creator["name"])

    @async_property
    async def root_place(self):
        if self._data["rootplaceid"] is None:
            await self._get_game_details()

        return await self._state.client.get_asset(self._data["rootplaceid"])

    @async_property
    async def url(self):
        return await (await self.root_place).url

    @async_property
    @g_info("visits", nocache=True)
    async def visits(self):
        pass

    @async_property
    @g_info("playing", nocache=True)
    async def playing(self):
        pass

    @async_property
    @g_info("maxplayers", nocache=True)
    async def max_players(self):
        pass
