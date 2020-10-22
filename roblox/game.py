import logging

import maya
from CaseInsensitiveDict import CaseInsensitiveDict
from async_property import async_property, async_cached_property

from roblox.abc import Server as _BaseServer
from roblox.abc import Universe as _BaseUniverse
from roblox.asset import Asset
from roblox.enums import ServerType
from roblox.http import Session
from roblox.iterables import AsyncIterator

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

    def servers(self, server_type: ServerType = None):
        server_type = server_type or ServerType.Public

        return ServersIterator(state=self._state, opts={
            "place": self,
            "type": server_type.value
        })


class ServersIterator(AsyncIterator):
    async def __aiter__(self):
        async for server_data in self._state.get_game_servers(await self._opts["place"].id, self._opts["type"]):
            yield Server(state=self._state, data=server_data, place=self._opts["place"])


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


class Universe(_BaseUniverse):
    __slots__ = ("_data", "_state")

    def __init__(self, *, state: Session, data):
        self._state = state
        self._data = CaseInsensitiveDict({
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
        })

        self._update(data)

    def __repr__(self):
        return "Universe({!r})".format(self._data["name"] or self._data["id"])

    def __hash__(self):
        return hash(self._data["id"] or -1)

    def _update(self, data):
        for k in list(data.keys()):
            data[k.lower()] = data[k]

        self._data.update(data)

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

    @property
    async def is_favorited(self) -> bool:
        data = await self._state.universe_favorited(await self.id)
        return data.get("isFavorited")

    async def favorite(self):
        await self._state.favorite_universe(await self.id, True)
        return True

    async def unfavorite(self):
        await self._state.favorite_universe(await self.id, False)
        return True

    @property
    async def favorites(self) -> int:
        data = await self._state.universe_favorites(await self.id)
        return data.get("favoritesCount")


class Server(_BaseServer):
    def __init__(self, *, state: Session, data, place: Place):
        self._state = state
        self._data = CaseInsensitiveDict({
            "id": None,
            "maxplayers": None,
            "playing": None,
            "fps": None,
            "ping": None,
            "name": None,
            "playerids": None,
            "vipserverid": None,
            "accesscode": None,
            "owneruserid": None
        })
        self.place = place

        self._update(data)

    def __repr__(self):
        if self._data.get("vipserverid"):
            return "PrivateServer({!r}, {!r})".format(self.place, self._data.get("name"))
        else:
            return "Server({!r}, {!r})".format(self.place, self._data.get("id"))

    def _update(self, data):
        for k in list(data.keys()):
            data[k.lower()] = data[k]

        self._data.update(data)

    @async_property
    async def id(self) -> str:
        return self._data.get("id")

    @async_property
    async def name(self) -> str:
        return self._data.get("name")

    @async_property
    async def playing(self) -> int:
        return self._data.get("playing") or 0

    @async_property
    async def max_players(self) -> int:
        return self._data.get("maxplayers")

    @async_property
    async def access_code(self) -> str:
        return self._data.get("accesscode")

    @async_property
    async def server_type(self) -> ServerType:
        return ServerType.Public if self._data.get("vipserverid") is None else ServerType.Private

    async def update_stats(self):
        """Searches for server in the game's server list in order to update the stats."""

        async for data in self._state.get_game_servers(await self.place.id, (await self.server_type).value):
            if "accessCode" in data and data["accessCode"] == await self.access_code:
                self._update(data)
                return
            elif "id" in data and data["id"] == await self.id:
                self._update(data)
                return
